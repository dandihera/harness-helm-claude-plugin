---
schema_version: 1
id: "CONV-20260531-016"
type: convention
status: stable
owner: tw.jang
security: internal
confidence: medium
target_runtime: included
source_references:
  - cookbooks/0300-workflow-contract/0306-compound-policy-config.md
module:
  - docs
  - workflow
tags:
  - harness-helm
  - h2-compound
  - knowledge
---

# Compound policy config

`.harness-helm/h2-compound.yml`은 `h2-compound`가 완료된 작업을 재사용 지식으로 전환하는 정책 파일이다.

## 정책 영역

- domain refinement mode와 run-level override 허용 여부
- reusable knowledge의 canonical destination mapping
- low-risk learning/solution write 기준
- spec, decision, convention, operation policy의 governed review gate
- generated/staged 문서에 필요한 retrieval hook field

## Write boundary

Low-risk knowledge는 overlap, schema, lint check 후 작성할 수 있다.

Governed canonical target은 owner, verifier, Tech Lead 승인 근거가 기록될 때까지 promotion candidate로 staging한다.

## fallback

Target project에 `.harness-helm/h2-compound.yml`이 없으면 conservative built-in default를 사용하고, compound artifact에 fallback 사실을 기록한다.

## 금지

- approval이 필요한 변경을 low-risk write로 우회하지 않는다.
- `h2-compound.yml`로 command provider나 routing을 바꾸지 않는다.

