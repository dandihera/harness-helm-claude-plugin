from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
from pathlib import Path

from . import paths
from .frontmatter import parse_frontmatter, render_frontmatter
from .run_lifecycle import stage_runtime_summary_json_path, stage_runtime_summary_md_path, write_runtime_summary
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
    suffix = re.sub(r"^\d+_", "", phase)
    if src.is_dir():
        return dest_root / f"{src.name}.{suffix}"
    # docs/03_review/{type}/{feature}.md: 동일 feature가 여러 review type(code/qa/security/cross)을
    # 가질 때 destination 충돌을 막기 위해 review type을 파일명에 포함한다.
    if phase == "03_review" and src.parent.name in {"code", "qa", "security", "cross"}:
        return dest_root / f"{src.stem}.{src.parent.name}.{suffix}{src.suffix}"
    return dest_root / f"{src.stem}.{suffix}{src.suffix}"


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
            paths.repository_rel(dest_root / "manifest.md"),
            paths.repository_rel(stage_runtime_summary_json_path(dest_root)),
            paths.repository_rel(stage_runtime_summary_md_path(dest_root)),
        ]:
            if artifact not in artifacts:
                artifacts.append(artifact)
        manifest["artifact_paths"] = artifacts
        write_text(manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")


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
    timestamp = now.strftime("%m%d-%H%M%S")
    dest_dir_name = f"{timestamp}_{feature}"
    dest_root = paths.DOCS / "_archive" / month / dest_dir_name
    sources = find_phase_sources(feature)
    if not sources:
        print(f"harness archive: no sources found for feature={feature}")
        return 1 if args.strict else 0
    owner = None
    for _, src in sources:
        if src.is_file():
            owner = parse_frontmatter(read_text(src))[0].get("owner")
            if owner:
                break
    manifest = {
        "feature": feature,
        "archived_at": now.isoformat(),
        "archive_path": dest_root.relative_to(paths.ROOT).as_posix(),
        "owner": owner,
        "source_trace": (args.source_trace or args.source_issue) or None,
        "source_pr": args.source_pr or None,
        "phase_docs_present": sorted({phase for phase, _ in sources}),
        "purpose": "Archive completed 01~04 PDCA artifacts; body excluded from default retrieval.",
    }
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
    manifest_path = dest_root / "manifest.md"
    if args.dry_run:
        print(f"  would write manifest {manifest_path.relative_to(paths.ROOT)}")
        print(f"  would write stage runtime summary {stage_runtime_summary_json_path(dest_root).relative_to(paths.ROOT)}")
        print(f"  would write stage runtime summary markdown {stage_runtime_summary_md_path(dest_root).relative_to(paths.ROOT)}")
        cleanup_archived_run(feature, dry_run=True, dest_root=dest_root)
    if not args.dry_run:
        lines = ["---"]
        for key, value in manifest.items():
            if isinstance(value, list):
                lines.append(f"{key}:")
                for item in value:
                    lines.append(f"  - {item}")
            elif value is None:
                lines.append(f"{key}: null")
            else:
                lines.append(f"{key}: {value}")
        lines.extend(["---", "", f"# Archive Manifest: {feature}", "", "Archive manifest metadata only. Do not include detailed implementation content here.", ""])
        write_text(manifest_path, "\n".join(lines))
        cleanup_archived_run(feature, dry_run=False, dest_root=dest_root)
        complete_archived_archive_snapshots(dest_root, completed_at=now)
        write_runtime_summary(dest_root, generated_at=now)
    return 0
