from __future__ import annotations

import argparse
import datetime as dt
import json

from . import paths
from .docs import Doc, is_archive, is_draft, is_excluded, is_index, is_pending, load_docs
from .frontmatter import list_value
from .schema import load_schema
from .utils import now_kst, print_report, write_text


INDEX_KB = "index_kb.jsonl"
INDEX_DOMAIN = "index_domain.jsonl"
INDEX_TAG = "index_tag.jsonl"
LEGACY_INDEXES = ("KB_INDEX.md", "DOMAIN_INDEX.md", "TAG_INDEX.md")


def include_in_index(doc: Doc, schema: dict | None = None) -> bool:
    if schema and is_excluded(doc, schema):
        return False
    if is_index(doc) or is_archive(doc):
        return False
    if is_draft(doc) or is_pending(doc):
        return False
    return True


def jsonl_line(row: dict) -> str:
    return json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def jsonl_meta(index_name: str) -> dict:
    return {
        "kind": "meta",
        "schema_version": 1,
        "index": index_name,
        "generated_by": "harness kb-index",
        "source": "docs",
        "do_not_edit": True,
    }


def sorted_values(value: object) -> list[str]:
    return sorted({item for item in list_value(value) if item})


def doc_row(doc: Doc) -> dict:
    security = str(doc.frontmatter.get("security", "internal"))
    title = doc.title
    tags = sorted_values(doc.frontmatter.get("tags"))
    domains = sorted_values(doc.frontmatter.get("domain"))
    modules = sorted_values(doc.frontmatter.get("module"))
    if security == "regulated":
        title = "[regulated]"
        tags = []
        domains = []
        modules = []
    row = {
        "kind": "doc",
        "title": title,
        "path": doc.rel,
        "type": str(doc.frontmatter.get("type", "unknown")),
        "status": str(doc.frontmatter.get("status", "unknown")),
        "security": security,
        "tags": tags,
        "domain": domains,
        "module": modules,
    }
    related = sorted_values(doc.frontmatter.get("related"))
    if related:
        row["related"] = related
    source_trace = doc.frontmatter.get("source_trace") or doc.frontmatter.get("source_pr")
    if source_trace:
        row["source_trace"] = str(source_trace)
    return row


def avoid_row(doc: Doc) -> dict:
    row = {
        "kind": "avoid",
        "path": doc.rel,
        "avoid": sorted_values(doc.frontmatter.get("ai_avoid_phrases")) or ["see document"],
        "reason": "rejected decision",
    }
    use_instead = sorted_values(doc.frontmatter.get("use_instead"))
    if use_instead:
        row["use_instead"] = use_instead
    revisit_trigger = doc.frontmatter.get("revisit_trigger")
    if revisit_trigger:
        row["revisit_trigger"] = str(revisit_trigger)
    return row


def write_jsonl(path, rows: list[dict]) -> None:
    write_text(path, "\n".join(jsonl_line(row) for row in rows) + "\n")


def add_route(route_map: dict[tuple[str, str], set[str]], route_type: str, key: str, path: str) -> None:
    if key:
        route_map.setdefault((route_type, key), set()).add(path)


def route_rows(index_name: str, route_map: dict[tuple[str, str], set[str]]) -> list[dict]:
    rows = [jsonl_meta(index_name)]
    for route_type, key in sorted(route_map):
        rows.append(
            {
                "kind": "route",
                "route_type": route_type,
                "key": key,
                "paths": sorted(route_map[(route_type, key)]),
            }
        )
    return rows


def command_index(args: argparse.Namespace) -> int:
    schema = load_schema()
    docs = load_docs()
    target = paths.DOCS / "_indexes"
    target.mkdir(parents=True, exist_ok=True)
    indexed = [doc for doc in docs if include_in_index(doc, schema)]
    rejected = [
        doc for doc in docs if doc.rel.startswith("docs/30_decisions/") and doc.path.name.endswith(".rejected.md")
    ]

    kb_rows = [jsonl_meta("kb")]
    kb_rows.extend(doc_row(doc) for doc in indexed)
    kb_rows.extend(avoid_row(doc) for doc in rejected)
    write_jsonl(target / INDEX_KB, kb_rows)

    domain_route_map: dict[tuple[str, str], set[str]] = {}
    tag_route_map: dict[tuple[str, str], set[str]] = {}
    domains = schema["domains"]
    for doc in indexed:
        for domain in sorted(domains):
            if (
                f"docs/10_domain/{domain}/" in doc.rel
                or domain in list_value(doc.frontmatter.get("tags"))
                or domain in list_value(doc.frontmatter.get("domain"))
            ):
                add_route(domain_route_map, "domain", domain, doc.rel)
        for module in sorted_values(doc.frontmatter.get("module")):
            add_route(domain_route_map, "module", module, doc.rel)
        for tag in sorted_values(doc.frontmatter.get("tags")):
            add_route(tag_route_map, "tag", tag, doc.rel)

    write_jsonl(target / INDEX_DOMAIN, route_rows("domain", domain_route_map))
    write_jsonl(target / INDEX_TAG, route_rows("tag", tag_route_map))

    for name in LEGACY_INDEXES:
        legacy = target / name
        if legacy.exists():
            legacy.unlink()

    print(f"kb-index: wrote {target / INDEX_KB}")
    print(f"kb-index: wrote {target / INDEX_DOMAIN}")
    print(f"kb-index: wrote {target / INDEX_TAG}")
    for name in LEGACY_INDEXES:
        print(f"kb-index: removed legacy {target / name}")
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
