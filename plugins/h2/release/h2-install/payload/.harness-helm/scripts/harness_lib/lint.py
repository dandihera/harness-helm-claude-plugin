from __future__ import annotations

import argparse

from .docs import Doc, is_archive, is_excluded, is_index, load_docs
from .frontmatter import list_value
from .schema import decision_suffix, generated_header_ok, load_compound_policy, load_schema, validate_doc_id
from .utils import print_report


def is_compound_generated_doc(doc: Doc) -> bool:
    return doc.frontmatter.get("generated_by") == "h2-compound"


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
            warnings.append(f"{doc.rel}: tags missing; TAG_INDEX routing may be weak.")
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

