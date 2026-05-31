# Claude Code Adapter Reference

Compact runtime snapshot of `0401 Claude Code Adapter`.

## Rule

The Claude Code adapter exposes the `h2-*` command surface through `/h2:{command}` slash commands and `.claude/skills/harness-helm/SKILL.md`.

It must preserve the same h2 command semantics, output contract, routing, staging, and verification rules as the core workflow.

## `h2-*` command surface

Claude Code should support:

`h2-context`, `h2-plan`, `h2-design`, `h2-autorun`, `h2-rewind`, `h2-analysis`, `h2-build`, `h2-test`, `h2-review`, `h2-report`, `h2-compound`, `h2-archive`, `h2-ops`, and `h2-cartridge`.

## Responsibilities

- Slash command files are thin aliases.
- `.claude/skills/harness-helm/SKILL.md` owns runtime command guidance.
- `references/` stores compact runtime snapshots.
- `.harness-helm/h2-cartridge.yml` owns provider, surface, fallback, routing, and registry values when installed.

## Boundaries

- Do not redefine core h2 semantics inside slash aliases.
- Do not reimplement gstack, superpowers, or compound-engineering.
- Do not create canonical 10/20/30/40/50 docs without approval.
- Do not treat fallback checklist execution as actual upstream invocation.
