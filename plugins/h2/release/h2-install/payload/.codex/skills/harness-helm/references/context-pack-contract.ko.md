# Context Pack Contract Reference

`0305 Context Pack Contract`의 압축 runtime snapshot입니다.

## Rule

context pack은 run-level retrieval snapshot입니다. 원문 문서 복사본이 아니며 그 자체가 canonical knowledge도 아닙니다.

`h2-context`가 context pack을 생성하거나 갱신합니다. 이후 `h2-*` command는 같은 run의 reading plan으로 이 파일을 사용합니다.

## Required Shape

context pack은 다음 항목을 기록합니다.

- `primary_docs`: 이번 run에서 먼저 읽을 문서
- `supporting_docs`: 필요할 수 있는 보조 문서
- `canonical_knowledge`: run에 재투입된 재사용 지식
- `excluded_by_policy`: 기본 context에서 의도적으로 제외한 문서 범주
- `assumptions`: retrieval 가정, freshness note, fallback 이유

## Routing

feature가 있는 run은 다음 경로를 사용합니다.

```text
.harness-helm/runs/{feature}/{run-id}/context-pack.md
```

탐색 run은 다음 경로를 사용합니다.

```text
.harness-helm/runs/_unscoped/{run-id}/context-pack.md
```

## Avoid

- 원문 문서 전체를 context pack에 붙여 넣지 않습니다.
- `h2-context`에서 `_indexes`를 생성하지 않습니다.
- index entry를 canonical docs보다 권위 있게 취급하지 않습니다.
- 제외 문서를 조용히 사용하지 않고, 필요하면 이유를 기록합니다.

