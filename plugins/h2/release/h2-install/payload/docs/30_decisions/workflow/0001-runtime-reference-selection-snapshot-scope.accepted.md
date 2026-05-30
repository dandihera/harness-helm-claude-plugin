---
schema_version: 1
id: "ADR-0001"
type: decision
status: accepted
owner: "harness-helm"
security: internal
confidence: medium
related:
  - docs/40_knowledge/conventions/guidelines/h2-runtime-reference-selection.md
source_trace: "https://github.com/dandihera/harness-helm/issues/1"
tags:
  - harness-helm
  - runtime-reference
  - snapshot
  - workflow
---

# ADR-0001: runtime reference selection guideline은 snapshot으로 복제하지 않는다

## Status

accepted

## Context

`docs/40_knowledge/conventions/guidelines/*`는 사용자와 운영자가 읽는 canonical guideline이다. `.claude/.codex/skills/harness-helm/references/*`는 agent runtime이 실행 중 빠르게 읽는 compact snapshot이다.

모든 guideline을 snapshot으로 복제하면 같은 정책을 두 위치에서 유지해야 하므로 drift 비용이 생긴다. 특히 `h2-runtime-reference-selection.md`는 "무엇을 docs guideline 또는 runtime snapshot으로 둘지"를 설명하는 meta guideline이다. Agent가 매 h2 command 실행 중 즉시 적용해야 하는 promotion, destination, upstream override 규칙과 성격이 다르다.

## Decision

`docs/40_knowledge/conventions/guidelines/h2-runtime-reference-selection.md`는 canonical guideline으로 유지하고, `.claude/.codex` runtime snapshot reference에서는 제거한다.

Runtime snapshot으로 유지하는 대표 guideline은 agent가 실행 중 직접 판단해야 하는 다음 3종으로 제한한다.

- `h2-canonical-promotion-flow`
- `h2-specs-vs-decisions`
- `h2-upstream-selection-and-override`

## Alternatives Considered

- 4종 snapshot 유지: 기존 구조를 보존하지만 meta guideline까지 compact snapshot으로 중복해 drift 비용이 늘어난다.
- snapshot 전체 제거: 중복은 줄지만 agent가 승인, destination, upstream override 규칙을 실행 중 빠르게 확인하기 어려워진다.
- hash 기반 sync 검증: semantic drift를 강하게 잡을 수 있지만 snapshot은 의도적으로 compact English derivative라 source hash equivalence가 맞지 않는다.

## Consequences

### Positive

- runtime snapshot set 축소
- canonical guideline과 runtime snapshot의 역할 분리 명확화
- `reference-validate --strict`가 실제 유지 대상만 검증

### Negative / Trade-offs

- runtime reference selection 기준이 필요하면 agent가 canonical docs guideline을 직접 확인해야 함
- SKILL bundled references 목록과 product-memory mapping 갱신 필요

## Revisit Trigger

Target project runtime에서 `h2-runtime-reference-selection.md`를 반복적으로 즉시 로드해야 하는 사례가 생기면 snapshot 복원을 재검토한다.

## AI Avoid Phrases (rejected decision 전용)

- 해당 없음

## References

- https://github.com/dandihera/harness-helm/issues/1
- `docs/40_knowledge/conventions/guidelines/h2-runtime-reference-selection.md`
