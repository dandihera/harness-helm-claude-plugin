---
schema_version: 1
id: "DOM-20260530-002"
type: domain
status: stable
owner: codex
security: internal
confidence: medium
related:
  - docs/10_domain/harness-helm/concepts.md
module:
  - docs
  - workflow
domain:
  - workflow
tags:
  - harness-helm
  - concepts
  - product-language
supersedes: []
---

# Harness Helm Domain

이 폴더는 harness-helm 제품에서 쓰는 핵심 개념, 용어, 기억해야 할 제품 판단, 반복 참조되는 개념 관계를 모으는 기준 위치다.

## 기준 문서

제품 개념 사전의 기준 문서는 다음 파일로 둔다.

```text
docs/10_domain/harness-helm/concepts.md
```

기존 `docs/40_knowledge/conventions/h2-product-memory.md`의 역할은 이 위치로 옮긴다. 다만 새 문서는 단순 복원이 아니라 역할을 바꾼다.

- 기존 역할: product memory convention
- 새 역할: harness-helm 제품 개념 사전과 상세 문서 라우터

## 왜 10_domain인가

`h2`, `context pack`, `canonical docs`, `h2-compound`, `runtime snapshot reference`, `cartridge` 같은 말은 단순 운영 규칙이 아니라 harness-helm의 제품 언어다.

`docs/40_knowledge/conventions/`는 "어떻게 운용할 것인가"에 가깝고, `docs/10_domain/harness-helm/`은 "무엇을 의미하는가"에 가깝다. 따라서 제품 개념의 기준 위치는 이 폴더가 더 적절하다.

## concepts.md에 담을 것

`concepts.md`에는 다음을 모은다.

- harness-helm에서 쓰는 핵심 단어
- h2 workflow 개념
- 기억해야 하는 제품 판단
- 반복 참조되는 개념 간 관계
- 상세 기준 문서를 어디서 봐야 하는지

## concepts.md에 담지 않을 것

`concepts.md`는 모든 상세 정책을 복사하는 문서가 아니다.

다음 내용은 요약과 링크만 두고, 상세는 해당 기준 문서로 보낸다.

- 긴 운영 절차
- 상세 구현 정책
- runtime adapter 세부 규칙
- release convention 같은 독립 정책
- command별 실행 절차 전체

## 문서 구조 권장안

`concepts.md`는 다음 구조를 기본으로 한다.

```markdown
# Harness Helm Concepts - 제품 개념 사전

## 목적
## 사용 원칙
## h2
## h2 workflow
## Context Pack
## Canonical Docs
## h2-compound
## Runtime Snapshot Reference
## Cartridge
## 기준 표현
## 관련 상세 문서
```

## 상세 기준 연결

제품 개념은 이 폴더에서 정의하되, 상세 기준은 각 주제의 소유 문서가 담당한다.

| 개념 | concepts.md 역할 | 상세 기준 |
|---|---|---|
| `h2` | harness-helm alias와 표기 기준 정의 | `0301 Core Workflow Spec` |
| Context Pack | 제품 의미와 사용 경계 요약 | `0305 Context Pack Contract` |
| Canonical Docs | 공식 기준 문서 개념 요약 | `0304 Canonical Promotion Flow`, `0106 Knowledge Classification and Product Concepts` |
| h2-compound | 지식 복리 루프에서의 역할 요약 | `0304 Canonical Promotion Flow` |
| Runtime Snapshot Reference | runtime용 압축 기준 문서 개념 요약 | `0105 Runtime Reference Selection` |
| Cartridge | h2 command별 upstream mapping 개념 요약 | `.harness-helm/h2-cartridge.yml`, `0601 Cartridge Command Mapping` |

## 운영 원칙

`concepts.md`는 harness-helm의 제품 언어를 한 곳에서 정의하고 상세 문서로 연결하는 허브다.

새 개념을 추가할 때는 다음을 지킨다.

1. 먼저 개념의 짧은 정의를 쓴다.
2. 이 개념이 왜 필요한지 한두 문단으로 설명한다.
3. 혼동하기 쉬운 개념과 경계를 밝힌다.
4. 상세 기준 문서가 있으면 링크한다.
5. 상세 절차나 정책을 길게 복제하지 않는다.

이 폴더의 목적은 "모든 내용을 한 파일에 쌓는 것"이 아니라, harness-helm에서 사용되는 단어와 기억해야 할 제품 판단을 다시 찾을 수 있는 기준 위치를 제공하는 것이다.
