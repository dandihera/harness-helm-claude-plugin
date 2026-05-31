# Provider Surface Selection and Override Reference

`docs/40_knowledge/conventions/guidelines/harness-helm/provider-surface-selection-and-override.md`의 압축 runtime snapshot입니다.

전체 canonical 절차는 `docs/40_knowledge/conventions/guidelines/harness-helm/provider-surface-selection-and-override.md`를 확인합니다.

Mapping 기준 정의 위치: `docs/40_knowledge/conventions/guidelines/harness-helm/runtime-reference-selection.md`.

## 규칙

Default upstream provider/surface 선택은 `.harness-helm/h2-cartridge.yml`에 정의됩니다.

사용자가 다른 provider/surface를 명시적으로 요청하면 run-level override를 허용합니다. 이는 현재 run만 바꾸며 adapter default를 바꾸지 않습니다.

Permanent mapping change는 adapter, references, parity snapshot을 함께 갱신해야 합니다.

## Selection Priority

1. User-specified provider/surface
2. `.harness-helm/h2-cartridge.yml` command primary provider/surface
3. `.harness-helm/h2-cartridge.yml` command alternatives
4. Bundled runtime references 또는 upstream surface map secondary candidates
5. 같은 목적의 tool registry surface
6. Adapter fallback checklist

User override는 command semantics나 routing을 바꾸면 안 됩니다.

## Run-Level Override

허용 입력 형식:

```text
$h2 plan {feature} upstream=superpowers surface=writing-plans
```

```text
이번 plan은 gstack 대신 superpowers writing-plans 기준으로 작성해줘.
```

처리 순서:

1. Command id를 확정합니다. 예: `$h2 plan` -> `h2-plan`.
2. Adapter primary mapping을 읽습니다.
3. 요청 surface가 cartridge alternatives에 있는지 확인합니다.
4. 없으면 bundled references와 registry에서 같은 목적 surface인지 확인합니다.
5. Runtime availability를 확인합니다.
6. Upstream output을 command h2 template으로 정규화합니다.
7. Override 사실을 h2 output에 기록합니다.
8. Actual invocation 또는 fallback을 `verification`에 기록합니다.

## Permanent Mapping Change

반복 override와 Tech Lead 승인이 default 변경을 정당화할 때만 사용합니다.

절차:

1. Command, old provider/surface, new provider/surface, run-level override가 아닌 이유를 설명합니다.
2. `.harness-helm/h2-cartridge.yml`을 수정합니다.
3. `fallback_label`과 `alternatives`를 다시 확인합니다.
4. Upstream invocation과 surface map references를 갱신합니다.
5. 필요하면 runtime parity snapshot을 갱신합니다.
6. Adapter/reference validation을 실행합니다.

## 피해야 할 것

- Override 때문에 command routing을 바꾸지 않습니다.
- Raw upstream output을 h2 plan/design/report로 저장하지 않습니다.
- Run-level override를 adapter default로 기록하지 않습니다.
- Fallback checklist를 actual invocation으로 표시하지 않습니다.
