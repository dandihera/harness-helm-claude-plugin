# 03_review - h2 Review Drafts

`h2-review` output lands here.

## Folder Mapping

```text
docs/03_review/{type}/{feature}.md
```

Review type examples:

- `code`
- `qa`
- `security`
- `cross`

## Template

Use `docs/_templates/review.md`.

Expected frontmatter follows `.harness-helm/h2-schema.yml` and `docs/_templates/review.md`:

- `type: review`
- `status: draft | active | done | archived`
- common fields: `schema_version`, `id`, `owner`, `security`, `confidence`, `related`

## Retrieval Policy

Review documents are supporting context unless they contain accepted decisions or reusable findings promoted elsewhere. Follow the retrieval policy and promotion flow when selecting or promoting review findings.

## Coexistence

Legacy `docs/03-analysis/**` is outside the current underscore-based docs lifecycle.
