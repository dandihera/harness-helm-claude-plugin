---
schema_version: 1
id: "CONV-20260525-001"
type: convention
status: stable
owner: tw.jang
security: internal
confidence: medium
target_runtime: included
related: []
source_references:
  - cookbooks/0300-workflow-contract/0304-canonical-promotion-flow.md
module:
  - docs
  - workflow
tags:
  - harness-helm
  - h2-compound
  - canonical-promotion
  - specs
  - decisions
  - hera-v4
  - gist-v2
---

# Convention: specs와 decisions 구분

## Rule

`20_specs`와 `30_decisions`는 둘 다 오래 남는 canonical docs지만 답하는 질문이 다르다.

```text
20_specs      = 앞으로 시스템이 지켜야 하는 계약
30_decisions  = 왜 그 계약/방향을 선택했는지에 대한 결정 기록
```

`20_specs`는 “무엇이 어떻게 동작해야 하는가”를 적고, `30_decisions`는 “왜 이 방식으로 하기로 했는가”를 적는다.

## Applies To

- `$h2 report`가 promotion candidate를 기록할 때
- `$h2 compound`가 `30_decisions`, `20_specs`, `40_knowledge` 후보를 목적지별로 분류할 때
- hera-v4 framework 기능과 gist-v2 project 기능의 책임 경계를 문서화할 때
- agent가 신규 canonical docs를 만들기 전에 목적지를 판단할 때

## 20_specs로 가는 내용

`20_specs`는 구현과 테스트가 따라야 할 contract다.

hera-v4 Excel upload 개선 예시:

```text
- 업로드 가능한 파일 형식은 xlsx다.
- 첫 번째 row는 header로 처리한다.
- column mapping은 template id 기준으로 해석한다.
- validation error response는 row, column, code, message를 포함한다.
- partial success를 허용할지 여부를 정의한다.
- import result API response shape을 정의한다.
- 최대 row 수와 file size 제한을 정의한다.
- 같은 파일 재업로드 시 idempotency 처리 방식을 정의한다.
```

즉 개발자나 agent가 나중에 구현/테스트할 때 “이게 맞는 동작인가?”를 판정할 수 있어야 한다.

`20_specs` 후보로 분류하는 질문:

- 구현이 따라야 할 input/output 계약인가?
- API, file format, validation rule, response schema인가?
- 테스트 케이스가 이 문서를 기준으로 pass/fail 될 수 있는가?
- “이 값, 필드, 동작이 맞다/틀리다”를 판정할 수 있는가?

## 30_decisions로 가는 내용

`30_decisions`는 선택과 기각의 이유를 남긴다.

hera-v4 Excel upload 개선 예시:

```text
- Excel parser는 hera-v4 framework 공통 기능으로 둔다.
- 보험 GA 업무 column mapping은 gist-v2 project spec으로 둔다.
- validation engine은 framework 공통으로 제공하되, rule set은 project에서 주입한다.
- 대안 A: gist-v2 전용 업로드 구현
- 대안 B: 모든 것을 hera-v4 공통으로 흡수
- 선택한 이유: parser/error report/streaming 처리는 반복 가능하지만, 보험 업무 mapping은 프로젝트별 변화가 크다.
- 결과: hera-v4는 extension point를 제공하고, gist-v2는 업무 rule을 구현한다.
```

즉 나중에 누가 “왜 Excel upload를 전부 framework에 넣지 않았지?” 또는 “왜 gist-v2에 parser를 따로 만들면 안 되지?”라고 물었을 때 답하는 문서다.

`30_decisions` 후보로 분류하는 질문:

- 여러 대안 중 하나를 선택했는가?
- 선택하지 않은 대안도 나중에 다시 제안될 수 있는가?
- framework vs project 책임 경계가 정해졌는가?
- 이 결정이 이후 설계에 constraint를 만드는가?
- “왜 이렇게 했는가”를 남기지 않으면 나중에 반복 논쟁이 생기는가?

## 둘 다 필요한 경우

framework 기능처럼 중요한 주제는 `20_specs`와 `30_decisions`가 둘 다 필요할 수 있다.

```text
30_decisions/framework/0001-excel-upload-framework-boundary.accepted.md
```

이 문서는 “hera-v4와 gist-v2의 책임 경계”를 결정한다.

```text
20_specs/integration/excel-upload-contract.md
```

이 문서는 “그 결정에 따라 실제 업로드 계약이 어떻게 생겼는지”를 정의한다.

둘의 관계는 다음과 같다.

```text
30_decisions: 왜 이 구조인가?
        ↓
20_specs: 그래서 시스템 계약은 무엇인가?
        ↓
build/test: 그 계약대로 구현됐는가?
```

따라서 decision 없이는 spec의 배경이 약해지고, spec 없이는 decision이 실제 구현 계약으로 내려오지 않는다.

## Do

```text
framework/project 책임 경계와 선택 이유는 30_decisions 후보로 기록한다.
업로드 파일, API, validation response 같은 동작 계약은 20_specs 후보로 기록한다.
```

## Avoid

`20_specs`에 다음 문장이 많으면 spec에 decision이 섞인 것이다.

```text
우리는 gist-v2 전용 구현 대신 hera-v4 공통 parser를 쓰기로 했다.
대안으로는 project별 parser를 두는 방법이 있었지만 유지보수 비용 때문에 배제했다.
```

이 내용은 `30_decisions`로 옮긴다.

반대로 `30_decisions`에 다음 내용이 너무 많으면 decision에 spec이 섞인 것이다.

```text
error.code는 REQUIRED_FIELD, INVALID_FORMAT, DUPLICATE_ROW 중 하나다.
response.errors[].rowIndex는 1-based index다.
업로드 API는 POST /api/imports/excel을 사용한다.
```

이 내용은 `20_specs`로 옮긴다.

## Verification

- `$h2 compound`의 `promotion_candidates`가 목적지별로 분리되어 있는지 확인한다.
- `30_decisions` 후보에는 선택 이유, 대안, 결과가 있는지 확인한다.
- `20_specs` 후보에는 구현과 테스트가 따를 계약이 있는지 확인한다.
- `kb-lint --strict`와 `kb-index`로 canonical docs 상태를 확인한다.
