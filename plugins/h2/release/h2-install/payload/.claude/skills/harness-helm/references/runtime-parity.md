# Runtime Parity Report

Compact runtime snapshot for Claude Code and Codex parity.

## Rule

Claude Code and Codex expose different command surfaces, but both must preserve the same h2 command meanings, output fields, routing, staging rules, and verification semantics.

## Runtime Surfaces

| Runtime | Entrypoint | Fixture |
|---|---|---|
| Claude Code | `/h2:{command}` slash commands | `.claude/skills/harness-helm/references/claude-entrypoint.md` |
| Codex | `$h2 {command}` skill alias | `.codex/skills/harness-helm/references/codex-entrypoint.md` |

## Parity Requirements

- Common input meaning: `command`, `feature`, `task`, optional `source_request`, `references`, and `constraints`.
- Common output meaning: `context_pack`, `artifacts`, `routing`, `verification`, and `next`.
- Routing must match `.harness-helm/h2-cartridge.yml` when installed.
- If `.harness-helm/h2-cartridge.yml` is absent, use `references/upstream-tool-invocation.md` as the compact runtime mapping.
- Fallback-only checks must not be recorded as actual upstream invocations.

## Upstream Invocation Parity

Both runtimes use the same provider/surface intent for h2 commands. Runtime-specific wording is allowed; semantic drift is not.

Use `actual:<provider>:<surface>` only when the upstream was actually invoked. Use `verified-fallback:<label>` when only a fallback checklist was applied.
