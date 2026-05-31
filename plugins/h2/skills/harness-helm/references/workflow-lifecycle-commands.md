# Workflow Lifecycle Commands Reference

Source cookbook: `cookbooks/0300-workflow-contract/0303-workflow-lifecycle-commands.md`.

This is a compact runtime snapshot for Claude Code and Codex h2 command meanings.

This file defines command meaning and routing. It does not choose upstream providers, implement agent tools, run tests, or promote canonical docs. Provider/surface/fallback mapping belongs to `.harness-helm/h2-cartridge.yml` and `references/cartridge-command-mapping.md`.

## Commands

- `h2-context`: create or update run context.
- `h2-plan`: plan work and route to `docs/01_plan/{feature}.md`.
- `h2-design`: create implementation design and route to `docs/02_design/{feature}.md`.
- `h2-analysis`: inspect plan/design gaps and route alignment notes to `docs/02_design/{feature}.analysis.md`.
- `h2-autorun`: after design, run `h2-analysis`, `h2-build`, `h2-test`, `h2-review`, `h2-report`, `h2-compound`, and `h2-archive` in order, stopping on `status: blocked`.
- `h2-rewind`: restore a specific `h2-autorun` pre-step snapshot; if the snapshot is missing, block with `blocked:no-snapshot`.
- `h2-build`: record implementation work and changed files.
- `h2-test`: record test execution, skipped checks, and remaining verification.
- `h2-review`: record review findings and route to `docs/03_review/{type}/{feature}.md`.
- `h2-report`: summarize lifecycle results and route to `docs/04_report/{feature}.md`.
- `h2-compound`: compound reusable knowledge and stage governed canonical promotion candidates.
- `h2-archive`: check for h2-compound run evidence as preflight (auto-trigger if absent); then plan archive movement for completed 01-04 workflow artifacts; actual movement and completed feature run-root cleanup are delegated to archive tooling.
- `h2-ops`: record operational follow-up candidates.
- `h2-cartridge`: inspect or update cartridge mappings.

## Runtime Note

Claude Code may expose `/h2:{command}` slash commands. Codex may expose `$h2 {command}` skill aliases. Both must preserve the same h2 semantics.
