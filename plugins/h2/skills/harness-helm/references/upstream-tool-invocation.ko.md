# 0601 Upstream Tool Invocation Reference

Upstream provider, surface, fallback, routing behavior의 압축 runtime snapshot입니다.

## 규칙

`.harness-helm/h2-cartridge.yml`은 설치된 provider, surface, fallback label, routing target, alternatives, external tool registry 값의 기준입니다.

Target project에 cartridge file이 없으면 이 reference를 compact runtime mapping으로 사용하고, cartridge file을 사용할 수 없었다고 기록합니다.

## Invocation Recording

- Actual upstream invocation: `actual:<provider>:<surface>`.
- Fallback checklist 또는 recorder mode: `verified-fallback:<fallback_label>`.
- Missing tool, skipped check, unverified claim: `verification.not_verified`.
- Blocked prerequisite: `verification.required`.

## Command Routing

Upstream tool은 input quality에 영향을 줄 수 있지만 h2 routing은 command semantics에 의해 고정됩니다.

- `h2-plan`은 `docs/01_plan/{feature}.md`로 route합니다.
- `h2-design`은 `docs/02_design/{feature}.md`로 route합니다.
- `h2-review`는 `docs/03_review/{type}/{feature}.md`로 route합니다.
- `h2-report`는 `docs/04_report/{feature}.md`로 route합니다.
- `h2-compound`는 검증 후 low-risk knowledge를 작성하고, canonical write 전에는 governed promotion candidate를 staging합니다.
- `h2-archive`는 harness archive flow를 사용합니다.

## Drift Control

0601, 0603, 0604, 0605 guidance가 바뀌면 필요에 따라 adapter, upstream references, runtime parity snapshot, matching docs guideline을 갱신합니다.

## 피해야 할 것

- Fallback checklist output을 actual upstream invocation이라고 기록하지 않습니다.
- 다른 provider를 사용했다는 이유로 routing을 바꾸지 않습니다.
- Adapter 값을 여러 기준 위치에 중복하지 않습니다.
