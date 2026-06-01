#!/usr/bin/env python3
"""HERA Harness Helm enforcement scripts."""

from __future__ import annotations

import argparse
import copy
import dataclasses
import datetime as dt
import fnmatch
import hashlib
import json
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
COMPOUND_POLICY_PATH = ROOT / ".harness-helm" / "h2-compound.yml"
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
RUNTIME_SUMMARY_NAME = "runtime-summary.json"
RUN_ID_PATTERN = re.compile(r"^\d{8}-\d{6}-h2-[a-z][a-z0-9-]*$")
DECISION_SUFFIX_PATTERN = re.compile(r"\.([a-z][a-z0-9_-]*)\.md$")
ROUTING_PLACEHOLDER_PATTERN = re.compile(r"{([^{}]+)}")
ALLOWED_ROUTING_PLACEHOLDERS = {"feature", "run-id", "type", "topic", "step"}
# This list is the cartridge/reference validation surface, not a 1:1 list of
# local CLI subcommands. Only h2-context is directly implemented by harness.py.
EXPECTED_COMMANDS = {
    "h2-context",
    "h2-plan",
    "h2-design",
    "h2-autorun",
    "h2-rewind",
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
REWINDABLE_STEPS = {
    "h2-analysis",
    "h2-build",
    "h2-test",
    "h2-review",
    "h2-report",
    "h2-compound",
    "h2-archive",
}
STEP_SNAPSHOT_SCOPE: dict[str, list[str]] = {
    "h2-analysis": [
        "docs/02_design/{feature}.analysis.md",
    ],
    "h2-build": [
        ".harness-helm/runs/{feature}/{run_id}/build.md",
    ],
    "h2-test": [
        ".harness-helm/runs/{feature}/{run_id}/test.md",
    ],
    "h2-review": [
        "docs/03_review/code/{feature}.md",
        "docs/03_review/qa/{feature}.md",
        "docs/03_review/security/{feature}.md",
        "docs/03_review/cross/{feature}.md",
    ],
    "h2-report": [
        "docs/04_report/{feature}.md",
    ],
    "h2-compound": [
        ".harness-helm/runs/{feature}/{run_id}/compound-candidates.md",
    ],
    "h2-archive": [
        "docs/01_plan/{feature}.md",
        "docs/02_design/{feature}.md",
        "docs/02_design/{feature}.analysis.md",
        "docs/03_review/code/{feature}.md",
        "docs/03_review/qa/{feature}.md",
        "docs/03_review/security/{feature}.md",
        "docs/03_review/cross/{feature}.md",
        "docs/04_report/{feature}.md",
    ],
}
H2_CLI_NOTE = (
    "Note: among the h2-* lifecycle commands, only h2-context is directly "
    "implemented by this CLI. Use .claude/commands/h2/*, the Codex h2 skill, "
    "or .harness-helm/h2-cartridge.yml mappings for the other h2-* commands."
)
COMMON_H2_OUTPUT_SECTIONS = {"Context Pack", "Artifacts", "Routing", "Verification", "Next"}
CANONICAL_KNOWLEDGE_ROOTS = (
    "docs/10_domain/",
    "docs/20_specs/",
    "docs/30_decisions/",
    "docs/40_knowledge/",
    "docs/50_operations/",
)
CANONICAL_KNOWLEDGE_LIMIT = 6
DEFAULT_COMPOUND_POLICY: dict[str, Any] = {
    "schema_version": 1,
    "domain_refinement": {
        "mode": "conservative",
        "allow_run_override": True,
    },
    "canonical_destination": {
        "domain_rule": "docs/10_domain",
        "implementation_pattern": "docs/40_knowledge/solutions",
        "convention": "docs/40_knowledge/conventions",
        "operational_rule": "docs/50_operations",
    },
    "review_gate": {
        "low_risk_auto_write": True,
        "governed_require_approval": True,
        "confidence_threshold": "high",
    },
    "retrieval_hook_policy": {
        "required": ["domain", "module", "tags"],
        "recommended": ["applies_to", "retrieval_triggers", "related"],
        "enforcement": "warn",
    },
}
REFERENCE_MANIFEST = {
    "shared": {
        "canonical-promotion-flow.md": [
            "docs/40_knowledge/conventions/guidelines/harness-helm/canonical-promotion-flow.md",
            "docs/40_knowledge/conventions/guidelines/harness-helm/runtime-reference-selection.md",
        ],
        "core-workflow.md": ["0301 Core Workflow Spec", "h2-context", "h2-plan"],
        "cartridge-tool-registry.md": ["0602 Upstream Tool Registry", ".harness-helm/h2-cartridge.yml"],
        "runtime-parity.md": ["Runtime Parity Report", "Claude Code", "Codex"],
        "skill-suite.md": ["0302 Skill Suite", "harness-helm"],
        "specs-vs-decisions.md": [
            "docs/40_knowledge/conventions/guidelines/harness-helm/specs-vs-decisions.md",
            "docs/40_knowledge/conventions/guidelines/harness-helm/runtime-reference-selection.md",
        ],
        "provider-surface-selection-and-override.md": [
            "docs/40_knowledge/conventions/guidelines/harness-helm/provider-surface-selection-and-override.md",
            "docs/40_knowledge/conventions/guidelines/harness-helm/runtime-reference-selection.md",
        ],
        "cartridge-output-normalization.md": [
            "Source cookbook: `0604 Upstream Output Normalization`",
            "not a canonical h2 artifact",
            "actual:<provider>:<surface>",
        ],
        "cartridge-surface-map.md": [
            "Source cookbook: `0603 Upstream Surface Map`",
            "h2-design",
            "compound-engineering",
        ],
        "cartridge-command-mapping.md": [
            "0601 Upstream Tool Invocation",
            ".harness-helm/h2-cartridge.yml",
        ],
        "context-pack-contract.md": [
            "0305 Context Pack Contract",
            ".harness-helm/runs/{feature}/{run-id}/context-pack.md",
        ],
        "runtime-folder-structure.md": [
            "0503 h2 Runtime Folder Structure",
            ".harness-helm/runs/{feature}/{run-id}/",
        ],
        "compound-policy-config.md": [
            "0306 Compound Policy Config",
            ".harness-helm/h2-compound.yml",
        ],
        "h2-rewind-recovery.md": [
            "blocked:no-snapshot",
            ".harness-helm/runs/{feature}/{run-id}/snapshots/{step}/",
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
MISLEADING_VALUE_SNAPSHOT_CLAIM = "Compact runtime snapshot of upstream provider, surface, fallback, and routing behavior."
GUIDELINE_DERIVED_REFERENCE_HEADERS = {
    "canonical-promotion-flow.md": "docs/40_knowledge/conventions/guidelines/harness-helm/canonical-promotion-flow.md",
    "specs-vs-decisions.md": "docs/40_knowledge/conventions/guidelines/harness-helm/specs-vs-decisions.md",
    "provider-surface-selection-and-override.md": "docs/40_knowledge/conventions/guidelines/harness-helm/provider-surface-selection-and-override.md",
}
REFERENCE_MAPPING_AUTHORITY = "docs/40_knowledge/conventions/guidelines/harness-helm/runtime-reference-selection.md"


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


def raw_list_value(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


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
            "target_runtime": set(enums.get("target_runtime", [])),
            "domains": set(raw.get("domain_slugs", [])),
            "modules": set(raw.get("module_slugs", [])),
            "decision_status_by_suffix": raw.get("decision_status_by_suffix", {}),
            "confidence_high_evidence_fields": set(raw.get("confidence_high_evidence_fields", [])),
            "generated_header": raw.get("generated_header", DEFAULT_GENERATED_HEADER),
            "stale_days": raw.get("stale_days", {}),
            "exclude_paths": raw.get("exclude_paths", {}),
            "compound_policy_schema": raw.get("compound_policy_schema", {}),
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
        "target_runtime": {"included", "source_only", "derived"},
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
        "compound_policy_schema": {
            "schema_versions": [1],
            "modes": ["conservative", "synthesis", "exploratory"],
            "destination_keys": ["domain_rule", "implementation_pattern", "convention", "operational_rule"],
            "enforcement": ["warn", "error"],
            "retrieval_hook_fields": ["domain", "module", "tags", "applies_to", "retrieval_triggers", "related"],
        },
    }


def rel_link(path: str) -> str:
    return path.replace(" ", "%20")


def has_path_escape(value: str) -> bool:
    path = Path(value)
    return path.is_absolute() or ".." in path.parts


def safe_path_segment(value: str, label: str) -> str:
    if not value:
        raise ValueError(f"{label} must not be empty.")
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


def deep_merge(default: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(default)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_compound_policy(schema: dict[str, Any]) -> tuple[dict[str, Any], str, list[str]]:
    if not COMPOUND_POLICY_PATH.exists():
        return copy.deepcopy(DEFAULT_COMPOUND_POLICY), "built-in-default", []

    raw = parse_simple_yaml(read_text(COMPOUND_POLICY_PATH))
    policy = deep_merge(DEFAULT_COMPOUND_POLICY, raw)
    return policy, ".harness-helm/h2-compound.yml", validate_compound_policy(policy, schema)


def validate_compound_policy(policy: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    policy_schema = schema.get("compound_policy_schema", {})
    versions = set(list_value(policy_schema.get("schema_versions", [1])))
    modes = set(list_value(policy_schema.get("modes", ["conservative", "synthesis", "exploratory"])))
    destination_keys = set(
        list_value(
            policy_schema.get(
                "destination_keys",
                ["domain_rule", "implementation_pattern", "convention", "operational_rule"],
            )
        )
    )
    enforcement_values = set(list_value(policy_schema.get("enforcement", ["warn", "error"])))

    version = str(policy.get("schema_version"))
    if version not in versions:
        warnings.append(f".harness-helm/h2-compound.yml: unsupported schema_version={version}.")

    refinement = policy.get("domain_refinement", {})
    if not isinstance(refinement, dict):
        warnings.append(".harness-helm/h2-compound.yml: domain_refinement must be a mapping.")
        refinement = {}
    mode = str(refinement.get("mode", "conservative"))
    if mode not in modes:
        warnings.append(f".harness-helm/h2-compound.yml: unknown domain_refinement.mode={mode}.")

    destinations = policy.get("canonical_destination", {})
    if not isinstance(destinations, dict):
        warnings.append(".harness-helm/h2-compound.yml: canonical_destination must be a mapping.")
        destinations = {}
    for key, value in destinations.items():
        if key not in destination_keys:
            warnings.append(f".harness-helm/h2-compound.yml: unknown canonical_destination key={key}.")
        if not isinstance(value, str) or has_path_escape(value):
            warnings.append(f".harness-helm/h2-compound.yml: invalid canonical_destination.{key}={value}.")

    review_gate = policy.get("review_gate", {})
    if not isinstance(review_gate, dict):
        warnings.append(".harness-helm/h2-compound.yml: review_gate must be a mapping.")
        review_gate = {}
    threshold = str(review_gate.get("confidence_threshold", "high"))
    if threshold not in schema.get("confidence", set()):
        warnings.append(f".harness-helm/h2-compound.yml: invalid review_gate.confidence_threshold={threshold}.")

    retrieval_policy = policy.get("retrieval_hook_policy", {})
    if not isinstance(retrieval_policy, dict):
        warnings.append(".harness-helm/h2-compound.yml: retrieval_hook_policy must be a mapping.")
        retrieval_policy = {}
    enforcement = str(retrieval_policy.get("enforcement", "warn"))
    if enforcement not in enforcement_values:
        warnings.append(f".harness-helm/h2-compound.yml: invalid retrieval_hook_policy.enforcement={enforcement}.")
    elif enforcement == "error":
        warnings.append(".harness-helm/h2-compound.yml: enforcement=error is accepted but downgraded to warning in this scope.")
    return warnings


def is_compound_generated_doc(doc: Doc) -> bool:
    return doc.frontmatter.get("generated_by") == "h2-compound"


def generated_header_ok(doc: Doc, schema: dict[str, Any]) -> bool:
    return read_text(doc.path).startswith(schema["generated_header"])


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
    archives = [
        doc
        for doc in docs
        if is_archive(doc)
        and doc.path.name.lower() in {"manifest.md", "_index.md"}
        and "/runs/" not in doc.rel
    ]

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
        "autorun-orchestrator",
        "snapshot-restore",
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


def run_manifest_path(feature: str | None, run_id_value: str) -> Path:
    return run_root(feature, run_id_value) / "manifest.md"


def command_from_run_id(run_id_value: str) -> str:
    run_segment = validate_run_id(run_id_value)
    return run_segment.split("-", 2)[2]


def validate_h2_command(command: str) -> str:
    if command not in EXPECTED_COMMANDS:
        raise ValueError(f"command must be one of: {', '.join(sorted(EXPECTED_COMMANDS))}.")
    return command


def format_run_timestamp(value: dt.datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=dt.timezone(dt.timedelta(hours=9)))
    return value.isoformat(timespec="seconds")


def started_at_from_run_id(run_id_value: str) -> dt.datetime:
    run_segment = validate_run_id(run_id_value)
    raw = run_segment[:15]
    naive = dt.datetime.strptime(raw, "%Y%m%d-%H%M%S")
    return naive.replace(tzinfo=dt.timezone(dt.timedelta(hours=9)))


def parse_run_timestamp(value: Any) -> dt.datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = dt.datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone(dt.timedelta(hours=9)))
    return parsed


def load_run_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    frontmatter, _ = parse_frontmatter(read_text(path))
    return frontmatter


def write_run_manifest(path: Path, manifest: dict[str, Any]) -> None:
    title = f"# Run Manifest: {manifest.get('feature', 'null')} {manifest.get('run_id', path.parent.name)}"
    write_text(path, render_frontmatter(manifest) + "\n" + title + "\n")


def start_run_manifest(
    feature: str | None,
    run_id_value: str,
    command: str,
    task: str | None = None,
    autorun_id: str | None = None,
) -> Path:
    path = run_manifest_path(feature, run_id_value)
    manifest = load_run_manifest(path)
    safe_feature = safe_path_segment(feature, "feature") if feature else "_unscoped"
    safe_run_id = validate_run_id(run_id_value)
    safe_command = validate_h2_command(command)
    existing_status = manifest.get("status")
    should_reset_timing = existing_status in {"completed", "failed", "incomplete"} or manifest.get("completed_at") is not None
    manifest.update(
        {
            "schema_version": 1,
            "type": "run-manifest",
            "feature": safe_feature,
            "run_id": safe_run_id,
            "command": safe_command,
            "status": "running",
        }
    )
    if should_reset_timing or not manifest.get("started_at"):
        manifest["started_at"] = format_run_timestamp(now_kst())
    manifest["completed_at"] = None
    manifest["autorun_id"] = validate_run_id(autorun_id) if autorun_id is not None else manifest.get("autorun_id")
    manifest.setdefault("artifact_paths", [])
    if task:
        manifest["task"] = task
    write_run_manifest(path, manifest)
    return path


def complete_run_manifest(
    feature: str | None,
    run_id_value: str,
    status: str = "completed",
    artifact_paths: list[str] | None = None,
) -> Path:
    if status not in {"completed", "failed", "incomplete"}:
        raise ValueError("status must be completed, failed, or incomplete.")
    root = run_root(feature, run_id_value)
    if not root.exists():
        raise FileNotFoundError(f"run folder does not exist: {repository_rel(root)}")
    path = root / "manifest.md"
    manifest = load_run_manifest(path)
    safe_feature = safe_path_segment(feature, "feature") if feature else "_unscoped"
    safe_run_id = validate_run_id(run_id_value)
    manifest.setdefault("schema_version", 1)
    manifest.setdefault("type", "run-manifest")
    manifest.setdefault("feature", safe_feature)
    manifest.setdefault("run_id", safe_run_id)
    manifest.setdefault("command", command_from_run_id(safe_run_id))
    manifest.setdefault("started_at", format_run_timestamp(started_at_from_run_id(safe_run_id)))
    manifest.setdefault("autorun_id", None)
    if artifact_paths is not None:
        existing = list_value(manifest.get("artifact_paths"))
        merged = existing[:]
        for artifact in artifact_paths:
            if artifact not in merged:
                merged.append(artifact)
        manifest["artifact_paths"] = merged
    else:
        manifest.setdefault("artifact_paths", [])
    manifest["status"] = status
    manifest["completed_at"] = None if status == "incomplete" else format_run_timestamp(now_kst())
    write_run_manifest(path, manifest)
    return path


def validate_rewind_step(step: str) -> str:
    if step not in REWINDABLE_STEPS:
        raise ValueError(f"step must be one of: {', '.join(sorted(REWINDABLE_STEPS))}.")
    return step


def snapshot_root(feature: str, run_id_value: str, step: str) -> Path:
    return run_root(feature, run_id_value) / "snapshots" / validate_rewind_step(step)


def snapshot_manifest_path(feature: str, run_id_value: str, step: str) -> Path:
    return snapshot_root(feature, run_id_value, step) / "manifest.json"


def repository_rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def snapshot_scope_paths(feature: str, run_id_value: str, step: str) -> list[Path]:
    safe_feature = safe_path_segment(feature, "feature")
    safe_run_id = validate_run_id(run_id_value)
    templates = STEP_SNAPSHOT_SCOPE[validate_rewind_step(step)]
    return [ROOT / template.format(feature=safe_feature, run_id=safe_run_id) for template in templates]


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def snapshot_file_path(root: Path, rel: str) -> Path:
    return root / "files" / rel


def archive_residue_paths(feature: str) -> list[str]:
    archive_root = DOCS / "_archive"
    if not archive_root.exists():
        return []
    matches: list[str] = []
    for path in sorted(archive_root.rglob("*")):
        if feature in path.name:
            matches.append(repository_rel(path))
    return matches


def load_snapshot_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError("snapshot not found; rewind requires h2-autorun pre-step snapshots.")
    raw = json.loads(read_text(path))
    if not isinstance(raw, dict):
        raise ValueError("snapshot manifest must be a JSON object.")
    if raw.get("schema_version") != 1:
        raise ValueError("snapshot manifest schema_version must be 1.")
    return raw


def command_snapshot_save(args: argparse.Namespace) -> int:
    try:
        root = snapshot_root(args.feature, args.run_id, args.step)
        paths = snapshot_scope_paths(args.feature, args.run_id, args.step)
    except ValueError as error:
        print(f"h2-snapshot save: {error}")
        return 1

    files: list[dict[str, Any]] = []
    for path in paths:
        rel = repository_rel(path)
        entry: dict[str, Any] = {
            "path": rel,
            "existed": path.exists(),
            "snapshot_path": None,
            "sha256": None,
            "size": 0,
        }
        if path.exists():
            target = snapshot_file_path(root, rel)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
            entry.update(
                {
                    "snapshot_path": repository_rel(target),
                    "sha256": file_sha256(path),
                    "size": path.stat().st_size,
                }
            )
        files.append(entry)

    manifest = {
        "schema_version": 1,
        "feature": args.feature,
        "run_id": args.run_id,
        "step": args.step,
        "created_at": now_kst().isoformat(),
        "kind": "pre-step-snapshot",
        "files": files,
        "archive_residue_policy": "preserve-and-warn",
    }
    write_text(root / "manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(f"h2-snapshot save: wrote {repository_rel(root / 'manifest.json')}")
    return 0


def command_snapshot_list(args: argparse.Namespace) -> int:
    try:
        feature = safe_path_segment(args.feature, "feature")
        run_id_filter = validate_run_id(args.run_id) if args.run_id else None
    except ValueError as error:
        print(f"h2-snapshot list: {error}")
        return 1
    feature_root = ROOT / ".harness-helm" / "runs" / feature
    if not feature_root.exists():
        print(f"h2-snapshot list: no runs for feature {feature}")
        return 0
    manifests = sorted(feature_root.glob("*/snapshots/*/manifest.json"))
    if run_id_filter:
        manifests = [path for path in manifests if path.parts[-4] == run_id_filter]
    if not manifests:
        print("h2-snapshot list: no snapshots found.")
        return 0
    for manifest_path in manifests:
        try:
            manifest = load_snapshot_manifest(manifest_path)
            print(f"{manifest.get('run_id')} {manifest.get('step')} {repository_rel(manifest_path)}")
        except (OSError, ValueError, json.JSONDecodeError) as error:
            print(f"{repository_rel(manifest_path)}: invalid manifest ({error})")
    return 0


def render_restore_report(
    manifest: dict[str, Any],
    actions: list[str],
    warnings: list[str],
    dry_run: bool,
) -> str:
    lines = [
        "---",
        "command: h2-rewind",
        f"feature: {manifest.get('feature')}",
        "status: skipped" if dry_run else "status: updated",
        "next:",
        f"  recommended_h2_step: {manifest.get('step')}",
        "---",
        "",
        f"# h2-rewind Restore: {manifest.get('step')}",
        "",
        "## Actions",
        "",
    ]
    lines.extend(f"- {action}" for action in actions)
    if warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in warnings)
    lines.extend(["", "## Next", "", f"- recommended_h2_step: {manifest.get('step')}", ""])
    return "\n".join(lines)


def command_snapshot_restore(args: argparse.Namespace) -> int:
    try:
        manifest_path = snapshot_manifest_path(args.feature, args.run_id, args.step)
        manifest = load_snapshot_manifest(manifest_path)
        if manifest.get("feature") != args.feature or manifest.get("run_id") != args.run_id or manifest.get("step") != args.step:
            raise ValueError("snapshot manifest does not match requested feature/run-id/step.")
    except FileNotFoundError as error:
        print(f"h2-snapshot restore: {error}")
        return 2
    except (ValueError, json.JSONDecodeError) as error:
        print(f"h2-snapshot restore: {error}")
        return 1

    timestamp = now_kst().strftime("%Y%m%d-%H%M%S")
    backup_root = run_root(args.feature, args.run_id) / "restore-backups" / timestamp / args.step
    actions: list[str] = []
    warnings: list[str] = []
    for item in manifest.get("files", []):
        if not isinstance(item, dict):
            print("h2-snapshot restore: manifest files entries must be objects.")
            return 1
        rel = str(item.get("path", ""))
        try:
            active = resolve_under_root(rel, ROOT, "snapshot file path")
        except ValueError as error:
            print(f"h2-snapshot restore: {error}")
            return 1
        backup = backup_root / rel
        existed = bool(item.get("existed"))
        if active.exists():
            actions.append(f"backup {rel} -> {repository_rel(backup)}")
            if not args.dry_run:
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(active, backup)
        if existed:
            snapshot_rel = str(item.get("snapshot_path") or "")
            try:
                source = resolve_under_root(snapshot_rel, ROOT, "snapshot_path")
            except ValueError as error:
                print(f"h2-snapshot restore: {error}")
                return 1
            if not source.exists():
                print(f"h2-snapshot restore: missing snapshot file {snapshot_rel}")
                return 1
            actions.append(f"restore {rel} from {snapshot_rel}")
            if not args.dry_run:
                active.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, active)
        elif active.exists():
            actions.append(f"remove active file absent at snapshot time: {rel}")
            if not args.dry_run:
                active.unlink()
        else:
            actions.append(f"leave absent: {rel}")

    if args.step == "h2-archive":
        residues = archive_residue_paths(args.feature)
        if residues:
            warnings.append("archive residue preserved: " + ", ".join(residues))

    report = render_restore_report(manifest, actions, warnings, args.dry_run)
    restore_path = snapshot_root(args.feature, args.run_id, args.step) / "restore.md"
    if not args.dry_run:
        write_text(restore_path, report)
    print(report)
    if not args.dry_run:
        print(f"h2-snapshot restore: wrote {repository_rel(restore_path)}")
    return 0


def command_snapshot(args: argparse.Namespace) -> int:
    if args.snapshot_action == "save":
        return command_snapshot_save(args)
    if args.snapshot_action == "list":
        return command_snapshot_list(args)
    if args.snapshot_action == "restore":
        return command_snapshot_restore(args)
    print("h2-snapshot: expected save, list, or restore.")
    return 1


def command_rewind(args: argparse.Namespace) -> int:
    args.snapshot_action = "restore"
    return command_snapshot_restore(args)


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


def is_canonical_knowledge_doc(doc: Doc, schema: dict[str, Any]) -> bool:
    if not doc.rel.startswith(CANONICAL_KNOWLEDGE_ROOTS):
        return False
    if doc.rel.startswith("docs/30_decisions/") and doc.path.name.endswith(".rejected.md"):
        return False
    return include_in_index(doc, schema)


def canonical_docs(docs: list[Doc], schema: dict[str, Any]) -> list[Doc]:
    return [doc for doc in docs if is_canonical_knowledge_doc(doc, schema)]


def index_freshness(index_paths: list[Path], candidates: list[Doc]) -> tuple[str, str]:
    missing = [path.relative_to(ROOT).as_posix() for path in index_paths if not path.exists()]
    if missing:
        return "absent", f"index freshness: missing {', '.join(missing)}; canonical docs direct scan fallback used."
    if not candidates:
        return "ok", "index freshness: indexes exist; no canonical docs were eligible for freshness comparison."

    oldest_index = min(path.stat().st_mtime for path in index_paths)
    newest_candidate = max(doc.path.stat().st_mtime for doc in candidates)
    if newest_candidate > oldest_index:
        return "stale", "index freshness: canonical docs are newer than docs/_indexes; run `.harness-helm/scripts/harness kb-index`."
    return "ok", "index freshness: docs/_indexes are present and not older than canonical docs."


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


def canonical_selected_by(doc: Doc, freshness_state: str) -> str:
    tags = ["canonical-knowledge"]
    if doc.rel.startswith("docs/40_knowledge/") or "canonical-promotion" in list_value(doc.frontmatter.get("tags")):
        tags.append("compound-loop")
    if freshness_state == "absent":
        tags.append("index-absent")
    elif freshness_state == "stale":
        tags.append("index-stale")
    return ", ".join(tags)


RUNTIME_SEED_RULES: list[tuple[set[str], list[str]]] = [
    ({"workflow", "h2", "lifecycle", "command", "cartridge", "adapter", "audit", "harness"},
     ["README.md", ".harness-helm/h2-cartridge.yml", ".harness-helm/h2-schema.yml",
      ".claude/skills/harness-helm/SKILL.md", ".codex/skills/harness-helm/SKILL.md",
      "docs/10_domain/harness-helm/concepts.md"]),
    ({"upstream", "gstack", "superpowers", "compound", "ce", "provider", "surface"},
     [".harness-helm/h2-cartridge.yml",
      ".claude/skills/harness-helm/references/cartridge-command-mapping.md",
      ".claude/skills/harness-helm/references/cartridge-surface-map.md"]),
    ({"normalization", "raw", "fixture", "evidence"},
     [".claude/skills/harness-helm/references/cartridge-output-normalization.md",
      ".harness-helm/h2-cartridge.yml"]),
    ({"reference", "snapshot", "parity", "drift"},
     [".claude/skills/harness-helm/references/runtime-parity.md",
      "docs/40_knowledge/conventions/guidelines/harness-helm/runtime-reference-selection.md"]),
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
    feature_doc_rels = {doc.rel for doc in feature_docs}
    task_docs = docs_matching_task(tokens, docs, schema, feature_doc_rels)
    index_docs = [DOCS / "_indexes" / name for name in ("KB_INDEX.md", "DOMAIN_INDEX.md", "TAG_INDEX.md")]
    canonical_candidates = canonical_docs(docs, schema)
    freshness_state, freshness_line = index_freshness(index_docs, canonical_candidates)
    canonical_entries = [
        (doc.rel, canonical_selected_by(doc, freshness_state))
        for doc in docs_matching_canonical_knowledge(tokens, args.feature, docs, schema)
    ]

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
    lines.extend(["", "### canonical_knowledge"])
    if canonical_entries:
        lines.extend(f"- {rel} (selected_by: {tag})" for rel, tag in canonical_entries)
    else:
        lines.append("- <none>")
    lines.extend(["", "### excluded_by_policy"])
    lines.extend(f"- {item}" for item in excluded)
    lines.extend(
        [
            "",
            "### assumptions",
            "- `_indexes` are routing hints; original docs remain the canonical reference.",
            "- If indexes are stale or absent, canonical docs are inspected directly and marked with `index-absent` or `index-stale`.",
            "- `selected_by` tags docs by source: index | feature-match | task-token | runtime-seed | canonical-knowledge | compound-loop | index-absent | index-stale.",
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
            "- canonical knowledge direct scan completed",
            *([f"- {freshness_line}"] if freshness_state == "ok" else []),
            "",
            "### not_verified",
            "- human review of context relevance",
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
        artifact_paths=[target.relative_to(ROOT).as_posix()],
    )
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
        for legacy_path in sorted(reference_root.glob("upstream-*")):
            hard.append(f"{legacy_path.relative_to(ROOT).as_posix()}: legacy upstream-* reference filename is not allowed.")
        for legacy_name in ("external-tool-registry.md", "external-tool-registry.ko.md"):
            legacy_path = reference_root / legacy_name
            if legacy_path.exists():
                hard.append(f"{legacy_path.relative_to(ROOT).as_posix()}: legacy external-tool-registry filename is not allowed.")
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
            if filename == "cartridge-command-mapping.md" and MISLEADING_VALUE_SNAPSHOT_CLAIM in text:
                hard.append(
                    f"{rel}: must not present itself as a provider/surface value snapshot; "
                    ".harness-helm/h2-cartridge.yml is the single value source."
                )
            if filename in GUIDELINE_DERIVED_REFERENCE_HEADERS:
                guideline = GUIDELINE_DERIVED_REFERENCE_HEADERS[filename]
                expected_snapshot_header = f"Compact runtime snapshot of `{guideline}`."
                expected_mapping_header = f"Mapping authority: `{REFERENCE_MAPPING_AUTHORITY}`."
                if expected_snapshot_header not in text:
                    hard.append(f"{rel}: missing guideline-derived snapshot header {expected_snapshot_header!r}.")
                if expected_mapping_header not in text:
                    hard.append(f"{rel}: missing mapping authority header {expected_mapping_header!r}.")

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
            if filename in GUIDELINE_DERIVED_REFERENCE_HEADERS:
                guideline = GUIDELINE_DERIVED_REFERENCE_HEADERS[filename]
                if guideline not in ko_text:
                    hard.append(
                        f"{ko_path.relative_to(ROOT).as_posix()}: missing canonical guideline path {guideline!r}."
                    )
                if REFERENCE_MAPPING_AUTHORITY not in ko_text:
                    hard.append(
                        f"{ko_path.relative_to(ROOT).as_posix()}: missing mapping authority path {REFERENCE_MAPPING_AUTHORITY!r}."
                    )

    print_report("reference-validate", hard, warnings)
    return 1 if hard and args.strict else 0


NORMALIZATION_FIXTURE_COMMANDS = {"h2-plan", "h2-design", "h2-report"}
TARGET_SMOKE_REQUIRED_PATHS = [
    "AGENTS.md",
    "CLAUDE.md",
    ".harness-helm/h2-cartridge.yml",
    ".harness-helm/h2-compound.yml",
    ".harness-helm/h2-schema.yml",
    ".harness-helm/scripts/harness.py",
    ".claude/commands/h2",
    ".claude/skills/harness-helm/SKILL.md",
    ".codex/skills/h2",
    ".codex/skills/harness-helm/SKILL.md",
    "docs",
    "docs/40_knowledge/conventions/guidelines/harness-helm",
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

        for rel in sorted((target / "docs" / "40_knowledge" / "conventions" / "guidelines").glob("h2-*.md")):
            hard.append(
                "target-smoke: legacy flat guideline filename remains in target project: "
                f"{rel.relative_to(target).as_posix()}."
            )
        for root in [
            target / ".claude" / "skills" / "harness-helm" / "references",
            target / ".codex" / "skills" / "harness-helm" / "references",
        ]:
            if root.exists():
                for rel in sorted(root.glob("upstream-*")):
                    hard.append(
                        "target-smoke: legacy upstream-* reference filename remains in target project: "
                        f"{rel.relative_to(target).as_posix()}."
                    )

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


def cleanup_archived_run(feature: str, dry_run: bool, dest_root: Path | None = None) -> None:
    run_path = ROOT / ".harness-helm" / "runs" / feature
    if not run_path.exists():
        return
    if dest_root is not None:
        runs_dest = dest_root / "runs"
        print(f"  {'would move' if dry_run else 'move'} {run_path.relative_to(ROOT)} -> {runs_dest.relative_to(ROOT)}")
        if not dry_run:
            runs_dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(run_path), str(runs_dest))
    else:
        print(f"  {'would remove' if dry_run else 'remove'} {run_path.relative_to(ROOT)}")
        if not dry_run:
            shutil.rmtree(run_path)


INSTALL_MANIFEST_SCHEMA_VERSION = 1
INSTALL_MARKER_VERSION = "v1"
INSTALL_MANIFEST_KINDS = {"copy", "copy_dir", "copy_if_absent", "managed"}
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
        print(f"  would write runtime summary {(dest_root / RUNTIME_SUMMARY_NAME).relative_to(ROOT)}")
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
        write_runtime_summary(dest_root, generated_at=now)
    return 0


@dataclasses.dataclass
class RunStatsEntry:
    feature: str
    run_id: str
    command: str
    status: str
    started_at: dt.datetime | None
    completed_at: dt.datetime | None
    elapsed_seconds: int | None
    manifest_path: Path | None
    warnings: list[str]
    autorun_id: str | None


def command_run_mark(args: argparse.Namespace) -> int:
    try:
        if args.run_mark_action == "start":
            path = start_run_manifest(
                args.feature,
                args.run_id,
                args.h2_command,
                task=args.task,
                autorun_id=args.autorun_id,
            )
            print(f"run-mark start: wrote {repository_rel(path)}")
            return 0
        if args.run_mark_action == "complete":
            path = complete_run_manifest(
                args.feature,
                args.run_id,
                status=args.status,
                artifact_paths=args.artifact,
            )
            print(f"run-mark complete: wrote {repository_rel(path)}")
            return 0
    except (FileNotFoundError, ValueError) as error:
        print(f"run-mark {args.run_mark_action}: {error}")
        return 1
    print(f"run-mark: unknown action {args.run_mark_action}")
    return 1


def iter_run_dirs(feature: str | None = None) -> list[Path]:
    root = ROOT / ".harness-helm" / "runs"
    if not root.exists():
        return []
    feature_dirs = [root / safe_path_segment(feature, "feature")] if feature else [
        path for path in sorted(root.iterdir()) if path.is_dir() and path.name != "_templates"
    ]
    run_dirs: list[Path] = []
    for feature_dir in feature_dirs:
        if not feature_dir.exists() or not feature_dir.is_dir():
            continue
        for path in sorted(feature_dir.iterdir()):
            if path.is_dir() and RUN_ID_PATTERN.match(path.name):
                run_dirs.append(path)
    return run_dirs


def resolve_existing_dir(value: str) -> Path | None:
    path = Path(value).expanduser()
    candidates = [path] if path.is_absolute() else [ROOT / path, path]
    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate.resolve()
    return None


def archive_feature(archive_path: Path) -> str:
    manifest = load_run_manifest(archive_path / "manifest.md")
    feature = manifest.get("feature")
    if isinstance(feature, str) and feature:
        return feature
    name = archive_path.name
    if "_" in name:
        return name.split("_", 1)[1]
    return name


def iter_archive_run_dirs(archive_path: Path) -> list[Path]:
    runs_root = archive_path / "runs"
    if not runs_root.exists() or not runs_root.is_dir():
        return []
    return sorted(
        path
        for path in runs_root.iterdir()
        if path.is_dir()
        and RUN_ID_PATTERN.match(path.name)
        and ((path / "manifest.md").exists() or (path / "context-pack.md").exists())
    )


def is_archive_run_stats_path(path: Path) -> bool:
    return (path / "runs").is_dir() and (path / "manifest.md").exists()


def build_run_stats_entry(run_dir: Path, feature_override: str | None = None) -> RunStatsEntry:
    feature = feature_override or run_dir.parent.name
    run_id_value = run_dir.name
    manifest_path = run_dir / "manifest.md"
    manifest_exists = manifest_path.exists()
    manifest = load_run_manifest(manifest_path)
    warnings: list[str] = []
    run_id_started_at = started_at_from_run_id(run_id_value)
    manifest_started_at = parse_run_timestamp(manifest.get("started_at"))
    started_at = manifest_started_at or run_id_started_at
    if manifest_started_at and abs((manifest_started_at - run_id_started_at).total_seconds()) >= 1:
        warnings.append("started_at differs from run-id timestamp")
    completed_at = parse_run_timestamp(manifest.get("completed_at"))
    command = str(manifest.get("command") or command_from_run_id(run_id_value))
    if not manifest_exists:
        status = "missing-manifest"
    else:
        status = str(manifest.get("status") or "incomplete")
    elapsed_seconds: int | None = None
    if completed_at and started_at and status not in {"missing-manifest", "running", "incomplete"}:
        elapsed_seconds = max(0, int((completed_at - started_at).total_seconds()))
    return RunStatsEntry(
        feature=feature,
        run_id=run_id_value,
        command=command,
        status=status,
        started_at=started_at,
        completed_at=completed_at,
        elapsed_seconds=elapsed_seconds,
        manifest_path=manifest_path if manifest_exists else None,
        warnings=warnings,
        autorun_id=manifest.get("autorun_id") if isinstance(manifest.get("autorun_id"), str) else None,
    )


def apply_archive_elapsed_fallback(entries: list[RunStatsEntry]) -> None:
    ordered = sorted(entries, key=lambda entry: entry.started_at or dt.datetime.max.replace(tzinfo=dt.timezone.utc))
    for index, entry in enumerate(ordered):
        if entry.elapsed_seconds is not None or entry.started_at is None:
            continue
        next_started_at = None
        for next_entry in ordered[index + 1 :]:
            if next_entry.started_at:
                next_started_at = next_entry.started_at
                break
        if next_started_at is None:
            continue
        entry.completed_at = next_started_at
        entry.elapsed_seconds = max(0, int((next_started_at - entry.started_at).total_seconds()))
        entry.status = "estimated"
        entry.warnings.append("elapsed estimated from next run start because manifest completed_at is missing")


def format_elapsed(seconds: int | None, status: str) -> str:
    if seconds is None:
        if status in {"running", "incomplete", "missing-manifest"}:
            return status
        return "not available"
    minutes, sec = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h {minutes:02d}m {sec:02d}s"
    if minutes:
        return f"{minutes}m {sec:02d}s"
    return f"{sec}s"


def run_stats_to_dict(entry: RunStatsEntry) -> dict[str, Any]:
    return {
        "feature": entry.feature,
        "run_id": entry.run_id,
        "command": entry.command,
        "status": entry.status,
        "started_at": format_run_timestamp(entry.started_at) if entry.started_at else None,
        "completed_at": format_run_timestamp(entry.completed_at) if entry.completed_at else None,
        "elapsed_seconds": entry.elapsed_seconds,
        "elapsed": format_elapsed(entry.elapsed_seconds, entry.status),
        "autorun_id": entry.autorun_id,
        "manifest_path": repository_rel(entry.manifest_path) if entry.manifest_path else None,
        "warnings": entry.warnings,
    }


def run_stats_entry_from_dict(item: dict[str, Any]) -> RunStatsEntry:
    manifest_path_value = item.get("manifest_path")
    manifest_path = None
    if isinstance(manifest_path_value, str) and manifest_path_value:
        path = Path(manifest_path_value)
        manifest_path = path if path.is_absolute() else ROOT / path
    return RunStatsEntry(
        feature=str(item.get("feature") or ""),
        run_id=str(item.get("run_id") or ""),
        command=str(item.get("command") or ""),
        status=str(item.get("status") or ""),
        started_at=parse_run_timestamp(item.get("started_at")),
        completed_at=parse_run_timestamp(item.get("completed_at")),
        elapsed_seconds=item.get("elapsed_seconds") if isinstance(item.get("elapsed_seconds"), int) else None,
        manifest_path=manifest_path,
        warnings=[str(warning) for warning in list_value(item.get("warnings"))],
        autorun_id=item.get("autorun_id") if isinstance(item.get("autorun_id"), str) else None,
    )


def latest_activity(entry: RunStatsEntry) -> dt.datetime:
    return entry.completed_at or entry.started_at or dt.datetime.min.replace(tzinfo=dt.timezone.utc)


def autorun_groups(entries: list[RunStatsEntry]) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    by_key: dict[tuple[str, str], list[RunStatsEntry]] = {}
    for entry in entries:
        if entry.autorun_id and entry.elapsed_seconds is not None and entry.started_at and entry.completed_at:
            by_key.setdefault((entry.feature, entry.autorun_id), []).append(entry)
    for (feature, autorun_id), grouped in sorted(by_key.items()):
        starts = [entry.started_at for entry in grouped if entry.started_at]
        ends = [entry.completed_at for entry in grouped if entry.completed_at]
        if not starts or not ends:
            continue
        total = max(0, int((max(ends) - min(starts)).total_seconds()))
        groups.append(
            {
                "feature": feature,
                "autorun_id": autorun_id,
                "stage_count": len(grouped),
                "started_at": format_run_timestamp(min(starts)),
                "completed_at": format_run_timestamp(max(ends)),
                "elapsed_seconds": total,
                "elapsed": format_elapsed(total, "completed"),
            }
        )
    return groups


def archive_wall_clock(entries: list[RunStatsEntry]) -> int | None:
    completed_entries = [entry for entry in entries if entry.started_at and entry.completed_at]
    if not completed_entries:
        return None
    starts = [entry.started_at for entry in completed_entries if entry.started_at]
    ends = [entry.completed_at for entry in completed_entries if entry.completed_at]
    return max(0, int((max(ends) - min(starts)).total_seconds()))


def build_archive_runtime_summary(archive_path: Path, generated_at: dt.datetime | None = None) -> dict[str, Any]:
    feature = archive_feature(archive_path)
    entries = [build_run_stats_entry(path, feature_override=feature) for path in iter_archive_run_dirs(archive_path)]
    apply_archive_elapsed_fallback(entries)
    entries.sort(key=latest_activity)
    total_elapsed_seconds = sum(entry.elapsed_seconds or 0 for entry in entries)
    wall_clock_seconds = archive_wall_clock(entries)
    warnings = sorted({warning for entry in entries for warning in entry.warnings})
    archive_rel = repository_rel(archive_path) if archive_path.is_relative_to(ROOT) else str(archive_path)
    summary: dict[str, Any] = {
        "schema_version": 1,
        "type": "runtime-summary",
        "feature": feature,
        "archive_path": archive_rel,
        "generated_at": format_run_timestamp(generated_at or now_kst()),
        "generated_from": "h2-archive",
        "runs": [run_stats_to_dict(entry) for entry in entries],
        "total_elapsed_seconds": total_elapsed_seconds,
        "total_elapsed": format_elapsed(total_elapsed_seconds, "completed"),
        "archive_wall_clock_seconds": wall_clock_seconds,
        "archive_wall_clock": format_elapsed(wall_clock_seconds, "completed") if wall_clock_seconds is not None else None,
        "autorun_groups": autorun_groups(entries),
        "warnings": warnings,
    }
    summary["totals"] = {
        "stage_elapsed_seconds": total_elapsed_seconds,
        "stage_elapsed": summary["total_elapsed"],
        "archive_wall_clock_seconds": wall_clock_seconds,
        "archive_wall_clock": summary["archive_wall_clock"],
    }
    return summary


def write_runtime_summary(archive_path: Path, generated_at: dt.datetime | None = None) -> Path:
    summary_path = archive_path / RUNTIME_SUMMARY_NAME
    summary = build_archive_runtime_summary(archive_path, generated_at=generated_at)
    summary["summary_path"] = repository_rel(summary_path) if summary_path.is_relative_to(ROOT) else str(summary_path)
    write_text(summary_path, json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    return summary_path


def load_runtime_summary(archive_path: Path) -> dict[str, Any] | None:
    summary_path = archive_path / RUNTIME_SUMMARY_NAME
    if not summary_path.exists():
        return None
    try:
        summary = json.loads(read_text(summary_path))
    except json.JSONDecodeError:
        return None
    return summary if isinstance(summary, dict) else None


def command_run_stats(args: argparse.Namespace) -> int:
    archive_path = resolve_existing_dir(args.feature) if args.feature else None
    archive_label: str | None = None
    runtime_summary: dict[str, Any] | None = None
    if archive_path and is_archive_run_stats_path(archive_path):
        runtime_summary = load_runtime_summary(archive_path)
        if runtime_summary:
            entries = [
                run_stats_entry_from_dict(item)
                for item in raw_list_value(runtime_summary.get("runs"))
                if isinstance(item, dict)
            ]
        else:
            feature = archive_feature(archive_path)
            entries = [build_run_stats_entry(path, feature_override=feature) for path in iter_archive_run_dirs(archive_path)]
            apply_archive_elapsed_fallback(entries)
        archive_label = repository_rel(archive_path) if archive_path.is_relative_to(ROOT) else str(archive_path)
    else:
        entries = [build_run_stats_entry(path) for path in iter_run_dirs(args.feature)]
    entries.sort(key=latest_activity, reverse=not archive_label)
    limit = args.limit
    if args.feature:
        selected = entries[:limit]
        payload = {
            "feature": runtime_summary.get("feature") if runtime_summary else archive_feature(archive_path) if archive_path and archive_label else args.feature,
            "archive_path": archive_label,
            "runs": [run_stats_to_dict(entry) for entry in selected],
            "total_elapsed_seconds": sum(entry.elapsed_seconds or 0 for entry in selected),
            "autorun_groups": autorun_groups(selected),
        }
        if runtime_summary:
            payload["summary_path"] = runtime_summary.get("summary_path")
            payload["generated_at"] = runtime_summary.get("generated_at")
            payload["total_elapsed_seconds"] = runtime_summary.get("total_elapsed_seconds")
            payload["total_elapsed"] = runtime_summary.get("total_elapsed")
            payload["archive_wall_clock_seconds"] = runtime_summary.get("archive_wall_clock_seconds")
            payload["archive_wall_clock"] = runtime_summary.get("archive_wall_clock")
            payload["autorun_groups"] = raw_list_value(runtime_summary.get("autorun_groups"))
            payload["warnings"] = list_value(runtime_summary.get("warnings"))
        else:
            archive_total = archive_wall_clock(selected)
            if archive_label and archive_total is not None:
                payload["archive_wall_clock_seconds"] = archive_total
                payload["archive_wall_clock"] = format_elapsed(archive_total, "completed")
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0
        print(f"feature: {payload['feature']}")
        if archive_label:
            print(f"archive: {archive_label}")
        if payload.get("summary_path"):
            print(f"summary: {payload['summary_path']}")
        print("")
        print("  run-id                    command      status            elapsed")
        for entry in selected:
            print(
                f"  {entry.run_id:<25} {entry.command:<12} {entry.status:<17} "
                f"{format_elapsed(entry.elapsed_seconds, entry.status)}"
            )
        total = payload["total_elapsed_seconds"]
        print("")
        print(f"  total: {payload.get('total_elapsed') or format_elapsed(total if isinstance(total, int) else None, 'completed')}")
        if "archive_wall_clock" in payload:
            print(f"  archive wall-clock: {payload['archive_wall_clock']}")
        for group in payload["autorun_groups"]:
            print(f"  autorun {group['autorun_id']}: {group['elapsed']}")
        warnings = sorted(set(list_value(payload.get("warnings")) or [warning for entry in selected for warning in entry.warnings]))
        if warnings:
            print("")
            for warning in warnings:
                print(f"  warning: {warning}")
        return 0

    latest_by_feature: dict[str, RunStatsEntry] = {}
    for entry in entries:
        latest_by_feature.setdefault(entry.feature, entry)
    selected_features = sorted(latest_by_feature.values(), key=latest_activity, reverse=True)[:limit]
    payload = {
        "features": [run_stats_to_dict(entry) for entry in selected_features],
        "shown": len(selected_features),
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    print("features:")
    print("")
    print("  feature                    latest-run                command      status            elapsed")
    for entry in selected_features:
        feature_label = entry.feature if len(entry.feature) <= 26 else entry.feature[:23] + "..."
        print(
            f"  {feature_label:<26} {entry.run_id:<25} {entry.command:<12} "
            f"{entry.status:<17} {format_elapsed(entry.elapsed_seconds, entry.status)}"
        )
    print("")
    print(f"  shown: {len(selected_features)} features")
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
        if path.name in {"normalized", "promotion-candidates", "snapshots", "restore-backups"} and age >= args.normalized_days:
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
    context.add_argument("--autorun-id")
    context.add_argument("--dry-run", action="store_true")
    context.set_defaults(func=command_context)

    run_mark = sub.add_parser("run-mark")
    run_mark_sub = run_mark.add_subparsers(dest="run_mark_action", required=True)
    run_mark_start = run_mark_sub.add_parser("start")
    run_mark_start.add_argument("--feature", required=True)
    run_mark_start.add_argument("--run-id", required=True)
    run_mark_start.add_argument("--command", dest="h2_command", required=True, choices=sorted(EXPECTED_COMMANDS))
    run_mark_start.add_argument("--task")
    run_mark_start.add_argument("--autorun-id")
    run_mark_start.set_defaults(func=command_run_mark)
    run_mark_complete = run_mark_sub.add_parser("complete")
    run_mark_complete.add_argument("--feature", required=True)
    run_mark_complete.add_argument("--run-id", required=True)
    run_mark_complete.add_argument("--status", choices=["completed", "failed", "incomplete"], default="completed")
    run_mark_complete.add_argument("--artifact", action="append")
    run_mark_complete.set_defaults(func=command_run_mark)

    run_stats = sub.add_parser("run-stats")
    run_stats.add_argument("feature", nargs="?")
    run_stats.add_argument("--limit", type=int, default=20)
    run_stats.add_argument("--json", action="store_true")
    run_stats.set_defaults(func=command_run_stats)

    snapshot = sub.add_parser("h2-snapshot")
    snapshot_sub = snapshot.add_subparsers(dest="snapshot_action", required=True)
    snapshot_save = snapshot_sub.add_parser("save")
    snapshot_save.add_argument("--feature", required=True)
    snapshot_save.add_argument("--run-id", required=True)
    snapshot_save.add_argument("--step", required=True, choices=sorted(REWINDABLE_STEPS))
    snapshot_save.set_defaults(func=command_snapshot)
    snapshot_list = snapshot_sub.add_parser("list")
    snapshot_list.add_argument("--feature", required=True)
    snapshot_list.add_argument("--run-id")
    snapshot_list.set_defaults(func=command_snapshot)
    snapshot_restore = snapshot_sub.add_parser("restore")
    snapshot_restore.add_argument("--feature", required=True)
    snapshot_restore.add_argument("--run-id", required=True)
    snapshot_restore.add_argument("--step", required=True, choices=sorted(REWINDABLE_STEPS))
    snapshot_restore.add_argument("--dry-run", action="store_true")
    snapshot_restore.add_argument("--force", action="store_true")
    snapshot_restore.set_defaults(func=command_snapshot)

    rewind = sub.add_parser("h2-rewind")
    rewind.add_argument("step", choices=sorted(REWINDABLE_STEPS))
    rewind.add_argument("--feature", required=True)
    rewind.add_argument("--run-id", required=True)
    rewind.add_argument("--dry-run", action="store_true")
    rewind.add_argument("--force", action="store_true")
    rewind.set_defaults(func=command_rewind)

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
    args = parser.parse_args(argv)
    quiet_logs = args.command == "run-stats" and getattr(args, "json", False)
    if not quiet_logs:
        print(LOG_START)
    try:
        return args.func(args)
    finally:
        if not quiet_logs:
            print(LOG_END)


if __name__ == "__main__":
    raise SystemExit(main())
