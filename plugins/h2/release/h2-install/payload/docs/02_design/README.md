# 02_design - h2 Design Drafts

`h2-design` output lands here. `h2-analysis` may update or annotate related design content.

## Folder Mapping

```text
docs/02_design/{feature}.md
```

## Template

Use `docs/_templates/design.md`.

Expected frontmatter follows `.harness-helm/h2-schema.yml` and `docs/_templates/design.md`:

- `type: design`
- `status: draft | active | done | archived`
- common fields: `schema_version`, `id`, `owner`, `security`, `confidence`, `related`

## Retrieval Policy

Design documents are selected as primary context for build/test/review work when they are relevant and not excluded by the retrieval policy.

## Coexistence

Legacy `docs/02-design/**` is outside the current underscore-based docs lifecycle.
