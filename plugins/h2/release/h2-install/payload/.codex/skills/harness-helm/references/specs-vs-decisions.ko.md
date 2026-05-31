# Specs vs Decisions Reference

`docs/40_knowledge/conventions/guidelines/harness-helm/specs-vs-decisions.md`의 압축 runtime snapshot입니다.

전체 공식 기준 지침은 `docs/40_knowledge/conventions/guidelines/harness-helm/specs-vs-decisions.md`를 확인합니다.

Mapping 기준 정의 위치: `docs/40_knowledge/conventions/guidelines/harness-helm/runtime-reference-selection.md`.

## 규칙

시스템이 어떻게 동작해야 하는지를 설명하는 contract는 `docs/20_specs/**`를 사용합니다.

여러 대안 중 왜 특정 방향을 선택했는지 설명하는 승인된 선택은 `docs/30_decisions/**`를 사용합니다.

## 20_specs

Spec은 다음에 답해야 합니다.

- 어떤 behavior, interface, data shape, integration contract, acceptance rule이 유지되어야 하는가?
- 구현이나 test가 이를 어떻게 검증할 수 있는가?
- 어떤 module 또는 system이 이를 따라야 하는가?

Spec은 product 변화에 따라 바뀔 수 있습니다. ADR numbering은 필요하지 않습니다.

## 30_decisions

Decision은 다음에 답해야 합니다.

- 어떤 선택을 했는가?
- 어떤 대안을 검토했는가?
- 왜 이 선택을 accepted 또는 rejected 했는가?
- 누가 언제 승인했는가?
- 이 결정의 결과는 무엇인가?

Decision 문서는 accepted canonical knowledge가 되기 전에 승인이 필요합니다.

## h2-compound Behavior

`h2-compound`는 spec과 decision promotion candidate를 모두 staging할 수 있지만, 승인 없이 accepted canonical document를 만들면 안 됩니다.
