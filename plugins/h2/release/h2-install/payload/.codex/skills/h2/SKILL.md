---
name: h2
description: Short alias skill for harness-helm h2 workflow commands. Use for $h2 context, $h2 plan, $h2 design, $h2 autorun, $h2 rewind, $h2 analysis, $h2 build, $h2 test, $h2 review, $h2 report, $h2 compound, $h2 archive, $h2 ops, and $h2 cartridge by delegating to the canonical harness-helm skill semantics.
---

# h2

Short user-facing alias for the canonical Codex skill:

```text
.codex/skills/harness-helm/SKILL.md
```

Detailed reference snapshots are not loaded from this alias directly. Use the canonical `harness-helm` skill and its `references/` directory when issue-level context is needed.

This skill does not define independent workflow rules. It routes concise `$h2 ...` invocations to the matching `harness-helm` command semantics.

Runtime guidance for Codex starts at root `AGENTS.md`, then delegates h2-specific semantics to `.codex/skills/harness-helm/SKILL.md` and its bundled `references/`.

## Alias Mapping

| User invocation | Canonical semantics |
|---|---|
| `$h2 context ...` | `harness-helm` `h2-context` |
| `$h2 plan ...` | `harness-helm` `h2-plan` |
| `$h2 design ...` | `harness-helm` `h2-design` |
| `$h2 autorun ...` | `harness-helm` `h2-autorun` |
| `$h2 rewind ...` | `harness-helm` `h2-rewind` |
| `$h2 analysis ...` | `harness-helm` `h2-analysis` |
| `$h2 build ...` | `harness-helm` `h2-build` |
| `$h2 test ...` | `harness-helm` `h2-test` |
| `$h2 review ...` | `harness-helm` `h2-review` |
| `$h2 report ...` | `harness-helm` `h2-report` |
| `$h2 compound ...` | `harness-helm` `h2-compound` |
| `$h2 archive ...` | `harness-helm` `h2-archive` |
| `$h2 ops ...` | `harness-helm` `h2-ops` |
| `$h2 cartridge ...` | `harness-helm` `h2-cartridge` |

## Rules

- Treat `$h2 context`, `$h2 plan`, `$h2 design`, `$h2 autorun`, `$h2 rewind`, `$h2 analysis`, `$h2 build`, `$h2 test`, `$h2 review`, `$h2 report`, `$h2 compound`, `$h2 archive`, `$h2 ops`, and `$h2 cartridge` as the matching canonical `h2-*` command ids.
- Preserve the common `context_pack`, `artifacts`, `routing`, `verification`, and `next` output meanings from `harness-helm`.
- Do not duplicate or override `harness-helm` workflow semantics.
- Use `.harness-helm/h2-cartridge.yml` through the canonical skill for provider, surface, fallback label, and routing target values.
- If this alias conflicts with `.codex/skills/harness-helm/SKILL.md`, the canonical `harness-helm` skill wins.
- Follow `AGENTS.md` first; if absent, follow project guidance.
