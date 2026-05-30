# 0402 Codex Adapter Reference

Compact runtime snapshot for the Codex adapter.

## Rule

The Codex adapter exposes the `h2-*` command surface through the `$h2 ...` alias and `.codex/skills/harness-helm/SKILL.md`.

It must preserve the same h2 command semantics, output contract, routing, staging, and verification rules as the core workflow and the Claude Code adapter.

## `h2-*` command surface

Codex should support:

`h2-context`, `h2-plan`, `h2-design`, `h2-analysis`, `h2-build`, `h2-test`, `h2-review`, `h2-report`, `h2-compound`, `h2-archive`, `h2-ops`, and `h2-cartridge`.

## Responsibilities

- `.codex/skills/h2/SKILL.md` is a thin alias.
- `.codex/skills/harness-helm/SKILL.md` owns runtime command guidance.
- `references/` stores compact runtime snapshots.
- `.harness-helm/h2-cartridge.yml` owns provider, surface, fallback, routing, and registry values when installed.

## Boundaries

- Do not redefine core h2 semantics inside the alias.
- Do not reimplement Claude Code, gstack, superpowers, or compound-engineering.
- Do not create canonical 10/20/30/40/50 docs without approval.
- Do not treat fallback checklist execution as actual upstream invocation.
