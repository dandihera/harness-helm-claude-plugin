---
schema_version: 1
id: "CONV-20260531-014"
type: convention
status: stable
owner: tw.jang
security: internal
confidence: medium
target_runtime: included
source_references:
  - cookbooks/0600-cartridge/0601-cartridge-command-mapping.md
module:
  - docs
  - workflow
tags:
  - harness-helm
  - cartridge
  - provider
  - surface
---

# Cartridge command mapping

`.harness-helm/h2-cartridge.yml`은 h2 command별 provider, surface, fallback label, routing target, output language의 실행 기준이다.

## 기준

- h2 command semantics와 routing은 workflow contract가 정한다.
- cartridge는 command를 실행하거나 보조할 provider/surface를 고른다.
- provider가 달라져도 h2 output contract는 유지한다.
- fallback checklist를 실제 upstream invocation처럼 기록하지 않는다.

## 검증 책임

- 값 기준: `.harness-helm/h2-cartridge.yml`
- 값 검증: `.harness-helm/scripts/harness cartridge-validate --strict`
- snapshot 검증: `.harness-helm/scripts/harness reference-validate --strict`

Runtime snapshot reference는 cartridge 값의 사본이 아니다. Snapshot은 invocation 기록 방식, fallback 처리, routing invariant를 압축해 설명한다. 설치된 provider, surface, fallback label, routing target, output language, alternatives, external tool registry 값은 `.harness-helm/h2-cartridge.yml`을 직접 읽어 확인한다.

## 기록 규칙

- 실제 upstream 호출: `actual:<provider>:<surface>`
- fallback checklist 또는 recorder mode: `verified-fallback:<fallback_label>`
- 사용할 수 없는 도구나 미확인 claim: `verification.not_verified`
- blocked prerequisite: `verification.required`

## 변경 규칙

기본 provider/surface/output language를 바꾸려면 `.harness-helm/h2-cartridge.yml`을 갱신하고, 관련 runtime snapshot은 값 사본이 아니라 책임·기록 규칙·routing invariant가 여전히 맞는지 확인한다. 일회성 override는 cartridge default 변경으로 기록하지 않는다.
