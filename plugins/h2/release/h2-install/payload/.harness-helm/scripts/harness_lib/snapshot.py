from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

from . import paths
from .run_lifecycle import normalize_invocation_mode, normalize_invoked_surface, run_root
from .utils import now_kst, read_text, write_text


REWINDABLE_STEPS = {
    "h2-analysis",
    "h2-build",
    "h2-test",
    "h2-review",
    "h2-report",
    "h2-compound",
    "h2-archive",
}
STEP_SNAPSHOT_SCOPE: dict[str, list[str]] = {
    "h2-analysis": [
        "docs/02_design/{feature}.analysis.md",
    ],
    "h2-build": [
        ".harness-helm/runs/{feature}/{run_id}/build.md",
    ],
    "h2-test": [
        ".harness-helm/runs/{feature}/{run_id}/test.md",
    ],
    "h2-review": [
        "docs/03_review/code/{feature}.md",
        "docs/03_review/qa/{feature}.md",
        "docs/03_review/security/{feature}.md",
        "docs/03_review/cross/{feature}.md",
    ],
    "h2-report": [
        "docs/04_report/{feature}.md",
    ],
    "h2-compound": [
        ".harness-helm/runs/{feature}/{run_id}/compound-candidates.md",
    ],
    "h2-archive": [],
}


def validate_rewind_step(step: str) -> str:
    if step not in REWINDABLE_STEPS:
        raise ValueError(f"step must be one of: {', '.join(sorted(REWINDABLE_STEPS))}.")
    return step


def snapshot_root(feature: str, run_id_value: str, step: str) -> Path:
    return run_root(feature, run_id_value) / "snapshots" / validate_rewind_step(step)


def snapshot_manifest_path(feature: str, run_id_value: str, step: str) -> Path:
    return snapshot_root(feature, run_id_value, step) / "manifest.json"


def snapshot_scope_paths(feature: str, run_id_value: str, step: str) -> list[Path]:
    safe_feature = paths.safe_path_segment(feature, "feature")
    safe_run_id = paths.validate_run_id(run_id_value)
    templates = STEP_SNAPSHOT_SCOPE[validate_rewind_step(step)]
    return [paths.ROOT / template.format(feature=safe_feature, run_id=safe_run_id) for template in templates]


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def snapshot_file_path(root: Path, rel: str) -> Path:
    return root / "files" / rel


def archive_residue_paths(feature: str) -> list[str]:
    archive_root = paths.DOCS / "_archive"
    if not archive_root.exists():
        return []
    matches: list[str] = []
    for path in sorted(archive_root.rglob("*")):
        if feature in path.name:
            matches.append(paths.repository_rel(path))
    return matches


def load_snapshot_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError("snapshot not found; rewind requires h2-autorun pre-step snapshots.")
    raw = json.loads(read_text(path))
    if not isinstance(raw, dict):
        raise ValueError("snapshot manifest must be a JSON object.")
    if raw.get("schema_version") != 1:
        raise ValueError("snapshot manifest schema_version must be 1.")
    return raw


def command_snapshot_save(args: argparse.Namespace) -> int:
    try:
        root = snapshot_root(args.feature, args.run_id, args.step)
        snapshot_paths = snapshot_scope_paths(args.feature, args.run_id, args.step)
    except ValueError as error:
        print(f"h2-snapshot save: {error}")
        return 1

    files: list[dict[str, Any]] = []
    for path in snapshot_paths:
        rel = paths.repository_rel(path)
        entry: dict[str, Any] = {
            "path": rel,
            "existed": path.exists(),
            "snapshot_path": None,
            "sha256": None,
            "size": 0,
        }
        if path.exists():
            target = snapshot_file_path(root, rel)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
            entry.update(
                {
                    "snapshot_path": paths.repository_rel(target),
                    "sha256": file_sha256(path),
                    "size": path.stat().st_size,
                }
            )
        files.append(entry)

    created_at = now_kst().isoformat()
    manifest = {
        "schema_version": 1,
        "feature": args.feature,
        "run_id": args.run_id,
        "step": args.step,
        "created_at": created_at,
        "kind": "pre-step-snapshot",
        "command": args.step,
        "status": "running",
        "started_at": created_at,
        "completed_at": None,
        "autorun_id": args.run_id,
        "artifact_paths": [],
        "files": files,
        "archive_residue_policy": "preserve-and-warn",
    }
    invoked_surface = normalize_invoked_surface(getattr(args, "invoked_surface", None))
    if invoked_surface is not None:
        manifest["invoked_surface"] = invoked_surface
    invocation_mode = getattr(args, "invocation_mode", None)
    if invocation_mode is not None:
        manifest["invocation_mode"] = normalize_invocation_mode(invocation_mode)
    write_text(root / "manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(f"h2-snapshot save: wrote {paths.repository_rel(root / 'manifest.json')}")
    return 0


def command_snapshot_complete(args: argparse.Namespace) -> int:
    try:
        manifest_path = snapshot_manifest_path(args.feature, args.run_id, args.step)
        manifest = load_snapshot_manifest(manifest_path)
        if manifest.get("feature") != args.feature or manifest.get("run_id") != args.run_id or manifest.get("step") != args.step:
            raise ValueError("snapshot manifest does not match requested feature/run-id/step.")
        if args.status not in {"completed", "failed", "incomplete"}:
            raise ValueError("status must be completed, failed, or incomplete.")
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as error:
        print(f"h2-snapshot complete: {error}")
        return 1

    artifacts = manifest.get("artifact_paths") if isinstance(manifest.get("artifact_paths"), list) else []
    for artifact in args.artifact or []:
        if artifact not in artifacts:
            artifacts.append(artifact)
    manifest["command"] = manifest.get("command") or args.step
    manifest["status"] = args.status
    manifest["started_at"] = manifest.get("started_at") or manifest.get("created_at") or now_kst().isoformat()
    manifest["completed_at"] = None if args.status == "incomplete" else now_kst().isoformat()
    manifest["autorun_id"] = manifest.get("autorun_id") or args.run_id
    manifest["artifact_paths"] = artifacts
    invoked_surface = normalize_invoked_surface(getattr(args, "invoked_surface", None))
    if invoked_surface is not None:
        manifest["invoked_surface"] = invoked_surface
    invocation_mode = getattr(args, "invocation_mode", None)
    if invocation_mode is not None:
        manifest["invocation_mode"] = normalize_invocation_mode(invocation_mode)
    write_text(manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(f"h2-snapshot complete: wrote {paths.repository_rel(manifest_path)}")
    return 0


def command_snapshot_list(args: argparse.Namespace) -> int:
    try:
        feature = paths.safe_path_segment(args.feature, "feature")
        run_id_filter = paths.validate_run_id(args.run_id) if args.run_id else None
    except ValueError as error:
        print(f"h2-snapshot list: {error}")
        return 1
    feature_root = paths.ROOT / ".harness-helm" / "runs" / feature
    if not feature_root.exists():
        print(f"h2-snapshot list: no runs for feature {feature}")
        return 0
    manifests = sorted(feature_root.glob("*/snapshots/*/manifest.json"))
    if run_id_filter:
        manifests = [path for path in manifests if path.parts[-4] == run_id_filter]
    if not manifests:
        print("h2-snapshot list: no snapshots found.")
        return 0
    for manifest_path in manifests:
        try:
            manifest = load_snapshot_manifest(manifest_path)
            print(f"{manifest.get('run_id')} {manifest.get('step')} {paths.repository_rel(manifest_path)}")
        except (OSError, ValueError, json.JSONDecodeError) as error:
            print(f"{paths.repository_rel(manifest_path)}: invalid manifest ({error})")
    return 0


def render_restore_report(
    manifest: dict[str, Any],
    actions: list[str],
    warnings: list[str],
    dry_run: bool,
) -> str:
    lines = [
        "---",
        "command: h2-rewind",
        f"feature: {manifest.get('feature')}",
        "status: skipped" if dry_run else "status: updated",
        "next:",
        f"  recommended_h2_step: {manifest.get('step')}",
        "---",
        "",
        f"# h2-rewind Restore: {manifest.get('step')}",
        "",
        "## Actions",
        "",
    ]
    lines.extend(f"- {action}" for action in actions)
    if warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in warnings)
    lines.extend(["", "## Next", "", f"- recommended_h2_step: {manifest.get('step')}", ""])
    return "\n".join(lines)


def command_snapshot_restore(args: argparse.Namespace) -> int:
    try:
        manifest_path = snapshot_manifest_path(args.feature, args.run_id, args.step)
        manifest = load_snapshot_manifest(manifest_path)
        if manifest.get("feature") != args.feature or manifest.get("run_id") != args.run_id or manifest.get("step") != args.step:
            raise ValueError("snapshot manifest does not match requested feature/run-id/step.")
    except FileNotFoundError as error:
        print(f"h2-snapshot restore: {error}")
        return 2
    except (ValueError, json.JSONDecodeError) as error:
        print(f"h2-snapshot restore: {error}")
        return 1

    timestamp = now_kst().strftime("%Y%m%d-%H%M%S")
    backup_root = run_root(args.feature, args.run_id) / "restore-backups" / timestamp / args.step
    actions: list[str] = []
    warnings: list[str] = []
    for item in manifest.get("files", []):
        if not isinstance(item, dict):
            print("h2-snapshot restore: manifest files entries must be objects.")
            return 1
        rel = str(item.get("path", ""))
        try:
            active = paths.resolve_under_root(rel, paths.ROOT, "snapshot file path")
        except ValueError as error:
            print(f"h2-snapshot restore: {error}")
            return 1
        backup = backup_root / rel
        existed = bool(item.get("existed"))
        if active.exists():
            actions.append(f"백업: {rel} -> {paths.repository_rel(backup)}")
            if not args.dry_run:
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(active, backup)
        if existed:
            snapshot_rel = str(item.get("snapshot_path") or "")
            try:
                source = paths.resolve_under_root(snapshot_rel, paths.ROOT, "snapshot_path")
            except ValueError as error:
                print(f"h2-snapshot restore: {error}")
                return 1
            if not source.exists():
                print(f"h2-snapshot restore: missing snapshot file {snapshot_rel}")
                return 1
            actions.append(f"복원: {rel} <- {snapshot_rel}")
            if not args.dry_run:
                active.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, active)
        elif active.exists():
            actions.append(f"snapshot 당시 없던 active file 삭제: {rel}")
            if not args.dry_run:
                active.unlink()
        else:
            actions.append(f"없음 유지: {rel}")

    if args.step == "h2-archive":
        residues = archive_residue_paths(args.feature)
        if residues:
            warnings.append("archive residue 보존: " + ", ".join(residues))

    report = render_restore_report(manifest, actions, warnings, args.dry_run)
    restore_path = snapshot_root(args.feature, args.run_id, args.step) / "restore.md"
    if not args.dry_run:
        write_text(restore_path, report)
    print(report)
    if not args.dry_run:
        print(f"h2-snapshot restore: wrote {paths.repository_rel(restore_path)}")
    return 0


def command_snapshot(args: argparse.Namespace) -> int:
    if args.snapshot_action == "save":
        return command_snapshot_save(args)
    if args.snapshot_action == "list":
        return command_snapshot_list(args)
    if args.snapshot_action == "complete":
        return command_snapshot_complete(args)
    if args.snapshot_action == "restore":
        return command_snapshot_restore(args)
    print("h2-snapshot: expected save, list, complete, or restore.")
    return 1


def command_rewind(args: argparse.Namespace) -> int:
    args.snapshot_action = "restore"
    return command_snapshot_restore(args)
