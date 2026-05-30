# 0602 Upstream Tool Registry Reference

Compact runtime snapshot of `0602 Upstream Tool Registry`.

## Rule

The upstream tool registry is managed through `.harness-helm/h2-cartridge.yml` under `external_tool_registry.tools`.

The registry lists upstream tools that h2 commands may invoke or reference. Initial tools are `gstack`, `superpowers`, and `compound-engineering`.

## Registry Fields

Each tool entry should define:

- `id`: stable registry id
- `display_name`: human-readable name
- `category`: workflow engine, skill system, engineering plugin, or similar
- `surfaces`: commands, skills, or plugin surfaces available to h2
- `availability`: required installation or activation condition
- `preferred_for`: h2 commands or workflow stages where the tool is preferred
- `fallback`: fallback behavior when unavailable
- `alternatives`: other tools with a similar purpose
- `source_of_truth`: where the mapping is maintained
- `validation`: smoke or dry-run checks
- `notes`: runtime-specific cautions

## Decisions

- Provider, surface, fallback, and routing values remain under `.harness-helm/h2-cartridge.yml`.
- `references/upstream-tool-invocation.md` records the compact runtime mapping.
- Claude Code and Codex may invoke tools differently, but the h2 output contract must stay equivalent.
- If an upstream tool is unavailable, preserve the command fallback label and record the reason in `verification.not_verified`.

## Avoid

- Do not install or introduce new upstream tools from this reference alone.
- Do not redefine h2 lifecycle command order or meaning.
- Do not reimplement gstack, superpowers, or compound-engineering.
