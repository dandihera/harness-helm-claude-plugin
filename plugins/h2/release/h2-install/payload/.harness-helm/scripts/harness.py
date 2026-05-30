#!/usr/bin/env python3
"""HERA Harness Helm enforcement scripts."""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import fnmatch
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
SCHEMA_PATH = ROOT / ".harness-helm" / "h2-schema.yml"
CARTRIDGE_PATH = ROOT / ".harness-helm" / "h2-cartridge.yml"
DEFAULT_GENERATED_HEADER = "<!-- AUTO-GENERATED: do not edit manually. Run .harness-helm/scripts/kb-index.sh. -->"
CANONICAL_TEMPLATES = {
    "plan": "plan.md",
    "design": "design.md",
    "analysis": "analysis.md",
    "review": "review.md",
    "report": "report.md",
    "domain": "domain.md",
    "spec": "spec.md",
    "decision": "decision.md",
    "solution": "solution.md",
    "convention": "convention.md",
    "learning": "learning.md",
    "runbook": "runbook.md",
    "incident": "incident.md",
    "release": "release.md",
}
STAGING_TEMPLATES = {
    "context-pack.md": {"Context Pack", "Artifacts", "Routing", "Verification", "Next"},
    "build.md": {"Context Pack", "Artifacts", "Routing", "Verification", "Next"},
    "test.md": {"Context Pack", "Artifacts", "Routing", "Verification", "Next"},
    "compound-candidates.md": {"Context Pack", "Artifacts", "Routing", "Verification", "Next"},
    "archive-plan.md": {"Context Pack", "Artifacts", "Routing", "Verification", "Next"},
    "cartridge-mapping.md": {"Context Pack", "Artifacts", "Routing", "Verification", "Next"},
}
REQUIRED_LINT_INDEX_EXCLUDES = {
    "docs/_templates/**",
    ".harness-helm/runs/_templates/**",
    "docs/01_plan/README.md",
    "docs/02_design/README.md",
    "docs/03_review/README.md",
    "docs/04_report/README.md",
    "docs/10_domain/README.md",
    "docs/20_specs/README.md",
    "docs/30_decisions/README.md",
    "docs/40_knowledge/**/README.md",
    "docs/50_operations/**/README.md",
    "docs/_indexes/INDEX_GUIDE.md",
}
TEMPLATE_TARGETS = {
    "plan": "docs/01_plan/{feature}.md",
    "design": "docs/02_design/{feature}.md",
    "analysis": "docs/02_design/{feature}.analysis.md",
    "review": "docs/03_review/code/{feature}.md",
    "report": "docs/04_report/{feature}.md",
    "domain": "docs/10_domain/{domain}/{topic}.md",
    "spec": "docs/20_specs/{area}/{topic}.md",
    "decision": "docs/30_decisions/project/{number}-{topic}.{status}.md",
    "solution": "docs/40_knowledge/solutions/{topic}.md",
    "convention": "docs/40_knowledge/conventions/{topic}.md",
    "learning": "docs/40_knowledge/learnings/{topic}.md",
    "runbook": "docs/50_operations/runbooks/{topic}.md",
    "incident": "docs/50_operations/incidents/{topic}.md",
    "release": "docs/50_operations/releases/{topic}.md",
}
LOG_START = "=== [DANDI] :: Harness Helm (_start_) ==="
LOG_END = "=== [DANDI] :: Harness Helm (__end__) ==="
RUN_ID_PATTERN = re.compile(r"^\d{8}-\d{6}-h2-[a-z][a-z0-9-]*$")
DECISION_SUFFIX_PATTERN = re.compile(r"\.([a-z][a-z0-9_-]*)\.md$")
ROUTING_PLACEHOLDER_PATTERN = re.compile(r"{([^{}]+)}")
ALLOWED_ROUTING_PLACEHOLDERS = {"feature", "run-id", "type", "topic"}
# This list is the cartridge/reference validation surface, not a 1:1 list of
# local CLI subcommands. Only h2-context is directly implemented by harness.py.
EXPECTED_COMMANDS = {
    "h2-context",
    "h2-plan",
    "h2-design",
    "h2-analysis",
    "h2-report",
    "h2-cartridge",
    "h2-build",
    "h2-test",
    "h2-review",
    "h2-compound",
    "h2-archive",
    "h2-ops",
}
H2_CLI_NOTE = (
    "Note: among the 12 h2-* lifecycle commands, only h2-context is directly "
    "implemented by this CLI. Use .claude/commands/h2/*, the Codex h2 skill, "
    "or .harness-helm/h2-cartridge.yml mappings for the other h2-* commands."
)
COMMON_H2_OUTPUT_SECTIONS = {"Context Pack", "Artifacts", "Routing", "Verification", "Next"}
REFERENCE_MANIFEST = {
    "shared": {
        "core-workflow.md": ["0301 Core Workflow Spec", "h2-context", "h2-plan"],
        "external-tool-registry.md": ["0602 Upstream Tool Registry", ".harness-helm/h2-cartridge.yml"],
        "runtime-parity.md": ["Runtime Parity Report", "Claude Code", "Codex"],
        "skill-suite.md": ["0302 Skill Suite", "harness-helm"],
        "upstream-output-normalization.md": [
            "Source cookbook: `0604 Upstream Output Normalization`",
            "not a canonical h2 artifact",
            "actual:<provider>:<surface>",
        ],
        "upstream-surface-map.md": [
            "Source cookbook: `0603 Upstream Surface Map`",
            "h2-design",
            "compound-engineering",
        ],
        "upstream-tool-invocation.md": [
            "0601 Upstream Tool Invocation",
            ".harness-helm/h2-cartridge.yml",
        ],
        "workflow-lifecycle-commands.md": [
            "Source cookbook: `cookbooks/0300-workflow-contract/0303-workflow-lifecycle-commands.md`",
            "compact runtime snapshot",
        ],
    },
    "claude": {
        "claude-adapter.md": ["0401 Claude Code Adapter", "`h2-*` command surface"],
        "claude-entrypoint.md": ["Claude Entrypoint Fixture", "h2-context"],
    },
    "codex": {
        "codex-adapter.md": ["0402 Codex Adapter", "`h2-*` command surface"],
        "codex-entrypoint.md": ["Codex Entrypoint Smoke", "$h2 plan"],
    },
}


@dataclasses.dataclass
class Doc:
    path: Path
    rel: str
    frontmatter: dict[str, Any]
    body: str
    title: str
    mtime: dt.datetime


class HarnessArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        if "invalid choice" in message or "the following arguments are required: command" in message:
            self.print_usage(sys.stderr)
            self.exit(2, f"{self.prog}: error: {message}\n{H2_CLI_NOTE}\n")
        super().error(message)


def now_kst() -> dt.datetime:
    return dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value in {"", "null", "~"}:
        return None
    if value in {"true", "false"}:
        return value == "true"
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [parse_scalar(part.strip()) for part in inner.split(",")]
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value


def parse_simple_yaml(text: str) -> dict[str, Any]:
    """Parse the small YAML subset used by harness config.

    This intentionally supports mappings, scalar values, and simple lists only.
    Use a real YAML parser before adding multiline values or complex quoting.
    """
    entries: list[tuple[int, str]] = []
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        entries.append((len(raw_line) - len(raw_line.lstrip(" ")), raw_line.strip()))

    root: dict[str, Any] = {}
    stack: list[tuple[int, Any]] = [(-1, root)]
    for index, (indent, stripped) in enumerate(entries):
        while indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]

        if stripped.startswith("- "):
            if isinstance(parent, list):
                parent.append(parse_scalar(stripped[2:]))
            continue

        if ":" not in stripped or not isinstance(parent, dict):
            continue
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value:
            parent[key] = parse_scalar(value)
            continue

        next_is_list = False
        if index + 1 < len(entries):
            next_indent, next_stripped = entries[index + 1]
            next_is_list = next_indent > indent and next_stripped.startswith("- ")
        container: list[Any] | dict[str, Any] = [] if next_is_list else {}
        parent[key] = container
        stack.append((indent, container))
    return root


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    raw = text[4:end].strip("\n")
    body = text[text.find("\n", end + 1) + 1 :]
    data: dict[str, Any] = {}
    current_key: str | None = None
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith((" ", "\t")) and current_key:
            stripped = line.strip()
            if stripped.startswith("- "):
                data.setdefault(current_key, [])
                if isinstance(data[current_key], list):
                    data[current_key].append(parse_scalar(stripped[2:]))
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        current_key = key
        if value == "":
            data[key] = []
        else:
            data[key] = parse_scalar(value)
    return data, body


def render_frontmatter(data: dict[str, Any]) -> str:
    lines = ["---"]
    for key, value in data.items():
        if isinstance(value, list):
            if not value:
                lines.append(f"{key}: []")
            else:
                lines.append(f"{key}:")
                for item in value:
                    lines.append(f"  - {item}")
        elif value is None:
            lines.append(f"{key}: null")
        elif isinstance(value, bool):
            lines.append(f"{key}: {'true' if value else 'false'}")
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def iter_markdown(root: Path = DOCS) -> list[Path]:
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
                rel=path.relative_to(ROOT).as_posix(),
                frontmatter=fm,
                body=body,
                title=title_from_body(body, path),
                mtime=dt.datetime.fromtimestamp(stat.st_mtime, tz=dt.timezone.utc),
            )
        )
    return docs


def list_value(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value if v is not None]
    return [str(value)]


def is_archive(doc: Doc) -> bool:
    return doc.rel.startswith("docs/_archive/") or doc.rel.startswith("docs/archive/")


def is_index(doc: Doc) -> bool:
    return doc.rel.startswith("docs/_indexes/")


def excluded_patterns(schema: dict[str, Any], key: str = "lint_index") -> list[str]:
    raw = schema.get("exclude_paths", {})
    if not isinstance(raw, dict):
        return []
    value = raw.get(key, [])
    if isinstance(value, list):
        return [str(pattern) for pattern in value]
    return [str(value)]


def is_excluded(doc: Doc, schema: dict[str, Any], key: str = "lint_index") -> bool:
    return any(fnmatch.fnmatch(doc.rel, pattern) for pattern in excluded_patterns(schema, key))


def is_draft(doc: Doc) -> bool:
    return doc.path.name.endswith(".draft.md") or doc.frontmatter.get("status") == "draft"


def is_pending(doc: Doc) -> bool:
    return doc.path.name.endswith(".pending.md") or doc.frontmatter.get("status") == "pending"


def decision_suffix(path: Path, schema: dict[str, Any]) -> str | None:
    match = DECISION_SUFFIX_PATTERN.search(path.name)
    if not match:
        return None
    suffix = match.group(1)
    suffix_map = schema.get("decision_status_by_suffix", {})
    if isinstance(suffix_map, dict) and suffix in suffix_map:
        return str(suffix_map[suffix])
    return None


def validate_doc_id(doc: Doc, doc_id: str) -> str | None:
    dtype = doc.frontmatter.get("type")
    if dtype == "decision" or doc.rel.startswith("docs/30_decisions/"):
        if not re.match(r"^ADR-\d{4}$", doc_id):
            return f"{doc.rel}: decision id must match ADR-NNNN ({doc_id})."
        return None
    if re.match(r"^[A-Z]+-\d{8}-\d{3}$", doc_id):
        return None
    if re.match(r"^[a-z0-9][a-z0-9._/-]*$", doc_id):
        return None
    return f"{doc.rel}: invalid id format {doc_id}"


def load_schema() -> dict[str, Any]:
    if SCHEMA_PATH.exists():
        raw = parse_simple_yaml(read_text(SCHEMA_PATH))
        enums = raw.get("enums", {})
        required_fields = raw.get("required_fields", {})
        return {
            "required": set(required_fields.get("default", [])),
            "type": set(enums.get("type", [])),
            "status": set(enums.get("status", [])),
            "security": set(enums.get("security", [])),
            "confidence": set(enums.get("confidence", [])),
            "domains": set(raw.get("domain_slugs", [])),
            "modules": set(raw.get("module_slugs", [])),
            "decision_status_by_suffix": raw.get("decision_status_by_suffix", {}),
            "confidence_high_evidence_fields": set(raw.get("confidence_high_evidence_fields", [])),
            "generated_header": raw.get("generated_header", DEFAULT_GENERATED_HEADER),
            "stale_days": raw.get("stale_days", {}),
            "exclude_paths": raw.get("exclude_paths", {}),
        }

    # Fallback keeps the command usable if the config file is missing.
    return {
        "required": {"type", "status", "security"},
        "type": {
            "plan",
            "design",
            "analysis",
            "review",
            "report",
            "decision",
            "domain",
            "spec",
            "solution",
            "convention",
            "learning",
            "runbook",
            "incident",
            "release",
        },
        "status": {
            "draft",
            "pending",
            "accepted",
            "rejected",
            "verified",
            "stable",
            "active",
            "reviewed",
            "released",
            "completed",
            "complete",
            "deprecated",
            "archived",
        },
        "security": {"public", "internal", "restricted", "regulated", "confidential"},
        "confidence": {"low", "medium", "high"},
        "domains": {"insurance", "commission", "hrm", "workflow", "integration"},
        "modules": {
            "bootstrap-system",
            "bootstrap-human-resource-mng",
            "bootstrap-workflow",
            "hera-webapp",
            "hera-system",
            "hera-human-resource-mng",
            "hera-workflow",
            "hera-domain-data",
            "hera-api-client",
            "hera-commons",
            "_msa-api-gateway",
            "_msa-service-discovery",
            "_system-doctor",
            "_hera-code-gen",
            "docs",
            "infra",
            "cross-cutting",
        },
        "decision_status_by_suffix": {
            "draft": "draft",
            "pending": "pending",
            "accepted": "accepted",
            "rejected": "rejected",
        },
        "confidence_high_evidence_fields": {"human_verified_by", "tests", "source_pr", "source_trace"},
        "generated_header": DEFAULT_GENERATED_HEADER,
        "stale_days": {"draft": 30, "pending": 14, "harness_raw": 7, "harness_normalized": 30},
        "exclude_paths": {},
    }


def rel_link(path: str) -> str:
    return path.replace(" ", "%20")


def has_path_escape(value: str) -> bool:
    path = Path(value)
    return path.is_absolute() or ".." in path.parts


def safe_path_segment(value: str, label: str) -> str:
    if has_path_escape(value) or "/" in value or "\\" in value:
        raise ValueError(f"{label} must be a single safe path segment.")
    return value


def validate_run_id(value: str) -> str:
    safe_path_segment(value, "run_id")
    if not RUN_ID_PATTERN.match(value):
        raise ValueError("run_id must match YYYYMMDD-HHMMSS-h2-step.")
    return value


def resolve_under_root(rel_path: str, root: Path, label: str) -> Path:
    path = Path(rel_path)
    if path.is_absolute():
        raise ValueError(f"{label} must be repository-relative.")
    resolved = (ROOT / path).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError(f"{label} must stay under {root.relative_to(ROOT)}.")
    return resolved


def generated_header_ok(doc: Doc, schema: dict[str, Any]) -> bool:
    return read_text(doc.path).startswith(schema["generated_header"])


def command_lint(args: argparse.Namespace) -> int:
    schema = load_schema()
    docs = load_docs()
    hard: list[str] = []
    warnings: list[str] = []
    ids: dict[str, str] = {}

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
        for field in ("type", "status", "security", "confidence"):
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

    print_report("kb-lint", hard, warnings)
    return 1 if hard and args.strict else 0


def include_in_index(doc: Doc, schema: dict[str, Any] | None = None) -> bool:
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
        return f"- [{doc.title}]({rel_link('../' + doc.rel.removeprefix('docs/'))}) — `{dtype}`, `{status}`, `{security}`"
    return f"- [{doc.title}]({rel_link('../' + doc.rel.removeprefix('docs/'))}) — `{dtype}`, `{status}`"


def command_index(args: argparse.Namespace) -> int:
    schema = load_schema()
    docs = load_docs()
    target = DOCS / "_indexes"
    target.mkdir(parents=True, exist_ok=True)
    indexed = [doc for doc in docs if include_in_index(doc, schema)]
    rejected = [
        doc for doc in docs if doc.rel.startswith("docs/30_decisions/") and doc.path.name.endswith(".rejected.md")
    ]
    archives = [doc for doc in docs if is_archive(doc) and doc.path.name.lower() in {"manifest.md", "_index.md"}]

    generated_header = schema["generated_header"]
    kb = [generated_header, "", "# KB Index", ""]
    for doc in indexed:
        kb.append(minimal_line(doc))
    if rejected:
        kb.extend(["", "## Do Not Use", ""])
        for doc in rejected:
            phrases = ", ".join(list_value(doc.frontmatter.get("ai_avoid_phrases"))) or "see document"
            kb.append(f"- [{doc.title}]({rel_link('../' + doc.rel.removeprefix('docs/'))}) — avoid: {phrases}")
    if archives:
        kb.extend(["", "## Archive Manifest", ""])
        for doc in archives:
            kb.append(minimal_line(doc))
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

    harness_root = ROOT / ".harness-helm" / "runs"
    if harness_root.exists():
        for path in harness_root.rglob("*"):
            if not path.is_dir():
                continue
            age = (current - dt.datetime.fromtimestamp(path.stat().st_mtime, tz=current.tzinfo)).days
            if path.name == "raw" and age >= args.harness_raw_days:
                warnings.append(f"{path.relative_to(ROOT)}: raw staging older than {age} days; cleanup first.")
            if path.name in {"normalized", "promotion-candidates"} and age >= args.harness_normalized_days:
                warnings.append(f"{path.relative_to(ROOT)}: staging older than {age} days; cleanup candidate.")
    print_report("kb-stale", [], warnings)
    return 0


def command_cartridge_validate(args: argparse.Namespace) -> int:
    hard: list[str] = []
    warnings: list[str] = []

    if not CARTRIDGE_PATH.exists():
        hard.append(".harness-helm/h2-cartridge.yml is missing.")
        print_report("h2-cartridge", hard, warnings)
        return 1

    cartridge = parse_simple_yaml(read_text(CARTRIDGE_PATH))
    registry = cartridge.get("external_tool_registry", {})
    commands = cartridge.get("commands", {})
    if not isinstance(registry, dict):
        hard.append("external_tool_registry must be a mapping.")
        registry = {}
    if not isinstance(commands, dict):
        hard.append("commands must be a mapping.")
        commands = {}

    tools = registry.get("tools", {}) if isinstance(registry, dict) else {}
    if not isinstance(tools, dict):
        hard.append("external_tool_registry.tools must be a mapping.")
        tools = {}

    required_tool_fields = set(registry.get("registration_fields", []))
    if not required_tool_fields:
        warnings.append("external_tool_registry.registration_fields is empty.")
    for tool_id, tool in tools.items():
        if not isinstance(tool, dict):
            hard.append(f"external_tool_registry.tools.{tool_id} must be a mapping.")
            continue
        for field in sorted(required_tool_fields):
            if field not in tool:
                hard.append(f"external_tool_registry.tools.{tool_id}: missing {field}.")
        if tool.get("id") and tool.get("id") != tool_id:
            hard.append(f"external_tool_registry.tools.{tool_id}: id mismatch ({tool.get('id')}).")

    required_command_fields = {"mode", "provider", "surface", "fallback_label", "routing_target"}
    missing_commands = sorted(EXPECTED_COMMANDS - set(commands))
    for command in missing_commands:
        hard.append(f"commands.{command}: missing command mapping.")

    provider_ids = set(tools) | {"harness"}
    known_surfaces: set[str] = {
        "context-pack",
        "gstack-superpowers-consistency-checklist",
        "harness cartridge-validate",
        "local-test-command",
        "harness-archive-dry-run",
        "archive-checklist",
        "ops-checklist",
        "codex-native-code-edit",
        "claude-native-code-edit",
    }
    for tool in tools.values():
        if isinstance(tool, dict):
            known_surfaces.update(str(surface) for surface in list_value(tool.get("surfaces")))

    for command, mapping in commands.items():
        if not isinstance(mapping, dict):
            hard.append(f"commands.{command} must be a mapping.")
            continue
        for field in sorted(required_command_fields):
            if field not in mapping:
                hard.append(f"commands.{command}: missing {field}.")
        provider = mapping.get("provider")
        if provider not in provider_ids:
            hard.append(f"commands.{command}: unknown provider {provider}.")
        surface = mapping.get("surface")
        if surface and surface not in known_surfaces:
            warnings.append(f"commands.{command}: surface {surface} is not registered; confirm it is intentional.")
        for alternative in list_value(mapping.get("alternatives")):
            if alternative not in known_surfaces:
                warnings.append(f"commands.{command}: alternative {alternative} is not registered; confirm it is intentional.")
        routing_target = str(mapping.get("routing_target", ""))
        if routing_target.startswith("/"):
            hard.append(f"commands.{command}: routing_target must be repository-relative.")
        placeholders = set(ROUTING_PLACEHOLDER_PATTERN.findall(routing_target))
        invalid_placeholders = sorted(placeholders - ALLOWED_ROUTING_PLACEHOLDERS)
        if invalid_placeholders:
            hard.append(
                f"commands.{command}: routing_target has invalid placeholders: {', '.join(invalid_placeholders)}."
            )
        if command == "h2-cartridge" and surface != "harness cartridge-validate":
            hard.append("commands.h2-cartridge: surface must be harness cartridge-validate.")

    print_report("h2-cartridge", hard, warnings)
    return 1 if hard and args.strict else 0
def run_id(command: str) -> str:
    return f"{now_kst().strftime('%Y%m%d-%H%M%S')}-{command}"


def run_root(feature: str | None, run_id_value: str) -> Path:
    slug = safe_path_segment(feature, "feature") if feature else "_unscoped"
    run_segment = validate_run_id(run_id_value)
    return ROOT / ".harness-helm" / "runs" / slug / run_segment


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


TASK_STOP_WORDS = {
    # English fillers
    "a", "an", "the", "and", "or", "but", "if", "of", "to", "in", "on", "for", "with",
    "from", "by", "at", "as", "is", "are", "was", "were", "be", "been", "do", "does",
    "did", "this", "that", "these", "those", "it", "its", "we", "i", "you", "they",
    "ai", "use", "make", "made", "run", "ran", "see", "saw", "have", "has", "had",
    # Korean fillers (token-level)
    "및", "또는", "그리고", "위한", "관한", "대한", "하기", "하는", "하여", "위해",
    "있다", "없다", "이다", "되다", "한다", "있는", "없는", "되는", "되었", "통해",
}


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


RUNTIME_SEED_RULES: list[tuple[set[str], list[str]]] = [
    ({"workflow", "h2", "lifecycle", "command", "cartridge", "adapter", "audit", "harness"},
     ["README.md", ".harness-helm/h2-cartridge.yml", ".harness-helm/h2-schema.yml",
      ".claude/skills/harness-helm/SKILL.md", ".codex/skills/harness-helm/SKILL.md",
      "docs/40_knowledge/conventions/h2-product-memory.md"]),
    ({"upstream", "gstack", "superpowers", "compound", "ce", "provider", "surface"},
     [".harness-helm/h2-cartridge.yml",
      ".claude/skills/harness-helm/references/upstream-tool-invocation.md",
      ".claude/skills/harness-helm/references/upstream-surface-map.md"]),
    ({"normalization", "raw", "fixture", "evidence"},
     [".claude/skills/harness-helm/references/upstream-output-normalization.md",
      ".harness-helm/h2-cartridge.yml"]),
    ({"reference", "snapshot", "parity", "drift"},
     [".claude/skills/harness-helm/references/runtime-parity.md",
      "docs/40_knowledge/conventions/guidelines/h2-runtime-reference-selection.md"]),
    ({"runbook", "incident", "release", "ops", "deploy"},
     ["docs/50_operations/README.md",
      ".harness-helm/h2-cartridge.yml"]),
    ({"docs", "kb", "lint", "schema", "frontmatter", "template"},
     [".harness-helm/h2-schema.yml",
      "docs/_indexes/KB_INDEX.md"]),
]


def runtime_seed_docs(tokens: list[str], existing: set[str]) -> list[str]:
    if not tokens:
        return []
    token_set = set(tokens)
    seeds: list[str] = []
    seen: set[str] = set(existing)
    for keywords, paths in RUNTIME_SEED_RULES:
        if token_set & keywords:
            for path in paths:
                if path not in seen and (ROOT / path).exists():
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
    feature_docs = docs_matching_feature(args.feature, docs, schema)
    tokens = tokenize_task(args.task)
    feature_doc_rels = {doc.rel for doc in feature_docs}
    task_docs = docs_matching_task(tokens, docs, schema, feature_doc_rels)
    index_docs = [DOCS / "_indexes" / name for name in ("KB_INDEX.md", "DOMAIN_INDEX.md", "TAG_INDEX.md")]

    # primary: indexes + feature-match + top task-token + runtime seed
    primary_entries: list[tuple[str, str]] = []
    for path in index_docs:
        if path.exists():
            primary_entries.append((path.relative_to(ROOT).as_posix(), "index"))
    for doc in feature_docs[:8]:
        primary_entries.append((doc.rel, "feature-match"))
    primary_rels = {rel for rel, _ in primary_entries}
    for doc in task_docs[:6]:
        if doc.rel not in primary_rels:
            primary_entries.append((doc.rel, "task-token"))
            primary_rels.add(doc.rel)
    for rel in runtime_seed_docs(tokens, primary_rels):
        primary_entries.append((rel, "runtime-seed"))
        primary_rels.add(rel)

    # supporting: 추가 feature docs + 추가 task-token docs
    supporting_entries: list[tuple[str, str]] = []
    for doc in feature_docs[8:16]:
        if doc.rel not in primary_rels:
            supporting_entries.append((doc.rel, "feature-match"))
    for doc in task_docs[6:14]:
        rels = primary_rels | {rel for rel, _ in supporting_entries}
        if doc.rel not in rels:
            supporting_entries.append((doc.rel, "task-token"))

    excluded = [
        "docs/_archive/** body",
        "docs/_templates/**",
        ".harness-helm/runs/_templates/**",
        "draft/pending documents unless task-scoped",
        "regulated documents unless explicitly task-scoped",
    ]
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
        lines.extend(f"- {rel} (selected_by: {tag})" for rel, tag in primary_entries)
    else:
        lines.append("- <none>")
    lines.extend(["", "### supporting_docs"])
    if supporting_entries:
        lines.extend(f"- {rel} (selected_by: {tag})" for rel, tag in supporting_entries)
    else:
        lines.append("- <none>")
    lines.extend(["", "### excluded_by_policy"])
    lines.extend(f"- {item}" for item in excluded)
    lines.extend(
        [
            "",
            "### assumptions",
            "- `_indexes` are routing hints; original docs remain the canonical reference.",
            "- If indexes are stale or absent, canonical docs are inspected directly.",
            "- `selected_by` tags primary/supporting docs by source: index | feature-match | task-token | runtime-seed.",
            "",
            "## Artifacts",
            "",
            "### created",
            f"- {target.relative_to(ROOT).as_posix()}",
            "",
            "### updated",
            "- <none>",
            "",
            "### suggested",
            "- <none>",
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
            "- Confirm selected docs match the task before using them as implementation context.",
            "",
            "### completed",
            "- context pack generated",
            "",
            "### not_verified",
            "- human review of context relevance",
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
    print(f"h2-context: wrote {target.relative_to(ROOT)}")
    return 0


def command_template_validate(args: argparse.Namespace) -> int:
    schema = load_schema()
    hard: list[str] = []
    warnings: list[str] = []
    for dtype, filename in CANONICAL_TEMPLATES.items():
        path = DOCS / "_templates" / filename
        if not path.exists():
            hard.append(f"docs/_templates/{filename}: missing canonical template.")
            continue
        fm, _ = parse_frontmatter(read_text(path))
        if fm.get("type") != dtype:
            hard.append(f"{path.relative_to(ROOT)}: expected type={dtype}, got {fm.get('type')}.")
        if fm.get("security") not in schema["security"]:
            hard.append(f"{path.relative_to(ROOT)}: invalid security={fm.get('security')}.")
    for filename, required_sections in STAGING_TEMPLATES.items():
        path = ROOT / ".harness-helm" / "runs" / "_templates" / filename
        if not path.exists():
            hard.append(f".harness-helm/runs/_templates/{filename}: missing staging template.")
            continue
        text = read_text(path)
        for section in sorted(required_sections):
            if f"## {section}" not in text:
                hard.append(f"{path.relative_to(ROOT)}: missing ## {section}.")
    excluded = set(excluded_patterns(schema))
    for pattern in sorted(REQUIRED_LINT_INDEX_EXCLUDES):
        if pattern not in excluded:
            hard.append(f".harness-helm/h2-schema.yml: exclude_paths.lint_index missing {pattern}.")
    print_report("template-validate", hard, warnings)
    return 1 if hard and args.strict else 0


def command_reference_validate(args: argparse.Namespace) -> int:
    hard: list[str] = []
    warnings: list[str] = []
    runtime_roots = {
        "claude": ROOT / ".claude" / "skills" / "harness-helm" / "references",
        "codex": ROOT / ".codex" / "skills" / "harness-helm" / "references",
    }
    runtime_names = {"claude": "Claude Code", "codex": "Codex"}

    def first_h1(text: str) -> str | None:
        for line in text.splitlines():
            if line.startswith("# "):
                return line.strip()
        return None

    for runtime, reference_root in runtime_roots.items():
        required = dict(REFERENCE_MANIFEST["shared"])
        required.update(REFERENCE_MANIFEST[runtime])
        for base_path in sorted(reference_root.glob("*.md")):
            if base_path.name.endswith(".ko.md"):
                original_path = base_path.with_name(base_path.name.removesuffix(".ko.md") + ".md")
                if not original_path.exists():
                    hard.append(f"{base_path.relative_to(ROOT).as_posix()}: Korean translation has no base reference.")
                continue
            base_text = read_text(base_path)
            if re.search(r"[가-힣]", base_text):
                hard.append(
                    f"{base_path.relative_to(ROOT).as_posix()}: base reference must stay English-only; put Korean text in {base_path.stem}.ko.md."
                )
            ko_path = base_path.with_name(f"{base_path.stem}.ko.md")
            if not ko_path.exists():
                hard.append(f"{ko_path.relative_to(ROOT).as_posix()}: missing Korean reference translation.")
            else:
                ko_text = read_text(ko_path)
                if not re.search(r"[가-힣]", ko_text):
                    hard.append(f"{ko_path.relative_to(ROOT).as_posix()}: Korean reference translation has no Korean text.")
                base_h1 = first_h1(base_text)
                ko_h1 = first_h1(ko_text)
                if base_h1 and ko_h1 and base_h1 != ko_h1:
                    hard.append(
                        f"{ko_path.relative_to(ROOT).as_posix()}: Korean reference H1 must match base reference H1 {base_h1!r}."
                    )
        for filename, markers in required.items():
            path = reference_root / filename
            rel = path.relative_to(ROOT).as_posix()
            if not path.exists():
                hard.append(f"{rel}: missing bundled reference.")
                continue
            text = read_text(path)
            for marker in markers:
                if marker not in text:
                    hard.append(f"{rel}: missing marker {marker!r}.")

            if filename == "workflow-lifecycle-commands.md":
                runtime_name = runtime_names[runtime]
                if runtime_name not in text:
                    hard.append(f"{rel}: missing runtime-specific surface marker {runtime_name}.")
                for command in EXPECTED_COMMANDS:
                    if f"`{command}`" not in text:
                        hard.append(f"{rel}: missing {command}.")

    codex_skill = ROOT / ".codex" / "skills" / "harness-helm" / "SKILL.md"
    if codex_skill.exists():
        text = read_text(codex_skill)
        if "references/claude-adapter.md" in text:
            hard.append(".codex/skills/harness-helm/SKILL.md: must not reference claude-adapter.md.")
        if "references/codex-adapter.md" not in text:
            hard.append(".codex/skills/harness-helm/SKILL.md: missing codex-adapter.md reference.")
        for filename in REFERENCE_MANIFEST["shared"]:
            if f"references/{filename}" not in text:
                warnings.append(f".codex/skills/harness-helm/SKILL.md: does not list references/{filename}.")

    claude_skill = ROOT / ".claude" / "skills" / "harness-helm" / "SKILL.md"
    if claude_skill.exists():
        text = read_text(claude_skill)
        if "references/codex-adapter.md" in text:
            hard.append(".claude/skills/harness-helm/SKILL.md: must not reference codex-adapter.md.")
        if "references/claude-adapter.md" not in text:
            hard.append(".claude/skills/harness-helm/SKILL.md: missing claude-adapter.md reference.")
        for filename in REFERENCE_MANIFEST["shared"]:
            if f"references/{filename}" not in text:
                warnings.append(f".claude/skills/harness-helm/SKILL.md: does not list references/{filename}.")

    # Order 4: shared reference parity (claude vs codex byte-identical) + .ko.md marker 보존
    # workflow-lifecycle-commands.md는 runtime-specific surface marker(Claude Code vs Codex)가
    # 의도된 차이로 들어있으므로 byte parity allowlist에서 제외한다.
    SHARED_PARITY_ALLOWLIST = {"workflow-lifecycle-commands.md"}
    for filename in REFERENCE_MANIFEST["shared"]:
        if filename in SHARED_PARITY_ALLOWLIST:
            continue
        claude_path = runtime_roots["claude"] / filename
        codex_path = runtime_roots["codex"] / filename
        if claude_path.exists() and codex_path.exists():
            if read_text(claude_path) != read_text(codex_path):
                hard.append(
                    f".claude vs .codex shared reference drift: {filename} (양 어댑터 byte-identical 필수, "
                    f"runtime-specific 차이는 allowlist에 추가)."
                )

    # .ko.md marker 보존: 영문 markers는 한국어 번역에서도 그대로 (cookbook 슬러그·경로·고유 명사) 유지되어야 한다.
    for runtime, reference_root in runtime_roots.items():
        required = dict(REFERENCE_MANIFEST["shared"])
        required.update(REFERENCE_MANIFEST[runtime])
        for filename, markers in required.items():
            ko_path = reference_root / f"{Path(filename).stem}.ko.md"
            if not ko_path.exists():
                continue
            ko_text = read_text(ko_path)
            for marker in markers:
                # marker가 알파벳·숫자·기호로만 구성된 식별자성이면 한국어 번역에서도 그대로 보존되어야 한다.
                if marker not in ko_text:
                    warnings.append(
                        f"{ko_path.relative_to(ROOT).as_posix()}: base marker {marker!r}이 한국어 번역에서 보존되지 않음 (식별자성 marker는 그대로 유지 권장)."
                    )

    print_report("reference-validate", hard, warnings)
    return 1 if hard and args.strict else 0


NORMALIZATION_FIXTURE_COMMANDS = {"h2-plan", "h2-design", "h2-report"}
TARGET_SMOKE_REQUIRED_PATHS = [
    "AGENTS.md",
    "CLAUDE.md",
    ".harness-helm/h2-cartridge.yml",
    ".harness-helm/h2-schema.yml",
    ".harness-helm/scripts/harness.py",
    ".claude/commands/h2",
    ".claude/skills/harness-helm/SKILL.md",
    ".codex/skills/h2",
    ".codex/skills/harness-helm/SKILL.md",
    "docs",
]
TARGET_SMOKE_EXCLUDED_PATHS = ["cookbooks"]


def command_target_smoke(args: argparse.Namespace) -> int:
    """target project minimal smoke: cookbooks/ 없이 핵심 surface만으로 검증 가능한지 확인."""
    import shutil
    import subprocess
    import tempfile

    hard: list[str] = []
    warnings: list[str] = []

    with tempfile.TemporaryDirectory(prefix="harness-target-smoke-") as tmpdir:
        target = Path(tmpdir) / "target-project"
        target.mkdir(parents=True, exist_ok=True)

        # 핵심 surface 복사 (cookbooks/ 제외)
        copy_items = [
            "AGENTS.md", "AGENTS.ko.md", "CLAUDE.md", "CLAUDE.ko.md",
            ".harness-helm", ".claude", ".codex", "docs", ".github",
        ]
        for item in copy_items:
            src = ROOT / item
            if not src.exists():
                continue
            dst = target / item
            if src.is_dir():
                shutil.copytree(src, dst, dirs_exist_ok=True,
                                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)

        # cookbooks/는 의도적으로 복사 안 함
        cookbooks_check = target / "cookbooks"
        if cookbooks_check.exists():
            hard.append(f"target-smoke: cookbooks/가 target에 존재하면 안 됨 ({cookbooks_check}).")

        # 필수 경로 존재 확인
        for rel in TARGET_SMOKE_REQUIRED_PATHS:
            if not (target / rel).exists():
                hard.append(f"target-smoke: required surface missing in target project: {rel}.")

        # 임시 디렉터리에서 4종 validator subprocess 실행
        script = target / ".harness-helm" / "scripts" / "harness.py"
        if not script.exists():
            hard.append("target-smoke: target harness.py script missing.")
        else:
            for cmd in ["kb-lint", "template-validate", "cartridge-validate", "reference-validate"]:
                try:
                    proc = subprocess.run(
                        ["python3", str(script), cmd, "--strict"],
                        capture_output=True, text=True, cwd=target, timeout=120,
                    )
                except subprocess.TimeoutExpired:
                    hard.append(f"target-smoke: {cmd} --strict timed out (>120s) in cookbooks-less target project.")
                    continue
                if proc.returncode != 0:
                    hard.append(
                        f"target-smoke: {cmd} --strict failed in cookbooks-less target project. "
                        f"stdout tail: {proc.stdout.strip().splitlines()[-3:] if proc.stdout else []}"
                    )

            # h2-context dry-run smoke
            try:
                proc = subprocess.run(
                    ["python3", str(script), "h2-context",
                     "--feature", "target-smoke", "--task", "target project install smoke", "--dry-run"],
                    capture_output=True, text=True, cwd=target, timeout=120,
                )
            except subprocess.TimeoutExpired:
                hard.append("target-smoke: h2-context dry-run timed out (>120s) in cookbooks-less target project.")
                proc = None
            if proc is not None and proc.returncode != 0:
                hard.append("target-smoke: h2-context dry-run failed in cookbooks-less target project.")

    print_report("target-smoke", hard, warnings)
    return 1 if hard and args.strict else 0


def command_normalization_validate(args: argparse.Namespace) -> int:
    hard: list[str] = []
    warnings: list[str] = []
    runs_root = ROOT / ".harness-helm" / "runs"
    fixtures_root = ROOT / ".harness-helm" / "reports" / "fixtures" / "normalized"

    normalized_files: list[Path] = []
    if runs_root.exists():
        normalized_files.extend(
            path
            for path in runs_root.rglob("normalized/*.md")
            if "_templates" not in path.relative_to(runs_root).parts
        )
    if fixtures_root.exists():
        normalized_files.extend(fixtures_root.rglob("*.md"))

    for path in normalized_files:
        rel = path.relative_to(ROOT).as_posix()
        text = read_text(path)
        for section in sorted(COMMON_H2_OUTPUT_SECTIONS):
            if f"## {section}" not in text:
                hard.append(f"{rel}: normalized artifact missing ## {section}.")
        if "actual:" not in text and "fallback" not in text and "not_verified" not in text:
            hard.append(
                f"{rel}: normalized artifact must record actual:<provider>:<surface>, fallback, or not_verified evidence."
            )

    if not normalized_files:
        warnings.append(
            ".harness-helm/runs/**/normalized/*.md and .harness-helm/reports/fixtures/normalized/*.md: no normalized artifacts found."
        )

    # Fixture coverage: 최소 h2-plan, h2-design, h2-report 3개 command 샘플이 fixtures_root에 있어야 한다.
    fixture_files = list(fixtures_root.rglob("*.md")) if fixtures_root.exists() else []
    fixture_commands = set()
    for path in fixture_files:
        text = read_text(path)
        for cmd in NORMALIZATION_FIXTURE_COMMANDS:
            if f"command: {cmd}" in text or f"# {cmd}" in text or path.stem == cmd:
                fixture_commands.add(cmd)
    missing = NORMALIZATION_FIXTURE_COMMANDS - fixture_commands
    if missing:
        warnings.append(
            f".harness-helm/reports/fixtures/normalized/: fixture coverage missing for {', '.join(sorted(missing))}."
        )

    print_report("normalization-validate", hard, warnings)
    return 1 if hard and args.strict else 0


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9가-힣]+", "-", value.strip()).strip("-")
    return slug.lower() or "untitled"


def render_template_text(text: str, args: argparse.Namespace, dtype: str) -> str:
    today = now_kst().strftime("%Y%m%d")
    title = args.title or args.topic or args.feature or dtype
    topic = slugify(args.topic or title)
    feature = slugify(args.feature or topic)
    replacements = {
        "<TODO: feature title>": title,
        "<TODO: task summary>": title,
        "<TODO: 도메인 규칙 또는 용어 제목>": title,
        "<TODO: contract 또는 명세 제목>": title,
        "<TODO: 규칙 제목>": title,
        "<TODO: 재사용 가능한 교훈 제목>": title,
        "<TODO: 해결책 제목>": title,
        "<TODO: 운영 절차 제목>": title,
        "<TODO: 사고 제목>": title,
        "<TODO: 버전 또는 릴리스 이름>": title,
        "YYYYMMDD": today,
        "NNNN": args.number,
        "NNN": args.sequence,
        "<TODO: git username 또는 team id>": args.owner,
        "<TODO: domain owner username 또는 team id>": args.owner,
        "<TODO: spec owner username 또는 team id>": args.owner,
        "<TODO: convention owner username 또는 team id>": args.owner,
        "<TODO: learning owner username 또는 team id>": args.owner,
        "<TODO: operations owner username>": args.owner,
        "<TODO: incident commander username>": args.owner,
        "<TODO: release manager username>": args.owner,
    }
    rendered = text
    for old, new in replacements.items():
        rendered = rendered.replace(old, new)
    if dtype == "decision":
        rendered = rendered.replace("ADR-NNNN", f"ADR-{args.number}")
    rendered = set_frontmatter_field(rendered, "status", args.status)
    rendered = set_frontmatter_field(rendered, "owner", f'"{args.owner}"')
    if dtype == "decision":
        rendered = set_frontmatter_field(rendered, "id", f'"ADR-{args.number}"')
    return rendered


def set_frontmatter_field(text: str, key: str, value: str) -> str:
    if not text.startswith("---\n"):
        return text
    end = text.find("\n---", 4)
    if end == -1:
        return text
    raw_lines = text[4:end].splitlines()
    for index, line in enumerate(raw_lines):
        if re.match(rf"^{re.escape(key)}\s*:", line):
            raw_lines[index] = f"{key}: {value}"
            break
    else:
        raw_lines.append(f"{key}: {value}")
    return "---\n" + "\n".join(raw_lines) + text[end:]


def command_new_doc(args: argparse.Namespace) -> int:
    dtype = args.type
    template_name = CANONICAL_TEMPLATES[dtype]
    template_path = DOCS / "_templates" / template_name
    if not template_path.exists():
        print(f"new-doc: missing template {template_path.relative_to(ROOT)}")
        return 1
    topic = slugify(args.topic or args.title or args.feature or dtype)
    feature = slugify(args.feature or topic)
    target_template = args.target or TEMPLATE_TARGETS[dtype]
    target_rel = target_template.format(
        feature=feature,
        topic=topic,
        domain=args.domain,
        area=args.area,
        number=args.number,
        status=args.status,
    )
    try:
        target = resolve_under_root(target_rel, DOCS, "target")
    except ValueError as error:
        print(f"new-doc: {error}")
        return 1
    content = render_template_text(read_text(template_path), args, dtype)
    if args.dry_run:
        print(f"new-doc: would write {target.relative_to(ROOT)}")
        return 0
    if target.exists() and not args.force:
        print(f"new-doc: target exists {target.relative_to(ROOT)}; use --force to overwrite.")
        return 1
    write_text(target, content)
    print(f"new-doc: wrote {target.relative_to(ROOT)}")
    return 0


def phase_dirs() -> list[tuple[str, list[Path]]]:
    return [
        ("01_plan", [DOCS / "01_plan", DOCS / "01-plan"]),
        ("02_design", [DOCS / "02_design", DOCS / "02-design"]),
        ("03_review", [DOCS / "03_review", DOCS / "03-analysis"]),
        ("04_report", [DOCS / "04_report", DOCS / "04-report"]),
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


def cleanup_archived_run(feature: str, dry_run: bool) -> None:
    run_path = ROOT / ".harness-helm" / "runs" / feature
    if not run_path.exists():
        return
    print(f"  {'would remove' if dry_run else 'remove'} {run_path.relative_to(ROOT)}")
    if not dry_run:
        shutil.rmtree(run_path)


INSTALL_MANIFEST_SCHEMA_VERSION = 1
INSTALL_MARKER_VERSION = "v1"
INSTALL_MANIFEST_KINDS = {"copy", "copy_dir", "managed"}
INSTALL_MARKER_BEGIN_RE = re.compile(r"<!--\s*harness-helm:managed:begin\s+(v\d+)\s*-->")
INSTALL_MARKER_END_RE = re.compile(r"<!--\s*harness-helm:managed:end\s+(v\d+)\s*-->")


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
    import hashlib
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha256_text(text: str) -> str:
    import hashlib
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


def command_install(args: argparse.Namespace) -> int:
    import json

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

    version_files = sorted(package_root.glob("h2-install-v*.txt"))
    package_version = version_files[0].stem.replace("h2-install-", "") if version_files else "unknown"

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

        elif rule.kind == "copy_dir":
            if not src.is_dir():
                errors.append(f"line {rule.line_no}: source dir missing: {rule.source}")
                status = "partial"
                continue
            sub_action = "unchanged"
            files = sorted(p for p in src.rglob("*") if p.is_file())
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


def command_archive(args: argparse.Namespace) -> int:
    feature = args.feature
    try:
        safe_path_segment(feature, "feature")
    except ValueError as error:
        print(f"harness archive: {error}")
        return 1
    now = now_kst()
    month = args.month or now.strftime("%Y-%m")
    try:
        safe_path_segment(month, "month")
    except ValueError as error:
        print(f"harness archive: {error}")
        return 1
    timestamp = now.strftime("%m%d-%H%M%S")
    dest_dir_name = f"{timestamp}_{feature}"
    dest_root = DOCS / "_archive" / month / dest_dir_name
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
        "archive_path": dest_root.relative_to(ROOT).as_posix(),
        "owner": owner,
        "source_trace": (args.source_trace or args.source_issue) or None,
        "source_pr": args.source_pr or None,
        "phase_docs_present": sorted({phase for phase, _ in sources}),
        "purpose": "Archive completed 01~04 PDCA artifacts; body excluded from default retrieval.",
    }
    print(f"harness archive: feature={feature}")
    for phase, src in sources:
        rel_dest = archive_destination(dest_root, phase, src)
        print(f"  {'would move' if args.dry_run else 'move'} {src.relative_to(ROOT)} -> {rel_dest.relative_to(ROOT)}")
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
        print(f"  would write manifest {manifest_path.relative_to(ROOT)}")
        cleanup_archived_run(feature, dry_run=True)
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
        cleanup_archived_run(feature, dry_run=False)
    return 0


def command_cleanup_runs(args: argparse.Namespace) -> int:
    root = ROOT / ".harness-helm" / "runs"
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
        if path.name in {"normalized", "promotion-candidates"} and age >= args.normalized_days:
            candidates.append(path)
    if not candidates:
        print("harness cleanup-runs: no cleanup candidates.")
        return 0
    for path in candidates:
        print(f"{'would remove' if args.dry_run else 'remove'} {path.relative_to(ROOT)}")
        if not args.dry_run:
            shutil.rmtree(path)
    return 0


def print_report(name: str, hard: list[str], warnings: list[str]) -> None:
    print(f"{name}: hard_errors={len(hard)} warnings={len(warnings)}")
    if hard:
        print("\n## Hard Errors")
        for item in hard:
            print(f"- {item}")
    if warnings:
        print("\n## Warnings")
        for item in warnings:
            print(f"- {item}")


def build_parser() -> argparse.ArgumentParser:
    schema = load_schema()
    stale_days = schema.get("stale_days", {})
    parser = HarnessArgumentParser(
        description="HERA Harness Helm enforcement scripts",
        epilog=H2_CLI_NOTE,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    lint = sub.add_parser("kb-lint")
    lint.add_argument("--strict", action="store_true", help="Exit non-zero when hard errors exist.")
    lint.set_defaults(func=command_lint)

    index = sub.add_parser("kb-index")
    index.set_defaults(func=command_index)

    stale = sub.add_parser("kb-stale")
    stale.add_argument("--draft-days", type=int, default=int(stale_days.get("draft", 30)))
    stale.add_argument("--pending-days", type=int, default=int(stale_days.get("pending", 14)))
    stale.add_argument("--harness-raw-days", type=int, default=int(stale_days.get("harness_raw", 7)))
    stale.add_argument("--harness-normalized-days", type=int, default=int(stale_days.get("harness_normalized", 30)))
    stale.set_defaults(func=command_stale)

    cartridge = sub.add_parser("cartridge-validate")
    cartridge.add_argument("--strict", action="store_true", help="Exit non-zero when hard errors exist.")
    cartridge.set_defaults(func=command_cartridge_validate)

    context = sub.add_parser("h2-context")
    context.add_argument("--feature")
    context.add_argument("--task", required=True)
    context.add_argument("--run-id")
    context.add_argument("--next")
    context.add_argument("--dry-run", action="store_true")
    context.set_defaults(func=command_context)

    templates = sub.add_parser("template-validate")
    templates.add_argument("--strict", action="store_true", help="Exit non-zero when hard errors exist.")
    templates.set_defaults(func=command_template_validate)

    references = sub.add_parser("reference-validate")
    references.add_argument("--strict", action="store_true", help="Exit non-zero when hard errors exist.")
    references.set_defaults(func=command_reference_validate)

    normalization = sub.add_parser("normalization-validate")
    normalization.add_argument("--strict", action="store_true", help="Exit non-zero when hard errors exist.")
    normalization.set_defaults(func=command_normalization_validate)

    new_doc = sub.add_parser("new-doc")
    new_doc.add_argument("type", choices=sorted(CANONICAL_TEMPLATES))
    new_doc.add_argument("--target", help="Repository-relative output path. Defaults to the type route.")
    new_doc.add_argument("--feature")
    new_doc.add_argument("--topic")
    new_doc.add_argument("--title")
    new_doc.add_argument("--owner", default="<TODO: git username 또는 team id>")
    new_doc.add_argument("--domain", default="insurance")
    new_doc.add_argument("--area", default="project")
    new_doc.add_argument("--number", default="0001")
    new_doc.add_argument("--sequence", default="001")
    new_doc.add_argument("--status", default="draft")
    new_doc.add_argument("--dry-run", action="store_true")
    new_doc.add_argument("--force", action="store_true")
    new_doc.set_defaults(func=command_new_doc)

    archive = sub.add_parser("archive")
    archive.add_argument("feature")
    archive.add_argument("--month")
    archive.add_argument("--source-trace")
    archive.add_argument("--source-issue", help=argparse.SUPPRESS)
    archive.add_argument("--source-pr")
    archive.add_argument("--dry-run", action="store_true")
    archive.add_argument("--strict", action="store_true")
    archive.set_defaults(func=command_archive)

    cleanup = sub.add_parser("cleanup-runs")
    cleanup.add_argument("--raw-days", type=int, default=int(stale_days.get("harness_raw", 7)))
    cleanup.add_argument("--normalized-days", type=int, default=int(stale_days.get("harness_normalized", 30)))
    cleanup.add_argument("--dry-run", action="store_true")
    cleanup.set_defaults(func=command_cleanup_runs)

    target_smoke = sub.add_parser("target-smoke")
    target_smoke.add_argument("--strict", action="store_true")
    target_smoke.set_defaults(func=command_target_smoke)

    install = sub.add_parser("install")
    install.add_argument("--target", default=".", help="Target repository root (default: cwd).")
    install.add_argument("--allow-non-git", action="store_true",
                         help="Allow target without .git/.")
    install.add_argument("--dry-run", action="store_true",
                         help="Print planned actions without modifying target.")
    install.add_argument("--backup", action="store_true",
                         help="Save *.bak-{timestamp} for each file the install would overwrite.")
    install.add_argument("--quiet", action="store_true",
                         help="Suppress the final summary line.")
    install.add_argument("--manifest", help="Path to h2-install/MANIFEST.txt (default: cwd/h2-install/MANIFEST.txt).")
    install.set_defaults(func=command_install)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    print(LOG_START)
    try:
        args = parser.parse_args(argv)
        return args.func(args)
    finally:
        print(LOG_END)


if __name__ == "__main__":
    raise SystemExit(main())
