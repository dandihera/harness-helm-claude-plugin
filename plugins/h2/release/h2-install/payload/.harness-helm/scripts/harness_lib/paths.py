from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DOCS = ROOT / "docs"
SCHEMA_PATH = ROOT / ".harness-helm" / "h2-schema.yml"
CARTRIDGE_PATH = ROOT / ".harness-helm" / "h2-cartridge.yml"
COMPOUND_POLICY_PATH = ROOT / ".harness-helm" / "h2-compound.yml"

RUN_ID_PATTERN = re.compile(r"^\d{8}-\d{6}-h2-[a-z][a-z0-9-]*$")


def rel_link(path: str) -> str:
    return path.replace(" ", "%20")


def has_path_escape(value: str) -> bool:
    path = Path(value)
    return path.is_absolute() or any(part == ".." for part in path.parts)


def safe_path_segment(value: str, label: str) -> str:
    if not value or "/" in value or "\\" in value or value in {".", ".."}:
        raise ValueError(f"{label} must be a single safe path segment")
    if has_path_escape(value):
        raise ValueError(f"{label} must not escape the repository")
    return value


def validate_run_id(value: str) -> str:
    if not RUN_ID_PATTERN.match(value):
        raise ValueError(f"invalid run-id: {value}")
    return value


def resolve_under_root(rel_path: str, root: Path, label: str) -> Path:
    if has_path_escape(rel_path):
        raise ValueError(f"{label} must be a relative path under repository root")
    path = (root / rel_path).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"{label} must stay under repository root") from exc
    return path


def repository_rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def display_path(path: Path) -> str:
    return repository_rel(path)

