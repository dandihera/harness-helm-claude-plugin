---
schema_version: 1
id: "CONV-20260526-001"
type: convention
status: stable
owner: tw.jang
security: internal
confidence: medium
target_runtime: included
related:
  - docs/40_knowledge/conventions/guidelines/harness-helm/canonical-promotion-flow.md
  - docs/40_knowledge/conventions/guidelines/harness-helm/specs-vs-decisions.md
  - docs/40_knowledge/conventions/guidelines/harness-helm/provider-surface-selection-and-override.md
source_references:
  - cookbooks/0100-knowledge-base-foundation/0105-runtime-reference-selection.md
module:
  - docs
  - workflow
tags:
  - harness-helm
  - runtime-reference
  - snapshot
  - cookbooks
  - h2
---

# Convention: h2 runtime reference selection

## Rule

`cookbooks/`의 모든 문서를 runtime reference로 옮기지 않는다.

Target project runtime에서 반복적으로 필요한 규칙은 `docs/40_knowledge/conventions/guidelines/harness-helm/`에 공식 기준 지침으로 둔다. Agent가 실행 중 빠르게 확인해야 하는 핵심 규칙은 `.claude/.codex` skill `references/`에 compact snapshot으로 둔다.

Snapshot은 공식 기준 원본이 아니다. 원본 기준은 docs guideline이고, snapshot은 docs guideline이 없거나 실행 중 전체 문서를 읽기에는 무거울 때 쓰는 fallback이다.

## Applies To

- cookbook의 정책을 target project runtime에서도 유지해야 할 때
- docs guideline을 skill `references/` snapshot으로 압축할지 판단할 때
- 신규 target project에 `cookbooks/`가 없어서 runtime 근거를 다시 정해야 할 때
- Claude Code와 Codex가 같은 h2 판단을 해야 할 때
- snapshot과 docs guideline의 동기화 범위를 정할 때

## Three Layers

| Layer | 위치 | 의미 |
|---|---|---|
| Source policy | `cookbooks/` | harness-helm source repository의 설계 기록, 정책 배경, 결정 이유 |
| Canonical runtime guideline | `docs/40_knowledge/conventions/guidelines/` | target project에서도 장기 기준으로 읽는 운영 지침 |
| Compact runtime snapshot | `.claude/.codex/skills/harness-helm/references/` | agent가 실행 중 빠르게 읽는 압축 fallback |

`.harness-helm/`은 문서 계층이 아니라 runtime implementation 계층이다. Script, schema, cartridge mapping, run-local template처럼 실행에 필요한 구현물을 둔다.

## source_references

`source_references`는 runtime dependency가 아니다.

이 harness-helm source repository 안에서는 docs guideline이 어떤 cookbook 정책에서 파생됐는지 추적하기 위해 `source_references`에 `cookbooks/**` 경로를 둘 수 있다. 하지만 신규 target project에는 `cookbooks/`가 없으므로, installed runtime은 `source_references`를 필수 읽기 순서나 필수 검증 근거로 삼지 않는다.

Target project에 docs guideline을 설치할 때는 `source_references`를 제거하거나, 남겨 두더라도 unresolved source trace로만 취급한다. Agent가 실제 runtime 판단에 사용하는 문서는 `related`, `docs/40_knowledge/**`, `.harness-helm/`, 그리고 skill `references/`다.

## Docs Guideline으로 옮기는 기준

다음 중 하나 이상에 해당하면 cookbook 내용은 docs guideline 후보가 된다.

- target project에도 같은 판단이 반복해서 필요하다.
- 사용자가 직접 찾아 읽어야 하는 운영 절차다.
- h2 command의 routing, approval, normalization, override 방식에 영향을 준다.
- `cookbooks/`가 없는 설치 환경에서도 유지되어야 한다.
- 일회성 구현 기록이 아니라 장기 convention으로 재사용된다.

Docs guideline은 충분히 자세해야 한다. 사용자가 “왜 이렇게 해야 하는지”, “어떤 순서로 해야 하는지”, “무엇을 하지 말아야 하는지”를 알 수 있어야 한다.

## Skill Reference Snapshot으로 옮기는 기준

Docs guideline 중에서도 다음 조건을 만족하면 `.claude/.codex` skill `references/` snapshot을 만든다.

- agent가 h2 command 실행 중 자주 확인해야 한다.
- docs guideline이 없거나 너무 무거운 상황에서도 fallback이 필요하다.
- Claude Code와 Codex가 같은 결정을 내려야 한다.
- command semantics, routing, approval, upstream override, output normalization처럼 drift가 생기면 위험하다.
- 전체 설명보다 rule, priority, avoid, verification만 빠르게 읽는 편이 안전하다.

Snapshot은 원문을 축약한다. 긴 배경, 역사적 맥락, 세부 예시는 docs guideline에 남기고, snapshot에는 runtime 판단에 필요한 최소 규칙을 둔다.

## Snapshot Header

Docs guideline에서 파생된 snapshot은 첫머리에 canonical guideline 경로와 mapping authority를 함께 적는다.

```text
Compact runtime snapshot of `docs/40_knowledge/conventions/guidelines/h2-{topic}.md`.
Mapping authority: `docs/40_knowledge/conventions/guidelines/harness-helm/runtime-reference-selection.md`.
```

Cookbook 또는 runtime evidence에서 직접 파생된 snapshot은 `Mapping authority`를 억지로 붙이지 않는다. 대신 source cookbook, fixture, parity evidence, cartridge mapping 같은 derivation trace를 명시한다.

`reference-validate --strict`는 guideline-derived snapshot으로 분류된 `canonical-promotion-flow.md`, `specs-vs-decisions.md`, `provider-surface-selection-and-override.md`의 canonical guideline path와 mapping authority path를 검증한다.

## Snapshot으로 만들지 않는 것

다음은 보통 snapshot 대상이 아니다.

- 완료된 구현 기록
- historical source나 GitHub issue trace
- 긴 배경 설명과 설계 논의
- target runtime 판단에 직접 쓰이지 않는 source repository 내부 세부사항
- 사용자가 필요할 때 docs에서 읽으면 충분한 설명
- `.harness-helm/h2-cartridge.yml`, script, schema가 이미 기준인 구현 값의 중복 사본

## 현재 Mapping

현재 공식 기준 지침과 compact snapshot의 대표 mapping은 다음과 같다.

| Canonical guideline | Runtime snapshot |
|---|---|
| `docs/40_knowledge/conventions/guidelines/harness-helm/canonical-promotion-flow.md` | `references/canonical-promotion-flow.md` |
| `docs/40_knowledge/conventions/guidelines/harness-helm/specs-vs-decisions.md` | `references/specs-vs-decisions.md` |
| `docs/40_knowledge/conventions/guidelines/harness-helm/provider-surface-selection-and-override.md` | `references/provider-surface-selection-and-override.md` |

`runtime-reference-selection.md` itself is a meta guideline for deciding snapshot scope. It stays as a docs guideline and is not duplicated as a bundled runtime snapshot.

`references/`는 Claude Code와 Codex 양쪽에 같은 의미로 존재해야 한다.

```text
.claude/skills/harness-helm/references/{topic}.md
.codex/skills/harness-helm/references/{topic}.md
```

## Sync Rule

동기화 우선순위는 다음과 같다.

1. Cookbook 정책이 바뀌면 대응 docs guideline을 확인한다.
2. Docs guideline이 바뀌면 대응 `.claude/.codex` snapshot을 확인한다.
3. Snapshot 첫머리에 공식 기준 지침 경로와 mapping 기준 정의 위치를 적는다.
4. Snapshot과 docs guideline이 충돌하면 docs guideline을 우선한다.
5. Mapping 기준 정의 위치는 이 문서(`docs/40_knowledge/conventions/guidelines/harness-helm/runtime-reference-selection.md`)에 둔다.
6. Cookbook-derived snapshot은 source cookbook 또는 runtime evidence trace를 적는다.

Runtime snapshot은 영어로 작성한다. Claude/Codex parity와 compact loading을 맞추기 위한 선택이다. Docs guideline은 한국어 작성자와 운영자가 읽기 쉽게 한국어로 작성한다.

## Avoid

다음을 하지 않는다.

- `cookbooks/` 전체를 target project runtime read order에 넣는다.
- Snapshot을 공식 기준 원본으로 취급한다.
- Docs guideline을 바꾸고 skill snapshot을 방치한다.
- Claude snapshot과 Codex snapshot의 의미를 다르게 둔다.
- Script/schema/adapter가 기준인 값을 snapshot에 장황하게 중복한다.

## Verification

변경 후 확인할 것:

- `docs/40_knowledge/conventions/guidelines/`에 canonical runtime guideline이 있다.
- 필요한 경우 `.claude/.codex` 양쪽에 같은 의미의 snapshot이 있다.
- guideline-derived snapshot은 canonical guideline path와 mapping authority path를 담고 있다.
- `SKILL.md`의 bundled runtime references 목록이 snapshot을 인지한다.
- 이 문서의 Runtime Snapshot Reference mapping이 최신이다.
- `reference-validate --strict`와 `kb-lint --strict`가 통과한다.
