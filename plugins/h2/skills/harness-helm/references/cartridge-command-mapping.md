# Cartridge Command Mapping Reference

Compatibility marker: 0601 Upstream Tool Invocation.

Compact runtime snapshot of h2 invocation recording, fallback handling, and routing invariants. Cartridge values are defined only in `.harness-helm/h2-cartridge.yml` and are not duplicated here.

## Rule

`.harness-helm/h2-cartridge.yml` is the source of truth for installed provider, surface, fallback label, routing target, output language, alternatives, and external tool registry values.

If the cartridge file is absent in a target project, use this reference for invocation recording, fallback handling, and routing invariants only. Record that the cartridge file was not available.

Read `.harness-helm/h2-cartridge.yml` directly to inspect installed provider, surface, fallback label, routing target, output language, alternatives, and external tool registry values.

## Invocation Recording

- Actual upstream invocation: `actual:<provider>:<surface>`.
- Fallback checklist or recorder mode: `verified-fallback:<fallback_label>`.
- Missing tool, skipped check, or unverified claim: `verification.not_verified`.
- Blocked prerequisite: `verification.required`.

## Command Routing

Upstream tools may influence input quality, but h2 routing stays fixed by command semantics.

- `h2-plan` routes to `docs/01_plan/{feature}.md`.
- `h2-design` routes to `docs/02_design/{feature}.md`.
- `h2-autorun` routes to `.harness-helm/runs/{feature}/{run-id}/autorun-summary.md`.
- `h2-rewind` routes to `.harness-helm/runs/{feature}/{run-id}/snapshots/{step}/restore.md`.
- `h2-review` routes to `docs/03_review/{type}/{feature}.md`.
- `h2-report` routes to `docs/04_report/{feature}.md`.
- `h2-compound` writes low-risk knowledge after checks and stages governed promotion candidates before canonical writes.
- `h2-archive` uses the harness archive flow.

## Drift Control

When 0601, 0603, 0604, or 0605 guidance changes, update the adapter, upstream references, runtime parity snapshot, and matching docs guideline as needed.

## Avoid

- Do not call fallback checklist output an actual upstream invocation.
- Do not change routing because a different provider was used.
- Do not duplicate cartridge values in bundled references.
