---
command: h2-build
feature: "<TODO: feature-slug>"
status: draft
next:
  recommended_h2_step: h2-test
---

<!-- harness-helm h2-build staging output. recorder mode: 코드 편집 actor를 대체하지 않는다.
     실제 design 실행 산출물은 superpowers/Claude Code/Codex/사용자가 만들고, 결과만 여기에 기록한다.
     산출물은 code, docs, workflow record, runtime configuration일 수 있다.
     See 0301 Core Workflow Spec, 0303 Workflow Lifecycle Commands.

     Evidence label 사용 예 (verification.completed에 기록):
       actual:claude-native-code-edit (실제 Claude Code가 코드 편집 수행)
       actual:codex-native-code-edit  (실제 Codex가 코드 편집 수행)
       actual:superpowers:test-driven-development (TDD discipline 적용)
       cartridge-checklist-fallback:changed-files-risk-recorder (actor 미실행, checklist만)
     실제 호출이 아니면 actual:... 라벨을 쓰지 않는다. checklist만이면 fallback 라벨 사용. -->

# h2-build — <TODO: feature title>

## Context Pack

### primary_docs
- <TODO: 관련 plan/design 경로>

### assumptions
- <TODO: build 시 가정한 사실>

## Artifacts

### Changed Files
- <TODO: path:line (예: src/main/java/.../FooService.java:42)>

### created
- <TODO: 새로 만든 파일>

### updated
- <TODO: 수정한 파일>

### suggested
- <TODO: 후속 추가 작업 제안>

## Routing

- target_docs: []
- archive_candidate: false
- promotion_candidates: []

## Verification

### required
- <TODO: 권장 검증 항목 (예: build 성공, 단위 테스트 통과)>

### completed
- <TODO: 이미 수행된 검증>

### not_verified
- <TODO: 사람 검토가 필요한 미검증 항목>

## Remaining Risks

- <TODO: 남은 구현 리스크. 다음 단계로 넘기는 경우 명시.>

## Next

- recommended_h2_step: h2-test
