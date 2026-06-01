from __future__ import annotations


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
