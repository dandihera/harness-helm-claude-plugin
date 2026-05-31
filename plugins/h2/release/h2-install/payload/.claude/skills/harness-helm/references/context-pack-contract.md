# Context Pack Contract Reference

Compact runtime snapshot of `0305 Context Pack Contract`.

## Rule

A context pack is a run-level retrieval snapshot. It is not a copy of source documents and is not canonical knowledge by itself.

`h2-context` creates or updates the context pack. Downstream `h2-*` commands use it as the shared reading plan for the run.

## Required Shape

The context pack records:

- `primary_docs`: documents to read first for this run
- `supporting_docs`: secondary documents that may be needed
- `canonical_knowledge`: reusable knowledge reinjected into the run
- `excluded_by_policy`: document classes intentionally left out of default context
- `assumptions`: retrieval assumptions, freshness notes, and fallback reasons

## Routing

Feature-scoped runs use:

```text
.harness-helm/runs/{feature}/{run-id}/context-pack.md
```

Unscoped exploration uses:

```text
.harness-helm/runs/_unscoped/{run-id}/context-pack.md
```

## Avoid

- Do not paste full source documents into the context pack.
- Do not generate `_indexes` from `h2-context`.
- Do not treat index entries as more authoritative than canonical docs.
- Do not silently use excluded docs; record the reason when they are needed.

