---
schema_version: 1
id: "REVIEW-YYYYMMDD-NNN"
type: review
status: draft
owner: "<TODO: git username 또는 team id>"
security: internal
confidence: low
related: []
# Recommended optional fields
# module:
#   - <TODO: module name>
# tests: []
# reviewer: "<TODO: reviewer username/team>"
# source_pr: "<TODO: PR number>"
---

<!-- harness-helm review template. status enum: draft|active|done|archived.
     review type: code | qa | security | cross. type별 sub-route는 docs/03_review/{type}/{feature}.md.
     See 0102 Frontmatter Schema, 0201 Cross Review Policy. -->

# Review: <TODO: feature or PR title>

## Review Type

<TODO: code | qa | security | cross>

## Scope

- <TODO: 검토 대상 파일/모듈/PR>

## Findings

### Must Fix
- <TODO: 머지 전 반드시 해결해야 하는 항목>

### Should Fix
- <TODO: 권장 수정 사항>

### Nice to Have
- <TODO: 선택적 개선>

## Cross Review (선택)

<!-- 0201 Cross Review Policy의 권장 trigger에 해당할 때만 작성. resolution.md는 별도 파일. -->

- conflict level: <TODO: none | minor | material | critical>
- claude.review.md: <TODO: path>
- codex.review.md: <TODO: path>
- resolution.md: <TODO: path>

## References

- <TODO: 관련 plan, design, prior reviews>
