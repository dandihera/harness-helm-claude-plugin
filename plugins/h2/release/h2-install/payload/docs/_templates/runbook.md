---
schema_version: 1
id: "RUNBOOK-YYYYMMDD-NNN"
type: runbook
status: draft
owner: "<TODO: operations owner username>"
security: internal
confidence: low
related: []
# Recommended optional fields
# module:
#   - <TODO: module name>
# legal_hold: false
# human_verified_by: "<TODO: 검증자 username>"
---

<!-- harness-helm runbook template. status enum: draft|active|deprecated. See 0102 Frontmatter Schema. -->

# Runbook: <TODO: 운영 절차 제목>

## When to Use

<TODO: 이 runbook을 따라야 하는 상황. 장애 유형, 배포 시점, 점검 트리거.>

## Pre-checks

- <TODO: 실행 전 확인 사항>

## Procedure

1. <TODO: 단계 1 - 명령/조작/예상 결과>
2. <TODO: 단계 2>
3. <TODO: 단계 3>

## Verification

- <TODO: 절차 성공 판정 기준>

## Rollback

<TODO: 실패 시 되돌리는 절차. 없으면 "N/A"로 명시.>

## Escalation

- 1차: <TODO: 담당자>
- 2차: <TODO: 담당자>

## Related Incidents / Releases

- <TODO: 이 runbook이 작성된 배경 incident/release>

## References

- <TODO: 관련 docs, dashboards, alert configs>
