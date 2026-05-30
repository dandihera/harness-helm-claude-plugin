---
schema_version: 1
id: "INC-YYYYMMDD-NNN"
type: incident
status: open
owner: "<TODO: incident commander username>"
security: internal
confidence: low
related: []
# Recommended optional fields
# module:
#   - <TODO: affected module>
# legal_hold: false
# source_trace: "<TODO: historical trace 또는 외부 작업 출처>"
---

<!-- harness-helm incident template. status enum: open|mitigated|resolved|reviewed.
     reviewed 후 반복 패턴은 40_knowledge 또는 50_operations/runbooks 승격 후보.
     See 0102 Frontmatter Schema, 0202 Operations Ownership. -->

# Incident: <TODO: 사고 제목>

## Timeline (Asia/Seoul)

- detected_at: <TODO: YYYY-MM-DD HH:MM>
- mitigated_at: <TODO: YYYY-MM-DD HH:MM 또는 N/A>
- resolved_at: <TODO: YYYY-MM-DD HH:MM 또는 N/A>
- reviewed_at: <TODO: YYYY-MM-DD HH:MM 또는 N/A>

## Impact

- 사용자 영향: <TODO>
- 영향 범위: <TODO: 모듈/지역/사용자 수>
- 비즈니스 영향: <TODO>

## Detection

<TODO: 어떻게 감지되었는지. 알림, 사용자 보고, 모니터링.>

## Root Cause

<TODO: 근본 원인. 추정이면 confidence를 명시.>

## Resolution

<TODO: 적용한 조치와 효과.>

## Follow-up Actions

- <TODO: 재발 방지 액션 1>
- <TODO: 재발 방지 액션 2>

## Lessons Learned

<TODO: 다음에 같은 일이 일어나지 않게 하려면 무엇을 바꿔야 하는지.>

## References

- <TODO: 관련 alerts, dashboards, PRs, runbooks>
