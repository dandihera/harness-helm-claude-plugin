from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from . import paths
from .frontmatter import list_value, parse_frontmatter, parse_simple_yaml
from .run_lifecycle import EXPECTED_COMMANDS
from .schema import excluded_patterns, load_schema
from .target_surface import TARGET_SMOKE_REQUIRED_PATHS
from .templates import CANONICAL_TEMPLATES
from .utils import print_report, read_text


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
COMMON_H2_OUTPUT_SECTIONS = {"Context Pack", "Artifacts", "Routing", "Verification", "Next"}
ROUTING_PLACEHOLDER_PATTERN = re.compile(r"{([^{}]+)}")
ALLOWED_ROUTING_PLACEHOLDERS = {"feature", "run-id", "type", "topic", "step"}
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
NORMALIZATION_FIXTURE_COMMANDS = {"h2-plan", "h2-design", "h2-report"}


@dataclass(frozen=True)
class ChangedPath:
    path: Path
    status: str


def _repo_relative(path: Path, root: Path) -> Path:
    if path.is_absolute():
        return path.relative_to(root)
    return path


def _is_runtime_skill_path(path: Path) -> bool:
    parts = path.parts
    return len(parts) >= 3 and parts[0] in {".claude", ".codex"} and parts[1] == "skills"


def runtime_translation_peer(path: Path) -> Path | None:
    if not _is_runtime_skill_path(path):
        return None
    if path.name == "SKILL.md":
        return path.with_name("SKILL.ko.md")
    if path.name == "SKILL.ko.md":
        return path.with_name("SKILL.md")
    if path.parent.name != "references":
        return None
    if path.name.endswith(".ko.md"):
        return path.with_name(path.name.removesuffix(".ko.md") + ".md")
    if path.suffix == ".md":
        return path.with_name(path.stem + ".ko.md")
    return None


def _changed_path_key(changed: ChangedPath) -> tuple[str, str]:
    return (changed.path.as_posix(), changed.status)


def changed_runtime_translation_pairs(
    changed: Iterable[ChangedPath],
    root: Path,
) -> tuple[list[str], list[str]]:
    hard: list[str] = []
    warnings: list[str] = []
    normalized = [
        ChangedPath(_repo_relative(item.path, root), item.status)
        for item in changed
    ]
    changed_by_path = {item.path.as_posix(): item for item in normalized}

    for item in sorted(normalized, key=_changed_path_key):
        peer = runtime_translation_peer(item.path)
        if peer is None:
            continue
        peer_item = changed_by_path.get(peer.as_posix())
        rel = item.path.as_posix()
        peer_rel = peer.as_posix()
        if peer_item is None:
            if item.status == "added" and (root / peer).exists():
                continue
            hard.append(f"{rel}: runtime translation pair changed without {peer_rel}.")
            continue
        if item.status == "deleted" and peer_item.status != "deleted":
            hard.append(f"{rel}: runtime translation pair deletion must also delete {peer_rel}.")
        elif item.status != "deleted" and peer_item.status == "deleted":
            hard.append(f"{rel}: runtime translation pair changed while {peer_rel} is deleted.")

    return hard, warnings


def _parse_name_status(stdout: str) -> list[ChangedPath]:
    changed: list[ChangedPath] = []
    for line in stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status_code = parts[0]
        status = status_code[0]
        if status == "D" and len(parts) >= 2:
            changed.append(ChangedPath(Path(parts[1]), "deleted"))
        elif status == "R" and len(parts) >= 3:
            changed.append(ChangedPath(Path(parts[1]), "deleted"))
            changed.append(ChangedPath(Path(parts[2]), "added"))
        elif status in {"A", "C"} and len(parts) >= 2:
            changed.append(ChangedPath(Path(parts[1]), "added"))
        elif len(parts) >= 2:
            changed.append(ChangedPath(Path(parts[1]), "modified"))
    return changed


def run_git_name_status(root: Path, args: Sequence[str]) -> tuple[list[ChangedPath], list[str]]:
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return [], [f"git {' '.join(args)} failed: {exc}"]
    if proc.returncode != 0:
        reason = proc.stderr.strip() or proc.stdout.strip() or f"exit {proc.returncode}"
        return [], [f"git {' '.join(args)} failed: {reason}"]
    return _parse_name_status(proc.stdout), []


def _run_git_untracked(root: Path) -> tuple[list[ChangedPath], list[str]]:
    try:
        proc = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return [], [f"git ls-files --others --exclude-standard failed: {exc}"]
    if proc.returncode != 0:
        reason = proc.stderr.strip() or proc.stdout.strip() or f"exit {proc.returncode}"
        return [], [f"git ls-files --others --exclude-standard failed: {reason}"]
    return [ChangedPath(Path(line), "added") for line in proc.stdout.splitlines() if line.strip()], []


def _github_event_diff_args() -> list[str] | None:
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        return None
    try:
        event = json.loads(Path(event_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    pull_request = event.get("pull_request")
    if isinstance(pull_request, dict):
        base = pull_request.get("base", {}).get("sha")
        head = pull_request.get("head", {}).get("sha")
        if base and head:
            return ["diff", "--name-status", f"{base}...{head}"]
    before = event.get("before")
    after = event.get("after")
    if before and after and not str(before).startswith("0000000"):
        return ["diff", "--name-status", f"{before}..{after}"]
    return None


def collect_changed_files(root: Path) -> tuple[list[ChangedPath], list[str]]:
    base_ref = os.environ.get("GITHUB_BASE_REF")
    if base_ref:
        changed, warnings = run_git_name_status(root, ["diff", "--name-status", f"origin/{base_ref}...HEAD"])
        if not warnings:
            return changed, []
        event_args = _github_event_diff_args()
        if event_args is not None:
            changed, event_warnings = run_git_name_status(root, event_args)
            if not event_warnings:
                return changed, []
    else:
        event_args = _github_event_diff_args()
        if event_args is not None:
            changed, event_warnings = run_git_name_status(root, event_args)
            if not event_warnings:
                return changed, []

    collected: list[ChangedPath] = []
    warnings: list[str] = []
    for args in (
        ["diff", "--name-status", "HEAD"],
        ["diff", "--cached", "--name-status"],
    ):
        changed, cmd_warnings = run_git_name_status(root, args)
        collected.extend(changed)
        warnings.extend(cmd_warnings)
    changed, cmd_warnings = _run_git_untracked(root)
    collected.extend(changed)
    warnings.extend(cmd_warnings)

    if warnings:
        return [], warnings
    deduped = sorted(set(collected), key=_changed_path_key)
    return deduped, []


def validate_runtime_skill_translation_files(root: Path) -> list[str]:
    hard: list[str] = []
    for skill_root in (root / ".claude" / "skills", root / ".codex" / "skills"):
        if not skill_root.exists():
            continue
        for skill_path in sorted(skill_root.glob("**/SKILL.md")):
            ko_path = skill_path.with_name("SKILL.ko.md")
            if not ko_path.exists():
                hard.append(f"{ko_path.relative_to(root).as_posix()}: missing Korean skill translation.")
        for ko_path in sorted(skill_root.glob("**/SKILL.ko.md")):
            skill_path = ko_path.with_name("SKILL.md")
            if not skill_path.exists():
                hard.append(f"{ko_path.relative_to(root).as_posix()}: Korean skill translation has no base SKILL.md.")
    return hard


def command_cartridge_validate(args: argparse.Namespace) -> int:
    hard: list[str] = []
    warnings: list[str] = []

    if not paths.CARTRIDGE_PATH.exists():
        hard.append(".harness-helm/h2-cartridge.yml is missing.")
        print_report("h2-cartridge", hard, warnings)
        return 1

    cartridge = parse_simple_yaml(read_text(paths.CARTRIDGE_PATH))
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

    required_command_fields = {"mode", "provider", "surface", "fallback_label", "routing_target", "output_language"}
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
        "harvest-inbox",
        "harvest-tag",
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


def command_template_validate(args: argparse.Namespace) -> int:
    schema = load_schema()
    hard: list[str] = []
    warnings: list[str] = []
    for dtype, filename in CANONICAL_TEMPLATES.items():
        path = paths.DOCS / "_templates" / filename
        if not path.exists():
            hard.append(f"docs/_templates/{filename}: missing canonical template.")
            continue
        fm, _ = parse_frontmatter(read_text(path))
        if fm.get("type") != dtype:
            hard.append(f"{path.relative_to(paths.ROOT)}: expected type={dtype}, got {fm.get('type')}.")
        if fm.get("security") not in schema["security"]:
            hard.append(f"{path.relative_to(paths.ROOT)}: invalid security={fm.get('security')}.")
    for filename, required_sections in STAGING_TEMPLATES.items():
        path = paths.ROOT / ".harness-helm" / "runs" / "_templates" / filename
        if not path.exists():
            hard.append(f".harness-helm/runs/_templates/{filename}: missing staging template.")
            continue
        text = read_text(path)
        for section in sorted(required_sections):
            if f"## {section}" not in text:
                hard.append(f"{path.relative_to(paths.ROOT)}: missing ## {section}.")
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
        "claude": paths.ROOT / ".claude" / "skills" / "harness-helm" / "references",
        "codex": paths.ROOT / ".codex" / "skills" / "harness-helm" / "references",
    }
    runtime_names = {"claude": "Claude Code", "codex": "Codex"}

    def first_h1(text: str) -> str | None:
        for line in text.splitlines():
            if line.startswith("# "):
                return line.strip()
        return None

    hard.extend(validate_runtime_skill_translation_files(paths.ROOT))
    changed, changed_warnings = collect_changed_files(paths.ROOT)
    warnings.extend(changed_warnings)
    changed_hard, changed_pair_warnings = changed_runtime_translation_pairs(changed, paths.ROOT)
    hard.extend(changed_hard)
    warnings.extend(changed_pair_warnings)

    for runtime, reference_root in runtime_roots.items():
        required = dict(REFERENCE_MANIFEST["shared"])
        required.update(REFERENCE_MANIFEST[runtime])
        for legacy_path in sorted(reference_root.glob("upstream-*")):
            hard.append(f"{legacy_path.relative_to(paths.ROOT).as_posix()}: legacy upstream-* reference filename is not allowed.")
        for legacy_name in ("external-tool-registry.md", "external-tool-registry.ko.md"):
            legacy_path = reference_root / legacy_name
            if legacy_path.exists():
                hard.append(f"{legacy_path.relative_to(paths.ROOT).as_posix()}: legacy external-tool-registry filename is not allowed.")
        for base_path in sorted(reference_root.glob("*.md")):
            if base_path.name.endswith(".ko.md"):
                original_path = base_path.with_name(base_path.name.removesuffix(".ko.md") + ".md")
                if not original_path.exists():
                    hard.append(f"{base_path.relative_to(paths.ROOT).as_posix()}: Korean translation has no base reference.")
                continue
            base_text = read_text(base_path)
            if re.search(r"[가-힣]", base_text):
                hard.append(
                    f"{base_path.relative_to(paths.ROOT).as_posix()}: base reference must stay English-only; put Korean text in {base_path.stem}.ko.md."
                )
            ko_path = base_path.with_name(f"{base_path.stem}.ko.md")
            if not ko_path.exists():
                hard.append(f"{ko_path.relative_to(paths.ROOT).as_posix()}: missing Korean reference translation.")
            else:
                ko_text = read_text(ko_path)
                if not re.search(r"[가-힣]", ko_text):
                    hard.append(f"{ko_path.relative_to(paths.ROOT).as_posix()}: Korean reference translation has no Korean text.")
                base_h1 = first_h1(base_text)
                ko_h1 = first_h1(ko_text)
                if base_h1 and ko_h1 and base_h1 != ko_h1:
                    hard.append(
                        f"{ko_path.relative_to(paths.ROOT).as_posix()}: Korean reference H1 must match base reference H1 {base_h1!r}."
                    )
        for filename, markers in required.items():
            path = reference_root / filename
            rel = path.relative_to(paths.ROOT).as_posix()
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

    codex_skill = paths.ROOT / ".codex" / "skills" / "harness-helm" / "SKILL.md"
    if codex_skill.exists():
        text = read_text(codex_skill)
        if "references/claude-adapter.md" in text:
            hard.append(".codex/skills/harness-helm/SKILL.md: must not reference claude-adapter.md.")
        if "references/codex-adapter.md" not in text:
            hard.append(".codex/skills/harness-helm/SKILL.md: missing codex-adapter.md reference.")
        for filename in REFERENCE_MANIFEST["shared"]:
            if f"references/{filename}" not in text:
                warnings.append(f".codex/skills/harness-helm/SKILL.md: does not list references/{filename}.")

    claude_skill = paths.ROOT / ".claude" / "skills" / "harness-helm" / "SKILL.md"
    if claude_skill.exists():
        text = read_text(claude_skill)
        if "references/codex-adapter.md" in text:
            hard.append(".claude/skills/harness-helm/SKILL.md: must not reference codex-adapter.md.")
        if "references/claude-adapter.md" not in text:
            hard.append(".claude/skills/harness-helm/SKILL.md: missing claude-adapter.md reference.")
        for filename in REFERENCE_MANIFEST["shared"]:
            if f"references/{filename}" not in text:
                warnings.append(f".claude/skills/harness-helm/SKILL.md: does not list references/{filename}.")

    shared_parity_allowlist = {"workflow-lifecycle-commands.md"}
    for filename in REFERENCE_MANIFEST["shared"]:
        if filename in shared_parity_allowlist:
            continue
        claude_path = runtime_roots["claude"] / filename
        codex_path = runtime_roots["codex"] / filename
        if claude_path.exists() and codex_path.exists():
            if read_text(claude_path) != read_text(codex_path):
                hard.append(
                    f".claude vs .codex shared reference drift: {filename} (양 어댑터 byte-identical 필수, "
                    f"runtime-specific 차이는 allowlist에 추가)."
                )

    for runtime, reference_root in runtime_roots.items():
        required = dict(REFERENCE_MANIFEST["shared"])
        required.update(REFERENCE_MANIFEST[runtime])
        for filename, markers in required.items():
            ko_path = reference_root / f"{Path(filename).stem}.ko.md"
            if not ko_path.exists():
                continue
            ko_text = read_text(ko_path)
            for marker in markers:
                if marker not in ko_text:
                    warnings.append(
                        f"{ko_path.relative_to(paths.ROOT).as_posix()}: base marker {marker!r}이 한국어 번역에서 보존되지 않음 (식별자성 marker는 그대로 유지 권장)."
                    )
            if filename in GUIDELINE_DERIVED_REFERENCE_HEADERS:
                guideline = GUIDELINE_DERIVED_REFERENCE_HEADERS[filename]
                if guideline not in ko_text:
                    hard.append(
                        f"{ko_path.relative_to(paths.ROOT).as_posix()}: missing canonical guideline path {guideline!r}."
                    )
                if REFERENCE_MAPPING_AUTHORITY not in ko_text:
                    hard.append(
                        f"{ko_path.relative_to(paths.ROOT).as_posix()}: missing mapping authority path {REFERENCE_MAPPING_AUTHORITY!r}."
                    )

    print_report("reference-validate", hard, warnings)
    return 1 if hard and args.strict else 0


def command_target_smoke(args: argparse.Namespace) -> int:
    """target project minimal smoke: cookbooks/ 없이 핵심 surface만으로 검증 가능한지 확인."""
    hard: list[str] = []
    warnings: list[str] = []

    with tempfile.TemporaryDirectory(prefix="harness-target-smoke-") as tmpdir:
        target = Path(tmpdir) / "target-project"
        target.mkdir(parents=True, exist_ok=True)

        copy_items = [
            "AGENTS.md", "AGENTS.ko.md", "CLAUDE.md", "CLAUDE.ko.md",
            ".harness-helm", ".claude", ".codex", "docs", ".github",
        ]
        for item in copy_items:
            src = paths.ROOT / item
            if not src.exists():
                continue
            dst = target / item
            if src.is_dir():
                shutil.copytree(src, dst, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)

        cookbooks_check = target / "cookbooks"
        if cookbooks_check.exists():
            hard.append(f"target-smoke: cookbooks/가 target에 존재하면 안 됨 ({cookbooks_check}).")

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

            try:
                proc = subprocess.run(
                    [
                        "python3", str(script), "h2-context",
                        "--feature", "target-smoke", "--task", "target project install smoke", "--dry-run",
                    ],
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
    runs_root = paths.ROOT / ".harness-helm" / "runs"
    fixtures_root = paths.ROOT / ".harness-helm" / "reports" / "fixtures" / "normalized"

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
        rel = path.relative_to(paths.ROOT).as_posix()
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
