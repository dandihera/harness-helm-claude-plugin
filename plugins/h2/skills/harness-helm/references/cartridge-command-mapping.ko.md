# Cartridge Command Mapping Reference

Compatibility marker: 0601 Upstream Tool Invocation.

h2 invocation recording, fallback handling, routing invariant의 압축 runtime snapshot입니다. Cartridge 값은 `.harness-helm/h2-cartridge.yml`에만 정의하고 이 reference에는 중복하지 않습니다.

## 규칙

`.harness-helm/h2-cartridge.yml`은 설치된 provider, surface, fallback label, routing target, output language, alternatives, external tool registry 값의 기준입니다.

Target project에 cartridge file이 없으면 이 reference는 invocation recording, fallback handling, routing invariant에만 사용합니다. cartridge file을 사용할 수 없었다고 기록합니다.

설치된 provider, surface, fallback label, routing target, output language, alternatives, external tool registry 값은 `.harness-helm/h2-cartridge.yml`을 직접 읽어 확인합니다.

## Invocation Recording

- Actual upstream invocation: `actual:<provider>:<surface>`.
- Fallback checklist 또는 recorder mode: `verified-fallback:<fallback_label>`.
- Missing tool, skipped check, unverified claim: `verification.not_verified`.
- Blocked prerequisite: `verification.required`.

## Command Routing

Upstream tool은 input quality에 영향을 줄 수 있지만 h2 routing은 command semantics에 의해 고정됩니다.

- `h2-plan`은 `docs/01_plan/{feature}.md`로 route합니다.
- `h2-design`은 `docs/02_design/{feature}.md`로 route합니다.
- `h2-autorun`은 `.harness-helm/runs/{feature}/{run-id}/autorun-summary.md`로 route합니다.
- `h2-rewind`는 `.harness-helm/runs/{feature}/{run-id}/snapshots/{step}/restore.md`로 route합니다.
- `h2-review`는 `docs/03_review/{type}/{feature}.md`로 route합니다.
- `h2-report`는 `docs/04_report/{feature}.md`로 route합니다.
- `h2-compound`는 검증 후 low-risk knowledge를 작성하고, canonical write 전에는 governed promotion candidate를 staging합니다.
- `h2-archive`는 harness archive flow를 사용합니다.

## Drift Control

0601, 0603, 0604, 0605 guidance가 바뀌면 필요에 따라 adapter, upstream references, runtime parity snapshot, matching docs guideline을 갱신합니다.

## 피해야 할 것

- Fallback checklist output을 actual upstream invocation이라고 기록하지 않습니다.
- 다른 provider를 사용했다는 이유로 routing을 바꾸지 않습니다.
- Cartridge 값을 bundled reference에 중복하지 않습니다.
