# Cartridge Output Normalization Reference

Source cookbook: `0604 Cartridge Output Normalization`.

Compatibility marker: Source cookbook: `0604 Upstream Output Normalization`.

This reference is the runtime summary for converting upstream raw output into h2 output.

Upstream raw output is not a canonical h2 artifact. Before writing official docs, normalize Claude Code, Codex, gstack, superpowers, and compound-engineering results into the h2 output contract.

## Flow

```text
upstream raw output
  -> h2 cartridge normalization
  -> h2 common output shape
  -> official docs or run artifacts
```

Creating `raw/`, `normalized/`, and `promotion-candidates/` folders is the responsibility of the runtime cartridge for each h2 command. `harness.py` validates produced staging artifacts and cleanup rules; it does not create those folders directly.

## Required Mapping

- Preserve the h2 `command`, not the upstream command name.
- Map existing created or updated files to `artifacts.created` and `artifacts.updated`.
- Map suggested docs, release notes, runbooks, or knowledge items to `artifacts.suggested` or `routing.promotion_candidates`.
- Map actual upstream invocations to `verification.completed` as `actual:<provider>:<surface>`.
- Map fallback execution to the fallback label from `.harness-helm/h2-cartridge.yml`.
- Map uncertain claims and skipped checks to `verification.not_verified`.
- Map blocked prerequisites to `verification.required`.
- Choose `next.recommended_h2_step` from the h2 lifecycle, not from the upstream tool.

## Command Notes

- `h2-plan`: normalize goals, scope, non-goals, done criteria, and risks to `docs/01_plan/{feature}.md`.
- `h2-design`: normalize implementation flow, module/interface boundary, data flow, and verification strategy to `docs/02_design/{feature}.md`.
- `h2-autorun`: normalize child step statuses, artifacts, warnings, and blocked reasons to `.harness-helm/runs/{feature}/{run-id}/autorun-summary.md`.
- `h2-rewind`: normalize restore actions, backup paths, archive residue warnings, and blocked no-snapshot reasons to `.harness-helm/runs/{feature}/{run-id}/snapshots/{step}/restore.md`.
- `h2-analysis`: normalize plan/design mismatch and gaps into analysis notes or sync sections.
- `h2-build`, `h2-test`, `h2-review`: normalize actor results to run artifacts or review docs. Do not replace actual execution evidence with upstream suggestions.
- `h2-report`: normalize lifecycle summary and follow-up needs to `docs/04_report/{feature}.md`.
- `h2-compound`: map low-risk learning/solution writes to `artifacts.created` or `artifacts.updated`; keep governed canonical targets in `routing.promotion_candidates` until approval.
- `h2-archive`, `h2-ops`, `h2-cartridge`: normalize archive execution or explicit dry-run preview, ops, and mapping validation output to configured routes.

Raw output must mask sensitive information and follow the core workflow staging cleanup policy.
