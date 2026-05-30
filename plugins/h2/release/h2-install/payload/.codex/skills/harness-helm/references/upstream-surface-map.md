# Upstream Surface Map Reference

Source cookbook: `0603 Upstream Surface Map`.

This reference is a runtime snapshot of upstream surface recommendations. It does not replace `.harness-helm/h2-cartridge.yml` or `references/upstream-tool-invocation.md` as the source of truth for provider, fallback label, or routing.

## Recommended Strengths

- `gstack`: planning review, QA, docs, and ops-oriented surfaces.
- `superpowers`: design discipline, TDD, systematic debugging, and verification gates.
- `compound-engineering`: plan, work, review, doc review, compound learning, and PR workflow surfaces.

## Selection Rule

Use this map when the adapter default is unavailable, when a user asks for a run-level upstream override, or when evaluating alternatives for a permanent mapping change.

Example: `h2-design` may use gstack, superpowers, or compound-engineering surfaces only when the resulting artifact is still normalized as an h2 design document.

## Boundaries

- Command semantics still come from h2.
- Fallback labels and routing targets belong to `.harness-helm/h2-cartridge.yml` and `references/upstream-tool-invocation.md`.
- Upstream raw output must be normalized through `references/upstream-output-normalization.md`.
- Do not claim actual invocation unless the upstream surface was actually called.
