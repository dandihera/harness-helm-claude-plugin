# Upstream Selection and Override Reference

Compact runtime snapshot of `docs/40_knowledge/conventions/guidelines/h2-upstream-selection-and-override.md`.

For the full canonical procedure, see `docs/40_knowledge/conventions/guidelines/h2-upstream-selection-and-override.md`.

Mapping authority: `docs/40_knowledge/conventions/guidelines/h2-runtime-reference-selection.md`.

## Rule

Default upstream provider/surface selection is defined by `.harness-helm/h2-cartridge.yml`.

Run-level override is allowed when the user explicitly requests another provider/surface. It changes only the current run, not adapter defaults.

Permanent mapping changes require adapter, references, and parity snapshots to be updated together.

## Selection Priority

1. User-specified provider/surface
2. `.harness-helm/h2-cartridge.yml` command primary provider/surface
3. `.harness-helm/h2-cartridge.yml` command alternatives
4. Bundled runtime references or upstream surface map secondary candidates
5. Tool registry surface with the same purpose
6. Adapter fallback checklist

User override must not change command semantics or routing.

## Run-Level Override

Accepted forms:

```text
$h2 plan {feature} upstream=superpowers surface=writing-plans
```

```text
Use superpowers writing-plans for this plan instead of gstack.
```

Processing:

1. Resolve command id, e.g. `$h2 plan` -> `h2-plan`.
2. Read cartridge primary mapping.
3. Check whether requested surface is in cartridge alternatives.
4. If not, check bundled references and registry for the same-purpose surface.
5. Confirm runtime availability.
6. Normalize upstream output into the command h2 template.
7. Record override in h2 output.
8. Record actual invocation or fallback in `verification`.

## Permanent Mapping Change

Use this only when repeated overrides and Tech Lead approval justify changing the default.

Steps:

1. Explain command, old provider/surface, new provider/surface, and why this is not just a run-level override.
2. Edit `.harness-helm/h2-cartridge.yml`.
3. Recheck `fallback_label` and `alternatives`.
4. Update upstream invocation and surface map references.
5. Update runtime parity snapshot if needed.
6. Run adapter/reference validation.

## Avoid

- Do not change command routing because of an override.
- Do not store raw upstream output as h2 plan/design/report.
- Do not record run-level override as adapter default.
- Do not mark fallback checklist as actual invocation.
