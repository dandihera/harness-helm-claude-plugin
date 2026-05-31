---
schema_version: 1
id: "CONV-20260531-012"
type: convention
status: stable
owner: tw.jang
security: internal
confidence: medium
target_runtime: included
source_references:
  - cookbooks/0300-workflow-contract/0305-context-pack-contract.md
module:
  - docs
  - workflow
tags:
  - harness-helm
  - context-pack
  - retrieval
---

# Context pack contract

Context pack은 h2 run의 retrieval snapshot이다. 원문 문서 복사본이 아니며, 후속 command가 같은 근거 문서와 제외 정책을 공유하도록 돕는 reading plan이다.

## 생성 경로

feature가 있는 run:

```text
.harness-helm/runs/{feature}/{run-id}/context-pack.md
```

feature가 아직 없는 탐색 run:

```text
.harness-helm/runs/_unscoped/{run-id}/context-pack.md
```

## 필수 항목

- `primary_docs`: 이번 run에서 먼저 읽을 문서
- `supporting_docs`: 보조 근거 문서
- `canonical_knowledge`: 재투입된 장기 지식
- `excluded_by_policy`: 기본 context에서 제외한 범주
- `assumptions`: retrieval 가정, index freshness, fallback 이유

## Preflight 관계

`h2-plan`, `h2-design`, `h2-analysis`, `h2-build`, `h2-test`, `h2-review`, `h2-report`는 작업 시작 시 `h2-context` 의미를 수행한다. 이미 같은 run의 context pack이 있으면 그 snapshot을 기준으로 삼고, 추가 문서가 필요하면 산출물에 사유를 남긴다.

## 금지

- 원문 문서 전체를 context pack에 복사하지 않는다.
- `h2-context`가 `_indexes`를 생성하지 않는다.
- index entry를 canonical docs보다 우선하지 않는다.

