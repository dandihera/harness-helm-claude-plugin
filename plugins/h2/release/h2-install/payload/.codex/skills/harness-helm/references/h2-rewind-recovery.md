# h2-rewind Recovery Reference

Compact runtime snapshot of h2 rewind recovery rules.

## Rule

`h2-autorun` creates rewindable pre-step snapshots before child steps. `h2-rewind` restores one requested step boundary from those snapshots.

Rewind is a workflow restore, not a destructive git reset.

## Required Inputs

`h2-rewind` requires:

- feature
- run-id
- step

If the snapshot manifest or requested step snapshot is missing, return `blocked:no-snapshot`.

## Runtime Paths

Snapshots live under:

```text
.harness-helm/runs/{feature}/{run-id}/snapshots/{step}/
```

Restore backups live under:

```text
.harness-helm/runs/{feature}/{run-id}/restore-backups/{timestamp}/{step}/
```

Restore evidence routes to:

```text
.harness-helm/runs/{feature}/{run-id}/snapshots/{step}/restore.md
```

## Archive Residue

If archive residue exists under `docs/_archive/**`, preserve it and warn. Do not delete archive residue automatically during rewind.

## Avoid

- Do not guess a run-id.
- Do not use `git reset --hard` as rewind.
- Do not restore without preserving overwritten files in `restore-backups`.
- Do not delete archive residue automatically.

