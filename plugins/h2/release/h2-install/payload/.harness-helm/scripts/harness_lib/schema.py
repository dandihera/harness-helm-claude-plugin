from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import Any

from . import paths
from .docs import Doc
from .frontmatter import list_value, parse_simple_yaml
from .utils import read_text


DEFAULT_GENERATED_HEADER = "<!-- AUTO-GENERATED: do not edit manually. Run .harness-helm/scripts/kb-index.sh. -->"
DECISION_SUFFIX_PATTERN = re.compile(r"\.([a-z][a-z0-9_-]*)\.md$")
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
DEFAULT_HARVEST_POLICY: dict[str, Any] = {
    "schema_version": 1,
    "canonical_destination": {
        "solution": "docs/40_knowledge/solutions",
        "convention": "docs/40_knowledge/conventions",
        "domain": "docs/10_domain",
        "spec": "docs/20_specs",
        "decision": "docs/30_decisions",
        "runbook": "docs/50_operations",
    },
    "review_gate": {
        "low_risk_auto_write": True,
        "governed_require_approval": True,
        "confidence_threshold": "high",
    },
    "staging": {
        "path": "docs/_harvest-inbox",
        "type_by_subfolder": {
            "solution": "solution",
            "convention": "convention",
            "domain": "domain",
            "spec": "spec",
            "decision": "decision",
            "ops": "runbook",
        },
    },
    "promoted_status": {
        "solution": "verified",
        "convention": "verified",
        "decision": "accepted",
        "spec": "stable",
        "domain": "stable",
        "runbook": "active",
    },
}


def excluded_patterns(schema: dict[str, Any], key: str = "lint_index") -> list[str]:
    raw = schema.get("exclude_paths", {})
    if not isinstance(raw, dict):
        return []
    value = raw.get(key, [])
    if isinstance(value, list):
        return [str(pattern) for pattern in value]
    return [str(value)]


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
    if paths.SCHEMA_PATH.exists():
        raw = parse_simple_yaml(read_text(paths.SCHEMA_PATH))
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
            "harvest_policy_schema": raw.get("harvest_policy_schema", {}),
        }

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
        "harvest_policy_schema": {
            "schema_versions": [1],
            "destination_keys": ["solution", "convention", "domain", "spec", "decision", "runbook"],
            "subfolder_keys": ["solution", "convention", "domain", "spec", "decision", "ops"],
        },
    }


def deep_merge(default: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(default)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_compound_policy(schema: dict[str, Any]) -> tuple[dict[str, Any], str, list[str]]:
    if not paths.COMPOUND_POLICY_PATH.exists():
        return copy.deepcopy(DEFAULT_COMPOUND_POLICY), "built-in-default", []

    raw = parse_simple_yaml(read_text(paths.COMPOUND_POLICY_PATH))
    policy = deep_merge(DEFAULT_COMPOUND_POLICY, raw)
    return policy, ".harness-helm/h2-compound.yml", validate_compound_policy(policy, schema)


def load_harvest_policy(schema: dict[str, Any]) -> tuple[dict[str, Any], str, list[str]]:
    if not paths.HARVEST_POLICY_PATH.exists():
        return copy.deepcopy(DEFAULT_HARVEST_POLICY), "built-in-default", []

    raw = parse_simple_yaml(read_text(paths.HARVEST_POLICY_PATH))
    policy = deep_merge(DEFAULT_HARVEST_POLICY, raw)
    return policy, ".harness-helm/h2-harvest.yml", validate_harvest_policy(policy, schema)


def validate_harvest_policy(policy: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    policy_schema = schema.get("harvest_policy_schema", {})
    versions = set(list_value(policy_schema.get("schema_versions", [1])))
    destination_keys = set(
        list_value(
            policy_schema.get(
                "destination_keys",
                ["solution", "convention", "domain", "spec", "decision", "runbook"],
            )
        )
    )
    subfolder_keys = set(
        list_value(
            policy_schema.get(
                "subfolder_keys",
                ["solution", "convention", "domain", "spec", "decision", "ops"],
            )
        )
    )

    version = str(policy.get("schema_version"))
    if version not in versions:
        warnings.append(f".harness-helm/h2-harvest.yml: unsupported schema_version={version}.")

    destinations = policy.get("canonical_destination", {})
    if not isinstance(destinations, dict):
        warnings.append(".harness-helm/h2-harvest.yml: canonical_destination must be a mapping.")
        destinations = {}
    for key, value in destinations.items():
        if key not in destination_keys:
            warnings.append(f".harness-helm/h2-harvest.yml: unknown canonical_destination key={key}.")
        if key not in schema.get("type", set()):
            warnings.append(f".harness-helm/h2-harvest.yml: canonical_destination key is not docs type={key}.")
        if not isinstance(value, str) or paths.has_path_escape(value):
            warnings.append(f".harness-helm/h2-harvest.yml: invalid canonical_destination.{key}={value}.")

    staging = policy.get("staging", {})
    if not isinstance(staging, dict):
        warnings.append(".harness-helm/h2-harvest.yml: staging must be a mapping.")
        staging = {}
    staging_path = staging.get("path")
    if not isinstance(staging_path, str) or paths.has_path_escape(staging_path):
        warnings.append(f".harness-helm/h2-harvest.yml: invalid staging.path={staging_path}.")
    subfolders = staging.get("type_by_subfolder", {})
    if not isinstance(subfolders, dict):
        warnings.append(".harness-helm/h2-harvest.yml: staging.type_by_subfolder must be a mapping.")
        subfolders = {}
    for key, value in subfolders.items():
        if key not in subfolder_keys:
            warnings.append(f".harness-helm/h2-harvest.yml: unknown staging.type_by_subfolder key={key}.")
        if value not in destinations:
            warnings.append(f".harness-helm/h2-harvest.yml: unknown type_by_subfolder.{key}={value}.")

    promoted = policy.get("promoted_status", {})
    if not isinstance(promoted, dict):
        warnings.append(".harness-helm/h2-harvest.yml: promoted_status must be a mapping.")
        promoted = {}
    for key, value in promoted.items():
        if key not in destinations:
            warnings.append(f".harness-helm/h2-harvest.yml: unknown promoted_status key={key}.")
        if value not in schema.get("status", set()):
            warnings.append(f".harness-helm/h2-harvest.yml: invalid promoted_status.{key}={value}.")

    review_gate = policy.get("review_gate", {})
    if not isinstance(review_gate, dict):
        warnings.append(".harness-helm/h2-harvest.yml: review_gate must be a mapping.")
        review_gate = {}
    threshold = str(review_gate.get("confidence_threshold", "high"))
    if threshold not in schema.get("confidence", set()):
        warnings.append(f".harness-helm/h2-harvest.yml: invalid review_gate.confidence_threshold={threshold}.")
    if review_gate.get("governed_require_approval") is False:
        warnings.append(".harness-helm/h2-harvest.yml: governed_require_approval=false is accepted but Phase 1 keeps governed types pending.")
    return warnings


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
        if not isinstance(value, str) or paths.has_path_escape(value):
            warnings.append(f".harness-helm/h2-compound.yml: invalid canonical_destination.{key}={value}.")

    review_gate = policy.get("review_gate", {})
    if not isinstance(review_gate, dict):
        warnings.append(".harness-helm/h2-compound.yml: review_gate must be a mapping.")
        review_gate = {}
    threshold = str(review_gate.get("confidence_threshold", "high"))
    if threshold not in schema.get("confidence", set()):
        warnings.append(f".harness-helm/h2-compound.yml: invalid review_gate.confidence_threshold={threshold}.")

    retrieval = policy.get("retrieval_hook_policy", {})
    if not isinstance(retrieval, dict):
        warnings.append(".harness-helm/h2-compound.yml: retrieval_hook_policy must be a mapping.")
        retrieval = {}
    enforcement = str(retrieval.get("enforcement", "warn"))
    if enforcement not in enforcement_values:
        warnings.append(f".harness-helm/h2-compound.yml: invalid retrieval_hook_policy.enforcement={enforcement}.")
    elif enforcement == "error":
        warnings.append(".harness-helm/h2-compound.yml: enforcement=error is accepted but downgraded to warning in this scope.")
    return warnings


def generated_header_ok(doc: Doc, schema: dict[str, Any]) -> bool:
    expected = str(schema.get("generated_header", DEFAULT_GENERATED_HEADER))
    return doc.body.startswith(expected) or read_text(doc.path).startswith(expected)
