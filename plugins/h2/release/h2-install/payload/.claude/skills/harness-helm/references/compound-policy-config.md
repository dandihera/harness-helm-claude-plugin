# Compound Policy Config Reference

Compact runtime snapshot of `0306 Compound Policy Config`.

## Rule

`.harness-helm/h2-compound.yml` controls how `h2-compound` turns completed work into reusable knowledge.

If the file is absent, use conservative built-in defaults and record the fallback in the compound artifact.

## Policy Areas

- domain refinement mode and allowed run-level overrides
- canonical destination mapping for reusable knowledge
- low-risk write policy for learnings and solutions
- governed review gate for specs, decisions, conventions, and operational policy
- retrieval hook fields required or recommended on generated knowledge

## Write Boundary

Low-risk knowledge may be written after overlap, schema, and lint checks.

Governed canonical targets must be staged as promotion candidates until owner, verifier, or Tech Lead approval is recorded.

## Avoid

- Do not bypass governed approval by calling a write low-risk.
- Do not change command provider or routing from `h2-compound.yml`.
- Do not write broad architecture or policy changes directly to canonical docs without review evidence.

