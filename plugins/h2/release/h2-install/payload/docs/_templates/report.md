---
schema_version: 1
id: "REPORT-YYYYMMDD-NNN"
type: report
status: draft
owner: "<TODO: git username 또는 team id>"
security: internal
confidence: low
related: []
# Recommended optional fields
# module:
#   - <TODO: module name>
# tests: []
# source_trace: "<TODO: historical trace 또는 외부 작업 출처>"
# source_pr: "<TODO: PR number>"
---

<!-- harness-helm report template. status enum: draft|active|done|archived. See 0102 Frontmatter Schema. -->

# Report: <TODO: feature title>

## Summary

<TODO: 무엇을 했고 어떤 결과가 나왔는지 3~5문장.>

## Plan / Design / Analysis 요약

- plan: <TODO: link or path>
- design: <TODO: link or path>
- analysis notes: <TODO: link or path>

## Implementation Results

- <TODO: 주요 변경 사항, 영향 범위>

## Verification

- completed: <TODO: 수행한 검증>
- not_verified: <TODO: 미검증/남은 검증>

## Promotion Candidates

<!-- 자동 승격 금지. owner/verifier 또는 Tech Lead 승인 후 canonical 영역 이동. -->

- <TODO: 10/20/30/40/50 승격 후보. 없으면 비워둔다.>

## Operations / Release Impact

- runbook 갱신 필요: <TODO: yes/no, 사유>
- incident 가능성: <TODO: yes/no, 사유>
- release notes 갱신 필요: <TODO: yes/no, 사유>

## References

- <TODO: 관련 plan, design, reviews, PRs>
