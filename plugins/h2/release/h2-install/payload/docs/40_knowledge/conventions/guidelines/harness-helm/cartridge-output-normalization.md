---
schema_version: 1
id: "CONV-20260531-015"
type: convention
status: stable
owner: tw.jang
security: internal
confidence: medium
target_runtime: included
source_references:
  - cookbooks/0600-cartridge/0604-cartridge-output-normalization.md
module:
  - docs
  - workflow
tags:
  - harness-helm
  - cartridge
  - normalization
---

# Cartridge output normalization

Upstream raw output은 canonical h2 artifact가 아니다. Claude Code, Codex, gstack, superpowers, compound-engineering 결과는 h2 output contract와 command별 template으로 정규화한 뒤 기록한다.

## 정규화 기준

- upstream command 이름이 아니라 h2 `command` 값을 보존한다.
- routing은 h2 command semantics를 따른다.
- raw output의 판단, evidence, risk는 h2 섹션으로 요약한다.
- 실제 호출 여부는 `verification.completed` 또는 `verification.not_verified`에 명확히 남긴다.

## 보안 기준

`raw/`에는 secret, token, 개인정보, 장문 로그가 섞일 수 있다. 공식 docs에 반영하기 전 masking과 요약을 수행한다.

## 금지

- raw output을 그대로 `docs/01_plan`, `docs/02_design`, `docs/04_report`에 저장하지 않는다.
- fallback checklist를 실제 호출로 기록하지 않는다.
- upstream output의 형식 때문에 h2 공통 output field를 생략하지 않는다.

