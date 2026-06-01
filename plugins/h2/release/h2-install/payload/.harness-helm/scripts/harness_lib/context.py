from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from . import paths
from .docs import Doc, is_archive, is_excluded, is_index, load_docs
from .frontmatter import list_value
from .index import INDEX_DOMAIN, INDEX_KB, INDEX_TAG, include_in_index
from .run_lifecycle import complete_run_manifest, run_id, run_root, start_run_manifest
from .schema import load_schema
from .utils import write_text


CANONICAL_KNOWLEDGE_ROOTS = (
    "docs/10_domain/",
    "docs/20_specs/",
    "docs/30_decisions/",
    "docs/40_knowledge/",
    "docs/50_operations/",
)
CANONICAL_KNOWLEDGE_LIMIT = 6
TASK_STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "if", "of", "to", "in", "on", "for", "with",
    "from", "by", "at", "as", "is", "are", "was", "were", "be", "been", "do", "does",
    "did", "this", "that", "these", "those", "it", "its", "we", "i", "you", "they",
    "ai", "use", "make", "made", "run", "ran", "see", "saw", "have", "has", "had",
    "및", "또는", "그리고", "위한", "관한", "대한", "하기", "하는", "하여", "위해",
    "있다", "없다", "이다", "되다", "한다", "있는", "없는", "되는", "되었", "통해",
}
RUNTIME_SEED_RULES: list[tuple[set[str], list[str]]] = [
    (
        {"workflow", "h2", "lifecycle", "command", "cartridge", "adapter", "audit", "harness"},
        [
            "README.md", ".harness-helm/h2-cartridge.yml", ".harness-helm/h2-schema.yml",
            ".claude/skills/harness-helm/SKILL.md", ".codex/skills/harness-helm/SKILL.md",
            "docs/10_domain/harness-helm/concepts.md",
        ],
    ),
    (
        {"upstream", "gstack", "superpowers", "compound", "ce", "provider", "surface"},
        [
            ".harness-helm/h2-cartridge.yml",
            ".claude/skills/harness-helm/references/cartridge-command-mapping.md",
            ".claude/skills/harness-helm/references/cartridge-surface-map.md",
        ],
    ),
    (
        {"normalization", "raw", "fixture", "evidence"},
        [
            ".claude/skills/harness-helm/references/cartridge-output-normalization.md",
            ".harness-helm/h2-cartridge.yml",
        ],
    ),
    (
        {"reference", "snapshot", "parity", "drift"},
        [
            ".claude/skills/harness-helm/references/runtime-parity.md",
            "docs/40_knowledge/conventions/guidelines/harness-helm/runtime-reference-selection.md",
        ],
    ),
    (
        {"runbook", "incident", "release", "ops", "deploy"},
        ["docs/50_operations/README.md", ".harness-helm/h2-cartridge.yml"],
    ),
    (
        {"docs", "kb", "lint", "schema", "frontmatter", "template"},
        [".harness-helm/h2-schema.yml"],
    ),
]


def docs_matching_feature(feature: str | None, docs: list[Doc], schema: dict[str, Any]) -> list[Doc]:
    if not feature:
        return []
    matched: list[Doc] = []
    for doc in docs:
        if is_archive(doc) or is_index(doc) or is_excluded(doc, schema):
            continue
        if feature in doc.rel or feature in doc.title or feature in " ".join(list_value(doc.frontmatter.get("tags"))):
            matched.append(doc)
    return matched


def tokenize_task(task: str) -> list[str]:
    if not task:
        return []
    raw = re.findall(r"[a-zA-Z0-9_\-가-힣]+", task.lower())
    seen: set[str] = set()
    tokens: list[str] = []
    for token in raw:
        if len(token) < 2 or token in TASK_STOP_WORDS:
            continue
        if token not in seen:
            seen.add(token)
            tokens.append(token)
    return tokens


def docs_matching_task(tokens: list[str], docs: list[Doc], schema: dict[str, Any], exclude: set[str]) -> list[Doc]:
    if not tokens:
        return []
    scored: list[tuple[int, Doc]] = []
    for doc in docs:
        if is_archive(doc) or is_index(doc) or is_excluded(doc, schema):
            continue
        if doc.rel in exclude:
            continue
        score = 0
        haystack = " ".join([
            doc.rel.lower(),
            doc.title.lower(),
            " ".join(list_value(doc.frontmatter.get("tags"))).lower(),
            " ".join(list_value(doc.frontmatter.get("module"))).lower(),
            " ".join(list_value(doc.frontmatter.get("domain"))).lower(),
        ])
        for token in tokens:
            if token in haystack:
                score += 1
        if score > 0:
            scored.append((score, doc))
    scored.sort(key=lambda pair: (-pair[0], pair[1].rel))
    return [doc for _, doc in scored]


def is_canonical_knowledge_doc(doc: Doc, schema: dict[str, Any]) -> bool:
    if not doc.rel.startswith(CANONICAL_KNOWLEDGE_ROOTS):
        return False
    if doc.rel.startswith("docs/30_decisions/") and doc.path.name.endswith(".rejected.md"):
        return False
    return include_in_index(doc, schema)


def canonical_docs(docs: list[Doc], schema: dict[str, Any]) -> list[Doc]:
    return [doc for doc in docs if is_canonical_knowledge_doc(doc, schema)]


def index_freshness(index_paths: list[Path], candidates: list[Doc]) -> tuple[str, str]:
    missing = [path.relative_to(paths.ROOT).as_posix() for path in index_paths if not path.exists()]
    if missing:
        return "absent", f"index freshness: {', '.join(missing)} 없음; JSONL KB fallback 또는 canonical docs direct scan fallback을 사용했다."
    if not candidates:
        return "ok", "index freshness: JSONL indexes가 존재하며 freshness 비교 대상 canonical docs가 없다."

    oldest_index = min(path.stat().st_mtime for path in index_paths)
    newest_candidate = max(doc.path.stat().st_mtime for doc in candidates)
    if newest_candidate > oldest_index:
        return "stale", "index freshness: canonical docs가 JSONL indexes보다 최신이다. `.harness-helm/scripts/harness kb-index`를 실행한다."
    return "ok", "index freshness: JSONL indexes가 존재하며 canonical docs보다 오래되지 않았다."


def read_jsonl_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            rows.append(value)
    return rows


def load_kb_rows() -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for row in read_jsonl_rows(paths.DOCS / "_indexes" / INDEX_KB):
        if row.get("kind") in {"doc", "avoid"} and isinstance(row.get("path"), str):
            rows[str(row["path"])] = row
    return rows


def route_candidate_paths(tokens: list[str]) -> set[str]:
    if not tokens:
        return set()
    token_set = set(tokens)
    selected: set[str] = set()
    for index_name in (INDEX_DOMAIN, INDEX_TAG):
        for row in read_jsonl_rows(paths.DOCS / "_indexes" / index_name):
            if row.get("kind") != "route":
                continue
            key = str(row.get("key", "")).lower()
            if key not in token_set:
                continue
            row_paths = row.get("paths", [])
            if isinstance(row_paths, list):
                selected.update(str(path) for path in row_paths)
    return selected


def kb_rows_matching_tokens(tokens: list[str], rows: dict[str, dict[str, Any]]) -> set[str]:
    if not tokens:
        return set()
    selected: set[str] = set()
    for rel, row in rows.items():
        if row.get("kind") != "doc":
            continue
        title = "" if row.get("title") == "[regulated]" else str(row.get("title", ""))
        haystack = " ".join(
            [
                rel.lower(),
                title.lower(),
                " ".join(str(item) for item in row.get("tags", []) if isinstance(row.get("tags", []), list)).lower(),
                " ".join(str(item) for item in row.get("module", []) if isinstance(row.get("module", []), list)).lower(),
                " ".join(str(item) for item in row.get("domain", []) if isinstance(row.get("domain", []), list)).lower(),
                str(row.get("type", "")).lower(),
                str(row.get("status", "")).lower(),
            ]
        )
        if any(token in haystack for token in tokens):
            selected.add(rel)
    return selected


def docs_by_rel(docs: list[Doc]) -> dict[str, Doc]:
    return {doc.rel: doc for doc in docs}


def docs_matching_canonical_knowledge(
    tokens: list[str],
    feature: str | None,
    docs: list[Doc],
    schema: dict[str, Any],
) -> list[Doc]:
    candidates = canonical_docs(docs, schema)
    if not candidates:
        return []
    scored: list[tuple[int, Doc]] = []
    for doc in candidates:
        score = 0
        haystack = " ".join([
            doc.rel.lower(),
            doc.title.lower(),
            " ".join(list_value(doc.frontmatter.get("tags"))).lower(),
            " ".join(list_value(doc.frontmatter.get("module"))).lower(),
            " ".join(list_value(doc.frontmatter.get("domain"))).lower(),
            " ".join(list_value(doc.frontmatter.get("related"))).lower(),
            " ".join(list_value(doc.frontmatter.get("source_trace"))).lower(),
        ])
        if feature and feature in haystack:
            score += 3
        for token in tokens:
            if token in haystack:
                score += 1
        if "docs/40_knowledge/" in doc.rel and {"compound", "canonical", "knowledge", "h2-compound"} & set(tokens):
            score += 2
        if score > 0:
            scored.append((score, doc))
    scored.sort(key=lambda pair: (-pair[0], pair[1].rel))
    return [doc for _, doc in scored[:CANONICAL_KNOWLEDGE_LIMIT]]


def canonical_selected_by(doc: Doc, freshness_state: str) -> list[str]:
    tags = ["canonical-knowledge"]
    if doc.rel.startswith("docs/40_knowledge/") or "canonical-promotion" in list_value(doc.frontmatter.get("tags")):
        tags.append("compound-loop")
    return with_freshness(tags, freshness_state)


def with_freshness(tags: list[str], freshness_state: str) -> list[str]:
    if freshness_state == "absent":
        tags.append("index-absent")
    elif freshness_state == "stale":
        tags.append("index-stale")
    return tags


def runtime_seed_docs(tokens: list[str], existing: set[str]) -> list[str]:
    if not tokens:
        return []
    token_set = set(tokens)
    seeds: list[str] = []
    seen: set[str] = set(existing)
    for keywords, path_values in RUNTIME_SEED_RULES:
        if token_set & keywords:
            for path in path_values:
                if path not in seen and (paths.ROOT / path).exists():
                    seeds.append(path)
                    seen.add(path)
    return seeds


def command_context(args: argparse.Namespace) -> int:
    schema = load_schema()
    docs = load_docs()
    command_run_id = args.run_id or run_id("h2-context")
    try:
        target = run_root(args.feature, command_run_id) / "context-pack.md"
    except ValueError as error:
        print(f"h2-context: {error}")
        return 1
    if not args.dry_run:
        start_run_manifest(
            args.feature,
            command_run_id,
            "h2-context",
            task=args.task,
            autorun_id=args.autorun_id,
        )
    feature_docs = docs_matching_feature(args.feature, docs, schema)
    tokens = tokenize_task(args.task)
    feature_tokens = tokenize_task(args.feature or "")
    selection_tokens = list(dict.fromkeys(tokens + feature_tokens))
    feature_doc_rels = {doc.rel for doc in feature_docs}
    task_docs = docs_matching_task(tokens, docs, schema, feature_doc_rels)
    index_docs = [paths.DOCS / "_indexes" / name for name in (INDEX_KB, INDEX_DOMAIN, INDEX_TAG)]
    canonical_candidates = canonical_docs(docs, schema)
    freshness_state, freshness_line = index_freshness(index_docs, canonical_candidates)
    kb_rows = load_kb_rows()
    docs_lookup = docs_by_rel(docs)
    structured_rels = route_candidate_paths(selection_tokens)
    structured_selection_note = "structured index route lookup"
    if freshness_state != "ok" or not structured_rels:
        structured_rels = kb_rows_matching_tokens(selection_tokens, kb_rows)
        structured_selection_note = "structured index KB fallback"
    structured_docs = [
        docs_lookup[rel]
        for rel in sorted(structured_rels)
        if rel in docs_lookup and not is_archive(docs_lookup[rel]) and not is_index(docs_lookup[rel]) and not is_excluded(docs_lookup[rel], schema)
    ]
    canonical_entries = [
        (doc.rel, canonical_selected_by(doc, freshness_state))
        for doc in docs_matching_canonical_knowledge(tokens, args.feature, docs, schema)
    ]

    primary_entries: list[tuple[str, list[str]]] = []
    for doc in structured_docs[:8]:
        primary_entries.append((doc.rel, with_freshness(["structured-index", "task-token"], freshness_state)))
    primary_rels = {rel for rel, _ in primary_entries}
    for doc in feature_docs[:8]:
        if doc.rel not in primary_rels:
            primary_entries.append((doc.rel, with_freshness(["feature-match"], freshness_state)))
            primary_rels.add(doc.rel)
    for doc in task_docs[:6]:
        if doc.rel not in primary_rels:
            primary_entries.append((doc.rel, with_freshness(["task-token"], freshness_state)))
            primary_rels.add(doc.rel)
    for rel in runtime_seed_docs(tokens, primary_rels):
        primary_entries.append((rel, ["runtime-seed"]))
        primary_rels.add(rel)

    supporting_entries: list[tuple[str, list[str]]] = []
    for doc in feature_docs[8:16]:
        if doc.rel not in primary_rels:
            supporting_entries.append((doc.rel, with_freshness(["feature-match"], freshness_state)))
    for doc in task_docs[6:14]:
        rels = primary_rels | {rel for rel, _ in supporting_entries}
        if doc.rel not in rels:
            supporting_entries.append((doc.rel, with_freshness(["task-token"], freshness_state)))

    excluded = [
        "docs/_archive/** body",
        "docs/_templates/**",
        ".harness-helm/runs/_templates/**",
        "draft/pending documents unless task-scoped",
        "regulated documents unless explicitly task-scoped",
    ]
    def render_entry(entry: tuple[str, list[str]]) -> str:
        rel, selected_by = entry
        return f"- {rel} (selected_by: {', '.join(selected_by)})"

    lines = [
        "---",
        "command: h2-context",
        f"feature: {args.feature or 'null'}",
        "status: updated",
        "next:",
        f"  recommended_h2_step: {args.next or 'null'}",
        "---",
        "",
        f"# h2-context — {args.task}",
        "",
        "## Context Pack",
        "",
        "### primary_docs",
    ]
    if primary_entries:
        lines.extend(render_entry(entry) for entry in primary_entries)
    else:
        lines.append("- 없음")
    lines.extend(["", "### supporting_docs"])
    if supporting_entries:
        lines.extend(render_entry(entry) for entry in supporting_entries)
    else:
        lines.append("- 없음")
    lines.extend(["", "### canonical_knowledge"])
    if canonical_entries:
        lines.extend(render_entry(entry) for entry in canonical_entries)
    else:
        lines.append("- 없음")
    lines.extend(["", "### excluded_by_policy"])
    lines.extend(f"- {item}" for item in excluded)
    lines.extend(
        [
            "",
            "### assumptions",
            "- `_indexes`는 routing hint이며 원본 문서가 canonical reference다.",
            f"- h2-context는 JSONL index를 `{structured_selection_note}` 방식으로 파싱하고, index 파일 자체를 primary_docs에 싣지 않는다.",
            "- index가 stale 또는 absent이면 JSONL KB fallback 또는 canonical docs direct scan을 사용하고 `index-absent` 또는 `index-stale`로 표시한다.",
            "- `selected_by`는 문서 선택 출처를 표시한다: structured-index | feature-match | task-token | runtime-seed | canonical-knowledge | compound-loop | index-absent | index-stale.",
            "",
            "## Artifacts",
            "",
            "### created",
            f"- {target.relative_to(paths.ROOT).as_posix()}",
            "",
            "### updated",
            "- 없음",
            "",
            "### suggested",
            "- 없음",
            "",
            "## Routing",
            "",
            "- target_docs: []",
            "- archive_candidate: false",
            "- promotion_candidates: []",
            "",
            "## Verification",
            "",
            "### required",
            "- 선택된 문서가 작업과 맞는지 확인한 뒤 구현 context로 사용한다.",
            "",
            "### completed",
            "- context pack 생성 완료",
            "- canonical knowledge 직접 확인 완료",
            *([f"- {freshness_line}"] if freshness_state == "ok" else []),
            "",
            "### not_verified",
            "- context 관련성 사람 검토 필요",
            *([f"- {freshness_line}"] if freshness_state != "ok" else []),
            "",
            "## Next",
            "",
            f"- recommended_h2_step: {args.next or 'null'}",
            "",
        ]
    )
    content = "\n".join(lines)
    if args.dry_run:
        print(content)
        return 0
    write_text(target, content)
    complete_run_manifest(
        args.feature,
        command_run_id,
        status="completed",
        artifact_paths=[target.relative_to(paths.ROOT).as_posix()],
    )
    print(f"h2-context: wrote {target.relative_to(paths.ROOT)}")
    return 0
