from __future__ import annotations

import argparse
import dataclasses
import json
from pathlib import Path
from typing import Any

from . import paths
from .schema import load_harvest_policy, load_schema
from .utils import now_kst, write_text


SUPPORTED_SUFFIXES = {".md", ".txt"}
UNKNOWN_TYPE = "unknown"


@dataclasses.dataclass
class RawFile:
    path: Path
    rel: str
    existing_type: str | None
    base_name: str
    supported: bool


@dataclasses.dataclass
class Classification:
    source: str
    suggested_type: str
    confidence: str
    reason: str


@dataclasses.dataclass
class TagResult:
    action: str
    source: str
    suggested_type: str
    confidence: str
    planned_action: str
    final_path: str | None
    reason: str


def _rel(path: Path) -> str:
    return paths.repository_rel(path)


def _report_path(run_id: str) -> Path:
    return paths.ROOT / ".harness-helm" / "runs" / "_unscoped" / run_id / "harvest-tag-report.md"


def _staging_root(policy: dict[str, Any]) -> Path:
    staging = policy.get("staging", {})
    rel = staging.get("path", "docs/_harvest-inbox") if isinstance(staging, dict) else "docs/_harvest-inbox"
    return paths.resolve_under_root(str(rel), paths.ROOT, "staging.path")


def _raw_root(policy: dict[str, Any]) -> Path:
    return _staging_root(policy) / "raw"


def _type_by_subfolder(policy: dict[str, Any]) -> dict[str, str]:
    staging = policy.get("staging", {})
    values = staging.get("type_by_subfolder", {}) if isinstance(staging, dict) else {}
    return {str(key): str(value) for key, value in values.items()} if isinstance(values, dict) else {}


def _types(policy: dict[str, Any]) -> set[str]:
    return set(_type_by_subfolder(policy).values())


def _subfolder_by_type(policy: dict[str, Any]) -> dict[str, str]:
    return {dtype: folder for folder, dtype in _type_by_subfolder(policy).items()}


def _strip_prefix(name: str, prefixes: set[str]) -> tuple[str | None, str]:
    for prefix in sorted(prefixes | {UNKNOWN_TYPE}, key=len, reverse=True):
        marker = f"{prefix}_"
        if name.startswith(marker):
            return prefix, name[len(marker) :]
    return None, name


def _scan_raw(policy: dict[str, Any]) -> list[RawFile]:
    raw = _raw_root(policy)
    if not raw.exists():
        return []
    prefixes = _types(policy)
    items: list[RawFile] = []
    for path in sorted(raw.iterdir()):
        if not path.is_file() or path.name == ".gitkeep":
            continue
        existing_type, base_name = _strip_prefix(path.name, prefixes)
        items.append(
            RawFile(
                path=path,
                rel=_rel(path),
                existing_type=existing_type,
                base_name=base_name,
                supported=path.suffix in SUPPORTED_SUFFIXES,
            )
        )
    return items


def raw_warning_counts(policy: dict[str, Any]) -> tuple[int, int]:
    unclassified = 0
    review_pending = 0
    for item in _scan_raw(policy):
        if not item.supported:
            continue
        if item.existing_type:
            review_pending += 1
        else:
            unclassified += 1
    return unclassified, review_pending


def _resolve_classification_path(value: str) -> Path:
    raw = Path(value)
    return raw.resolve() if raw.is_absolute() else paths.resolve_under_root(value, paths.ROOT, "classification_json")


def _load_classifications(value: str | None, hard: list[str]) -> dict[str, Classification]:
    if not value:
        return {}
    path = _resolve_classification_path(value)
    if not path.exists():
        hard.append(f"{_rel(path)}: classification_json file does not exist.")
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        hard.append(f"{_rel(path)}: invalid classification JSON: {error.msg}.")
        return {}
    if not isinstance(payload, list):
        hard.append(f"{_rel(path)}: classification JSON must be an array.")
        return {}
    results: dict[str, Classification] = {}
    for index, row in enumerate(payload):
        if not isinstance(row, dict):
            hard.append(f"{_rel(path)}[{index}]: classification row must be an object.")
            continue
        source = str(row.get("source") or "")
        if not source.startswith("docs/_harvest-inbox/raw/"):
            hard.append(f"{_rel(path)}[{index}]: source must be under docs/_harvest-inbox/raw/.")
            continue
        results[source] = Classification(
            source=source,
            suggested_type=str(row.get("suggested_type") or UNKNOWN_TYPE),
            confidence=str(row.get("confidence") or "low"),
            reason=str(row.get("reason") or "no reason provided"),
        )
    return results


def _normalize(classification: Classification | None, policy: dict[str, Any]) -> Classification:
    if classification is None:
        return Classification("", UNKNOWN_TYPE, "low", "no classification provided")
    suggested = classification.suggested_type
    confidence = classification.confidence
    if suggested not in _types(policy) or confidence != "high":
        suggested = UNKNOWN_TYPE
    if confidence not in {"high", "medium", "low"}:
        confidence = "low"
    return Classification(classification.source, suggested, confidence, classification.reason)


def _render_report(
    run_id: str,
    dry_run: bool,
    autorun: bool,
    hard: list[str],
    warnings: list[str],
    results: list[TagResult],
    raw_count: int,
    mutation_count: int,
) -> str:
    high_count = sum(1 for result in results if result.confidence == "high" and result.suggested_type != UNKNOWN_TYPE)
    unknown_count = sum(1 for result in results if result.suggested_type == UNKNOWN_TYPE)
    blocked_mutation_count = mutation_count if hard else 0
    lines = [
        "---",
        "command: h2-harvest-tag",
        "feature: null",
        "status: blocked" if hard else "status: updated",
        "next:",
        "  recommended_h2_step: h2-harvest",
        "---",
        "",
        "# h2-harvest-tag report",
        "",
        "## Summary",
        "",
        f"- run_id: {run_id}",
        f"- dry_run: {'true' if dry_run else 'false'}",
        f"- autorun: {'true' if autorun else 'false'}",
        f"- raw_file_count: {raw_count}",
        f"- high_confidence_count: {high_count}",
        f"- unknown_count: {unknown_count}",
        f"- mutation_count: {0 if hard else mutation_count}",
        f"- blocked_mutation_count: {blocked_mutation_count}",
        "",
        "## Results",
    ]
    if results:
        for result in results:
            lines.extend(
                [
                    f"- action: {result.action}",
                    f"  source: {result.source}",
                    f"  suggested_type: {result.suggested_type}",
                    f"  confidence: {result.confidence}",
                    f"  planned_action: {result.planned_action}",
                    f"  final_path: {result.final_path or 'null'}",
                    f"  reason: {result.reason}",
                ]
            )
    else:
        lines.append("- 없음")
    lines.extend(["", "## Warnings"])
    if warnings:
        lines.extend(f"- {item}" for item in warnings)
    else:
        lines.append("- 없음")
    lines.extend(["", "## Hard Errors"])
    if hard:
        lines.extend(f"- {item}" for item in hard)
    else:
        lines.append("- 없음")
    return "\n".join(lines) + "\n"


def command_harvest_tag(args: argparse.Namespace) -> int:
    schema = load_schema()
    policy, _policy_source, policy_warnings = load_harvest_policy(schema)
    run_id = paths.validate_run_id(args.run_id) if args.run_id else now_kst().strftime("%Y%m%d-%H%M%S-h2-harvest-tag")
    hard: list[str] = []
    classifications = _load_classifications(getattr(args, "classification_json", None), hard)
    raw_files = _scan_raw(policy)
    classification_sources = set(classifications)
    raw_sources = {item.rel for item in raw_files}
    for source in sorted(classification_sources - raw_sources):
        hard.append(f"{source}: classification source does not match a raw file.")

    results: list[TagResult] = []
    planned_moves: list[tuple[RawFile, Path]] = []
    subfolder_by_type = _subfolder_by_type(policy)
    raw_root = _raw_root(policy)
    for item in raw_files:
        if not item.supported:
            results.append(TagResult("skipped", item.rel, UNKNOWN_TYPE, "low", "skipped", None, "unsupported_extension"))
            continue
        normalized = _normalize(classifications.get(item.rel), policy)
        suggested = normalized.suggested_type
        if item.existing_type:
            reason = "already_tagged"
            if suggested != UNKNOWN_TYPE and suggested != item.existing_type:
                reason = "prefix_conflict"
            results.append(TagResult("skipped", item.rel, suggested, normalized.confidence, "skipped", item.rel, reason))
            continue
        target_name = f"{suggested}_{item.path.name}"
        if suggested == UNKNOWN_TYPE or not getattr(args, "autorun", False):
            target = raw_root / target_name
            planned_action = "rename"
        else:
            target = _staging_root(policy) / subfolder_by_type[suggested] / target_name
            planned_action = "move"
        planned_moves.append((item, target))
        results.append(
            TagResult(
                planned_action,
                item.rel,
                suggested,
                normalized.confidence,
                planned_action,
                _rel(target),
                normalized.reason,
            )
        )

    mutation_count = len(planned_moves)
    for item, target in planned_moves:
        if target.exists() and target != item.path:
            hard.append(f"{item.rel}: collision at {_rel(target)}.")

    report_path = _report_path(run_id)
    if not hard and not getattr(args, "dry_run", False):
        for item, target in planned_moves:
            target.parent.mkdir(parents=True, exist_ok=True)
            item.path.rename(target)

    write_text(
        report_path,
        _render_report(
            run_id,
            bool(getattr(args, "dry_run", False)),
            bool(getattr(args, "autorun", False)),
            hard,
            policy_warnings,
            results,
            len(raw_files),
            mutation_count,
        ),
    )
    print(f"h2-harvest-tag: wrote {_rel(report_path)}")
    for item in hard:
        print(f"h2-harvest-tag: {item}")
    return 1 if hard else 0
