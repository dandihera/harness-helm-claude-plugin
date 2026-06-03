---
schema_version: 1
id: "CONV-20260531-010"
type: convention
status: stable
owner: tw.jang
security: internal
confidence: medium
target_runtime: included
module:
  - docs
  - workflow
tags:
  - harness-helm
  - runtime-reference
  - guideline
---

# harness-helm runtime guideline

이 폴더는 target project에 설치되는 harness-helm runtime guideline의 canonical namespace다.

기존 flat `docs/40_knowledge/conventions/guidelines/h2-*.md` guideline은 이 폴더로 이동되었다. 사용자는 이 폴더에서 h2 workflow의 장기 운영 기준을 읽고, agent는 필요할 때 같은 문서를 canonical guideline으로 참조한다.

## 문서 계층

| 계층 | 위치 | 역할 |
|---|---|---|
| Source policy | `cookbooks/` | source repository의 설계 배경과 결정 기록 |
| Runtime guideline | `docs/40_knowledge/conventions/guidelines/harness-helm/` | target project에서도 읽는 canonical 운영 지침 |
| Compact snapshot | `.claude/.codex/skills/harness-helm/references/` | agent가 빠르게 읽는 fallback |

Target project에는 `cookbooks/`가 설치되지 않는다. 따라서 target runtime 판단은 이 폴더, `.harness-helm/`, root agent guide, bundled reference snapshot을 기준으로 한다.

## 포함 지침

- `runtime-reference-selection.md`: source policy, runtime guideline, compact snapshot을 나누는 기준
- `workflow-lifecycle-commands.md`: h2 command lifecycle과 routing 기준
- `context-pack-contract.md`: context pack의 역할, 출력 구조, preflight 관계
- `runtime-folder-structure.md`: `.harness-helm/` runtime 폴더와 run staging 구조
- `feature-naming.md`: GitHub/GitLab 이슈에서 시작한 h2 feature slug naming 기준
- `cartridge-command-mapping.md`: provider/surface/fallback/routing/output language mapping 기준
- `provider-surface-selection-and-override.md`: run-level provider/surface override와 permanent mapping change 기준
- `cartridge-output-normalization.md`: upstream raw output을 h2 artifact로 정규화하는 기준
- `compound-policy-config.md`: `h2-compound` write boundary와 review gate 기준
- `canonical-promotion-flow.md`: promotion candidate를 canonical docs로 승격하는 기준
- `specs-vs-decisions.md`: `20_specs`와 `30_decisions` 목적지 선택 기준
- `h2-rewind-recovery.md`: `h2-autorun` snapshot과 `h2-rewind` restore 기준

## 운영 규칙

- guideline이 바뀌면 대응 compact snapshot을 확인한다.
- snapshot과 guideline이 충돌하면 guideline을 우선한다.
- `.harness-helm/h2-cartridge.yml`, `.harness-helm/h2-schema.yml`, `.harness-helm/h2-compound.yml`이 실행 기준인 값은 문서에 중복 선언하지 않는다.
- source-only 배경, issue trace, release 과정은 cookbook이나 workflow artifact에 남기고 target manual 본문 중심에 두지 않는다.
