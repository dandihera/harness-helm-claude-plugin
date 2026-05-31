# 01_plan - h2 Plan Drafts

`h2-plan` output lands here.

## Folder Mapping

```text
docs/01_plan/{feature}.md
```

## Template

Use `docs/_templates/plan.md`.

Expected frontmatter follows `.harness-helm/h2-schema.yml` and `docs/_templates/plan.md`:

- `type: plan`
- `status: draft | active | done | archived`
- common fields: `schema_version`, `id`, `owner`, `security`, `confidence`, `related`

## Retrieval Policy

Draft and active plan documents are working context. They are not canonical knowledge until later review or promotion. Follow the retrieval policy in `cookbooks/0100-knowledge-base-foundation/0103-retrieval-and-index-policy.md` when selecting context.

## Coexistence

Legacy `docs/01-plan/**` is outside the current underscore-based docs lifecycle.
