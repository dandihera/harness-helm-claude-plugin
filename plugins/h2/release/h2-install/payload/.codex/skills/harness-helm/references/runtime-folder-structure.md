# Runtime Folder Structure Reference

Compact runtime snapshot of `0503 h2 Runtime Folder Structure`.

## Rule

`.harness-helm/` is the installed runtime substrate for h2. It contains executable policy, schema, cartridge mapping, staging templates, and run-local evidence.

`docs/` is long-lived knowledge. `.harness-helm/runs/` is staging and is not canonical docs.

## Runtime Roots

- `.harness-helm/h2-schema.yml`: docs frontmatter and validation settings
- `.harness-helm/h2-cartridge.yml`: provider, surface, fallback, routing, and output language mapping
- `.harness-helm/h2-compound.yml`: compound destination and review-gate policy
- `.harness-helm/scripts/`: validation and workflow helper implementation
- `.harness-helm/runs/`: run-local context, raw output, normalized drafts, snapshots, and restore backups

## Runs Layout

```text
.harness-helm/runs/{feature}/{run-id}/
├── context-pack.md
├── raw/
├── normalized/
├── promotion-candidates/
├── snapshots/
└── restore-backups/
```

Use `_unscoped` instead of `{feature}` when the feature is unknown.

## Archive Retention

After `h2-archive`, archive-local `runs/` keeps only flattened Markdown artifacts directly under `runs/`, such as `plan-context-pack.md`, `design-context-pack.md`, `autorun-context-pack.md`, `archive-plan.md`, `autorun-summary.md`, `build.md`, `test.md`, and `compound-candidates.md`. The archive root keeps `runs-summary.md`. Run manifests, transient `runs/stage-runtime-summary.json`, run-id directories, snapshots, raw, normalized, promotion candidates, and restore backups are pruned after the Markdown summary is generated.

## Avoid

- Do not treat `.harness-helm/runs/**` as official KB.
- Do not copy secrets or raw logs into canonical docs.
- Do not delete archive residue automatically during rewind or archive review.
