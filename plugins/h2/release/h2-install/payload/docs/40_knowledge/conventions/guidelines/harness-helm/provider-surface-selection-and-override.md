---
schema_version: 1
id: "CONV-20260525-004"
type: convention
status: stable
owner: tw.jang
security: internal
confidence: medium
target_runtime: included
related:
  - docs/40_knowledge/conventions/guidelines/harness-helm/canonical-promotion-flow.md
  - docs/40_knowledge/conventions/guidelines/harness-helm/specs-vs-decisions.md
source_references:
  - cookbooks/0600-cartridge/0605-provider-surface-selection-and-override.md
module:
  - docs
  - workflow
tags:
  - harness-helm
  - h2-cartridge
  - provider
  - surface
  - gstack
  - superpowers
  - compound-engineering
---

# Convention: h2 provider/surface selection and override

## Rule

기본 provider/surface 선택의 기준은 `.harness-helm/h2-cartridge.yml`이다.

개별 run에서는 사용자가 명시한 upstream override를 허용할 수 있다. 다만 run-level override는 이번 실행의 선택일 뿐이며, `.harness-helm/h2-cartridge.yml`의 기본 mapping을 바꾼 것으로 기록하지 않는다.

영구 변경은 cartridge mapping, 관련 cookbook, runtime reference snapshot을 함께 갱신해야 한다.

## Applies To

- `$h2 plan`, `$h2 design`, `$h2 build` 같은 h2 command에서 기본 upstream과 다른 provider/surface를 쓰고 싶을 때
- 사용자가 “이번 plan은 gstack 대신 superpowers로 작성해줘”처럼 run-level override를 요청했을 때
- cartridge 기본 provider/surface를 영구 변경하려 할 때
- upstream raw output을 h2 output contract로 정규화해야 할 때

## Selection Priority

upstream surface 선택은 아래 순서로 판단한다.

1. 사용자가 명시한 provider/surface
2. `.harness-helm/h2-cartridge.yml`의 command primary provider/surface
3. `.harness-helm/h2-cartridge.yml`의 command alternatives
4. runtime reference 또는 upstream surface map의 secondary 후보
5. upstream tool registry에 등록된 같은 목적의 surface
6. cartridge fallback checklist

사용자 명시가 있어도 command semantics와 routing을 깨면 사용할 수 없다. 예를 들어 `h2-plan`에서 superpowers `writing-plans`를 사용할 수는 있지만, 결과는 여전히 `h2-plan` output contract와 `docs/01_plan/{feature}.md` routing을 따라야 한다.

## Run-level Override

run-level override는 한 번의 `h2-*` 실행에서 기본 provider/surface 대신 다른 후보를 쓰는 방식이다.

사용자는 자연어 또는 key-value 형태로 override를 명시할 수 있다.

```text
$h2 plan {feature} upstream=superpowers surface=writing-plans
```

```text
$h2 plan {feature}
이번 plan은 gstack 대신 superpowers writing-plans 기준으로 작성해줘.
```

Claude Code slash command에서도 같은 의미로 표현한다.

```text
/h2:plan {feature} upstream=superpowers surface=writing-plans
```

처리 절차:

1. command id를 확정한다.
   - 예: `$h2 plan` -> `h2-plan`
2. cartridge 기본 mapping을 확인한다.
3. 요청한 override가 cartridge alternatives에 있는지 확인한다.
4. alternatives에 없으면 runtime reference, upstream surface map, tool registry에서 같은 목적 surface인지 확인한다.
5. surface가 설치되어 있거나 runtime에서 사용할 수 있는지 확인한다.
6. upstream output을 command별 h2 template으로 정규화한다.
7. h2 output에 override 사실을 기록한다.
8. actual invocation인지 fallback/checklist인지 `verification`에 남긴다.

## h2-plan Example

현재 `h2-plan` 기본 upstream이 gstack이고, 이번 run에서만 superpowers `writing-plans`를 쓰고 싶다면 다음처럼 요청한다.

```text
$h2 plan hera-excel-upload-improvement upstream=superpowers surface=writing-plans
```

이때 산출물은 여전히 `h2-plan` 산출물이다.

```text
docs/01_plan/hera-excel-upload-improvement.md
```

superpowers output은 그대로 저장하지 않는다. h2 plan template의 goal, scope, non-goals, done criteria, risks, verification 기준으로 다시 작성한다.

권장 기록:

```yaml
command: h2-plan
feature: feature-slug
status: updated
context_pack:
  assumptions:
    - run-level upstream override requested: superpowers writing-plans instead of cartridge primary.
artifacts:
  updated:
    - docs/01_plan/feature-slug.md
routing:
  target_docs:
    - docs/01_plan/feature-slug.md
verification:
  completed:
    - actual:superpowers:writing-plans
next:
  recommended_h2_step: h2-design
```

actual invocation이 아니라 checklist로만 반영했다면 다음처럼 기록한다.

```yaml
verification:
  completed:
    - verified-fallback:superpowers-workflow-checklist
  not_verified:
    - superpowers writing-plans was requested but not actually invoked in this runtime.
```

## Permanent Mapping Change

permanent mapping change는 특정 command의 기본 provider/surface를 바꾸는 작업이다.

예를 들어 앞으로 `h2-plan`의 기본을 gstack `gstack-autoplan`에서 superpowers `writing-plans`로 바꾸려면 permanent mapping change다.

영구 변경은 다음 조건을 만족할 때만 진행한다.

- 여러 run에서 같은 override가 반복된다.
- 현재 primary보다 다른 provider가 command semantics에 더 잘 맞는다는 합의가 있다.
- Tech Lead가 default behavior 변경을 승인했다.
- Claude Code/Codex 양쪽 runtime parity를 유지할 수 있다.

변경 절차:

1. 변경 이유를 정리한다.
2. `.harness-helm/h2-cartridge.yml`을 수정한다.
3. `fallback_label`을 새 primary provider에 맞게 검토한다.
4. `alternatives`에 기존 primary를 보존할지 결정한다.
5. command mapping reference를 갱신한다 — runtime reference는 `references/cartridge-command-mapping.md`, source repository는 `0601 Cartridge Command Mapping` cookbook이 기준.
6. upstream surface recommendation reference를 갱신한다 — runtime reference는 `references/cartridge-surface-map.md`, source repository는 `0603 Cartridge Surface Map` cookbook이 기준.
7. runtime parity snapshot을 필요에 따라 갱신한다 — runtime reference는 `references/runtime-parity.md`.
8. cartridge와 reference 검증을 실행한다.
9. h2 output 또는 review log에 변경 사실과 검증 결과를 기록한다.

주의: cartridge만 수정하고 runtime reference를 방치하면 기준 drift가 생긴다.

## Normalization Rule

upstream raw output은 canonical h2 artifact가 아니다.

gstack, superpowers, compound-engineering 결과는 cartridge가 h2 output contract와 command별 template으로 정규화한 뒤 공식 문서 또는 staging 산출물로 기록한다.

예를 들어 superpowers `writing-plans`가 세부 implementation plan을 만들었더라도, `h2-plan` 결과는 다음을 채워야 한다.

```text
goal
scope
non-goals
done criteria
risks
verification
next.recommended_h2_step
```

promotion candidate가 생기면 바로 canonical 문서로 만들지 않고 `docs/40_knowledge/conventions/guidelines/harness-helm/canonical-promotion-flow.md`의 승인 절차를 따른다.

## Avoid

다음을 하지 않는다.

- 사용자 override를 이유로 command routing을 바꾼다.
- upstream raw output을 h2 plan/design/report 문서로 그대로 저장한다.
- run-level override를 `.harness-helm/h2-cartridge.yml`의 기본값처럼 기록한다.
- permanent mapping change를 cartridge만 수정하고 reference snapshot은 방치한다.
- 설치되지 않았거나 호출되지 않은 upstream surface를 `actual:<provider>:<surface>`로 기록한다.
- fallback checklist 실행을 actual invocation으로 표기한다.

## Verification

run-level override 검증:

```bash
.harness-helm/scripts/harness cartridge-validate --strict
```

permanent mapping change 검증:

```bash
.harness-helm/scripts/harness cartridge-validate --strict
.harness-helm/scripts/harness reference-validate --strict
.harness-helm/scripts/harness kb-lint --strict
```

확인할 것:

- cartridge의 `commands.*`가 `provider`, `surface`, `fallback_label`, `routing_target`을 가진다.
- override surface가 cartridge alternatives, runtime reference, upstream surface map, tool registry 중 하나에서 근거를 가진다.
- upstream raw output이 h2 output contract로 정규화되어 있다.
- run-level override는 cartridge 기준 변경처럼 기록되지 않는다.
- permanent mapping change는 cartridge와 bundled reference가 drift되지 않는다.
