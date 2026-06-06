from __future__ import annotations

import dataclasses
import datetime as dt
import json
import argparse
from pathlib import Path
from typing import Any

from . import paths
from .frontmatter import list_value, parse_frontmatter, parse_simple_yaml, raw_list_value
from .utils import now_kst


STAGE_RUNTIME_SUMMARY_JSON_NAME = "stage-runtime-summary.json"
STAGE_RUNTIME_SUMMARY_MD_NAME = "runs-summary.md"
LEGACY_RUNTIME_SUMMARY_NAME = "runtime-summary.json"
LEGACY_RUNTIME_SUMMARY_WARNING = "legacy runtime-summary.json fallback"
STAGE_RUNTIME_SUMMARY_TEMPLATE = "docs/_templates/runs-summary.md"
DEFAULT_STAGE_RUNTIME_SUMMARY_MARKDOWN_TEMPLATE = """# Runs Summary: {{feature}}

Generated: {{generated_at}}
Archive: `{{archive_path}}`

## Totals

| result | stage_elapsed | archive_wall_clock | runs | warnings |
|---|---:|---:|---:|---:|
{{totals_rows}}

## Runs

| stage | result | duration | surface | run_id |
|---|---|---:|---|---|
{{runs_rows}}

## Autorun Groups

| autorun_id | stage_count | elapsed | stages | slowest_stage |
|---|---:|---:|---|---|
{{autorun_group_rows}}

## Autorun Iterations

| autorun_id | iteration | stage | attempt | status | back_edge_from | reason | resolution |
|---|---:|---|---:|---|---|---|---|
{{autorun_iteration_rows}}

## Warnings

{{warnings_block}}
"""
RUN_MANIFEST_NAME = "manifest.json"
RUN_MANIFEST_FIELD_ORDER = [
    "schema_version",
    "type",
    "feature",
    "run_id",
    "command",
    "status",
    "started_at",
    "completed_at",
    "autorun_id",
    "invoked_surface",
    "invocation_mode",
    "artifact_paths",
    "task",
]
INVOCATION_MODES = {"actual", "fallback", "recorder", "unknown"}
SNAPSHOT_STAGE_COMMANDS = {
    "h2-analysis",
    "h2-build",
    "h2-test",
    "h2-review",
    "h2-report",
    "h2-compound",
    "h2-archive",
}


EXPECTED_COMMANDS = {
    "h2-context",
    "h2-plan",
    "h2-design",
    "h2-autorun",
    "h2-rewind",
    "h2-analysis",
    "h2-report",
    "h2-cartridge",
    "h2-build",
    "h2-test",
    "h2-review",
    "h2-compound",
    "h2-archive",
    "h2-ops",
    "h2-harvest",
    "h2-harvest-tag",
}


def run_id(command: str) -> str:
    return f"{now_kst().strftime('%Y%m%d-%H%M%S')}-{command}"


def run_root(feature: str | None, run_id_value: str) -> Path:
    paths.validate_run_id(run_id_value)
    feature_dir = paths.safe_path_segment(feature or "_unscoped", "feature")
    return paths.ROOT / ".harness-helm" / "runs" / feature_dir / run_id_value


def run_manifest_path(feature: str | None, run_id_value: str) -> Path:
    return run_root(feature, run_id_value) / RUN_MANIFEST_NAME


def stage_runtime_summary_json_path(archive_path: Path) -> Path:
    return archive_path / "runs" / STAGE_RUNTIME_SUMMARY_JSON_NAME


def stage_runtime_summary_md_path(archive_path: Path) -> Path:
    return archive_path / STAGE_RUNTIME_SUMMARY_MD_NAME


def legacy_runtime_summary_path(archive_path: Path) -> Path:
    return archive_path / LEGACY_RUNTIME_SUMMARY_NAME


def command_from_run_id(run_id_value: str) -> str:
    paths.validate_run_id(run_id_value)
    return run_id_value.split("-", 2)[2]


def validate_h2_command(command: str) -> str:
    if command not in EXPECTED_COMMANDS:
        raise ValueError(f"invalid h2 command: {command}")
    return command


def normalize_invoked_surface(value: Any) -> str | None:
    if isinstance(value, str) and value:
        return value
    return None


def normalize_invocation_mode(value: Any) -> str:
    if isinstance(value, str) and value in INVOCATION_MODES:
        return value
    return "unknown"


def cartridge_fallback_surface(command: str) -> str | None:
    if not paths.CARTRIDGE_PATH.exists():
        return None
    cartridge = parse_simple_yaml(paths.CARTRIDGE_PATH.read_text(encoding="utf-8"))
    commands = cartridge.get("commands")
    if not isinstance(commands, dict):
        return None
    mapping = commands.get(command)
    if not isinstance(mapping, dict):
        return None
    fallback_label = mapping.get("fallback_label")
    if not isinstance(fallback_label, str) or not fallback_label:
        return None
    return f"fallback:{fallback_label}"


def cartridge_primary_surface(command: str) -> str | None:
    if not paths.CARTRIDGE_PATH.exists():
        return None
    cartridge = parse_simple_yaml(paths.CARTRIDGE_PATH.read_text(encoding="utf-8"))
    commands = cartridge.get("commands")
    if not isinstance(commands, dict):
        return None
    mapping = commands.get(command)
    if not isinstance(mapping, dict):
        return None
    provider = mapping.get("provider")
    surface = mapping.get("surface")
    if not isinstance(provider, str) or not provider or not isinstance(surface, str) or not surface:
        return None
    return f"{provider}:{surface}"


def summary_invoked_surface(command: str, value: Any) -> str | None:
    surface = normalize_invoked_surface(value)
    if surface == f"harness:{command}":
        return cartridge_primary_surface(command) or surface
    return surface


def format_run_timestamp(value: dt.datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=dt.timezone(dt.timedelta(hours=9)))
    return value.isoformat(timespec="seconds")


def started_at_from_run_id(run_id_value: str) -> dt.datetime:
    paths.validate_run_id(run_id_value)
    raw = run_id_value[:15]
    return dt.datetime.strptime(raw, "%Y%m%d-%H%M%S").replace(tzinfo=dt.timezone(dt.timedelta(hours=9)))


def parse_run_timestamp(value: Any) -> dt.datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = dt.datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone(dt.timedelta(hours=9)))
    return parsed


def load_run_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid run manifest JSON: {paths.display_path(path)}: {error.msg}") from error
    if not isinstance(manifest, dict):
        raise ValueError(f"run manifest must be a JSON object: {paths.display_path(path)}")
    return manifest


def ordered_run_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    ordered = {key: manifest[key] for key in RUN_MANIFEST_FIELD_ORDER if key in manifest}
    for key in manifest:
        if key not in ordered:
            ordered[key] = manifest[key]
    return ordered


def write_run_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(ordered_run_manifest(manifest), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def start_run_manifest(
    feature: str | None,
    run_id_value: str,
    command: str,
    task: str | None = None,
    autorun_id: str | None = None,
    invoked_surface: str | None = None,
    invocation_mode: str | None = None,
) -> Path:
    path = run_manifest_path(feature, run_id_value)
    existing = load_run_manifest(path)
    safe_feature = paths.safe_path_segment(feature, "feature") if feature else "_unscoped"
    safe_run_id = paths.validate_run_id(run_id_value)
    safe_command = validate_h2_command(command)
    existing_status = existing.get("status")
    should_reset_timing = existing_status in {"completed", "failed", "incomplete"} or existing.get("completed_at") is not None
    started_at = existing.get("started_at")
    manifest = {
        "schema_version": 1,
        "type": "run-manifest",
        "feature": safe_feature,
        "run_id": safe_run_id,
        "command": safe_command,
        "status": "running",
        "started_at": format_run_timestamp(now_kst()) if should_reset_timing or not started_at else started_at,
        "completed_at": None,
        "autorun_id": paths.validate_run_id(autorun_id) if autorun_id is not None else existing.get("autorun_id"),
        "artifact_paths": existing.get("artifact_paths", []),
    }
    if task:
        manifest["task"] = task
    normalized_surface = normalize_invoked_surface(invoked_surface)
    if normalized_surface is not None:
        manifest["invoked_surface"] = normalized_surface
    if invocation_mode is not None:
        manifest["invocation_mode"] = normalize_invocation_mode(invocation_mode)
    write_run_manifest(path, manifest)
    return path


def complete_run_manifest(
    feature: str | None,
    run_id_value: str,
    status: str = "completed",
    artifact_paths: list[str] | None = None,
    invoked_surface: str | None = None,
    invocation_mode: str | None = None,
) -> Path:
    if status not in {"completed", "failed", "incomplete"}:
        raise ValueError("status must be completed, failed, or incomplete.")
    root = run_root(feature, run_id_value)
    if not root.exists():
        raise FileNotFoundError(f"run folder does not exist: {paths.repository_rel(root)}")
    path = run_manifest_path(feature, run_id_value)
    manifest = load_run_manifest(path)
    safe_feature = paths.safe_path_segment(feature, "feature") if feature else "_unscoped"
    safe_run_id = paths.validate_run_id(run_id_value)
    if not manifest:
        manifest = {
            "schema_version": 1,
            "type": "run-manifest",
            "feature": safe_feature,
            "run_id": safe_run_id,
            "command": command_from_run_id(safe_run_id),
            "started_at": format_run_timestamp(started_at_from_run_id(safe_run_id)),
            "autorun_id": None,
            "artifact_paths": [],
        }
    manifest.setdefault("schema_version", 1)
    manifest.setdefault("type", "run-manifest")
    manifest.setdefault("feature", safe_feature)
    manifest.setdefault("run_id", safe_run_id)
    manifest.setdefault("command", command_from_run_id(safe_run_id))
    manifest.setdefault("started_at", format_run_timestamp(started_at_from_run_id(safe_run_id)))
    manifest.setdefault("autorun_id", None)
    existing = list_value(manifest.get("artifact_paths"))
    for artifact in artifact_paths or []:
        if artifact not in existing:
            existing.append(artifact)
    manifest["status"] = status
    manifest["completed_at"] = None if status == "incomplete" else format_run_timestamp(now_kst())
    manifest["artifact_paths"] = existing
    normalized_surface = normalize_invoked_surface(invoked_surface)
    if normalized_surface is not None:
        manifest["invoked_surface"] = normalized_surface
    if invocation_mode is not None:
        manifest["invocation_mode"] = normalize_invocation_mode(invocation_mode)
    write_run_manifest(path, manifest)
    return path


@dataclasses.dataclass
class RunStatsEntry:
    feature: str
    run_id: str
    command: str
    status: str
    started_at: dt.datetime | None
    completed_at: dt.datetime | None
    elapsed_seconds: int | None
    manifest_path: Path | None
    warnings: list[str]
    autorun_id: str | None
    invoked_surface: str | None = None
    invocation_mode: str = "unknown"
    iteration_index: int | None = None
    stage_attempt: int | None = None
    back_edge_from: str | None = None
    back_edge_reason: str | None = None
    back_edge_reason_key: str | None = None
    back_edge_reason_key_source: str | None = None
    autorun_resolution: str | None = None
    next_recommended_h2_step: str | None = None


def iter_run_dirs(feature: str | None = None) -> list[Path]:
    root = paths.ROOT / ".harness-helm" / "runs"
    if not root.exists():
        return []
    feature_dirs = [root / paths.safe_path_segment(feature, "feature")] if feature else [
        path for path in sorted(root.iterdir()) if path.is_dir() and path.name != "_templates"
    ]
    run_dirs: list[Path] = []
    for feature_dir in feature_dirs:
        if not feature_dir.exists() or not feature_dir.is_dir():
            continue
        for path in sorted(feature_dir.iterdir()):
            if path.is_dir() and paths.RUN_ID_PATTERN.match(path.name):
                run_dirs.append(path)
    return run_dirs


def resolve_existing_dir(value: str) -> Path | None:
    path = Path(value).expanduser()
    candidates = [path] if path.is_absolute() else [paths.ROOT / path, path]
    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate.resolve()
    return None


def archive_feature(archive_path: Path) -> str:
    manifest_path = archive_path / "manifest.md"
    if manifest_path.exists():
        frontmatter, _ = parse_frontmatter(manifest_path.read_text(encoding="utf-8"))
        feature = frontmatter.get("feature")
        if isinstance(feature, str) and feature:
            return feature
    return archive_path.name.split("_", 1)[-1]


def iter_archive_run_dirs(archive_path: Path) -> list[Path]:
    runs = archive_path / "runs"
    if not runs.exists() or not runs.is_dir():
        return []
    return sorted(
        path
        for path in runs.iterdir()
        if path.is_dir()
        and paths.RUN_ID_PATTERN.match(path.name)
        and (
            (path / RUN_MANIFEST_NAME).exists()
            or (path / "manifest.md").exists()
            or (path / "context-pack.md").exists()
            or any(path.glob("*.md"))
        )
    )


def command_from_markdown_artifact(path: Path) -> str | None:
    try:
        frontmatter, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
    except OSError:
        frontmatter = {}
    command = frontmatter.get("command")
    if isinstance(command, str) and command in SNAPSHOT_STAGE_COMMANDS | {"h2-autorun"}:
        return command
    return {
        "build": "h2-build",
        "test": "h2-test",
        "review": "h2-review",
        "report": "h2-report",
        "compound-candidates": "h2-compound",
        "archive-plan": "h2-archive",
    }.get(path.stem)


def infer_context_stage(run_dir: Path, manifest: dict[str, Any]) -> str | None:
    try:
        run_id_command = command_from_run_id(run_dir.name)
    except ValueError:
        run_id_command = None
    if run_id_command and run_id_command != "h2-context":
        return run_id_command
    context_pack = run_dir / "context-pack.md"
    try:
        text = context_pack.read_text(encoding="utf-8")
    except OSError:
        text = ""
    task = manifest.get("task")
    haystack = f"{task if isinstance(task, str) else ''}\n{text}".lower()
    if "h2-autorun" in haystack:
        return "h2-autorun"
    if "recommended_h2_step: h2-design" in haystack:
        return "h2-plan"
    if "h2-design" in haystack:
        return "h2-design"
    return None


def context_only_surface(value: Any) -> str | None:
    surface = normalize_invoked_surface(value)
    if surface and surface.startswith("fallback:"):
        return surface
    return cartridge_primary_surface("h2-context") or "harness:context-pack"


def build_markdown_stage_entries(run_dir: Path, feature_override: str | None = None) -> list[RunStatsEntry]:
    try:
        parent_command = command_from_run_id(run_dir.name)
    except ValueError:
        return []
    if parent_command != "h2-autorun":
        return []
    artifacts: list[tuple[Path, str, dt.datetime]] = []
    for path in sorted(run_dir.glob("*.md")):
        command = command_from_markdown_artifact(path)
        if command not in SNAPSHOT_STAGE_COMMANDS:
            continue
        completed_at = dt.datetime.fromtimestamp(path.stat().st_mtime, tz=dt.timezone(dt.timedelta(hours=9)))
        artifacts.append((path, command, completed_at))
    if not artifacts:
        return []
    artifacts.sort(key=lambda item: (item[2], item[1]))
    feature = feature_override or run_dir.parent.name
    previous = started_at_from_run_id(run_dir.name)
    entries: list[RunStatsEntry] = []
    for path, command, completed_at in artifacts:
        started_at = previous
        elapsed = max(0, int((completed_at - started_at).total_seconds()))
        entries.append(
            RunStatsEntry(
                feature=feature,
                run_id=f"{run_dir.name}/{command}",
                command=command,
                status="recorded-estimated",
                started_at=started_at,
                completed_at=completed_at,
                elapsed_seconds=elapsed,
                manifest_path=None,
                warnings=[
                    f"{path.name}: elapsed estimated from markdown artifact mtime because manifest metadata is missing"
                ],
                autorun_id=run_dir.name,
                invoked_surface=cartridge_fallback_surface(command),
                invocation_mode="fallback" if cartridge_fallback_surface(command) else "unknown",
            )
        )
        previous = completed_at
    return entries


def _manifest_int(manifest: dict[str, Any], key: str) -> int | None:
    value = manifest.get(key)
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


def _manifest_str(manifest: dict[str, Any], key: str) -> str | None:
    value = manifest.get(key)
    if isinstance(value, str) and value:
        return value
    return None


def iter_archive_snapshot_stage_manifests(archive_path: Path) -> list[Path]:
    runs = archive_path / "runs"
    if not runs.exists() or not runs.is_dir():
        return []
    manifests: list[Path] = []
    for path in sorted(runs.glob("*/snapshots/*/manifest.json")):
        autorun_dir = path.parents[2]
        step = path.parent.name
        if not paths.RUN_ID_PATTERN.match(autorun_dir.name):
            continue
        if step not in SNAPSHOT_STAGE_COMMANDS:
            continue
        manifests.append(path)
    return manifests


def is_archive_run_stats_path(path: Path) -> bool:
    return (path / "runs").is_dir()


def build_run_stats_entry(run_dir: Path, feature_override: str | None = None) -> RunStatsEntry:
    feature = feature_override or run_dir.parent.name
    run_id_value = run_dir.name
    manifest_path = run_dir / RUN_MANIFEST_NAME
    manifest_exists = manifest_path.exists()
    manifest = load_run_manifest(manifest_path)
    warnings: list[str] = []
    run_id_started_at = started_at_from_run_id(run_id_value)
    manifest_started_at = parse_run_timestamp(manifest.get("started_at"))
    started_at = manifest_started_at or run_id_started_at
    if manifest_started_at and abs((manifest_started_at - run_id_started_at).total_seconds()) >= 1:
        warnings.append("started_at differs from run-id timestamp")
    command = str(manifest.get("command") or command_from_run_id(run_id_value))
    inferred_context_stage = False
    if command == "h2-context":
        inferred = infer_context_stage(run_dir, manifest)
        if inferred is not None:
            command = inferred
            inferred_context_stage = True
    invoked_surface = (
        context_only_surface(manifest.get("invoked_surface"))
        if inferred_context_stage
        else summary_invoked_surface(command, manifest.get("invoked_surface"))
    )
    invocation_mode = normalize_invocation_mode(manifest.get("invocation_mode"))
    if invoked_surface is None:
        fallback_surface = cartridge_fallback_surface(command)
        if fallback_surface is not None:
            invoked_surface = fallback_surface
            invocation_mode = "fallback"
            warnings.append("invoked_surface filled from cartridge fallback_label because manifest metadata is missing")
    if not manifest:
        return RunStatsEntry(
            feature=feature,
            run_id=run_id_value,
            command=command,
            status="missing-manifest",
            started_at=started_at,
            completed_at=None,
            elapsed_seconds=None,
            manifest_path=None,
            warnings=warnings,
            autorun_id=None,
            invoked_surface=invoked_surface,
            invocation_mode=invocation_mode,
        )
    completed_at = parse_run_timestamp(manifest.get("completed_at"))
    status = str(manifest.get("status") or "incomplete") if manifest_exists else "missing-manifest"
    elapsed = None
    if completed_at and started_at and status not in {"missing-manifest", "running", "incomplete"}:
        elapsed = max(0, int((completed_at - started_at).total_seconds()))
    if inferred_context_stage:
        status = "context-only"
        elapsed = None
        warnings.append("context preflight timing is not lifecycle stage duration")
    return RunStatsEntry(
        feature=str(manifest.get("feature") or feature),
        run_id=str(manifest.get("run_id") or run_id_value),
        command=command,
        status=status,
        started_at=started_at,
        completed_at=completed_at,
        elapsed_seconds=elapsed,
        manifest_path=manifest_path if manifest_exists else None,
        warnings=warnings,
        autorun_id=manifest.get("autorun_id") if isinstance(manifest.get("autorun_id"), str) else None,
        invoked_surface=invoked_surface,
        invocation_mode=invocation_mode,
        iteration_index=_manifest_int(manifest, "iteration_index"),
        stage_attempt=_manifest_int(manifest, "stage_attempt"),
        back_edge_from=_manifest_str(manifest, "back_edge_from"),
        back_edge_reason=_manifest_str(manifest, "back_edge_reason"),
        back_edge_reason_key=_manifest_str(manifest, "back_edge_reason_key"),
        back_edge_reason_key_source=_manifest_str(manifest, "back_edge_reason_key_source"),
        autorun_resolution=_manifest_str(manifest, "autorun_resolution"),
        next_recommended_h2_step=_manifest_str(manifest, "next_recommended_h2_step"),
    )


def build_snapshot_stage_entry(manifest_path: Path, feature_override: str | None = None) -> RunStatsEntry:
    manifest = load_run_manifest(manifest_path)
    warnings: list[str] = []
    command = str(manifest.get("command") or manifest.get("step") or manifest_path.parent.name)
    autorun_id = str(manifest.get("autorun_id") or manifest.get("run_id") or manifest_path.parents[2].name)
    started_at = parse_run_timestamp(manifest.get("started_at")) or parse_run_timestamp(manifest.get("created_at"))
    completed_at = parse_run_timestamp(manifest.get("completed_at"))
    status = str(manifest.get("status") or ("completed" if completed_at else "incomplete"))
    elapsed = None
    if completed_at and started_at and status not in {"running", "incomplete"}:
        elapsed = max(0, int((completed_at - started_at).total_seconds()))
    if completed_at is None:
        warnings.append("snapshot stage completed_at missing")
    feature = feature_override or str(manifest.get("feature") or archive_feature(manifest_path.parents[4]))
    return RunStatsEntry(
        feature=feature,
        run_id=f"{autorun_id}/{command}",
        command=command,
        status=status,
        started_at=started_at,
        completed_at=completed_at,
        elapsed_seconds=elapsed,
        manifest_path=manifest_path,
        warnings=warnings,
        autorun_id=autorun_id,
        invoked_surface=summary_invoked_surface(command, manifest.get("invoked_surface")),
        invocation_mode=normalize_invocation_mode(manifest.get("invocation_mode")),
        iteration_index=_manifest_int(manifest, "iteration_index"),
        stage_attempt=_manifest_int(manifest, "stage_attempt"),
        back_edge_from=_manifest_str(manifest, "back_edge_from"),
        back_edge_reason=_manifest_str(manifest, "back_edge_reason"),
        back_edge_reason_key=_manifest_str(manifest, "back_edge_reason_key"),
        back_edge_reason_key_source=_manifest_str(manifest, "back_edge_reason_key_source"),
        autorun_resolution=_manifest_str(manifest, "autorun_resolution"),
        next_recommended_h2_step=_manifest_str(manifest, "next_recommended_h2_step"),
    )


def apply_archive_elapsed_fallback(entries: list[RunStatsEntry]) -> None:
    ordered = sorted(entries, key=lambda entry: entry.started_at or dt.datetime.max.replace(tzinfo=dt.timezone.utc))
    for index, entry in enumerate(ordered):
        if entry.elapsed_seconds is not None or entry.started_at is None:
            continue
        next_started_at = None
        for next_entry in ordered[index + 1 :]:
            if next_entry.started_at:
                next_started_at = next_entry.started_at
                break
        if next_started_at is None:
            continue
        entry.completed_at = next_started_at
        entry.elapsed_seconds = max(0, int((next_started_at - entry.started_at).total_seconds()))
        entry.status = "estimated"
        entry.warnings.append("elapsed estimated from next run start because manifest completed_at is missing")


def format_elapsed(seconds: int | None, status: str) -> str:
    if seconds is None:
        if status in {"running", "incomplete", "missing-manifest"}:
            return status
        return "not available"
    minutes, sec = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h {minutes:02d}m {sec:02d}s"
    if minutes:
        return f"{minutes}m {sec:02d}s"
    return f"{sec}s"


def run_stats_to_dict(entry: RunStatsEntry) -> dict[str, Any]:
    return {
        "feature": entry.feature,
        "run_id": entry.run_id,
        "command": entry.command,
        "status": entry.status,
        "started_at": entry.started_at.isoformat() if entry.started_at else None,
        "completed_at": entry.completed_at.isoformat() if entry.completed_at else None,
        "elapsed_seconds": entry.elapsed_seconds,
        "elapsed": format_elapsed(entry.elapsed_seconds, entry.status),
        "autorun_id": entry.autorun_id,
        "invoked_surface": entry.invoked_surface,
        "invocation_mode": entry.invocation_mode,
        "iteration_index": entry.iteration_index,
        "stage_attempt": entry.stage_attempt,
        "back_edge_from": entry.back_edge_from,
        "back_edge_reason": entry.back_edge_reason,
        "back_edge_reason_key": entry.back_edge_reason_key,
        "back_edge_reason_key_source": entry.back_edge_reason_key_source,
        "autorun_resolution": entry.autorun_resolution,
        "next_recommended_h2_step": entry.next_recommended_h2_step,
        "manifest_path": paths.display_path(entry.manifest_path) if entry.manifest_path else None,
        "warnings": entry.warnings,
    }


def run_stats_entry_from_dict(item: dict[str, Any]) -> RunStatsEntry:
    manifest_path = item.get("manifest_path")
    resolved_manifest_path = None
    if isinstance(manifest_path, str) and manifest_path:
        path = Path(manifest_path)
        resolved_manifest_path = path if path.is_absolute() else paths.ROOT / path
    return RunStatsEntry(
        feature=str(item.get("feature") or ""),
        run_id=str(item.get("run_id") or ""),
        command=str(item.get("command") or ""),
        status=str(item.get("status") or ""),
        started_at=parse_run_timestamp(item.get("started_at")),
        completed_at=parse_run_timestamp(item.get("completed_at")),
        elapsed_seconds=item.get("elapsed_seconds") if isinstance(item.get("elapsed_seconds"), int) else None,
        manifest_path=resolved_manifest_path,
        warnings=[str(warning) for warning in list_value(item.get("warnings"))],
        autorun_id=item.get("autorun_id") if isinstance(item.get("autorun_id"), str) else None,
        invoked_surface=normalize_invoked_surface(item.get("invoked_surface")),
        invocation_mode=normalize_invocation_mode(item.get("invocation_mode")),
        iteration_index=item.get("iteration_index") if isinstance(item.get("iteration_index"), int) else None,
        stage_attempt=item.get("stage_attempt") if isinstance(item.get("stage_attempt"), int) else None,
        back_edge_from=item.get("back_edge_from") if isinstance(item.get("back_edge_from"), str) else None,
        back_edge_reason=item.get("back_edge_reason") if isinstance(item.get("back_edge_reason"), str) else None,
        back_edge_reason_key=item.get("back_edge_reason_key") if isinstance(item.get("back_edge_reason_key"), str) else None,
        back_edge_reason_key_source=(
            item.get("back_edge_reason_key_source")
            if isinstance(item.get("back_edge_reason_key_source"), str)
            else None
        ),
        autorun_resolution=item.get("autorun_resolution") if isinstance(item.get("autorun_resolution"), str) else None,
        next_recommended_h2_step=(
            item.get("next_recommended_h2_step")
            if isinstance(item.get("next_recommended_h2_step"), str)
            else None
        ),
    )


def latest_activity(entry: RunStatsEntry) -> dt.datetime:
    return entry.completed_at or entry.started_at or dt.datetime.min.replace(tzinfo=dt.timezone.utc)


def autorun_groups(entries: list[RunStatsEntry]) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    by_key: dict[tuple[str, str], list[RunStatsEntry]] = {}
    for entry in entries:
        if (
            entry.autorun_id
            and entry.command != "h2-autorun"
            and entry.elapsed_seconds is not None
            and entry.started_at
            and entry.completed_at
        ):
            by_key.setdefault((entry.feature, entry.autorun_id), []).append(entry)
    for (feature, autorun_id), grouped in sorted(by_key.items()):
        starts = [entry.started_at for entry in grouped if entry.started_at]
        ends = [entry.completed_at for entry in grouped if entry.completed_at]
        if not starts or not ends:
            continue
        total = max(0, int((max(ends) - min(starts)).total_seconds()))
        groups.append(
            {
                "feature": feature,
                "autorun_id": autorun_id,
                "stage_count": len(grouped),
                "started_at": format_run_timestamp(min(starts)),
                "completed_at": format_run_timestamp(max(ends)),
                "elapsed_seconds": total,
                "elapsed": format_elapsed(total, "completed"),
                "iteration_summary": autorun_iteration_summary(grouped),
            }
        )
    return groups


def autorun_iteration_summary(entries: list[RunStatsEntry]) -> str:
    grouped: dict[int, list[str]] = {}
    for entry in sorted(entries, key=latest_activity):
        if entry.iteration_index is None:
            continue
        grouped.setdefault(entry.iteration_index, []).append(entry.command)
    if not grouped:
        return ""
    return "; ".join(
        f"{iteration}: {', '.join(commands)}"
        for iteration, commands in sorted(grouped.items())
    )


def archive_wall_clock(entries: list[RunStatsEntry]) -> int | None:
    completed_entries = [entry for entry in entries if entry.started_at and entry.completed_at]
    if not completed_entries:
        return None
    starts = [entry.started_at for entry in completed_entries if entry.started_at]
    ends = [entry.completed_at for entry in completed_entries if entry.completed_at]
    return max(0, int((max(ends) - min(starts)).total_seconds()))


def build_archive_runtime_summary(archive_path: Path, generated_at: dt.datetime | None = None) -> dict[str, Any]:
    feature = archive_feature(archive_path)
    direct_entries = [build_run_stats_entry(path, feature_override=feature) for path in iter_archive_run_dirs(archive_path)]
    apply_archive_elapsed_fallback(direct_entries)
    snapshot_entries = [
        build_snapshot_stage_entry(path, feature_override=feature)
        for path in iter_archive_snapshot_stage_manifests(archive_path)
    ]
    markdown_stage_entries: list[RunStatsEntry] = []
    if not snapshot_entries:
        for path in iter_archive_run_dirs(archive_path):
            markdown_stage_entries.extend(build_markdown_stage_entries(path, feature_override=feature))
    entries = direct_entries + snapshot_entries + markdown_stage_entries
    entries.sort(key=latest_activity)
    if snapshot_entries or markdown_stage_entries:
        total_entries = [entry for entry in entries if entry.command != "h2-autorun"]
    else:
        total_entries = entries
    total_elapsed_seconds = sum(entry.elapsed_seconds or 0 for entry in total_entries)
    wall_clock_seconds = archive_wall_clock(entries)
    warnings = sorted({warning for entry in entries for warning in entry.warnings})
    archive_rel = paths.repository_rel(archive_path)
    summary: dict[str, Any] = {
        "schema_version": 1,
        "type": "stage-runtime-summary",
        "feature": feature,
        "archive_path": archive_rel,
        "generated_at": format_run_timestamp(generated_at or now_kst()),
        "generated_from": "h2-archive",
        "runs": [run_stats_to_dict(entry) for entry in entries],
        "total_elapsed_seconds": total_elapsed_seconds,
        "total_elapsed": format_elapsed(total_elapsed_seconds, "completed"),
        "archive_wall_clock_seconds": wall_clock_seconds,
        "archive_wall_clock": format_elapsed(wall_clock_seconds, "completed") if wall_clock_seconds is not None else None,
        "autorun_groups": autorun_groups(entries),
        "warnings": warnings,
    }
    summary["totals"] = {
        "stage_elapsed_seconds": total_elapsed_seconds,
        "stage_elapsed": summary["total_elapsed"],
        "archive_wall_clock_seconds": wall_clock_seconds,
        "archive_wall_clock": summary["archive_wall_clock"],
    }
    return summary


def _markdown_cell(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("|", "\\|")


def _stage_runtime_summary_template_text() -> str:
    path = paths.ROOT / STAGE_RUNTIME_SUMMARY_TEMPLATE
    if path.exists():
        return path.read_text(encoding="utf-8")
    return DEFAULT_STAGE_RUNTIME_SUMMARY_MARKDOWN_TEMPLATE


def _render_stage_runtime_summary_template(template: str, values: dict[str, Any]) -> str:
    rendered = template
    for key, value in values.items():
        rendered = rendered.replace("{{" + key + "}}", str(value))
    return rendered.rstrip() + "\n"


def _stage_runtime_summary_result(runs: list[dict[str, Any]], warnings: list[str]) -> str:
    if not runs:
        return "empty"
    statuses = {str(run.get("status") or "") for run in runs}
    if statuses.intersection({"failed", "error", "incomplete"}):
        return "attention"
    if warnings:
        return "warning"
    return "completed"


def _autorun_group_stage_entries(runs: list[dict[str, Any]], autorun_id: Any) -> list[dict[str, Any]]:
    if not autorun_id:
        return []
    return [run for run in runs if run.get("autorun_id") == autorun_id]


def _autorun_group_stages(runs: list[dict[str, Any]], autorun_id: Any) -> str:
    entries = _autorun_group_stage_entries(runs, autorun_id)
    return ", ".join(str(entry.get("command") or "") for entry in entries if entry.get("command"))


def _autorun_group_slowest_stage(runs: list[dict[str, Any]], autorun_id: Any) -> str:
    entries = [
        entry
        for entry in _autorun_group_stage_entries(runs, autorun_id)
        if isinstance(entry.get("elapsed_seconds"), int)
    ]
    if not entries:
        return ""
    slowest = max(entries, key=lambda entry: entry.get("elapsed_seconds") or 0)
    command = str(slowest.get("command") or "")
    elapsed = str(slowest.get("elapsed") or "")
    if not command:
        return elapsed
    if not elapsed:
        return command
    return f"{command} ({elapsed})"


def _has_autorun_iteration_metadata(run: dict[str, Any]) -> bool:
    return any(
        run.get(key) is not None
        for key in (
            "iteration_index",
            "stage_attempt",
            "back_edge_from",
            "back_edge_reason",
            "back_edge_reason_key",
            "autorun_resolution",
        )
    )


def _autorun_iteration_rows(runs: list[dict[str, Any]]) -> str:
    entries = [run for run in runs if run.get("autorun_id") and _has_autorun_iteration_metadata(run)]
    if not entries:
        return "| none |  |  |  |  |  |  |  |"
    entries.sort(
        key=lambda run: (
            str(run.get("autorun_id") or ""),
            run.get("iteration_index") if isinstance(run.get("iteration_index"), int) else 0,
            run.get("stage_attempt") if isinstance(run.get("stage_attempt"), int) else 0,
            str(run.get("command") or ""),
        )
    )
    rows: list[str] = []
    for run in entries:
        rows.append(
            "| "
            + " | ".join(
                [
                    _markdown_cell(run.get("autorun_id")),
                    _markdown_cell(run.get("iteration_index")),
                    _markdown_cell(run.get("command")),
                    _markdown_cell(run.get("stage_attempt")),
                    _markdown_cell(run.get("status")),
                    _markdown_cell(run.get("back_edge_from")),
                    _markdown_cell(run.get("back_edge_reason")),
                    _markdown_cell(run.get("autorun_resolution")),
                ]
            )
            + " |"
        )
    return "\n".join(rows)


def render_stage_runtime_summary_markdown(summary: dict[str, Any]) -> str:
    feature = str(summary.get("feature") or "")
    runs = [item for item in raw_list_value(summary.get("runs")) if isinstance(item, dict)]
    groups = [item for item in raw_list_value(summary.get("autorun_groups")) if isinstance(item, dict)]
    warnings = list_value(summary.get("warnings"))
    totals_rows = (
        "| "
        + " | ".join(
            [
                _markdown_cell(_stage_runtime_summary_result(runs, warnings)),
                _markdown_cell(summary.get("total_elapsed") or "not available"),
                _markdown_cell(summary.get("archive_wall_clock") or "not available"),
                _markdown_cell(len(runs)),
                _markdown_cell(len(warnings)),
            ]
        )
        + " |"
    )
    run_rows: list[str] = []
    if runs:
        for run in runs:
            run_rows.append(
                "| "
                + " | ".join(
                    [
                        _markdown_cell(run.get("command")),
                        _markdown_cell(run.get("status")),
                        _markdown_cell(run.get("elapsed")),
                        _markdown_cell(run.get("invoked_surface")),
                        _markdown_cell(run.get("run_id")),
                    ]
                )
                + " |"
            )
    else:
        run_rows.append("| none |  |  |  |  |")
    autorun_group_rows: list[str] = []
    if groups:
        for group in groups:
            autorun_group_rows.append(
                "| "
                + " | ".join(
                    [
                        _markdown_cell(group.get("autorun_id")),
                        _markdown_cell(group.get("stage_count")),
                        _markdown_cell(group.get("elapsed")),
                        _markdown_cell(_autorun_group_stages(runs, group.get("autorun_id"))),
                        _markdown_cell(_autorun_group_slowest_stage(runs, group.get("autorun_id"))),
                    ]
                )
                + " |"
            )
    else:
        autorun_group_rows.append("| none | 0 |  |  |  |")
    if warnings:
        warning_lines = ["| count | warning |", "|---:|---|"]
        for index, warning in enumerate(warnings, start=1):
            warning_lines.append(f"| {index} | {_markdown_cell(warning)} |")
        warnings_block = "\n".join(warning_lines)
    else:
        warnings_block = "- none"
    return _render_stage_runtime_summary_template(
        _stage_runtime_summary_template_text(),
        {
            "feature": feature,
            "generated_at": summary.get("generated_at") or "",
            "archive_path": summary.get("archive_path") or "",
            "totals_rows": totals_rows,
            "runs_rows": "\n".join(run_rows),
            "autorun_group_rows": "\n".join(autorun_group_rows),
            "autorun_iteration_rows": _autorun_iteration_rows(runs),
            "warnings_block": warnings_block,
        },
    )


def write_runtime_summary(archive_path: Path, generated_at: dt.datetime | None = None) -> Path:
    path = stage_runtime_summary_json_path(archive_path)
    markdown_path = stage_runtime_summary_md_path(archive_path)
    summary = build_archive_runtime_summary(archive_path, generated_at)
    summary["summary_path"] = paths.repository_rel(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(render_stage_runtime_summary_markdown(summary), encoding="utf-8")
    return path


def load_runtime_summary(archive_path: Path) -> dict[str, Any] | None:
    path = stage_runtime_summary_json_path(archive_path)
    legacy_path = legacy_runtime_summary_path(archive_path)
    is_legacy = False
    if not path.exists():
        if not legacy_path.exists():
            return None
        path = legacy_path
        is_legacy = True
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    if is_legacy:
        warnings = list_value(data.get("warnings"))
        if LEGACY_RUNTIME_SUMMARY_WARNING not in warnings:
            warnings.append(LEGACY_RUNTIME_SUMMARY_WARNING)
        data["warnings"] = warnings
        data["summary_path"] = paths.repository_rel(path)
    return data

def command_run_mark(args: argparse.Namespace) -> int:
    try:
        if args.run_mark_action == "start":
            path = start_run_manifest(
                args.feature,
                args.run_id,
                args.h2_command,
                task=args.task,
                autorun_id=args.autorun_id,
                invoked_surface=args.invoked_surface,
                invocation_mode=args.invocation_mode,
            )
            print(f"run-mark start: wrote {paths.repository_rel(path)}")
            return 0
        if args.run_mark_action == "complete":
            path = complete_run_manifest(
                args.feature,
                args.run_id,
                status=args.status,
                artifact_paths=args.artifact,
                invoked_surface=args.invoked_surface,
                invocation_mode=args.invocation_mode,
            )
            print(f"run-mark complete: wrote {paths.repository_rel(path)}")
            return 0
    except (FileNotFoundError, ValueError) as error:
        print(f"run-mark {args.run_mark_action}: {error}")
        return 1
    print(f"run-mark: unknown action {args.run_mark_action}")
    return 1


def command_run_stats(args: argparse.Namespace) -> int:
    archive_path = resolve_existing_dir(args.feature) if args.feature else None
    archive_label: str | None = None
    runtime_summary: dict[str, Any] | None = None
    if archive_path and is_archive_run_stats_path(archive_path):
        runtime_summary = load_runtime_summary(archive_path)
        if runtime_summary:
            entries = [
                run_stats_entry_from_dict(item)
                for item in raw_list_value(runtime_summary.get("runs"))
                if isinstance(item, dict)
            ]
        else:
            runtime_summary = build_archive_runtime_summary(archive_path)
            entries = [
                run_stats_entry_from_dict(item)
                for item in raw_list_value(runtime_summary.get("runs"))
                if isinstance(item, dict)
            ]
        archive_label = paths.repository_rel(archive_path)
    else:
        entries = [build_run_stats_entry(path) for path in iter_run_dirs(args.feature)]
    entries.sort(key=latest_activity, reverse=not archive_label)
    limit = args.limit
    if args.feature:
        selected = entries[:limit]
        payload = {
            "feature": runtime_summary.get("feature") if runtime_summary else archive_feature(archive_path) if archive_path and archive_label else args.feature,
            "archive_path": archive_label,
            "runs": [run_stats_to_dict(entry) for entry in selected],
            "total_elapsed_seconds": sum(entry.elapsed_seconds or 0 for entry in selected),
            "autorun_groups": autorun_groups(selected),
        }
        if runtime_summary:
            payload["summary_path"] = runtime_summary.get("summary_path")
            payload["generated_at"] = runtime_summary.get("generated_at")
            payload["total_elapsed_seconds"] = runtime_summary.get("total_elapsed_seconds")
            payload["total_elapsed"] = runtime_summary.get("total_elapsed")
            payload["archive_wall_clock_seconds"] = runtime_summary.get("archive_wall_clock_seconds")
            payload["archive_wall_clock"] = runtime_summary.get("archive_wall_clock")
            payload["autorun_groups"] = raw_list_value(runtime_summary.get("autorun_groups"))
            payload["warnings"] = list_value(runtime_summary.get("warnings"))
        elif archive_label:
            archive_total = archive_wall_clock(selected)
            if archive_total is not None:
                payload["archive_wall_clock_seconds"] = archive_total
                payload["archive_wall_clock"] = format_elapsed(archive_total, "completed")
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0
        print(f"feature: {payload['feature']}")
        if archive_label:
            print(f"archive: {archive_label}")
        if payload.get("summary_path"):
            print(f"summary: {payload['summary_path']}")
        print("")
        print("  run-id                    command      status            elapsed")
        for entry in selected:
            print(
                f"  {entry.run_id:<25} {entry.command:<12} {entry.status:<17} "
                f"{format_elapsed(entry.elapsed_seconds, entry.status)}"
            )
        total = payload["total_elapsed_seconds"]
        print("")
        print(f"  total: {payload.get('total_elapsed') or format_elapsed(total if isinstance(total, int) else None, 'completed')}")
        if "archive_wall_clock" in payload:
            print(f"  archive wall-clock: {payload['archive_wall_clock']}")
        for group in payload["autorun_groups"]:
            print(f"  autorun {group['autorun_id']}: {group['elapsed']}")
        warnings = sorted(set(list_value(payload.get("warnings")) or [warning for entry in selected for warning in entry.warnings]))
        if warnings:
            print("")
            for warning in warnings:
                print(f"  warning: {warning}")
        return 0

    latest_by_feature: dict[str, RunStatsEntry] = {}
    for entry in entries:
        latest_by_feature.setdefault(entry.feature, entry)
    selected_features = sorted(latest_by_feature.values(), key=latest_activity, reverse=True)[:limit]
    payload = {
        "features": [run_stats_to_dict(entry) for entry in selected_features],
        "shown": len(selected_features),
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    print("features:")
    print("")
    print("  feature                    latest-run                command      status            elapsed")
    for entry in selected_features:
        feature_label = entry.feature if len(entry.feature) <= 26 else entry.feature[:23] + "..."
        print(
            f"  {feature_label:<26} {entry.run_id:<25} {entry.command:<12} "
            f"{entry.status:<17} {format_elapsed(entry.elapsed_seconds, entry.status)}"
        )
    print("")
    print(f"  shown: {len(selected_features)} features")
    return 0
