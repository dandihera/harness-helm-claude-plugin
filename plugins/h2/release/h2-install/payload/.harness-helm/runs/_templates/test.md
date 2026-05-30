---
command: h2-test
feature: "<TODO: feature-slug>"
status: draft
next:
  recommended_h2_step: h2-review
---

<!-- harness-helm h2-test staging output. status enum: draft|updated|skipped|blocked.
     skip 시 사유는 verification.not_verified에 명시한다. See 0301 Core Workflow Spec.

     Evidence label 사용 예 (verification.completed에 기록):
       actual:harness:local-test-command (로컬 test command 실행)
       actual:gstack:gstack-health       (gstack health 실행)
       actual:gstack:gstack-qa           (gstack QA 실행)
       cartridge-checklist-fallback:test-skip-or-result-recorder (test 미실행, skip 사유만)
     실제 실행이 아니면 actual:... 라벨을 쓰지 않는다. skip은 fallback 라벨 + Skip Rationale 절에 사유. -->

# h2-test — <TODO: feature title>

## Context Pack

### primary_docs
- <TODO: 관련 plan/design/build 결과 경로>

## Artifacts

### created
- <TODO: 새로 만든 test 파일>

### updated
- <TODO: 수정한 test 파일>

### suggested
- <TODO: 추가하면 좋은 test 시나리오>

## Routing

- target_docs: []
- archive_candidate: false
- promotion_candidates: []

## Verification

### Test Run Summary

- command: `<TODO: 예: ./gradlew :bootstrap-system:test>`
- result: <TODO: passed | failed | skipped>
- timestamp (Asia/Seoul): <TODO: YYYY-MM-DD HH:MM>

### completed
- <TODO: 통과한 검증 항목>

### not_verified
- <TODO: skip 사유 또는 사람 검토가 필요한 항목>

## Failures (있을 때만)

- <TODO: 실패한 테스트와 원인 요약>

## Skip Rationale (skip한 경우 필수)

- <TODO: 왜 skip했는지. 문서/설정/사소한 변경 등 검증 영향이 낮은 사유.>

## Next

- recommended_h2_step: h2-review
