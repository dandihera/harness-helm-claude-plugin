from __future__ import annotations

import argparse
import datetime as dt

from . import paths
from .docs import Doc, is_archive, is_draft, is_excluded, is_index, is_pending, load_docs
from .frontmatter import list_value
from .schema import load_schema
from .utils import now_kst, print_report, write_text


def include_in_index(doc: Doc, schema: dict | None = None) -> bool:
    if schema and is_excluded(doc, schema):
        return False
    if is_index(doc) or is_archive(doc):
        return False
    if is_draft(doc) or is_pending(doc):
        return False
    return True


def minimal_line(doc: Doc) -> str:
    security = doc.frontmatter.get("security", "unknown")
    status = doc.frontmatter.get("status", "unknown")
    dtype = doc.frontmatter.get("type", "unknown")
    if security in {"regulated", "confidential"}:
        return f"- [{doc.title}]({paths.rel_link('../' + doc.rel.removeprefix('docs/'))}) — `{dtype}`, `{status}`, `{security}`"
    return f"- [{doc.title}]({paths.rel_link('../' + doc.rel.removeprefix('docs/'))}) — `{dtype}`, `{status}`"


def command_index(args: argparse.Namespace) -> int:
    schema = load_schema()
    docs = load_docs()
    target = paths.DOCS / "_indexes"
    target.mkdir(parents=True, exist_ok=True)
    indexed = [doc for doc in docs if include_in_index(doc, schema)]
    rejected = [
        doc for doc in docs if doc.rel.startswith("docs/30_decisions/") and doc.path.name.endswith(".rejected.md")
    ]
    generated_header = schema["generated_header"]
    kb = [generated_header, "", "# KB Index", ""]
    for doc in indexed:
        kb.append(minimal_line(doc))
    if rejected:
        kb.extend(["", "## Do Not Use", ""])
        for doc in rejected:
            phrases = ", ".join(list_value(doc.frontmatter.get("ai_avoid_phrases"))) or "see document"
            kb.append(f"- [{doc.title}]({paths.rel_link('../' + doc.rel.removeprefix('docs/'))}) — avoid: {phrases}")
    write_text(target / "KB_INDEX.md", "\n".join(kb) + "\n")

    domains = schema["domains"]
    domain_lines = [generated_header, "", "# Domain Index", ""]
    for domain in sorted(domains):
        items = [
            doc
            for doc in indexed
            if f"docs/10_domain/{domain}/" in doc.rel
            or domain in list_value(doc.frontmatter.get("tags"))
            or domain in list_value(doc.frontmatter.get("module"))
            or domain in list_value(doc.frontmatter.get("domain"))
        ]
        if items:
            domain_lines.extend([f"## {domain}", ""])
            domain_lines.extend(minimal_line(doc) for doc in items)
            domain_lines.append("")
    write_text(target / "DOMAIN_INDEX.md", "\n".join(domain_lines).rstrip() + "\n")

    tag_map: dict[str, list[Doc]] = {}
    for doc in indexed:
        for tag in list_value(doc.frontmatter.get("tags")):
            tag_map.setdefault(tag, []).append(doc)
    tag_lines = [generated_header, "", "# Tag Index", ""]
    for tag in sorted(tag_map):
        tag_lines.extend([f"## {tag}", ""])
        tag_lines.extend(minimal_line(doc) for doc in tag_map[tag])
        tag_lines.append("")
    write_text(target / "TAG_INDEX.md", "\n".join(tag_lines).rstrip() + "\n")

    print(f"kb-index: wrote {target / 'KB_INDEX.md'}")
    print(f"kb-index: wrote {target / 'DOMAIN_INDEX.md'}")
    print(f"kb-index: wrote {target / 'TAG_INDEX.md'}")
    return 0


def command_stale(args: argparse.Namespace) -> int:
    schema = load_schema()
    docs = load_docs()
    current = now_kst()
    warnings: list[str] = []
    for doc in docs:
        if is_excluded(doc, schema):
            continue
        age = (current - doc.mtime.astimezone(current.tzinfo)).days
        status = doc.frontmatter.get("status")
        if status == "draft" and age >= args.draft_days:
            warnings.append(f"{doc.rel}: draft for {age} days.")
        if status == "pending" and age >= args.pending_days:
            warnings.append(f"{doc.rel}: pending for {age} days.")
        if status == "deprecated" and not doc.frontmatter.get("related"):
            warnings.append(f"{doc.rel}: deprecated without replacement.")
        if doc.frontmatter.get("confidence") == "high":
            evidence = schema["confidence_high_evidence_fields"]
            if not any(doc.frontmatter.get(key) for key in evidence):
                warnings.append(f"{doc.rel}: confidence=high evidence should be reviewed.")
        if not doc.frontmatter.get("owner") and doc.frontmatter:
            warnings.append(f"{doc.rel}: owner is empty.")
        if doc.frontmatter.get("security") in {"regulated", "confidential"}:
            warnings.append(f"{doc.rel}: {doc.frontmatter.get('security')} document needs owner review.")

    harness_root = paths.ROOT / ".harness-helm" / "runs"
    if harness_root.exists():
        for path in harness_root.rglob("*"):
            if not path.is_dir():
                continue
            age = (current - dt.datetime.fromtimestamp(path.stat().st_mtime, tz=current.tzinfo)).days
            if path.name == "raw" and age >= args.harness_raw_days:
                warnings.append(f"{path.relative_to(paths.ROOT)}: raw staging older than {age} days; cleanup first.")
            if path.name in {"normalized", "promotion-candidates"} and age >= args.harness_normalized_days:
                warnings.append(f"{path.relative_to(paths.ROOT)}: staging older than {age} days; cleanup candidate.")
    print_report("kb-stale", [], warnings)
    return 0
