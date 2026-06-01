from __future__ import annotations

import dataclasses
import datetime as dt
import fnmatch
from pathlib import Path
from typing import Any

from . import paths
from .frontmatter import parse_frontmatter
from .utils import read_text


@dataclasses.dataclass
class Doc:
    path: Path
    rel: str
    frontmatter: dict[str, Any]
    body: str
    title: str
    mtime: dt.datetime


def iter_markdown(root: Path | None = None) -> list[Path]:
    root = root or paths.DOCS
    if not root.exists():
        return []
    return sorted(
        path
        for path in root.rglob("*.md")
        if ".git" not in path.parts and path.is_file()
    )


def title_from_body(body: str, path: Path) -> str:
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem


def load_docs() -> list[Doc]:
    docs: list[Doc] = []
    for path in iter_markdown():
        text = read_text(path)
        fm, body = parse_frontmatter(text)
        stat = path.stat()
        docs.append(
            Doc(
                path=path,
                rel=path.relative_to(paths.ROOT).as_posix(),
                frontmatter=fm,
                body=body,
                title=title_from_body(body, path),
                mtime=dt.datetime.fromtimestamp(stat.st_mtime, tz=dt.timezone.utc),
            )
        )
    return docs


def is_archive(doc: Doc) -> bool:
    return doc.rel.startswith("docs/_archive/") or doc.rel.startswith("docs/archive/")


def is_index(doc: Doc) -> bool:
    return doc.rel.startswith("docs/_indexes/")


def is_excluded(doc: Doc, schema: dict[str, Any], key: str = "lint_index") -> bool:
    raw = schema.get("exclude_paths", {})
    if not isinstance(raw, dict):
        return False
    value = raw.get(key, [])
    patterns = [str(pattern) for pattern in value] if isinstance(value, list) else [str(value)]
    return any(fnmatch.fnmatch(doc.rel, pattern) for pattern in patterns)


def is_draft(doc: Doc) -> bool:
    return doc.path.name.endswith(".draft.md") or doc.frontmatter.get("status") == "draft"


def is_pending(doc: Doc) -> bool:
    return doc.path.name.endswith(".pending.md") or doc.frontmatter.get("status") == "pending"

