# Skill Suite Reference

Compact runtime snapshot of `0302 Skill Suite`.

## Rule

`harness-helm` is the canonical skill that owns h2 workflow semantics. `h2` is a short alias surface that delegates to the canonical skill.

## Responsibilities

- `harness-helm`: common h2 command semantics, output contract, routing, staging, and boundaries.
- `h2`: short user-facing alias for `$h2 ...` or slash command entrypoints.
- Runtime references: compact snapshots for command semantics, adapters, upstream mapping, parity, and operational guidelines.
- `.harness-helm/h2-cartridge.yml`: provider, surface, fallback label, routing target, output language, and registry source of truth when installed.

## Required h2 Commands

`h2-context`, `h2-plan`, `h2-design`, `h2-autorun`, `h2-rewind`, `h2-analysis`, `h2-build`, `h2-test`, `h2-review`, `h2-report`, `h2-compound`, `h2-archive`, `h2-ops`, and `h2-cartridge`.

## Boundaries

- Alias skills must not redefine workflow semantics.
- Agent-specific wording is allowed, but output meaning and routing must stay equivalent.
- Runtime references should stay compact and should not replace canonical docs.
- Installed target projects do not require `cookbooks/`.

## Minimal Runtime Shape

```text
.codex/skills/harness-helm/SKILL.md
.codex/skills/h2/SKILL.md
.codex/skills/harness-helm/references/

.claude/skills/harness-helm/SKILL.md
.claude/commands/h2/*.md
.claude/skills/harness-helm/references/
```
