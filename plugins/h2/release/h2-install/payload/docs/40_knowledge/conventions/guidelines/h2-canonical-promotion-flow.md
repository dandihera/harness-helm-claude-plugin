---
schema_version: 1
id: "CONV-20260525-003"
type: convention
status: stable
owner: tw.jang
security: internal
confidence: medium
related:
  - docs/40_knowledge/conventions/guidelines/h2-specs-vs-decisions.md
source_references:
  - cookbooks/0300-workflow-contract/0304-canonical-promotion-flow.md
module:
  - docs
  - workflow
tags:
  - harness-helm
  - h2-compound
  - h2-report
  - h2-archive
  - canonical-promotion
---

# Convention: h2 canonical promotion flow

## Rule

`h2-compound`는 reusable knowledge를 축적하되, governed canonical 문서를 승인 없이 생성하지 않는다.

`h2-compound`는 `h2-report`까지 모인 결과를 보고 반복 가능한 해결책과 학습을 `docs/40_knowledge`에 축적한다. Low-risk `docs/40_knowledge/solutions/**`와 `docs/40_knowledge/learnings/**`는 overlap, schema, lint 확인 후 작성하거나 갱신할 수 있다. 실제 governed canonical 문서는 owner/verifier, PR reviewer, 또는 Tech Lead 승인 기록이 남은 뒤에만 작성하거나 갱신한다.

`canonical`은 검증되어 장기 참조 기준이 되는 원본 지식을 뜻한다. `20_specs`와 `30_decisions` 같은 목적지 판단은 `docs/40_knowledge/conventions/guidelines/h2-specs-vs-decisions.md`를 따른다.

## Applies To

- `$h2 report`가 장기 문서 후보를 발견했을 때
- `$h2 compound`가 low-risk knowledge를 작성하거나 governed promotion candidate를 staging할 때
- 사용자가 “이 후보 승인”, “이 후보를 canonical 문서로 만들어도 됨”, `$h2 compound approve <candidate-path>`처럼 승인 의사를 표현했을 때
- agent가 승인된 후보를 canonical 문서로 작성하거나 갱신하려 할 때
- `$h2 archive`가 완료된 01~04 작업 산출물을 정리할 때

## Flow

canonical 승격은 다음 순서로 진행한다.

1. `h2-report`가 승격 필요성을 기록한다.
2. `h2-compound`가 low-risk learning/solution은 작성 또는 갱신하고, governed 후보는 `compound-candidates.md`에 staging한다.
3. owner/verifier 또는 Tech Lead가 후보를 승인, 보류, 기각한다.
4. h2 command 또는 agent가 승인 기록을 repository에 남긴다.
5. 승인된 governed 후보만 canonical 문서로 작성하거나 갱신한다.
6. `kb-lint --strict`로 schema와 frontmatter를 검증한다.
7. `kb-index`로 retrieval index를 갱신한다.
8. `h2-archive`는 preflight에서 compound 실행 증거를 확인하고 미실행이면 `h2-compound`를 자동 트리거한 뒤, 완료된 01~04 작업 문서를 archive한다.

요약하면 `h2-compound`는 low-risk 지식은 축적하고 governed 후보는 staging한다. 승인은 governed 후보를 canonical 문서로 만들 수 있게 하며, `h2-archive`는 compound 실행을 보장하고 완료된 작업 산출물을 정리한다.

## Responsibilities

### h2-report

`h2-report`는 plan, design, analysis, build, test, review 결과를 묶고 남은 승격 필요성을 기록한다.

장기 문서 후보가 보이면 report의 `Promotion Candidates` 섹션이나 h2 output의 `routing.promotion_candidates`에 넣을 수 있다. 단, `h2-report`는 canonical 문서를 생성하지 않는다.

### h2-compound

`h2-compound`는 reusable knowledge를 축적하고 governed 승격 후보를 staging한다.

`h2-compound`가 남겨야 하는 내용:

- low-risk 작성/갱신 대상 경로 또는 governed 후보 canonical 경로
- 작성/갱신 또는 후보로 올리는 이유
- 필요한 승인자 또는 검증자
- 근거가 되는 plan, design, report, review
- governed 후보는 승인 전에는 canonical 문서가 아니라는 상태

권장 staging 위치:

```text
.harness-helm/runs/{feature}/{run-id}/compound-candidates.md
```

### owner/verifier

owner/verifier 또는 Tech Lead는 후보를 보고 다음 중 하나로 판단한다.

| 상태 | 의미 | 다음 행동 |
|---|---|---|
| `approved` | canonical 문서로 작성 가능 | 승인 기록을 남긴 뒤 문서를 작성하거나 갱신한다. |
| `pending` | 아직 판단하지 않음 | 후보만 유지하고 canonical 문서는 만들지 않는다. |
| `rejected` | 승격하지 않음 | 기각 이유를 후보 기록이나 report에 남긴다. |

승인자는 직접 문서를 만들지 않아도 된다. 중요한 것은 누가, 무엇을, 어떤 근거로 승인했는지가 repository 안에 남는 것이다.

### h2-archive

`h2-archive`는 승격 command가 아니다.

`h2-archive`는 preflight에서 `.harness-helm/runs/{feature}/*/compound-candidates.md` 존재 여부를 확인한다. compound 실행 증거가 없으면 `h2-compound`를 자동으로 트리거한 뒤 archive를 진행한다. 이로써 사용자가 `h2-compound`를 별도로 실행하지 않아도 지식 축적이 보장된다.

`h2-archive`는 완료된 `01_plan`, `02_design`, `03_review`, `04_report` 작업 산출물을 `_archive`로 이동해 기본 retrieval에서 제외하는 정리 단계다. archive된 본문은 historical record이며 공식 기준 원본이 아니다.

## Approval Input

승인은 구두 합의로 끝나면 안 된다. 후보가 canonical 문서로 승격되려면 승인 대상, 승인자, 승인 상태, 근거 문서가 repository에 남아야 한다.

사용자가 YAML을 직접 작성할 필요는 없다. 사용자는 “이 후보 승인”, “이 후보를 canonical 문서로 만들어도 됨”, `$h2 compound approve <candidate-path>`처럼 승인 의사만 명시한다. 그러면 h2 command 또는 agent가 `compound-candidates.md`에 approval metadata를 기록한다.

`$h2 compound approve <candidate-path>`는 별도 canonical command id가 아니다. 이는 `h2-compound` 안에서 특정 후보를 승인 대상으로 지정하는 입력 형식이다.

승인 입력을 받으면 agent 또는 h2 command는 다음 순서로 처리한다.

1. `<candidate-path>`가 `compound-candidates.md`의 `routing.promotion_candidates` 또는 후보 목록에 있는지 확인한다.
2. 후보의 근거 문서가 plan, design, report, review 중 어디에 남아 있는지 확인한다.
3. 사용자가 owner/verifier 또는 Tech Lead 승인 권한을 가진 사람인지 기록한다.
4. 승인 범위가 후보 전체인지, 일부 canonical 경로만 승인하는지 확인한다.
5. `approval.status: approved` metadata를 `compound-candidates.md`에 추가한다.
6. 아직 canonical 문서는 만들지 않고, 다음 단계가 canonical 작성임을 `next`나 report에 남긴다.

승인 입력이 모호하면 canonical 문서를 만들지 않는다. 승인 대상 경로가 없거나, 후보 목록에 없는 경로를 승인하거나, 승인자가 불명확하면 `approval.status: pending`으로 남기고 확인이 필요한 항목을 적는다.

권장 승인 기록:

```yaml
approval:
  status: approved
  approved_by: owner-id
  approved_at: 2026-05-25
  scope:
    - docs/{canonical-route}/candidate-name.md
  evidence:
    - docs/01_plan/{feature}.md
    - docs/02_design/{feature}.md
    - docs/04_report/{feature}.md
  notes:
    - Candidate approved for canonical promotion.
```

권장 기록 위치는 다음 순서다.

1. `.harness-helm/runs/{feature}/{run-id}/compound-candidates.md`
2. `docs/04_report/{feature}.md`
3. PR review comment 또는 commit message

## Promotion Write Rule

Low-risk `docs/40_knowledge/solutions/**`와 `docs/40_knowledge/learnings/**`는 approval 없이 작성하거나 갱신할 수 있다. 이때 기본값은 `status: draft`, `confidence: medium`이며, `verified`, `stable`, `confidence: high`는 schema가 요구하는 검증 근거가 있을 때만 사용한다.

Governed canonical 문서는 `approval.status: approved`가 확인된 후보만 작성하거나 갱신한다.

작성 순서:

1. `compound-candidates.md`에서 승인 상태와 승인자를 확인한다.
2. 관련 schema, convention, template을 보고 canonical 목적지를 확정한다.
3. `harness new-doc` 또는 template으로 문서를 작성한다.
4. frontmatter에 승인 근거를 반영한다.
5. 본문에 canonical 문서로 필요한 최소 내용을 채운다.
6. `kb-lint --strict`를 실행한다.
7. `kb-index`를 실행한다.
8. 필요하면 report 또는 PR description에 승격 완료 사실을 기록한다.

주의:

- 승인 전 governed 후보는 canonical 문서가 아니다.
- 승인 전 후보를 `_indexes`에 canonical knowledge로 노출하지 않는다.
- `confidence: high`를 쓰려면 `human_verified_by`, `tests`, `source_pr`, `source_trace` 중 하나 이상이 필요하다.
- 목적지별 filename, status, frontmatter 규칙은 `.harness-helm/h2-schema.yml`과 관련 schema를 따른다.

## Avoid

다음을 하지 않는다.

- `h2-compound`가 governed canonical 문서를 승인 없이 생성한다.
- `h2-archive`가 canonical 승격을 대신한다.
- 승인 없는 governed 후보를 canonical 문서로 저장한다.
- 목적지 판단 기준을 이 문서에 중복 정의한다.

## Verification

- `$h2 compound`가 low-risk knowledge와 governed 후보를 구분했는지 확인한다.
- 승인된 governed 후보만 canonical 문서로 작성됐는지 확인한다.
- 승인 metadata에 승인자, 승인 대상, 근거 문서가 있는지 확인한다.
- `kb-lint --strict`와 `kb-index`로 canonical docs 상태를 확인한다.
