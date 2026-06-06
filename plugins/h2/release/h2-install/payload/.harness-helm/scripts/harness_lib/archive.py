from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
from pathlib import Path

from . import paths
from .frontmatter import parse_frontmatter, render_frontmatter
from .run_lifecycle import command_from_run_id, stage_runtime_summary_json_path, stage_runtime_summary_md_path, write_runtime_summary
from .utils import now_kst, read_text, write_text


def phase_dirs() -> list[tuple[str, list[Path]]]:
    return [
        ("01_plan", [paths.DOCS / "01_plan", paths.DOCS / "01-plan"]),
        ("02_design", [paths.DOCS / "02_design", paths.DOCS / "02-design"]),
        ("03_review", [paths.DOCS / "03_review", paths.DOCS / "03-analysis"]),
        ("04_report", [paths.DOCS / "04_report", paths.DOCS / "04-report"]),
    ]


def find_phase_sources(feature: str) -> list[tuple[str, Path]]:
    found: list[tuple[str, Path]] = []
    for phase, roots in phase_dirs():
        for root in roots:
            if not root.exists():
                continue
            direct_file = root / f"{feature}.md"
            if direct_file.exists():
                found.append((phase, direct_file))
            direct_dir = root / feature
            if direct_dir.exists():
                found.append((phase, direct_dir))
            for path in root.rglob(f"*{feature}*.md"):
                if path not in [item[1] for item in found]:
                    found.append((phase, path))
    return found


def archived_text(text: str) -> str:
    fm, body = parse_frontmatter(text)
    if not fm:
        return text
    fm["status"] = "archived"
    return render_frontmatter(fm) + body.lstrip("\n")


def archive_destination(dest_root: Path, phase: str, src: Path) -> Path:
    phase_number = phase.split("_", 1)[0]
    phase_suffix = re.sub(r"^\d+_", "", phase)
    if src.is_dir():
        return dest_root / f"{phase_number}.{src.name}.{phase_suffix}"
    # docs/03_review/{type}/{feature}.md: 동일 feature가 여러 review type(code/qa/security/cross)을
    # 가질 때 destination 충돌을 막기 위해 review type을 파일명에 포함한다.
    if phase == "03_review" and src.parent.name in {"code", "qa", "security", "cross"}:
        return dest_root / f"{phase_number}.{src.stem}.{src.parent.name}.{phase_suffix}{src.suffix}"
    return dest_root / f"{phase_number}.{src.stem}.{phase_suffix}{src.suffix}"


def cleanup_archived_run(feature: str, dry_run: bool, dest_root: Path | None = None) -> None:
    run_path = paths.ROOT / ".harness-helm" / "runs" / feature
    if not run_path.exists():
        return
    if dest_root is not None:
        runs_dest = dest_root / "runs"
        print(f"  {'would move' if dry_run else 'move'} {run_path.relative_to(paths.ROOT)} -> {runs_dest.relative_to(paths.ROOT)}")
        if not dry_run:
            runs_dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(run_path), str(runs_dest))
    else:
        print(f"  {'would remove' if dry_run else 'remove'} {run_path.relative_to(paths.ROOT)}")
        if not dry_run:
            shutil.rmtree(run_path)


def stage_label_from_command(command: str | None, fallback: str = "run") -> str:
    if command:
        return command.removeprefix("h2-")
    return fallback


def archived_run_command(run_dir: Path) -> str | None:
    manifest_path = run_dir / "manifest.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(read_text(manifest_path))
        except json.JSONDecodeError:
            manifest = {}
        if isinstance(manifest, dict) and isinstance(manifest.get("command"), str):
            return manifest["command"]
    try:
        return command_from_run_id(run_dir.name)
    except ValueError:
        return None


def artifact_stage_label(command: str | None, artifact: Path) -> str:
    command_label = stage_label_from_command(command)
    if command == "h2-autorun":
        autorun_artifact_stages = {
            "archive-plan": "archive",
            "autorun-summary": "autorun",
            "build": "build",
            "compound-candidates": "compound",
            "review": "review",
            "report": "report",
            "test": "test",
        }
        return autorun_artifact_stages.get(artifact.stem, command_label)
    return command_label


def child_step_from_autorun_artifact(artifact: Path) -> str | None:
    return {
        "analysis": "h2-analysis",
        "build": "h2-build",
        "test": "h2-test",
        "review": "h2-review",
        "report": "h2-report",
        "compound-candidates": "h2-compound",
        "archive-plan": "h2-archive",
    }.get(artifact.stem)


def validate_autorun_timing_evidence(feature: str) -> list[str]:
    errors: list[str] = []
    runs_root = paths.ROOT / ".harness-helm" / "runs" / feature
    if not runs_root.exists():
        return errors
    for run_dir in sorted(runs_root.glob("*-h2-autorun")):
        if not run_dir.is_dir() or not paths.RUN_ID_PATTERN.match(run_dir.name):
            continue
        for artifact in sorted(run_dir.glob("*.md")):
            step = child_step_from_autorun_artifact(artifact)
            if step is None:
                continue
            manifest = run_dir / "snapshots" / step / "manifest.json"
            if not manifest.exists():
                errors.append(
                    f"{artifact.relative_to(paths.ROOT).as_posix()}: missing autorun timing evidence "
                    f"{manifest.relative_to(paths.ROOT).as_posix()}."
                )
    return errors


def unresolved_autorun_resolution(manifest: dict[str, object]) -> str | None:
    resolution = manifest.get("autorun_resolution")
    if not isinstance(resolution, str) or not resolution:
        return None
    if resolution == "unresolved" or resolution.startswith("blocked:"):
        return resolution
    return None


def validate_autorun_iteration_resolution(feature: str) -> list[str]:
    errors: list[str] = []
    runs_root = paths.ROOT / ".harness-helm" / "runs" / feature
    if not runs_root.exists():
        return errors
    for run_dir in sorted(runs_root.glob("*-h2-autorun")):
        if not run_dir.is_dir() or not paths.RUN_ID_PATTERN.match(run_dir.name):
            continue
        # Snapshot manifests are the authoritative child-stage evidence. Fall back to
        # run manifests only when structured snapshot evidence is absent.
        manifest_paths = sorted(run_dir.glob("snapshots/*/manifest.json"))
        if not manifest_paths:
            manifest_paths = [run_dir / "manifest.json"] if (run_dir / "manifest.json").exists() else []
        for manifest_path in manifest_paths:
            try:
                manifest = json.loads(read_text(manifest_path))
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(manifest, dict):
                continue
            resolution = unresolved_autorun_resolution(manifest)
            if resolution is None:
                continue
            step = manifest.get("step") or manifest.get("command") or manifest_path.parent.name
            errors.append(
                f"{manifest_path.relative_to(paths.ROOT).as_posix()}: unresolved autorun iteration "
                f"{resolution} at {step}."
            )
    return errors


def flattened_artifact_name(command: str | None, artifact: Path) -> str:
    label = artifact_stage_label(command, artifact)
    if artifact.name == "context-pack.md":
        return f"{label}-context-pack.md"
    return artifact.name


def collision_safe_destination(runs_root: Path, name: str, stage_label: str, seen: dict[str, int]) -> Path:
    if name not in seen and not (runs_root / name).exists():
        seen[name] = 1
        return runs_root / name
    source = Path(name)
    index = seen.get(name, 1) + 1
    while True:
        target = runs_root / f"{source.stem}--{stage_label}-{index}{source.suffix}"
        if not target.exists():
            seen[name] = index
            return target
        index += 1


def prune_archived_runs(dest_root: Path) -> None:
    runs_root = dest_root / "runs"
    if not runs_root.exists() or not runs_root.is_dir():
        return
    seen: dict[str, int] = {}
    for child in sorted(runs_root.iterdir()):
        if child.is_file():
            child.unlink()
            continue
        if not child.is_dir():
            continue
        if not paths.RUN_ID_PATTERN.match(child.name):
            shutil.rmtree(child)
            continue
        command = archived_run_command(child)
        for item in sorted(child.iterdir()):
            if item.is_file():
                if item.suffix == ".md":
                    stage_label = artifact_stage_label(command, item)
                    target_name = flattened_artifact_name(command, item)
                    target = collision_safe_destination(runs_root, target_name, stage_label, seen)
                    shutil.move(str(item), str(target))
                continue
            shutil.rmtree(item)
        shutil.rmtree(child)


def complete_archived_archive_snapshots(dest_root: Path, completed_at: dt.datetime) -> None:
    for manifest_path in sorted((dest_root / "runs").glob("*/snapshots/h2-archive/manifest.json")):
        try:
            manifest = json.loads(read_text(manifest_path))
        except json.JSONDecodeError:
            continue
        if not isinstance(manifest, dict):
            continue
        if manifest.get("status") == "completed" and manifest.get("completed_at"):
            continue
        manifest["command"] = manifest.get("command") or "h2-archive"
        manifest["status"] = "completed"
        manifest["started_at"] = manifest.get("started_at") or manifest.get("created_at") or completed_at.isoformat()
        manifest["completed_at"] = completed_at.isoformat()
        manifest["autorun_id"] = manifest.get("autorun_id") or manifest.get("run_id")
        artifacts = manifest.get("artifact_paths") if isinstance(manifest.get("artifact_paths"), list) else []
        for artifact in [
            paths.repository_rel(stage_runtime_summary_md_path(dest_root)),
        ]:
            if artifact not in artifacts:
                artifacts.append(artifact)
        manifest["artifact_paths"] = artifacts
        write_text(manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
        parent_manifest_path = manifest_path.parents[2] / "manifest.json"
        if parent_manifest_path.exists():
            try:
                parent_manifest = json.loads(read_text(parent_manifest_path))
            except json.JSONDecodeError:
                parent_manifest = {}
            if isinstance(parent_manifest, dict) and parent_manifest.get("command") == "h2-autorun":
                parent_manifest["status"] = "completed"
                parent_manifest["completed_at"] = completed_at.isoformat()
                parent_artifacts = (
                    parent_manifest.get("artifact_paths")
                    if isinstance(parent_manifest.get("artifact_paths"), list)
                    else []
                )
                summary_artifact = paths.repository_rel(stage_runtime_summary_md_path(dest_root))
                if summary_artifact not in parent_artifacts:
                    parent_artifacts.append(summary_artifact)
                parent_manifest["artifact_paths"] = parent_artifacts
                write_text(parent_manifest_path, json.dumps(parent_manifest, ensure_ascii=False, indent=2) + "\n")


def command_cleanup_runs(args: argparse.Namespace) -> int:
    root = paths.ROOT / ".harness-helm" / "runs"
    if not root.exists():
        print("harness cleanup-runs: .harness-helm/runs does not exist.")
        return 0
    current = now_kst()
    candidates: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_dir():
            continue
        age = (current - dt.datetime.fromtimestamp(path.stat().st_mtime, tz=current.tzinfo)).days
        if path.name == "raw" and age >= args.raw_days:
            candidates.append(path)
        if path.name in {"normalized", "promotion-candidates", "snapshots", "restore-backups"} and age >= args.normalized_days:
            candidates.append(path)
    if not candidates:
        print("harness cleanup-runs: no cleanup candidates.")
        return 0
    for path in candidates:
        print(f"{'would remove' if args.dry_run else 'remove'} {path.relative_to(paths.ROOT)}")
        if not args.dry_run:
            shutil.rmtree(path)
    return 0


def command_archive(args: argparse.Namespace) -> int:
    feature = args.feature
    try:
        paths.safe_path_segment(feature, "feature")
    except ValueError as error:
        print(f"harness archive: {error}")
        return 1
    now = now_kst()
    month = args.month or now.strftime("%Y-%m")
    try:
        paths.safe_path_segment(month, "month")
    except ValueError as error:
        print(f"harness archive: {error}")
        return 1
    timestamp = now.strftime("%m%d-%H%M")
    dest_dir_name = f"{timestamp}_{feature}"
    dest_root = paths.DOCS / "_archive" / month / dest_dir_name
    sources = find_phase_sources(feature)
    if not sources:
        print(f"harness archive: no sources found for feature={feature}")
        return 1 if args.strict else 0
    timing_errors = validate_autorun_timing_evidence(feature)
    if timing_errors:
        print("harness archive: missing h2-autorun timing evidence")
        for error in timing_errors:
            print(f"  {error}")
        return 1
    iteration_errors = validate_autorun_iteration_resolution(feature)
    if iteration_errors:
        print("harness archive: unresolved h2-autorun iteration")
        for error in iteration_errors:
            print(f"  {error}")
        return 1
    print(f"harness archive: feature={feature}")
    for phase, src in sources:
        rel_dest = archive_destination(dest_root, phase, src)
        print(f"  {'would move' if args.dry_run else 'move'} {src.relative_to(paths.ROOT)} -> {rel_dest.relative_to(paths.ROOT)}")
        if args.dry_run:
            continue
        rel_dest.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            if rel_dest.exists():
                shutil.rmtree(rel_dest)
            shutil.move(str(src), str(rel_dest))
            for md in rel_dest.rglob("*.md"):
                write_text(md, archived_text(read_text(md)))
        else:
            text = archived_text(read_text(src))
            write_text(rel_dest, text)
            src.unlink()
    if args.dry_run:
        print(f"  would write transient stage runtime summary {stage_runtime_summary_json_path(dest_root).relative_to(paths.ROOT)}")
        print(f"  would write runs summary markdown {stage_runtime_summary_md_path(dest_root).relative_to(paths.ROOT)}")
        print(f"  would prune transient stage runtime summary {stage_runtime_summary_json_path(dest_root).relative_to(paths.ROOT)}")
        cleanup_archived_run(feature, dry_run=True, dest_root=dest_root)
    if not args.dry_run:
        cleanup_archived_run(feature, dry_run=False, dest_root=dest_root)
        complete_archived_archive_snapshots(dest_root, completed_at=now)
        write_runtime_summary(dest_root, generated_at=now)
        prune_archived_runs(dest_root)
    return 0
