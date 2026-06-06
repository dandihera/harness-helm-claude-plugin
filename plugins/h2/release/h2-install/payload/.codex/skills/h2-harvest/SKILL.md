---
name: h2-harvest
description: Curate staged Markdown or text notes from docs/_harvest-inbox into canonical docs using the harness h2-harvest CLI. Use when the user asks to harvest inbox notes, promote/reject a staged knowledge file, or inspect h2-harvest behavior.
---

# h2-harvest

Use `h2-harvest` for inbox-based knowledge curation outside the feature lifecycle.

Runtime command:

```bash
.harness-helm/scripts/harness h2-harvest [--promote <path> | --reject <path>] [--dry-run] [--force] [--skip-raw]
```

Inputs must live under `docs/_harvest-inbox/{solution,convention,domain,spec,decision,ops}/` and must be `.md` or `.txt`. `.txt` inputs are written to canonical destinations as `.md`.

If `docs/_harvest-inbox/raw/` has prefix-free files, `h2-harvest` prints a warning and suggests running `h2-harvest-tag` first. Use `--skip-raw` only when intentionally ignoring raw inbox files.

Phase 1 does not use LLM or embedding classification. It applies deterministic policy from `.harness-helm/h2-harvest.yml`, validates frontmatter, warns on possible semantic type mismatches, and keeps governed destinations pending unless explicitly approved by the workflow.

Low-risk `solution` and `convention` entries can auto-write only when `confidence: high` and evidence metadata are present. Governed entries (`domain`, `spec`, `decision`, `ops`) remain pending. `--reject` or `status: rejected` hard-deletes the inbox source after writing the run report; use `--dry-run` to preview.

Reports are written to `.harness-helm/runs/_unscoped/{run-id}/harvest-report.md`.
