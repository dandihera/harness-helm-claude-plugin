from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Any

from .target_surface import TARGET_SMOKE_EXCLUDED_PATHS, TARGET_SMOKE_REQUIRED_PATHS
from .utils import now_kst, read_text


INSTALL_MANIFEST_SCHEMA_VERSION = 1
INSTALL_MARKER_VERSION = "v1"
INSTALL_MANIFEST_KINDS = {"copy", "copy_dir", "copy_if_absent", "managed"}
INSTALL_MARKER_BEGIN_RE = re.compile(r"<!--\s*harness-helm:managed:begin\s+(v\d+)\s*-->")
INSTALL_MARKER_END_RE = re.compile(r"<!--\s*harness-helm:managed:end\s+(v\d+)\s*-->")
INSTALL_VERSION_RE = re.compile(r"^v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


@dataclasses.dataclass
class InstallRule:
    kind: str
    source: str
    destination: str
    line_no: int


def parse_install_manifest(text: str) -> tuple[list[InstallRule], list[str]]:
    rules: list[InstallRule] = []
    errors: list[str] = []
    seen: set[str] = set()
    for idx, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) != 3:
            errors.append(f"line {idx}: expected 'kind source destination', got {len(parts)} tokens")
            continue
        kind, source, destination = parts
        if kind not in INSTALL_MANIFEST_KINDS:
            errors.append(f"line {idx}: unknown kind '{kind}'")
            continue
        if kind == "copy_dir" and not source.endswith("/"):
            errors.append(f"line {idx}: copy_dir source must end with '/'")
        if ".." in Path(source).parts or ".." in Path(destination).parts:
            errors.append(f"line {idx}: '..' is not allowed in paths")
        if destination.startswith("/"):
            errors.append(f"line {idx}: destination must be relative")
        if destination in seen:
            errors.append(f"line {idx}: duplicate destination '{destination}'")
        seen.add(destination)
        rules.append(InstallRule(kind=kind, source=source, destination=destination, line_no=idx))
    return rules, errors


def validate_manifest_coverage(
    rules: list[InstallRule],
    required: list[str],
    excluded: list[str],
) -> list[str]:
    errors: list[str] = []
    destinations = [Path(rule.destination.rstrip("/")) for rule in rules]
    for req in required:
        req_path = Path(req)
        covered = False
        for dest in destinations:
            if dest == req_path:
                covered = True
                break
            try:
                dest.relative_to(req_path)
                covered = True
                break
            except ValueError:
                pass
            try:
                req_path.relative_to(dest)
                covered = True
                break
            except ValueError:
                pass
        if not covered:
            errors.append(f"manifest does not cover required surface: {req}")
    for exc in excluded:
        exc_path = Path(exc)
        for dest in destinations:
            if dest == exc_path:
                errors.append(f"manifest references excluded surface: {exc} (via {dest})")
                break
            try:
                dest.relative_to(exc_path)
                errors.append(f"manifest references excluded surface: {exc} (via {dest})")
                break
            except ValueError:
                continue
    return errors


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def apply_managed_block(
    target_file: Path,
    body: str,
    marker_version: str = INSTALL_MARKER_VERSION,
) -> tuple[str, str | None, str]:
    """Return (new_text, before_sha256_or_None, action)."""
    block = (
        f"<!-- harness-helm:managed:begin {marker_version} -->\n"
        f"{body.rstrip()}\n"
        f"<!-- harness-helm:managed:end {marker_version} -->\n"
    )
    if not target_file.exists():
        return block, None, "inserted"
    original = read_text(target_file)
    before_sha = _sha256_text(original)
    begins = list(INSTALL_MARKER_BEGIN_RE.finditer(original))
    ends = list(INSTALL_MARKER_END_RE.finditer(original))
    if len(begins) != len(ends):
        raise ValueError(f"{target_file}: marker pair mismatch ({len(begins)} begin, {len(ends)} end)")
    if len(begins) > 1:
        raise ValueError(f"{target_file}: multiple managed-block pairs are not supported")
    if not begins:
        suffix = "" if original.endswith("\n") else "\n"
        new_text = original + suffix + "\n" + block
        return new_text, before_sha, "inserted"
    begin = begins[0]
    end = ends[0]
    if end.start() < begin.end():
        raise ValueError(f"{target_file}: end marker appears before begin marker")
    # Preserve original whitespace before/after the marker pair so user content
    # added after the managed block stays idempotent on re-runs.
    new_text = original[: begin.start()] + block.rstrip("\n") + original[end.end():]
    if _sha256_text(new_text) == before_sha:
        return new_text, before_sha, "unchanged"
    return new_text, before_sha, "updated"


def _atomic_write_bytes(dest: Path, data: bytes, timestamp: str) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + f".tmp-{timestamp}")
    tmp.write_bytes(data)
    os.replace(tmp, dest)


def _atomic_copy(src: Path, dest: Path, timestamp: str) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + f".tmp-{timestamp}")
    shutil.copy2(src, tmp)
    os.replace(tmp, dest)


def _maybe_backup(dest: Path, target: Path, timestamp: str) -> str | None:
    if not dest.is_file():
        return None
    bak = dest.with_name(dest.name + f".bak-{timestamp}")
    shutil.copy2(dest, bak)
    return str(bak.relative_to(target))


def iter_copy_dir_files(src: Path) -> list[Path]:
    return sorted(
        path
        for path in src.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    )


def _install_marker_version(path: Path) -> tuple[int, int, int] | None:
    version = path.stem.replace("h2-install-", "", 1)
    match = INSTALL_VERSION_RE.match(version)
    if not match:
        return None
    return tuple(int(part) for part in match.groups())


def resolve_package_version(package_root: Path) -> str:
    version_files = []
    for path in package_root.glob("h2-install-v*.txt"):
        parsed = _install_marker_version(path)
        if parsed is not None:
            version_files.append((parsed, path))
    if not version_files:
        return "unknown"
    return max(version_files, key=lambda item: item[0])[1].stem.replace("h2-install-", "", 1)


def command_install(args: argparse.Namespace) -> int:
    target = Path(args.target).resolve()
    if not (target / ".git").exists() and not args.allow_non_git:
        print(f"install: target {target} has no .git/. Use --allow-non-git to override.", file=sys.stderr)
        return 1
    if not args.dry_run:
        target.mkdir(parents=True, exist_ok=True)

    if args.manifest:
        manifest_path = Path(args.manifest).resolve()
    else:
        manifest_path = (Path.cwd() / "h2-install" / "MANIFEST.txt").resolve()
    if not manifest_path.is_file():
        print(f"install: manifest not found: {manifest_path}", file=sys.stderr)
        return 1
    package_root = manifest_path.parent

    package_version = resolve_package_version(package_root)

    rules, parse_errors = parse_install_manifest(read_text(manifest_path))
    if parse_errors:
        for err in parse_errors:
            print(f"install: manifest parse error: {err}", file=sys.stderr)
        return 1

    coverage_errors = validate_manifest_coverage(
        rules, TARGET_SMOKE_REQUIRED_PATHS, TARGET_SMOKE_EXCLUDED_PATHS
    )
    if coverage_errors:
        for err in coverage_errors:
            print(f"install: {err}", file=sys.stderr)
        return 1

    payload_entries: list[dict[str, Any]] = []
    managed_entries: list[dict[str, Any]] = []
    backups: list[str] = []
    errors: list[str] = []
    status = "ok"
    now = now_kst()
    timestamp = now.strftime("%Y%m%dT%H%M%S%z")
    installed_at = now.isoformat()

    for rule in rules:
        src = (package_root / rule.source).resolve()
        dest = (target / rule.destination).resolve()
        try:
            dest.relative_to(target)
        except ValueError:
            errors.append(f"line {rule.line_no}: destination escapes target ({rule.destination})")
            status = "partial"
            continue

        if rule.kind == "copy":
            if not src.is_file():
                errors.append(f"line {rule.line_no}: source missing: {rule.source}")
                status = "partial"
                continue
            new_sha = _sha256_file(src)
            action = "unchanged"
            if not dest.is_file() or _sha256_file(dest) != new_sha:
                action = "copied"
            if action == "copied":
                if args.dry_run:
                    print(f"  would copy {rule.source} -> {rule.destination}")
                else:
                    if args.backup:
                        b = _maybe_backup(dest, target, timestamp)
                        if b:
                            backups.append(b)
                    _atomic_copy(src, dest, timestamp)
            reported = "skipped" if args.dry_run and action == "copied" else action
            payload_entries.append({
                "kind": "copy",
                "source": rule.source,
                "destination": rule.destination,
                "action": reported,
                "sha256": new_sha,
            })

        elif rule.kind == "copy_if_absent":
            if not src.is_file():
                errors.append(f"line {rule.line_no}: source missing: {rule.source}")
                status = "partial"
                continue
            new_sha = _sha256_file(src)
            action = "unchanged"
            if not dest.is_file():
                action = "copied"
            if action == "copied":
                if args.dry_run:
                    print(f"  would copy-if-absent {rule.source} -> {rule.destination}")
                else:
                    _atomic_copy(src, dest, timestamp)
            reported = "skipped" if args.dry_run and action == "copied" else action
            payload_entries.append({
                "kind": "copy_if_absent",
                "source": rule.source,
                "destination": rule.destination,
                "action": reported,
                "sha256": new_sha,
            })

        elif rule.kind == "copy_dir":
            if not src.is_dir():
                errors.append(f"line {rule.line_no}: source dir missing: {rule.source}")
                status = "partial"
                continue
            sub_action = "unchanged"
            files = iter_copy_dir_files(src)
            for f in files:
                rel = f.relative_to(src)
                dst_file = dest / rel
                new_sha = _sha256_file(f)
                if dst_file.is_file() and _sha256_file(dst_file) == new_sha:
                    continue
                sub_action = "copied"
                if args.dry_run:
                    print(f"  would copy {rule.source}{rel} -> {rule.destination}{rel}")
                    continue
                if args.backup:
                    b = _maybe_backup(dst_file, target, timestamp)
                    if b:
                        backups.append(b)
                _atomic_copy(f, dst_file, timestamp)
            reported = "skipped" if args.dry_run and sub_action == "copied" else sub_action
            payload_entries.append({
                "kind": "copy_dir",
                "source": rule.source,
                "destination": rule.destination,
                "action": reported,
                "files": len(files),
            })

        else:  # managed
            if not src.is_file():
                errors.append(f"line {rule.line_no}: managed template missing: {rule.source}")
                status = "partial"
                continue
            body = read_text(src)
            try:
                new_text, before_sha, action = apply_managed_block(dest, body)
            except ValueError as e:
                errors.append(f"line {rule.line_no}: managed-block error: {e}")
                status = "partial"
                continue
            if action == "unchanged":
                managed_entries.append({
                    "file": rule.destination,
                    "marker": "harness-helm:managed",
                    "marker_version": INSTALL_MARKER_VERSION,
                    "action": "unchanged",
                    "before_sha256": before_sha,
                    "after_sha256": before_sha,
                })
                continue
            if args.dry_run:
                print(f"  would update managed block in {rule.destination}")
                managed_entries.append({
                    "file": rule.destination,
                    "marker": "harness-helm:managed",
                    "marker_version": INSTALL_MARKER_VERSION,
                    "action": "skipped",
                    "before_sha256": before_sha,
                    "after_sha256": None,
                })
            else:
                if args.backup:
                    b = _maybe_backup(dest, target, timestamp)
                    if b:
                        backups.append(b)
                _atomic_write_bytes(dest, new_text.encode("utf-8"), timestamp)
                managed_entries.append({
                    "file": rule.destination,
                    "marker": "harness-helm:managed",
                    "marker_version": INSTALL_MARKER_VERSION,
                    "action": action,
                    "before_sha256": before_sha,
                    "after_sha256": _sha256_text(new_text),
                })

    record = {
        "schema_version": INSTALL_MANIFEST_SCHEMA_VERSION,
        "package_version": package_version,
        "installed_at": installed_at,
        "target": str(target),
        "status": status,
        "options": {
            "allow_non_git": bool(args.allow_non_git),
            "dry_run": bool(args.dry_run),
            "backup": bool(args.backup),
        },
        "payload": payload_entries,
        "managed_blocks": managed_entries,
        "backups": backups,
        "errors": errors,
    }
    record_path = target / ".harness-helm" / "install-manifest.json"
    if args.dry_run:
        print(f"  would write install-manifest.json to {record_path}")
    else:
        record_path.parent.mkdir(parents=True, exist_ok=True)
        record_path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if not args.quiet:
        print(
            f"install: status={status} target={target} "
            f"payload={len(payload_entries)} managed={len(managed_entries)} "
            f"backups={len(backups)} errors={len(errors)}"
        )
        for err in errors:
            print(f"  error: {err}", file=sys.stderr)

    return 0 if status == "ok" else 1
