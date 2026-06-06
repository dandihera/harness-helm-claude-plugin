# Workflow Lifecycle Commands Reference

Source cookbook: `cookbooks/0300-workflow-contract/0303-workflow-lifecycle-commands.md`.

This is a compact runtime snapshot for Claude Code and Codex h2 command meanings.

This file defines command meaning and routing. It does not choose upstream providers, implement agent tools, run tests, or promote canonical docs. Provider/surface/fallback mapping belongs to `.harness-helm/h2-cartridge.yml` and `references/cartridge-command-mapping.md`.

## Commands

- `h2-context`: create or update run context.
- `h2-plan`: plan work and route to `docs/01_plan/{feature}.md`.
- `h2-design`: create implementation design and route to `docs/02_design/{feature}.md`.
- `h2-analysis`: inspect plan/design gaps and route alignment notes to `docs/02_design/{feature}.analysis.md`.
- `h2-autorun`: after design, run `h2-analysis`, then iterate the `h2-build -> h2-test -> h2-review` state machine when test or review returns `next.recommended_h2_step: h2-build`. Run `h2-report`, `h2-compound`, and `h2-archive` only after the latest test and review allow forward progress; stop on `status: blocked`, repeated unresolved reason, missing review, or max iteration overflow.
- `h2-rewind`: restore a specific `h2-autorun` pre-step snapshot; if the snapshot is missing, block with `blocked:no-snapshot`.
- `h2-build`: record implementation work and changed files.
- `h2-test`: record test execution, skipped checks, and remaining verification.
- `h2-review`: record review findings and route to `docs/03_review/{type}/{feature}.md`.
- `h2-report`: summarize lifecycle results and route to `docs/04_report/{feature}.md`.
- `h2-compound`: compound reusable knowledge and stage governed canonical promotion candidates.
- `h2-harvest`: curate `docs/_harvest-inbox/**` notes into canonical docs and route the report to `.harness-helm/runs/_unscoped/{run-id}/harvest-report.md`.
- `h2-harvest-tag`: classify `docs/_harvest-inbox/raw/**` files into prefixed raw suggestions or typed inbox folders and route the report to `.harness-helm/runs/_unscoped/{run-id}/harvest-tag-report.md`.
- `h2-archive`: check for h2-compound run evidence as preflight (auto-trigger if absent); then execute archive movement for completed 01-04 workflow artifacts and the completed feature run-root through archive tooling. Use dry-run only when the user explicitly asks for preview-only behavior.
- `h2-ops`: record operational follow-up candidates.
- `h2-cartridge`: inspect or update cartridge mappings.

## Runtime Note

Claude Code may expose `/h2:{command}` slash commands. Codex may expose `$h2 {command}` skill aliases. Both must preserve the same h2 semantics.
