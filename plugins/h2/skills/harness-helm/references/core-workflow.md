# Core Workflow Spec Reference

Compact runtime snapshot of `0301 Core Workflow Spec`.

## Purpose

`harness-helm` standardizes agent work into h2 lifecycle commands, a common output contract, staging artifacts, and docs routing. It wraps Claude Code, Codex, gstack, superpowers, and compound-engineering without replacing them.

## Command Lifecycle

- `h2-context`: select primary, supporting, and excluded docs; create or update a run context pack.
- `h2-plan`: create or update `docs/01_plan/{feature}.md` with goal, scope, non-goals, done criteria, risk, and verification.
- `h2-design`: create or update `docs/02_design/{feature}.md` with implementation design based on the plan.
- `h2-analysis`: compare plan and design, record gaps, and recommend alignment work in `docs/02_design/{feature}.analysis.md`.
- `h2-autorun`: after design, orchestrate `h2-analysis` through `h2-archive` and summarize step status in `.harness-helm/runs/{feature}/{run-id}/autorun-summary.md`.
- `h2-rewind`: restore a specific `h2-autorun` pre-step snapshot and record evidence in `.harness-helm/runs/{feature}/{run-id}/snapshots/{step}/restore.md`.
- `h2-build`: record implementation work, changed files, risks, and blocked items.
- `h2-test`: record test commands, results, skipped checks, failures, and remaining verification.
- `h2-review`: record code, QA, security, or cross-review findings in `docs/03_review/{type}/{feature}.md`.
- `h2-report`: summarize plan, design, analysis, build, test, and review into `docs/04_report/{feature}.md`.
- `h2-compound`: compound reusable knowledge. It may write low-risk `40_knowledge` learning/solution docs after checks, and stages governed canonical candidates until approval.
- `h2-archive`: execute archive movement for completed 01-04 workflow artifacts and move the completed feature run-root through archive tooling. Use dry-run only when the user explicitly asks for preview-only behavior.
- `h2-ops`: record operational follow-ups such as runbooks, releases, incidents, or branch cleanup.
- `h2-cartridge`: inspect or update provider, surface, fallback, and routing mappings.

## Common Output

Every h2 command should preserve:

```yaml
command: h2-command
feature: feature-slug-or-null
status: draft | updated | skipped | blocked
context_pack:
  primary_docs: []
  supporting_docs: []
  canonical_knowledge: []
  excluded_by_policy: []
  assumptions: []
artifacts:
  created: []
  updated: []
  suggested: []
routing:
  target_docs: []
  archive_candidate: false
  promotion_candidates: []
verification:
  required: []
  completed: []
  not_verified: []
next:
  recommended_h2_step: null
```

## Routing Rules

- PDCA workflow docs live under `docs/01_plan`, `docs/02_design`, `docs/03_review`, and `docs/04_report`.
- Canonical knowledge lives under `docs/10_domain`, `docs/20_specs`, `docs/30_decisions`, `docs/40_knowledge`, and `docs/50_operations`.
- Run-local staging lives under `.harness-helm/runs/{feature}/{run-id}/`.
- `_archive` is historical and excluded from default retrieval.

## Guardrails

- Do not change command semantics because a different upstream tool was used.
- Do not store raw upstream output as canonical h2 output.
- Do not write governed canonical docs without approval. Low-risk `40_knowledge/solutions` and `40_knowledge/learnings` writes are allowed after overlap, schema, and lint checks.
- Do not generate `_indexes` from `h2-context`; use `kb-index`.
