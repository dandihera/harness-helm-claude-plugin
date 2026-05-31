---
schema_version: 1
id: "CONV-20260531-011"
type: convention
status: stable
owner: tw.jang
security: internal
confidence: medium
target_runtime: included
source_references:
  - cookbooks/0300-workflow-contract/0303-workflow-lifecycle-commands.md
module:
  - docs
  - workflow
tags:
  - harness-helm
  - h2
  - lifecycle
---

# h2 workflow lifecycle commands

`h2-*` command는 같은 output contract와 routing 규칙을 공유한다. Runtime adapter는 Claude Code, Codex, gstack, superpowers, compound-engineering을 대체하지 않고, 그 결과를 h2 lifecycle 산출물로 정규화한다.

## 기본 흐름

권장 순서는 다음과 같다.

```text
h2-context -> h2-plan -> h2-design -> h2-analysis -> h2-build -> h2-test -> h2-review -> h2-report -> h2-compound -> h2-archive
```

`h2-autorun`은 위 흐름 중 analysis부터 archive까지를 이어서 실행하는 orchestration command다. 각 child step 전에 rewind 가능한 snapshot을 남겨야 한다.

## 공통 출력

각 command 산출물은 아래 의미를 보존한다.

- `context_pack`: 이번 run에서 읽은 근거와 제외 정책
- `artifacts`: 생성/수정/제안 산출물
- `routing`: 공식 문서 위치와 승격 후보
- `verification`: 실행한 검증, 필요한 검증, 미검증 항목
- `next`: 다음 권장 h2 step

## Routing 기준

- `h2-plan`: `docs/01_plan/{feature}.md`
- `h2-design`: `docs/02_design/{feature}.md`
- `h2-analysis`: `docs/02_design/{feature}.analysis.md`
- `h2-review`: `docs/03_review/{type}/{feature}.md`
- `h2-report`: `docs/04_report/{feature}.md`
- `h2-build`, `h2-test`, `h2-compound`, `h2-archive`: `.harness-helm/runs/{feature}/{run-id}/` 아래 staging artifact

## 금지

- provider가 달라졌다는 이유로 command routing을 바꾸지 않는다.
- upstream raw output을 h2 공식 artifact로 그대로 저장하지 않는다.
- review 또는 approval이 필요한 canonical 변경을 lifecycle command가 자동 승격하지 않는다.

