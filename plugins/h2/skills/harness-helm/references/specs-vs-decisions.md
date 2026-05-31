# Specs vs Decisions Reference

Compact runtime snapshot of `docs/40_knowledge/conventions/guidelines/harness-helm/specs-vs-decisions.md`.

For the full canonical guideline, see `docs/40_knowledge/conventions/guidelines/harness-helm/specs-vs-decisions.md`.

Mapping authority: `docs/40_knowledge/conventions/guidelines/harness-helm/runtime-reference-selection.md`.

## Rule

Use `docs/20_specs/**` for contracts that describe how the system should behave.

Use `docs/30_decisions/**` for approved choices that explain why one direction was selected over alternatives.

## 20_specs

A spec should answer:

- What behavior, interface, data shape, integration contract, or acceptance rule must hold?
- How can implementation or tests verify it?
- Which modules or systems must follow it?

Specs can change as the product evolves. They do not need ADR numbering.

## 30_decisions

A decision should answer:

- What choice was made?
- Which alternatives were considered?
- Why was this choice accepted or rejected?
- Who approved it and when?
- What consequences follow from the decision?

Decision documents require approval before they become accepted canonical knowledge.

## h2-compound Behavior

`h2-compound` may stage both spec and decision promotion candidates, but it must not create accepted canonical documents without approval.
