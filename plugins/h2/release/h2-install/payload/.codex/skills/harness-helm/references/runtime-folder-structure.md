# Runtime Folder Structure Reference

Compact runtime snapshot of `0503 h2 Runtime Folder Structure`.

## Rule

`.harness-helm/` is the installed runtime substrate for h2. It contains executable policy, schema, cartridge mapping, staging templates, and run-local evidence.

`docs/` is long-lived knowledge. `.harness-helm/runs/` is staging and is not canonical docs.

## Runtime Roots

- `.harness-helm/h2-schema.yml`: docs frontmatter and validation settings
- `.harness-helm/h2-cartridge.yml`: provider, surface, fallback, and routing mapping
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

## Avoid

- Do not treat `.harness-helm/runs/**` as official KB.
- Do not copy secrets or raw logs into canonical docs.
- Do not delete archive residue automatically during rewind or archive review.

