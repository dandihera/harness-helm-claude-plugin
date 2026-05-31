# Canonical Promotion Flow Reference

`docs/40_knowledge/conventions/guidelines/harness-helm/canonical-promotion-flow.md`의 압축 runtime snapshot입니다.

전체 canonical 절차는 `docs/40_knowledge/conventions/guidelines/harness-helm/canonical-promotion-flow.md`를 확인합니다.

Mapping 기준 정의 위치: `docs/40_knowledge/conventions/guidelines/harness-helm/runtime-reference-selection.md`.

## 규칙

`h2-compound`는 reusable knowledge를 축적하고 governed promotion candidate를 staging합니다. 승인 없이 governed canonical 문서를 생성하지 않습니다.

Low-risk `docs/40_knowledge/solutions/**`와 `docs/40_knowledge/learnings/**`는 overlap, schema, lint 확인 후 작성하거나 갱신할 수 있습니다. Governed 후보는 owner, verifier, PR reviewer 또는 Tech Lead 승인 기록이 repository에 남은 뒤에만 canonical 문서가 될 수 있습니다.

`.harness-helm/h2-compound.yml`이 있으면 h2-compound의 domain refinement mode, canonical destination mapping, review gate, retrieval hook policy 기준으로 사용합니다. 없으면 conservative built-in default를 사용하고 그 fallback을 `compound-candidates.md`에 기록합니다.

## 흐름

1. `h2-report`가 장기 지식으로 남길 필요를 기록합니다.
2. `h2-compound`가 low-risk learning/solution 문서는 작성하거나 갱신하고, governed 후보는 `.harness-helm/runs/{feature}/{run-id}/compound-candidates.md`에 staging합니다.
   적용된 effective compound policy와 `policy:mode:*`, `policy:destination:*` run-level override trace를 artifact 본문에 기록합니다.
3. owner, verifier 또는 Tech Lead가 후보를 승인, 보류, 기각합니다.
4. agent는 canonical docs를 쓰기 전에 approval metadata를 기록합니다.
5. 승인된 governed 후보만 `docs/10_domain`, `docs/20_specs`, `docs/30_decisions`, governed `docs/40_knowledge`, `docs/50_operations`에 작성합니다.
6. canonical 작성 후 `kb-lint --strict`와 `kb-index`를 실행합니다.
7. `h2-archive`는 preflight에서 compound 실행 증거를 확인하고(미실행이면 `h2-compound` 자동 트리거), 완료된 01~04 작업 산출물을 archive합니다.

## 승인 입력

사용자가 YAML을 직접 작성할 필요는 없습니다. `이 후보 승인`, `이 후보를 canonical로 만들어도 됨`, `$h2 compound approve <candidate-path>`처럼 표현할 수 있습니다.

Agent는 다음을 기록해야 합니다.

- 후보 경로
- 승인 상태
- 승인자
- 승인일
- 근거 문서
- 승인 범위

## 피해야 할 것

- 승인 전에 governed canonical docs를 작성하지 않습니다.
- `h2-archive`를 승격 command로 취급하지 않습니다.
- 승인되지 않은 후보를 canonical knowledge로 노출하지 않습니다.
- 목적지 정책을 여기서 재정의하지 않습니다. Compound destination mapping은 `.harness-helm/h2-compound.yml`, `20_specs`와 `30_decisions` 구분은 `references/specs-vs-decisions.md`를 사용합니다.
