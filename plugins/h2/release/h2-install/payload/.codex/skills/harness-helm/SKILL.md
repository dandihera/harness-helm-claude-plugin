---
name: harness-helm
description: Codex adapter for harness-helm h2 workflows. Use for $h2 context, $h2 plan, $h2 design, $h2 autorun, $h2 rewind, $h2 analysis, $h2 build, $h2 test, $h2 review, $h2 report, $h2 compound, $h2 harvest, $h2 archive, $h2 ops, and $h2 cartridge while preserving the 0301-core-workflow-spec command semantics, output fields, staging rules, and docs routing.
---

# harness-helm

`harness-helm` is the canonical Codex skill for the HERA AI-native docs lifecycle. It does not replace gstack, superpowers, compound-engineering, Claude Code, or Codex. It wraps available work into the shared `h2-*` workflow, output contract, staging rules, and routing defined by the core references.

Bundled runtime references:

- `references/skill-suite.md`: `0302 Skill Suite` boundary and `h2` prefix.
- `references/core-workflow.md`: `0301 Core Workflow Spec` `h2-*` core workflow.
- `references/codex-adapter.md`: `0402 Codex Adapter` scope and `h2-*` entrypoints.
- `references/codex-entrypoint.md`: Codex smoke/parity example for runtime parity checks.
- `references/runtime-parity.md`: `0403 Runtime Parity Test` parity result between Claude Code and Codex.
- `references/workflow-lifecycle-commands.md`: `0303 Workflow Lifecycle Commands` `h2-*` command semantics.
- `references/context-pack-contract.md`: `0305 Context Pack Contract` retrieval snapshot rules.
- `references/runtime-folder-structure.md`: `0503 h2 Runtime Folder Structure` installed runtime and run staging layout.
- `references/compound-policy-config.md`: `0306 Compound Policy Config` h2-compound write and review-gate policy.
- `references/h2-rewind-recovery.md`: h2-autorun snapshot and h2-rewind restore boundary rules.
- `references/cartridge-command-mapping.md`: `0601 Cartridge Command Mapping` invocation recording, fallback handling, and routing invariants.
- `references/cartridge-tool-registry.md`: `0602 External Tool Registry` integration targets, alternatives, availability, and registration rules.
- `references/cartridge-surface-map.md`: `0603 Cartridge Surface Map` upstream surface recommendations and drift notes.
- `references/cartridge-output-normalization.md`: `0604 Cartridge Output Normalization` raw upstream output to h2 template mapping rules.
- `references/canonical-promotion-flow.md`: runtime snapshot for `h2-compound` promotion approval and canonical write rules.
- `references/specs-vs-decisions.md`: runtime snapshot for choosing between `20_specs` and `30_decisions`.
- `references/provider-surface-selection-and-override.md`: runtime snapshot for run-level upstream override and permanent mapping change.

Canonical runtime conventions are stored under `docs/40_knowledge/conventions/guidelines/*.md` when docs are installed. Bundled `references/canonical-promotion-flow.md`, `references/specs-vs-decisions.md`, and `references/provider-surface-selection-and-override.md` provide compact runtime snapshots when those docs are absent or too expensive to load. The meta guideline for choosing snapshot scope remains in `docs/40_knowledge/conventions/guidelines/harness-helm/runtime-reference-selection.md` and is not bundled as a runtime snapshot.

Base `references/*.md` files are English snapshots for Claude/Codex parity and compact loading. Matching `references/*.ko.md` files are stakeholder Korean translations and must not be loaded into the default agent context; read them only when the user explicitly requests Korean review.

Installed target projects do not include `cookbooks/`. Use this `SKILL.md`, `.codex/skills/h2/SKILL.md`, bundled `references/*.md`, root `AGENTS.md`, `docs/`, and `.harness-helm/` as the runtime surface.

Load bundled references only when this compact rule file is insufficient or when checking detailed acceptance criteria.

## Docs Artifact Language

Markdown files under the numbered user-facing docs folders must be written in Korean by default. This applies to `docs/01_plan/**`, `docs/02_design/**`, `docs/03_review/**`, `docs/04_report/**`, `docs/10_domain/**`, `docs/20_specs/**`, `docs/30_decisions/**`, `docs/40_knowledge/**`, and `docs/50_operations/**`.

Generated machine-facing index documents under `docs/_indexes/**` are the exception. Write those index markdown files in English because h2 primarily consumes them as retrieval and routing aids.

Keep technical identifiers, command names, file paths, frontmatter keys, proper nouns, and source quotations in their original form. Use another language only when the user explicitly requests it or when preserving an exact quoted source.

## Runtime Read Order

1. Follow root `AGENTS.md` and project-specific instructions first.
2. Use this `SKILL.md` for canonical `h2-*` command semantics, output fields, staging rules, and docs routing.
3. Treat `.codex/skills/h2/SKILL.md` as a thin `$h2` alias only.
4. Load bundled `references/*.md` only when detailed criteria, parity evidence, upstream mapping, normalization, or promotion rules are needed.
5. Use `.harness-helm/h2-cartridge.yml` for editable provider, surface, fallback, routing, and output language values when installed; otherwise use `references/cartridge-command-mapping.md` only for invocation recording, fallback handling, and routing invariants.
6. Use `.harness-helm/h2-compound.yml` for h2-compound domain refinement, canonical destination, review gate, and retrieval hook policy when installed; if absent, use built-in conservative defaults.
7. Use `.harness-helm/h2-harvest.yml` for h2-harvest inbox curation policy when installed; if absent, use built-in conservative defaults.

## Runtime Source Hierarchy

- Source repository design records live in `cookbooks/`, but installed target projects do not include `cookbooks/`.
- Installed runtime command semantics come from this `SKILL.md`, `references/core-workflow.md`, and `references/workflow-lifecycle-commands.md`.
- Runtime provider, surface, fallback, routing, and output language mapping comes from `.harness-helm/h2-cartridge.yml` when installed. Bundled upstream references are fallback guidance for invocation recording, fallback handling, and routing invariants, not cartridge value copies.
- Runtime h2-compound knowledge policy comes from `.harness-helm/h2-compound.yml` when installed, with built-in conservative defaults as fallback.
- Runtime h2-harvest inbox curation policy comes from `.harness-helm/h2-harvest.yml` when installed, with built-in conservative defaults as fallback.
- Runtime schema validation comes from `.harness-helm/h2-schema.yml`.
- Root `AGENTS.md` provides project-wide entrypoint guidance and must not duplicate the full workflow contract.

## Runtime Parity Boundary

- Claude and Codex may differ in invocation syntax and file layout.
- They must preserve the same `h2-*` command ids, common output fields, docs routing, staging rules, and cartridge mapping semantics.
- Runtime-specific guide files under skill folders are not part of the target surface; use root guidance, this `SKILL.md`, aliases, bundled references, `docs/`, and `.harness-helm/`.

## Codex Invocation

Codex does not use Claude Code-style `.claude/commands/h2/*.md` slash command aliases for this adapter.

Canonical skill:

```text
.codex/skills/harness-helm/SKILL.md
```

User-facing alias:

```text
.codex/skills/h2/SKILL.md
```

The `$h2` alias must delegate to this canonical `harness-helm` skill. It must not duplicate or override workflow semantics.

## Command Surface

Codex must provide these `h2-*` user invocations:

- `$h2 context`
- `$h2 plan`
- `$h2 design`
- `$h2 autorun`
- `$h2 rewind`
- `$h2 analysis`
- `$h2 build`
- `$h2 test`
- `$h2 review`
- `$h2 report`
- `$h2 compound`
- `$h2 harvest`
- `$h2 archive`
- `$h2 ops`
- `$h2 cartridge`

Internal canonical command ids:

- `h2-context`
- `h2-plan`
- `h2-design`
- `h2-autorun`
- `h2-rewind`
- `h2-analysis`
- `h2-build`
- `h2-test`
- `h2-review`
- `h2-report`
- `h2-compound`
- `h2-harvest`
- `h2-archive`
- `h2-ops`
- `h2-cartridge`

Use `.harness-helm/h2-cartridge.yml` as the shared source of truth for provider, surface, fallback label, routing target, output language values, and upstream tool registry entries when it is installed. If it is absent in a target project, use bundled `references/cartridge-command-mapping.md` only for invocation recording, fallback handling, and routing invariants. Load `references/cartridge-tool-registry.md` for tool alternatives and registration rules, and `references/workflow-lifecycle-commands.md` when detailed workflow lifecycle command semantics are needed.

## Common Input

Preserve these meanings even if Codex invocation is natural language:

```yaml
command: h2-context | h2-plan | h2-design | h2-autorun | h2-rewind | h2-analysis | h2-build | h2-test | h2-review | h2-report | h2-compound | h2-harvest | h2-archive | h2-ops | h2-cartridge
feature: "<feature-slug or null>"
task: "<user request or work summary>"
source_request: "<original request, optional>"
mode: "create | update | inspect"
references:
  docs: []
  prs: []
constraints:
  security: "public | internal | restricted | regulated"
```

Minimum input is `command`, `feature`, and `task`. `h2-context` may use `feature: null`; in that case use `.harness-helm/runs/_unscoped/{run-id}/`.

Issue-derived feature names use `<kebab-case-feature>_<issue-number>` by default, for example `snapshot-archive-scope_124`. If the workflow did not start from a GitHub/GitLab issue, use the plain kebab-case feature slug without a suffix, for example `h2-run-stats`. Multi-provider projects may use `_gh_` or `_gl_` only when issue-number collision must be avoided.

## Common Output

Responses and artifacts must preserve these fields:

```yaml
command: "<h2-command>"
feature: "<feature-slug or null>"
status: "draft | updated | skipped | blocked"
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
  recommended_h2_step: "<h2-command or null>"
```

Recommended Markdown shape:

- frontmatter: `command`, `feature`, `status`, `next.recommended_h2_step`
- sections: `## Context Pack`, `## Artifacts`, `## Routing`, `## Verification`

## Command Semantics

### h2-context

- Select primary/supporting/excluded docs using `0103 Retrieval and Index Policy` and core workflow rules in bundled `references/`.
- Include applicable canonical docs in `context_pack.canonical_knowledge` so compounded knowledge reinjection is visible.
- Parse `docs/_indexes/index_kb.jsonl`, `index_domain.jsonl`, and `index_tag.jsonl` when present; if indexes are absent or stale, inspect canonical source docs directly.
- Record index absent/stale freshness warnings in `verification.not_verified`; do not generate indexes.
- Do not generate `_indexes`.
- Generate or update the context pack at `.harness-helm/runs/{feature}/{run-id}/context-pack.md` or `.harness-helm/runs/_unscoped/{run-id}/context-pack.md`; downstream `h2-*` commands should start from the same snapshot.
- Set `next.recommended_h2_step` to `null` or the first command implied by the user request.

### h2-plan

- Run `h2-context` meaning as preflight.
- Summarize goal, scope, non-goals, done criteria, and key risks.
- Route to `docs/01_plan/{feature}.md`.
- Set `next.recommended_h2_step` to `h2-design`.

### h2-design

- Run `h2-context` meaning as preflight.
- Use the plan to define implementation flow, interfaces, data flow, and verification strategy.
- Route to `docs/02_design/{feature}.md`.
- If the plan is missing, use `status: blocked` and explain the missing plan in `verification.required`.
- Set `next.recommended_h2_step` to `h2-analysis`.

### h2-autorun

- Run `h2-context` meaning as preflight and create a fresh context pack for this autorun; older context packs may be referenced as supporting docs.
- Require `docs/02_design/{feature}.md` before starting. If the design is missing or explicitly blocked, use `status: blocked`.
- Execute `h2-analysis`, `h2-build`, `h2-test`, `h2-review`, `h2-report`, `h2-compound`, and `h2-archive` in that order.
- Before each child step, save the pre-step snapshot using the `h2-snapshot save` meaning so `h2-rewind` can restore that step boundary.
- Use `code` as the default `h2-review` type. User input may override it with `review=code|qa|security|cross`; select `security`, `qa`, or `cross` only when design/test evidence or Cross Review policy criteria support that route.
- Stop immediately when a child step returns `status: blocked`.
- Treat `verification.not_verified` as a warning and summarize it, except that missing human review evidence must be highlighted in the summary.
- Evaluate the `h2-report` recommendation of `h2-archive` as a special case before generic next-step mismatch; still run `h2-compound` explicitly before `h2-archive`.
- When `h2-autorun` reaches `h2-archive`, execute the real archive by default. Do not downgrade archive to `--dry-run` unless the user explicitly requested dry-run, preview-only, or no archive.
- Route to `.harness-helm/runs/{feature}/{run-id}/autorun-summary.md`.
- Set `next.recommended_h2_step` to `null`.

### h2-rewind

- Restore a specific `h2-autorun` pre-step snapshot for `h2-analysis`, `h2-build`, `h2-test`, `h2-review`, `h2-report`, `h2-compound`, or `h2-archive`.
- Require `feature`, `run-id`, and `step`; do not guess a run id.
- If the snapshot manifest is missing, use `status: blocked` with `blocked:no-snapshot`.
- Preserve archive residue under `docs/_archive/**` and warn rather than deleting it automatically.
- Route restore evidence to `.harness-helm/runs/{feature}/{run-id}/snapshots/{step}/restore.md`.
- Set `next.recommended_h2_step` to the restored step.

### h2-analysis

- Compare plan goal/scope/done criteria with design implementation and verification strategy.
- Route the analysis artifact to `docs/02_design/{feature}.analysis.md`.
- Record plan/design mismatches, gaps, and exact recommended alignment changes there.
- Put human-judgment gaps in `verification.not_verified`.
- Set `next.recommended_h2_step` to `h2-build`.

### h2-build

- Record design execution artifacts, changed files, implementation risk, and blocked/skipped reasons in harness-helm output shape. Artifacts may be code, documentation, workflow records, or runtime configuration.
- Do not replace Claude Code, Codex, superpowers, or gstack as code-editing actors.
- Current mode is recorder unless an actual upstream actor invocation is verified.
- Route to `.harness-helm/runs/{feature}/{run-id}/build.md`.
- Set `next.recommended_h2_step` to `h2-test`.

### h2-test

- Record test commands, results, skip reasons, failures, and remaining verification.
- Put executed checks in `verification.completed`.
- Put skipped/failed/unverified checks in `verification.not_verified`.
- Route to `.harness-helm/runs/{feature}/{run-id}/test.md`.
- Set `next.recommended_h2_step` to `h2-review`.

### h2-review

- Support `code`, `qa`, `security`, and `cross` review types.
- Route review candidates to `docs/03_review/{type}/{feature}.md`.
- Run Cross Review only when the Cross Review policy criteria are met.
- Write all generated review content in Korean. Technical identifiers, command names, file paths, and source quotations remain in their original form.
- Set `next.recommended_h2_step` to `h2-report`.

### h2-report

- Run `h2-context` meaning as preflight.
- Summarize plan/design/analysis/build/test/review results.
- Route to `docs/04_report/{feature}.md`.
- If build/test/review evidence was produced manually or by upstream tools, record it; otherwise list the missing evidence in `verification.not_verified`.
- Put 10/20/30/40/50 candidates only in `routing.promotion_candidates` or `artifacts.suggested`; do not auto-promote.
- Set `next.recommended_h2_step` to `h2-archive` or `h2-compound`.

### h2-compound

- Compound reusable knowledge from completed work.
- Read `.harness-helm/h2-compound.yml` when present to determine domain refinement mode, canonical destination mapping, review gate, and retrieval hook policy. If absent, use conservative built-in defaults and record that fallback in the compound artifact.
- Run-level policy overrides such as `mode=synthesis` and `destination=docs/40_knowledge/solutions` do not change the defaults; record them with `policy:mode:*` and `policy:destination:*` traces.
- Low-risk learning/solution docs under `docs/40_knowledge/solutions/**` or `docs/40_knowledge/learnings/**` may be created or updated after overlap, schema, and lint checks.
- Governed canonical targets such as `docs/20_specs/**`, `docs/30_decisions/**.accepted.md`, team/runtime conventions, and operational policy must be staged until owner/verifier or Tech Lead approval is recorded.
- Record governed candidates in `routing.promotion_candidates`; record low-risk writes in `artifacts.created` or `artifacts.updated`.
- Route to `.harness-helm/runs/{feature}/{run-id}/compound-candidates.md`.
- Set `next.recommended_h2_step` to `h2-archive` or `null`.

### h2-harvest

- Curate staged notes from `docs/_harvest-inbox/{solution,convention,domain,spec,decision,ops}/`.
- Use `.harness-helm/scripts/harness h2-harvest` and `.harness-helm/h2-harvest.yml` when installed.
- Do not infer `confidence: high` from prose. It must be user-declared and supported by deterministic evidence metadata.
- Treat possible body/type mismatch as warning-only unless frontmatter explicitly overrides the type.
- Route reports to `.harness-helm/runs/_unscoped/{run-id}/harvest-report.md`.
- Set `next.recommended_h2_step` to `null`.

### h2-archive

- Check whether `h2-compound` has run for this feature by looking for `.harness-helm/runs/{feature}/*/compound-candidates.md`. If no compound evidence exists, run `h2-compound` meaning automatically as preflight before proceeding.
- Run `.harness-helm/scripts/harness archive {feature}` to execute the archive. Use `--dry-run` to preview changes without applying them.
- In `h2-autorun`, `h2-archive` is an execute step, not a preview step. Use non-dry-run archive by default because the user has already requested automatic progression through the lifecycle.
- Do not reimplement archive file movement.
- `harness archive` moves `.harness-helm/runs/{feature}/` to `docs/_archive/{archive-folder}/runs/`, writes transient `runs/stage-runtime-summary.json`, writes root `stage-runtime-summary.md`, then prunes the transient JSON and keeps only run root-level Markdown artifacts such as `context-pack.md`, `archive-plan.md`, `autorun-summary.md`, `build.md`, `test.md`, and `compound-candidates.md`; run manifests, snapshots, raw, normalized, promotion candidates, and restore backups are pruned after summary generation.
- After archive completes, run `.harness-helm/scripts/harness kb-index` to refresh `docs/_indexes/*.md` after active docs move out of indexed locations. Include the regenerated index files in the same archive commit/PR; otherwise `harness-validate` (or equivalent CI) flags index drift on the next push.
- Route to `.harness-helm/runs/{feature}/{run-id}/archive-plan.md`.
- Set `next.recommended_h2_step` to `h2-ops` or `null`.

### h2-ops

- Record incident, release, runbook, and branch sweep operation candidates.
- Route operation candidates to `docs/50_operations/{type}/{topic}.md`.
- Set `next.recommended_h2_step` to `null`.

### h2-cartridge

- Run `.harness-helm/scripts/harness cartridge-validate` when `.harness-helm/` is installed; otherwise inspect bundled `references/cartridge-command-mapping.md` for invocation recording, fallback handling, and routing invariants.
- Confirm each command defines `provider`, `surface`, `fallback_label`, `routing_target`, and `output_language`.
- Record unavailable or invalid surfaces in `verification.not_verified` or `verification.required`.
- Route to `.harness-helm/runs/{feature}/{run-id}/cartridge-mapping.md`.

## Staging

Use the staging rules from this skill and bundled `references/core-workflow.md`:

```text
.harness-helm/runs/{feature}/{run-id}/
├── context-pack.md
├── raw/
├── normalized/
└── promotion-candidates/
```

- Use `.harness-helm/runs/_unscoped/{run-id}/` when `feature` is unknown.
- `run-id` format is `YYYYMMDD-HHMMSS-h2-{command}` using `Asia/Seoul`, and harness scripts validate it.
- The runtime adapter executing the h2 command creates `raw/`, `normalized/`, and `promotion-candidates/`; `harness.py` validates and cleans them up but does not create them for every lifecycle command.
- `.harness-helm/runs/**` is not official KB and is not default retrieval input. On `h2-archive`, the feature runs folder is moved to `docs/_archive/{archive-folder}/runs/` and then minimized to run-level Markdown artifacts only; archive root `stage-runtime-summary.md` keeps the human-readable timing summary.
- Remove or mask sensitive/raw output before moving anything to official docs.

## Upstream Override Input

Users may override the default upstream provider/surface for a single run. Recognize two input shapes when parsing the user request.

- key-value form: `$h2 plan {feature} upstream=<provider> surface=<surface>`. Recognize only `upstream` and `surface` keys. On duplicates, the last value wins.
- natural language: e.g. "이번 plan은 gstack 대신 superpowers writing-plans 기준으로 작성해줘". Extract provider and surface names.

When both forms appear in the same request, key-value wins.

Apply the override using the selection priority and recording rules defined in `references/provider-surface-selection-and-override.md` or the canonical docs guideline at `docs/40_knowledge/conventions/guidelines/harness-helm/provider-surface-selection-and-override.md`. Do not change command routing because of an override. The result is still routed to the command's `routing_target` and recorded via the command's h2 template; only the input provider/surface changes. Record run-level overrides in `verification.completed` (`actual:<provider>:<surface>`) and never as a change to `.harness-helm/h2-cartridge.yml` defaults.

## Codex Adapter Rules

- Follow `AGENTS.md` first, then project instructions.
- This skill is subordinate to `AGENTS.md`; if they conflict, `AGENTS.md` wins.
- Codex-specific wording, file location, and invocation details may differ, but output meaning and routing must match this skill and bundled `references/core-workflow.md`.
- Preserve bundled `references/codex-adapter.md` command meanings for the full `h2-*` command surface.
- Do not reimplement gstack, superpowers, compound-engineering, enforcement scripts, `_indexes` generation, or canonical promotion.
- Upstream tool execution is optional; when upstream results are unavailable, record the gap in `verification.not_verified`.
- Compatibility note: older `hera-harness` assets may exist in this repository; `harness-helm` is the suite name and current Codex adapter entrypoint.

## External Skill Integration: mattpocock/skills

`mattpocock/skills` is installed globally rather than bundled in this repo:

- Claude Code: 14 Engineering+Productivity skills in `~/.claude/skills/` (`diagnose`, `grill-with-docs`, `improve-codebase-architecture`, `prototype`, `setup-matt-pocock-skills`, `tdd`, `to-issues`, `to-prd`, `triage`, `zoom-out`, `caveman`, `grill-me`, `handoff`, `write-a-skill`)
- Codex: the same 14 plus 4 misc (`git-guardrails-claude-code`, `migrate-to-shoehorn`, `scaffold-exercises`, `setup-pre-commit`) in `~/.agents/skills/`

These external skills assume per-repo configuration normally written to `AGENTS.md` and `docs/agents/`. For harness-helm, that configuration lives in this section so the root `AGENTS.md`/`CLAUDE.md` stay h2-focused and `docs/` stays a workflow-artifact tree. The sub-sections below apply whenever one of these skills runs inside this repo.

### Issue tracker

Issues live in GitHub at `dandihera/harness-helm`. Skills that "publish to the issue tracker" or "fetch the relevant ticket" (`to-issues`, `triage`, `to-prd`, and similar) call the `gh` CLI: `gh issue create`, `gh issue view <n> --comments`, `gh issue edit <n> --add-label …`, `gh issue close <n>`, etc. `gh` infers the repo from `git remote -v`. Old GitHub issue numbers stay out of `cookbooks/` titles and canonical references per root `AGENTS.md`.

### Triage labels

Five canonical labels exist on the GitHub repo and map 1:1 to the mattpocock role names. Apply with `gh issue edit <number> --add-label <label>`.

| Role              | Label             | Meaning                                  |
| ----------------- | ----------------- | ---------------------------------------- |
| `needs-triage`    | `needs-triage`    | Maintainer needs to evaluate             |
| `needs-info`      | `needs-info`      | Waiting on reporter                      |
| `ready-for-agent` | `ready-for-agent` | Fully specified, AFK-ready for an agent  |
| `ready-for-human` | `ready-for-human` | Requires human implementation            |
| `wontfix`         | `wontfix`         | Will not be actioned                     |

### Domain docs

harness-helm uses the HERA workflow layout instead of the mattpocock defaults (`CONTEXT.md` and `docs/adr/` do not exist and should not be created). When skills like `diagnose`, `tdd`, `improve-codebase-architecture`, or `zoom-out` ask for "domain context" or "ADRs", read:

- `docs/10_domain/` — entities, vocabulary, lifecycle (replaces `CONTEXT.md`)
- `docs/30_decisions/` — architectural and process decisions (replaces `docs/adr/`)
- `docs/10_domain/harness-helm/concepts.md` — harness-helm product concepts and vocabulary
- `docs/40_knowledge/conventions/` — naming and structure conventions
- `docs/40_knowledge/references/` — compact external references, including `matt-pocock-skills.md`
- GitHub Issues — backlog, follow-ups, and issue-level workflow tracking

If any of these are missing for the area you're touching, proceed silently — new domain terms and decisions get added lazily through the normal h2 workflow (`h2-design`, `h2-report`, `h2-compound`). When your output names a harness-helm product concept, use the term as defined under `docs/10_domain/harness-helm/concepts.md`; use broader domain terms from `docs/10_domain/` and conventions from `docs/40_knowledge/conventions/`. Use `docs/40_knowledge/references/` as comparison material, not as harness-helm authority. If your output contradicts an existing decision in `docs/30_decisions/`, surface it explicitly rather than silently overriding.
