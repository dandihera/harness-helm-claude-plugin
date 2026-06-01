from __future__ import annotations

import argparse
import json
from pathlib import Path

from .docs import Doc, is_archive, is_excluded, is_index, load_docs
from .frontmatter import list_value
from .index import INDEX_DOMAIN, INDEX_KB, INDEX_TAG
from .schema import decision_suffix, generated_header_ok, load_compound_policy, load_schema, validate_doc_id
from .utils import print_report


def is_compound_generated_doc(doc: Doc) -> bool:
    return doc.frontmatter.get("generated_by") == "h2-compound"


def read_jsonl(path: Path, hard: list[str]) -> list[dict]:
    rows: list[dict] = []
    if not path.exists():
        hard.append(f"{path.relative_to(path.parents[2]) if len(path.parents) > 2 else path}: missing generated JSONL index.")
        return rows
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as error:
            hard.append(f"{path}: line {lineno}: invalid JSON ({error.msg}).")
            continue
        if not isinstance(value, dict):
            hard.append(f"{path}: line {lineno}: JSONL row must be an object.")
            continue
        rows.append(value)
    return rows


def validate_meta(path: Path, rows: list[dict], expected_index: str, hard: list[str]) -> None:
    if not rows:
        hard.append(f"{path}: JSONL index is empty.")
        return
    meta = rows[0]
    if meta.get("kind") != "meta":
        hard.append(f"{path}: first row must be kind=meta.")
    for field in ("schema_version", "index", "generated_by", "do_not_edit"):
        if field not in meta:
            hard.append(f"{path}: meta row missing {field}.")
    if meta.get("index") != expected_index:
        hard.append(f"{path}: meta index must be {expected_index}.")
    if meta.get("do_not_edit") is not True:
        hard.append(f"{path}: meta do_not_edit must be true.")


def validate_jsonl_indexes(hard: list[str]) -> None:
    from . import paths

    schema = load_schema()
    domains = sorted(schema.get("domains", set()))
    index_root = paths.DOCS / "_indexes"
    kb_path = index_root / INDEX_KB
    domain_path = index_root / INDEX_DOMAIN
    tag_path = index_root / INDEX_TAG
    kb_rows = read_jsonl(kb_path, hard)
    domain_rows = read_jsonl(domain_path, hard)
    tag_rows = read_jsonl(tag_path, hard)
    validate_meta(kb_path, kb_rows, "kb", hard)
    validate_meta(domain_path, domain_rows, "domain", hard)
    validate_meta(tag_path, tag_rows, "tag", hard)

    known_paths: set[str] = set()
    route_sources: dict[tuple[str, str], set[str]] = {}
    for row in kb_rows[1:]:
        kind = row.get("kind")
        path = row.get("path")
        if kind == "doc":
            required = ("title", "path", "type", "status", "security", "tags", "domain", "module")
            for field in required:
                if field not in row:
                    hard.append(f"{kb_path}: doc row missing {field}: {row}")
            if isinstance(path, str):
                known_paths.add(path)
                row_tags = row.get("tags", []) if isinstance(row.get("tags", []), list) else []
                row_domains = row.get("domain", []) if isinstance(row.get("domain", []), list) else []
                for domain in domains:
                    if f"docs/10_domain/{domain}/" in path or domain in row_tags or domain in row_domains:
                        route_sources.setdefault(("domain", domain), set()).add(path)
                for tag in row_tags:
                    route_sources.setdefault(("tag", str(tag)), set()).add(path)
                for module in row.get("module", []) if isinstance(row.get("module"), list) else []:
                    route_sources.setdefault(("module", str(module)), set()).add(path)
            else:
                hard.append(f"{kb_path}: doc row path must be a string: {row}")
            for field in ("tags", "domain", "module"):
                if field in row and not isinstance(row[field], list):
                    hard.append(f"{kb_path}: doc row {field} must be an array: {row}")
        elif kind == "avoid":
            for field in ("path", "avoid", "reason"):
                if field not in row:
                    hard.append(f"{kb_path}: avoid row missing {field}: {row}")
            if isinstance(path, str):
                known_paths.add(path)
            else:
                hard.append(f"{kb_path}: avoid row path must be a string: {row}")
            if "avoid" in row and not isinstance(row["avoid"], list):
                hard.append(f"{kb_path}: avoid row avoid must be an array: {row}")
            if "use_instead" in row and not isinstance(row["use_instead"], list):
                hard.append(f"{kb_path}: avoid row use_instead must be an array: {row}")
        elif kind != "meta":
            hard.append(f"{kb_path}: unsupported row kind {kind}.")

    for path, rows, expected_types in (
        (domain_path, domain_rows, {"domain", "module"}),
        (tag_path, tag_rows, {"tag"}),
    ):
        seen_routes: set[tuple[str, str]] = set()
        for row in rows[1:]:
            if row.get("kind") != "route":
                hard.append(f"{path}: unsupported row kind {row.get('kind')}; expected route.")
                continue
            route_type = str(row.get("route_type", ""))
            key = str(row.get("key", ""))
            route_paths = row.get("paths")
            if route_type not in expected_types:
                hard.append(f"{path}: invalid route_type {route_type}.")
            if not key:
                hard.append(f"{path}: route row missing key: {row}")
            if not isinstance(route_paths, list):
                hard.append(f"{path}: route row paths must be an array: {row}")
                continue
            route_key = (route_type, key)
            seen_routes.add(route_key)
            if route_paths != sorted(route_paths):
                hard.append(f"{path}: route paths must be sorted lexicographically for {route_type}:{key}.")
            if len(route_paths) != len(set(route_paths)):
                hard.append(f"{path}: route paths contain duplicates for {route_type}:{key}.")
            for route_path in route_paths:
                if route_path not in known_paths:
                    hard.append(f"{path}: route path missing from {INDEX_KB}: {route_path}")
            expected_paths = route_sources.get(route_key, set())
            if expected_paths and set(route_paths) != expected_paths:
                hard.append(f"{path}: route drift for {route_type}:{key}.")
        for route_key in sorted(route_sources):
            route_type, key = route_key
            if route_type in expected_types and route_key not in seen_routes:
                hard.append(f"{path}: missing route for {route_type}:{key}.")


def command_lint(args: argparse.Namespace) -> int:
    schema = load_schema()
    compound_policy, _compound_policy_source, compound_warnings = load_compound_policy(schema)
    docs = load_docs()
    hard: list[str] = []
    warnings: list[str] = list(compound_warnings)
    ids: dict[str, str] = {}
    retrieval_required = list_value(
        compound_policy.get("retrieval_hook_policy", {}).get("required", [])
        if isinstance(compound_policy.get("retrieval_hook_policy"), dict)
        else []
    )

    validate_jsonl_indexes(hard)

    for doc in docs:
        fm = doc.frontmatter
        if is_index(doc) and not is_excluded(doc, schema) and not generated_header_ok(doc, schema):
            hard.append(f"{doc.rel}: _indexes file is missing generated header.")
        if "99_indexes" in doc.body or "99_indexes" in doc.rel:
            allowed = doc.rel.endswith(".rejected.md") and "Do Not Use" in doc.body
            if not allowed:
                hard.append(f"{doc.rel}: deprecated expression 99_indexes is not allowed.")

        if is_archive(doc) or is_index(doc) or is_excluded(doc, schema):
            continue

        missing = [field for field in schema["required"] if field not in fm]
        if missing:
            hard.append(f"{doc.rel}: missing required frontmatter fields: {', '.join(missing)}")
        for field in ("type", "status", "security", "confidence", "target_runtime"):
            if field in fm and fm[field] not in schema.get(field, set()):
                hard.append(f"{doc.rel}: invalid {field}={fm[field]}")
        doc_id = fm.get("id")
        if doc_id:
            doc_id = str(doc_id)
            id_error = validate_doc_id(doc, doc_id)
            if id_error:
                hard.append(id_error)
            if doc_id in ids:
                hard.append(f"{doc.rel}: duplicate id {doc_id} also in {ids[doc_id]}")
            ids[doc_id] = doc.rel

        suffix = decision_suffix(doc.path, schema)
        if doc.rel.startswith("docs/30_decisions/") and suffix:
            if fm.get("status") != suffix:
                hard.append(f"{doc.rel}: decision suffix/status mismatch ({suffix} != {fm.get('status')})")
            if suffix == "rejected" and "ai_avoid_phrases" not in fm:
                hard.append(f"{doc.rel}: rejected decision must define ai_avoid_phrases.")

        if fm.get("confidence") == "high":
            evidence = schema["confidence_high_evidence_fields"]
            if not any(fm.get(key) for key in evidence):
                hard.append(f"{doc.rel}: confidence=high requires evidence field.")
        if fm.get("status") in {"draft", "pending"}:
            warnings.append(f"{doc.rel}: {fm.get('status')} document should be triaged if stale.")
        if fm.get("status") == "deprecated" and not fm.get("related"):
            warnings.append(f"{doc.rel}: deprecated document has no related replacement.")
        if fm.get("type") == "decision" and fm.get("status") == "accepted" and not fm.get("related"):
            warnings.append(f"{doc.rel}: accepted decision has empty related.")
        related_cookbooks = [
            item
            for item in list_value(fm.get("related"))
            if item.startswith("cookbooks/") or item.startswith("./cookbooks/") or item.startswith("../cookbooks/")
        ]
        if related_cookbooks:
            hard.append(
                f"{doc.rel}: related must not reference cookbooks/**; use source_references instead ({', '.join(related_cookbooks)})."
            )
        invalid_modules = [module for module in list_value(fm.get("module")) if module not in schema.get("modules", set())]
        if invalid_modules:
            hard.append(f"{doc.rel}: invalid module values: {', '.join(invalid_modules)}")
        if not list_value(fm.get("tags")):
            warnings.append(f"{doc.rel}: tags missing; tag-based search-time retrieval may be weak.")
        if not (fm.get("source_trace") or fm.get("source_pr")) and fm.get("type") in {"plan", "design", "analysis", "report"}:
            warnings.append(f"{doc.rel}: PDCA doc has no source_trace/source_pr.")
        if is_compound_generated_doc(doc):
            missing_retrieval = [field for field in retrieval_required if not list_value(fm.get(field))]
            if missing_retrieval:
                warnings.append(
                    f"{doc.rel}: h2-compound generated doc missing retrieval hook fields: {', '.join(missing_retrieval)}."
                )

    print_report("kb-lint", hard, warnings)
    return 1 if hard and args.strict else 0
