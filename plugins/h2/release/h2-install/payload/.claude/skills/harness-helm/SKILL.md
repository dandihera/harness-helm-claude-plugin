---
name: harness-helm
description: Claude Code adapter for harness-helm h2 workflow contracts. Use for h2-context, h2-plan, h2-design, h2-analysis, h2-build, h2-test, h2-review, h2-report, h2-compound, h2-archive, h2-ops, and h2-cartridge while preserving the 0301-core-workflow-spec command semantics, output fields, staging rules, and docs routing.
---

# harness-helm

`harness-helm` is a thin Claude Code adapter for the HERA AI-native docs lifecycle. It does not replace gstack, superpowers, compound-engineering, Claude Code, or Codex. It wraps their work into the shared `h2-*` workflow, output contract, staging rules, and routing defined by the core references.

Bundled runtime references:

- `references/skill-suite.md`: `0302 Skill Suite` boundary and `h2` prefix.
- `references/core-workflow.md`: `0301 Core Workflow Spec` `h2-*` core workflow.
- `references/claude-adapter.md`: `0401 Claude Code Adapter` scope and `h2-*` entrypoints.
- `references/claude-entrypoint.md`: `0403 Runtime Parity Test` Claude smoke/parity example.
- `references/runtime-parity.md`: `0403 Runtime Parity Test` parity result between Claude Code and Codex.
- `references/workflow-lifecycle-commands.md`: `0303 Workflow Lifecycle Commands` `h2-*` command semantics.
- `references/upstream-tool-invocation.md`: `0601 Upstream Tool Invocation` upstream provider/surface/fallback mapping.
- `references/external-tool-registry.md`: `0602 Upstream Tool Registry` integration targets, alternatives, availability, and registration rules.
- `references/upstream-surface-map.md`: `0603 Upstream Surface Map` upstream surface recommendations and drift notes.
- `references/upstream-output-normalization.md`: `0604 Upstream Output Normalization` raw upstream output to h2 template mapping rules.
- `references/canonical-promotion-flow.md`: runtime snapshot for `h2-compound` promotion approval and canonical write rules.
- `references/specs-vs-decisions.md`: runtime snapshot for choosing between `20_specs` and `30_decisions`.
- `references/upstream-selection-and-override.md`: runtime snapshot for run-level upstream override and permanent mapping change.

Canonical runtime conventions are stored under `docs/40_knowledge/conventions/guidelines/*.md` when docs are installed. Bundled `references/canonical-promotion-flow.md`, `references/specs-vs-decisions.md`, and `references/upstream-selection-and-override.md` provide compact runtime snapshots when those docs are absent or too expensive to load. The meta guideline for choosing snapshot scope remains in `docs/40_knowledge/conventions/guidelines/h2-runtime-reference-selection.md` and is not bundled as a runtime snapshot.

Base `references/*.md` files are English snapshots for Claude/Codex parity and compact loading. Matching `references/*.ko.md` files are stakeholder Korean translations and must not be loaded into the default agent context; read them only when the user explicitly requests Korean review.

Installed target projects do not include `cookbooks/`. Use this `SKILL.md`, `.claude/commands/h2/*.md`, bundled `references/*.md`, root `CLAUDE.md`/`AGENTS.md`, `docs/`, and `.harness-helm/` as the runtime surface.

Load bundled reference snapshots when a compact rule below is not enough or when checking detailed acceptance criteria.

## Docs Artifact Language

Markdown files under the numbered user-facing docs folders must be written in Korean by default. This applies to `docs/01_plan/**`, `docs/02_design/**`, `docs/03_review/**`, `docs/04_report/**`, `docs/10_domain/**`, `docs/20_specs/**`, `docs/30_decisions/**`, `docs/40_knowledge/**`, and `docs/50_operations/**`.

Generated machine-facing index documents under `docs/_indexes/**` are the exception. Write those index markdown files in English because h2 primarily consumes them as retrieval and routing aids.

Keep technical identifiers, command names, file paths, frontmatter keys, proper nouns, and source quotations in their original form. Use another language only when the user explicitly requests it or when preserving an exact quoted source.

## Runtime Read Order

1. Follow root `AGENTS.md`, root `CLAUDE.md`, and project-specific instructions first.
2. Use this `SKILL.md` for canonical `h2-*` command semantics, output fields, staging rules, and docs routing.
3. Treat `.claude/commands/h2/*.md` as thin slash-command aliases only.
4. Load bundled `references/*.md` only when detailed criteria, parity evidence, upstream mapping, normalization, or promotion rules are needed.
5. Use `.harness-helm/h2-cartridge.yml` for editable provider, surface, fallback, and routing values when installed; otherwise use `references/upstream-tool-invocation.md`.

## Runtime Source Hierarchy

- Source repository design records live in `cookbooks/`, but installed target projects do not include `cookbooks/`.
- Installed runtime command semantics come from this `SKILL.md`, `references/core-workflow.md`, and `references/workflow-lifecycle-commands.md`.
- Runtime provider and surface mapping comes from `.harness-helm/h2-cartridge.yml` when installed, with bundled upstream references as fallback.
- Runtime schema validation comes from `.harness-helm/h2-schema.yml`.
- Root `CLAUDE.md` and `AGENTS.md` provide project-wide entrypoint guidance and must not duplicate the full workflow contract.

## Runtime Parity Boundary

- Claude and Codex may differ in invocation syntax and file layout.
- They must preserve the same `h2-*` command ids, common output fields, docs routing, staging rules, and cartridge mapping semantics.
- Runtime-specific guide files under skill folders are not part of the target surface; use root guidance, this `SKILL.md`, aliases, bundled references, `docs/`, and `.harness-helm/`.

## Command Surface

Claude Code must expose these `h2-*` commands:

- `h2-context`
- `h2-plan`
- `h2-design`
- `h2-analysis`
- `h2-build`
- `h2-test`
- `h2-review`
- `h2-report`
- `h2-compound`
- `h2-archive`
- `h2-ops`
- `h2-cartridge`

Use `.harness-helm/h2-cartridge.yml` as the shared source of truth for provider, surface, fallback label, routing target values, and upstream tool registry entries when it is installed. If it is absent in a target project, use bundled `references/upstream-tool-invocation.md` as the runtime mapping. Load `references/external-tool-registry.md` for tool alternatives and registration rules, and `references/workflow-lifecycle-commands.md` when detailed workflow lifecycle command semantics are needed.

## Common Input

Preserve these meanings even if Claude Code invocation is natural language:

```yaml
command: h2-context | h2-plan | h2-design | h2-analysis | h2-build | h2-test | h2-review | h2-report | h2-compound | h2-archive | h2-ops | h2-cartridge
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

## Common Output

Responses and artifacts must preserve these fields:

```yaml
command: "<h2-command>"
feature: "<feature-slug or null>"
status: "draft | updated | skipped | blocked"
context_pack:
  primary_docs: []
  supporting_docs: []
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

- Select primary/supporting/excluded docs using the retrieval policy and core workflow rules in bundled `references/`.
- Read `docs/_indexes/KB_INDEX.md` when present; if indexes are absent or stale, inspect canonical source docs directly.
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

### h2-analysis

- Compare plan goal/scope/done criteria with design implementation and verification strategy.
- Prefer updating the relevant plan/design content or suggesting exact changes.
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
- Low-risk learning/solution docs under `docs/40_knowledge/solutions/**` or `docs/40_knowledge/learnings/**` may be created or updated after overlap, schema, and lint checks.
- Governed canonical targets such as `docs/20_specs/**`, `docs/30_decisions/**.accepted.md`, team/runtime conventions, and operational policy must be staged until owner/verifier or Tech Lead approval is recorded.
- Record governed candidates in `routing.promotion_candidates`; record low-risk writes in `artifacts.created` or `artifacts.updated`.
- Route to `.harness-helm/runs/{feature}/{run-id}/compound-candidates.md`.
- Set `next.recommended_h2_step` to `h2-archive` or `null`.

### h2-archive

- Check whether `h2-compound` has run for this feature by looking for `.harness-helm/runs/{feature}/*/compound-candidates.md`. If no compound evidence exists, run `h2-compound` meaning automatically as preflight before proceeding.
- Run `.harness-helm/scripts/harness archive {feature}` to execute the archive. Use `--dry-run` to preview changes without applying them.
- Do not reimplement archive file movement.
- After archive completes, run `.harness-helm/scripts/harness kb-index` to refresh `docs/_indexes/*.md` so the new archive manifest entry is registered. Include the regenerated index files in the same archive commit/PR; otherwise `harness-validate` (or equivalent CI) flags an index drift on the next push.
- Route to `.harness-helm/runs/{feature}/{run-id}/archive-plan.md`.
- Set `next.recommended_h2_step` to `h2-ops` or `null`.

### h2-ops

- Record incident, release, runbook, and branch sweep operation candidates.
- Route operation candidates to `docs/50_operations/{type}/{topic}.md`.
- Set `next.recommended_h2_step` to `null`.

### h2-cartridge

- Run `.harness-helm/scripts/harness cartridge-validate` when `.harness-helm/` is installed; otherwise inspect bundled `references/upstream-tool-invocation.md`.
- Confirm each command defines `provider`, `surface`, `fallback_label`, and `routing_target`.
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
- `run-id` format is `{YYYYMMDD-HHMMSS}-{h2-step}` using `Asia/Seoul`, and harness scripts validate it.
- The runtime adapter executing the h2 command creates `raw/`, `normalized/`, and `promotion-candidates/`; `harness.py` validates and cleans them up but does not create them for every lifecycle command.
- `.harness-helm/runs/**` is not official KB and is not default retrieval input.
- Remove or mask sensitive/raw output before moving anything to official docs.

## Upstream Override Input

Users may override the default upstream provider/surface for a single run. Recognize two input shapes when parsing the user request.

- key-value form: `/h2:plan {feature} upstream=<provider> surface=<surface>`. Recognize only `upstream` and `surface` keys. On duplicates, the last value wins.
- natural language: e.g. "이번 plan은 gstack 대신 superpowers writing-plans 기준으로 작성해줘". Extract provider and surface names.

When both forms appear in the same request, key-value wins.

Apply the override using the selection priority and recording rules defined in `references/upstream-selection-and-override.md` or the canonical docs guideline at `docs/40_knowledge/conventions/guidelines/h2-upstream-selection-and-override.md`. Do not change command routing because of an override. The result is still routed to the command's `routing_target` and recorded via the command's h2 template; only the input provider/surface changes. Record run-level overrides in `verification.completed` (`actual:<provider>:<surface>`) and never as a change to `.harness-helm/h2-cartridge.yml` defaults.

## Adapter Rules

- Follow `AGENTS.md` first, then `CLAUDE.md` and project instructions.
- Do not copy or change core semantics in command aliases; reference this skill and bundled `references/core-workflow.md` instead.
- Claude-specific wording, file location, and invocation details may differ, but output meaning and routing must match this skill, bundled `references/core-workflow.md`, and Codex parity expectations.
- Do not reimplement gstack, superpowers, compound-engineering, enforcement scripts, `_indexes` generation, or canonical promotion.
- Compatibility note: older `hera-harness` assets may exist in this repository; `harness-helm` is the suite name and current Claude adapter entrypoint.

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
- `docs/40_knowledge/conventions/` — naming, structure, product memory
- `docs/40_knowledge/references/` — compact external references, including `matt-pocock-skills.md`
- GitHub Issues — backlog, follow-ups, and issue-level workflow tracking

If any of these are missing for the area you're touching, proceed silently — new domain terms and decisions get added lazily through the normal h2 workflow (`h2-design`, `h2-report`, `h2-compound`). When your output names a domain concept, use the term as defined under `docs/10_domain/` and `docs/40_knowledge/conventions/`. Use `docs/40_knowledge/references/` as comparison material, not as harness-helm authority. If your output contradicts an existing decision in `docs/30_decisions/`, surface it explicitly rather than silently overriding.
