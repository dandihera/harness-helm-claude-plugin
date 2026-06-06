from __future__ import annotations

import argparse
import dataclasses
from pathlib import Path
from typing import Any

from . import index as harness_index
from . import harvest_tag
from . import paths
from .frontmatter import parse_frontmatter, render_frontmatter
from .schema import load_harvest_policy, load_schema
from .utils import now_kst, read_text, write_text


SUPPORTED_SUFFIXES = {".md", ".txt"}
LOW_RISK_TYPES = {"solution", "convention"}
MISMATCH_SIGNALS = {
    "domain": {"concept", "vocabulary", "term", "glossary", "domain", "개념", "용어", "사전"},
    "spec": {"must", "should", "contract", "api", "schema", "requirement", "명세", "요구사항", "계약"},
    "decision": {"decision", "adr", "accepted", "rejected", "rationale", "결정", "대안", "근거"},
    "runbook": {"runbook", "procedure", "incident", "release", "operation", "절차", "운영", "장애", "릴리스"},
    "solution": {"problem", "solution", "verification", "해결", "문제", "검증"},
    "convention": {"convention", "guideline", "rule", "naming", "규칙", "가이드", "네이밍"},
}


@dataclasses.dataclass
class HarvestItem:
    path: Path
    rel: str
    folder_type: str
    dtype: str
    frontmatter: dict[str, Any]
    body: str
    explicit_type: bool


@dataclasses.dataclass
class HarvestResult:
    item: HarvestItem
    action: str
    destination: str | None
    status: str | None
    reason: str


@dataclasses.dataclass
class HarvestWarning:
    rel: str
    declared_type: str
    suggested_type: str
    reason: str
    action: str


def _rel(path: Path) -> str:
    return paths.repository_rel(path)


def _report_path(run_id: str) -> Path:
    return paths.ROOT / ".harness-helm" / "runs" / "_unscoped" / run_id / "harvest-report.md"


def _staging_root(policy: dict[str, Any]) -> Path:
    staging = policy.get("staging", {})
    rel = staging.get("path", "docs/_harvest-inbox") if isinstance(staging, dict) else "docs/_harvest-inbox"
    return paths.resolve_under_root(str(rel), paths.ROOT, "staging.path")


def _type_by_subfolder(policy: dict[str, Any]) -> dict[str, str]:
    staging = policy.get("staging", {})
    values = staging.get("type_by_subfolder", {}) if isinstance(staging, dict) else {}
    return {str(key): str(value) for key, value in values.items()} if isinstance(values, dict) else {}


def _destinations(policy: dict[str, Any]) -> dict[str, str]:
    values = policy.get("canonical_destination", {})
    return {str(key): str(value) for key, value in values.items()} if isinstance(values, dict) else {}


def _promoted_status(policy: dict[str, Any]) -> dict[str, str]:
    values = policy.get("promoted_status", {})
    return {str(key): str(value) for key, value in values.items()} if isinstance(values, dict) else {}


def _candidate_destination(item: HarvestItem, policy: dict[str, Any]) -> Path:
    destinations = _destinations(policy)
    dest_root = paths.resolve_under_root(destinations[item.dtype], paths.ROOT, f"canonical_destination.{item.dtype}")
    name = item.path.with_suffix(".md").name
    return dest_root / name


def _resolve_input_path(value: str, staging_root: Path) -> Path:
    raw = Path(value)
    path = raw.resolve() if raw.is_absolute() else paths.resolve_under_root(value, paths.ROOT, "harvest path")
    try:
        path.relative_to(staging_root.resolve())
    except ValueError as exc:
        raise ValueError(f"{_rel(path)} must be under {_rel(staging_root)}") from exc
    return path


def _scan_candidate_paths(staging_root: Path) -> list[Path]:
    if not staging_root.exists():
        return []
    raw_root = staging_root / "raw"
    paths_to_process: list[Path] = []
    for path in sorted(path for path in staging_root.rglob("*") if path.is_file() and path.name != ".gitkeep"):
        try:
            path.relative_to(raw_root)
        except ValueError:
            paths_to_process.append(path)
    return paths_to_process


def _validate_and_load(path: Path, staging_root: Path, policy: dict[str, Any], hard: list[str]) -> HarvestItem | None:
    if not path.is_file():
        hard.append(f"{_rel(path)}: harvest input file does not exist.")
        return None
    try:
        relative = path.resolve().relative_to(staging_root.resolve())
    except ValueError:
        hard.append(f"{_rel(path)}: path is outside harvest inbox.")
        return None
    parts = relative.parts
    if len(parts) < 2:
        hard.append(f"{_rel(path)}: files must be placed under a typed subfolder.")
        return None
    folder = parts[0]
    subfolders = _type_by_subfolder(policy)
    if folder not in subfolders:
        hard.append(f"{_rel(path)}: unknown harvest subfolder {folder}.")
        return None
    if path.suffix not in SUPPORTED_SUFFIXES:
        hard.append(f"{_rel(path)}: unsupported extension {path.suffix}; only .md and .txt are supported.")
        return None
    text = read_text(path)
    fm, body = parse_frontmatter(text)
    explicit_type = "type" in fm
    dtype = str(fm.get("type") or subfolders[folder])
    if dtype not in _destinations(policy):
        hard.append(f"{_rel(path)}: unknown harvest type {dtype}.")
        return None
    return HarvestItem(
        path=path,
        rel=_rel(path),
        folder_type=str(subfolders[folder]),
        dtype=dtype,
        frontmatter=fm,
        body=body,
        explicit_type=explicit_type,
    )


def _first_content(text: str) -> str:
    lines = [line.strip("# ").strip() for line in text.splitlines() if line.strip()]
    return " ".join(lines[:4]).lower()


def _semantic_warning(item: HarvestItem) -> HarvestWarning | None:
    if item.explicit_type:
        return None
    content = _first_content(item.body)
    scores: dict[str, int] = {}
    for dtype, signals in MISMATCH_SIGNALS.items():
        score = sum(1 for signal in signals if signal.lower() in content)
        if score:
            scores[dtype] = score
    if not scores:
        return None
    high = max(scores.values())
    winners = sorted(dtype for dtype, score in scores.items() if score == high)
    if len(winners) != 1:
        return None
    suggested = winners[0]
    if suggested == item.dtype:
        return None
    return HarvestWarning(
        rel=item.rel,
        declared_type=item.dtype,
        suggested_type=suggested,
        reason=f"title/body matched {suggested} signals more strongly than {item.dtype}",
        action=f"move to docs/_harvest-inbox/{suggested}/ or add type: {suggested}",
    )


def _ensure_frontmatter(item: HarvestItem, policy: dict[str, Any], promoted: bool) -> tuple[dict[str, Any], str]:
    fm = dict(item.frontmatter)
    fm.setdefault("type", item.dtype)
    fm.setdefault("security", "internal")
    fm.setdefault("confidence", "medium")
    if promoted:
        status = _promoted_status(policy)[item.dtype]
    else:
        status = "pending"
    fm["status"] = status
    return fm, status


def _has_high_evidence(fm: dict[str, Any], schema: dict[str, Any]) -> bool:
    return any(fm.get(field) for field in schema.get("confidence_high_evidence_fields", set()))


def _is_auto_write(item: HarvestItem, policy: dict[str, Any], schema: dict[str, Any]) -> bool:
    review_gate = policy.get("review_gate", {})
    low_risk_auto_write = review_gate.get("low_risk_auto_write", True) if isinstance(review_gate, dict) else True
    threshold = str(review_gate.get("confidence_threshold", "high")) if isinstance(review_gate, dict) else "high"
    return (
        bool(low_risk_auto_write)
        and item.dtype in LOW_RISK_TYPES
        and item.frontmatter.get("confidence") == threshold
        and _has_high_evidence(item.frontmatter, schema)
    )


def _validate_destination(
    item: HarvestItem,
    policy: dict[str, Any],
    force: bool,
    hard: list[str],
) -> Path:
    dest = _candidate_destination(item, policy)
    if dest.exists() and not force:
        hard.append(f"{item.rel}: destination exists {_rel(dest)}; use --force to overwrite.")
    return dest


def _write_markdown(path: Path, fm: dict[str, Any], body: str) -> None:
    write_text(path, render_frontmatter(fm) + body.lstrip("\n"))


def _render_report(
    run_id: str,
    dry_run: bool,
    hard: list[str],
    policy_warnings: list[str],
    warnings: list[HarvestWarning],
    results: list[HarvestResult],
    index_ran: bool,
) -> str:
    lines = [
        "---",
        "command: h2-harvest",
        "feature: null",
        "status: blocked" if hard else "status: updated",
        "next:",
        "  recommended_h2_step: null",
        "---",
        "",
        "# h2-harvest report",
        "",
        "## Summary",
        "",
        f"- run_id: {run_id}",
        f"- dry_run: {'true' if dry_run else 'false'}",
        f"- kb_index_ran: {'true' if index_ran else 'false'}",
        "",
        "## Results",
    ]
    if results:
        for result in results:
            lines.extend(
                [
                    f"- action: {result.action}",
                    f"  source: {result.item.rel}",
                    f"  type: {result.item.dtype}",
                    f"  status: {result.status or 'null'}",
                    f"  destination: {result.destination or 'null'}",
                    f"  reason: {result.reason}",
                ]
            )
    else:
        lines.append("- 없음")
    lines.extend(["", "## Warnings"])
    if policy_warnings or warnings:
        for item in policy_warnings:
            lines.append(f"- policy: {item}")
        for warning in warnings:
            lines.extend(
                [
                    "- warning: possible_type_mismatch",
                    f"  file: {warning.rel}",
                    f"  declared_type: {warning.declared_type}",
                    f"  suggested_type: {warning.suggested_type}",
                    f"  reason: {warning.reason}",
                    f"  action: {warning.action}",
                ]
            )
    else:
        lines.append("- 없음")
    lines.extend(["", "## Hard Errors"])
    if hard:
        lines.extend(f"- {item}" for item in hard)
    else:
        lines.append("- 없음")
    return "\n".join(lines) + "\n"


def command_harvest(args: argparse.Namespace) -> int:
    schema = load_schema()
    policy, _policy_source, policy_warnings = load_harvest_policy(schema)
    run_id = paths.validate_run_id(args.run_id) if args.run_id else now_kst().strftime("%Y%m%d-%H%M%S-h2-harvest")
    staging_root = _staging_root(policy)
    hard: list[str] = []
    results: list[HarvestResult] = []
    warnings: list[HarvestWarning] = []

    if not bool(getattr(args, "skip_raw", False)):
        unclassified_raw, review_pending_raw = harvest_tag.raw_warning_counts(policy)
        if unclassified_raw or review_pending_raw:
            print(
                "h2-harvest: raw inbox has "
                f"unclassified files: {unclassified_raw}, review-pending files: {review_pending_raw}"
            )
            if unclassified_raw:
                print("h2-harvest: run .harness-helm/scripts/harness h2-harvest-tag first.")

    explicit_inputs = [value for value in (getattr(args, "promote", None), getattr(args, "reject", None)) if value]
    if len(explicit_inputs) > 1:
        hard.append("--promote and --reject are mutually exclusive.")
        paths_to_process: list[Path] = []
    elif explicit_inputs:
        try:
            paths_to_process = [_resolve_input_path(str(explicit_inputs[0]), staging_root)]
        except ValueError as error:
            hard.append(str(error))
            paths_to_process = []
    else:
        paths_to_process = _scan_candidate_paths(staging_root)

    items = [
        item
        for path in paths_to_process
        if (item := _validate_and_load(path, staging_root, policy, hard)) is not None
    ]

    for item in items:
        if warning := _semantic_warning(item):
            warnings.append(warning)

    promote_requested = getattr(args, "promote", None) is not None
    reject_requested = getattr(args, "reject", None) is not None
    destination_by_rel: dict[str, Path] = {}
    for item in items:
        status = str(item.frontmatter.get("status") or "")
        should_promote = promote_requested or status == "approved" or _is_auto_write(item, policy, schema)
        if reject_requested or status == "rejected":
            continue
        if should_promote:
            destination_by_rel[item.rel] = _validate_destination(item, policy, bool(getattr(args, "force", False)), hard)

    report_path = _report_path(run_id)
    if hard:
        write_text(report_path, _render_report(run_id, bool(args.dry_run), hard, policy_warnings, warnings, results, False))
        for item in hard:
            print(f"h2-harvest: {item}")
        return 1

    promoted_count = 0
    for item in items:
        status = str(item.frontmatter.get("status") or "")
        if reject_requested or status == "rejected":
            results.append(HarvestResult(item, "rejected", None, "rejected", "explicit reject"))
            if not args.dry_run:
                item.path.unlink()
            continue

        should_promote = promote_requested or status == "approved" or _is_auto_write(item, policy, schema)
        if should_promote:
            dest = destination_by_rel[item.rel]
            fm, promoted_status = _ensure_frontmatter(item, policy, promoted=True)
            results.append(HarvestResult(item, "promoted", _rel(dest), promoted_status, "approved or auto-write"))
            promoted_count += 1
            if not args.dry_run:
                _write_markdown(dest, fm, item.body)
                item.path.unlink()
            continue

        fm, pending_status = _ensure_frontmatter(item, policy, promoted=False)
        results.append(HarvestResult(item, "pending", None, pending_status, "approval required"))
        if not args.dry_run:
            _write_markdown(item.path.with_suffix(".md") if item.path.suffix == ".txt" else item.path, fm, item.body)
            if item.path.suffix == ".txt":
                item.path.unlink()

    index_ran = False
    if promoted_count > 0 and not args.dry_run:
        harness_index.command_index(argparse.Namespace())
        index_ran = True

    write_text(report_path, _render_report(run_id, bool(args.dry_run), hard, policy_warnings, warnings, results, index_ran))
    print(f"h2-harvest: wrote {_rel(report_path)}")
    return 0
