# 04_report - h2 Reports

`h2-report` output lands here.

## Folder Mapping

```text
docs/04_report/{feature}.md
```

## Template

Use `docs/_templates/report.md`.

Expected frontmatter follows `.harness-helm/h2-schema.yml` and `docs/_templates/report.md`:

- `type: report`
- `status: draft | active | done | archived`
- common fields: `schema_version`, `id`, `owner`, `security`, `confidence`, `related`

## Retrieval Policy

Reports summarize plan/design/build/test/review evidence. They can suggest promotion candidates, but canonical promotion follows the h2 promotion flow.

## Coexistence

Legacy `docs/04-report/**` is outside the current underscore-based docs lifecycle.
