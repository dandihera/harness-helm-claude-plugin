# Canonical Promotion Flow Reference

Compact runtime snapshot of `docs/40_knowledge/conventions/guidelines/harness-helm/canonical-promotion-flow.md`.

For the full canonical procedure, see `docs/40_knowledge/conventions/guidelines/harness-helm/canonical-promotion-flow.md`.

Mapping authority: `docs/40_knowledge/conventions/guidelines/harness-helm/runtime-reference-selection.md`.

## Rule

`h2-compound` compounds reusable knowledge and stages governed promotion candidates. It does not create governed canonical documents without approval.

Low-risk `docs/40_knowledge/solutions/**` and `docs/40_knowledge/learnings/**` may be written or updated after overlap, schema, and lint checks. Governed candidates may become canonical documents only after owner, verifier, PR reviewer, or Tech Lead approval is recorded in the repository.

When `.harness-helm/h2-compound.yml` exists, use it as the h2-compound policy for domain refinement mode, canonical destination mapping, review gate, and retrieval hook policy. If it is absent, use conservative built-in defaults and record that fallback in `compound-candidates.md`.

## Flow

1. `h2-report` records the need for long-lived knowledge.
2. `h2-compound` writes or updates low-risk learning/solution docs, and stages governed candidates in `.harness-helm/runs/{feature}/{run-id}/compound-candidates.md`.
   Record the effective compound policy in the artifact body, including any `policy:mode:*` or `policy:destination:*` run-level override traces.
3. The owner, verifier, or Tech Lead approves, defers, or rejects the candidate.
4. The agent records approval metadata before writing canonical docs.
5. Only approved governed candidates are written to `docs/10_domain`, `docs/20_specs`, `docs/30_decisions`, governed `docs/40_knowledge`, or `docs/50_operations`.
6. Run `kb-lint --strict` and `kb-index` after canonical writes.
7. `h2-archive` checks for compound evidence as preflight (auto-triggers `h2-compound` if absent), then archives completed 01-04 workflow artifacts.

## Approval Input

Users do not need to write YAML manually. They can say `approve this candidate`, `this candidate may become canonical`, or `$h2 compound approve <candidate-path>`.

The agent must record:

- candidate path
- approval status
- approver identity
- approval date
- evidence docs
- approved scope

## Avoid

- Do not write governed canonical docs before approval.
- Do not treat `h2-archive` as a promotion command.
- Do not expose unapproved candidates as canonical knowledge.
- Do not redefine destination policy here; use `.harness-helm/h2-compound.yml` for compound destination mapping and `references/specs-vs-decisions.md` for `20_specs` vs `30_decisions`.
