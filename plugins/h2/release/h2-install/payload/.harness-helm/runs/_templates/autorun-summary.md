---
command: h2-autorun
feature: "<TODO: feature slug>"
status: updated
next:
  recommended_h2_step: null
---

<!-- harness-helm h2-autorun staging output. 하위 h2 lifecycle command의 실행 결과를 요약한다. -->

# h2-autorun Summary: <TODO: feature title>

## Context Pack

### primary_docs

- <TODO: docs/02_design/{feature}.md>

### supporting_docs

- <TODO: context pack 경로>

### excluded_by_policy

- <TODO: 제외된 문서>

### assumptions

- <TODO: autorun 가정>

## Autorun Plan

- expected_steps:
  - h2-analysis
  - h2-build
  - h2-test
  - h2-review
  - h2-report
  - h2-compound
  - h2-archive
- review_type: <TODO: code | qa | security | cross>
- context_pack: <TODO: .harness-helm/runs/{feature}/{run-id}/context-pack.md>
- design_readiness: <TODO: ready | blocked | warning>

## Step Results

| step | status | artifact | next_recommended_h2_step | warnings | blocked_reason |
|---|---|---|---|---|---|
| h2-analysis | <TODO> | <TODO> | <TODO> | <TODO> | <TODO> |
| h2-build | <TODO> | <TODO> | <TODO> | <TODO> | <TODO> |
| h2-test | <TODO> | <TODO> | <TODO> | <TODO> | <TODO> |
| h2-review | <TODO> | <TODO> | <TODO> | <TODO> | <TODO> |
| h2-report | <TODO> | <TODO> | <TODO> | <TODO> | <TODO> |
| h2-compound | <TODO> | <TODO> | <TODO> | <TODO> | <TODO> |
| h2-archive | <TODO> | <TODO> | <TODO> | <TODO> | <TODO> |

## Blocked Reason

- <TODO: blocked 단계와 사유. 없으면 <없음>>

## Verification

### required

- <TODO>

### completed

- <TODO>

### not_verified

- <TODO>

## Next

- recommended_h2_step: null
