# Codex Adapter Reference

`0402 Codex Adapter`의 압축 runtime snapshot입니다.

## 규칙

Codex adapter는 `$h2 ...` alias와 `.codex/skills/harness-helm/SKILL.md`를 통해 `h2-*` command surface를 제공합니다.

Core workflow와 Claude Code adapter와 같은 h2 command semantics, output contract, routing, staging, verification rule을 보존해야 합니다.

## `h2-*` command surface

Codex는 다음을 지원해야 합니다.

`h2-context`, `h2-plan`, `h2-design`, `h2-autorun`, `h2-rewind`, `h2-analysis`, `h2-build`, `h2-test`, `h2-review`, `h2-report`, `h2-compound`, `h2-archive`, `h2-ops`, `h2-cartridge`.

## 책임

- `.codex/skills/h2/SKILL.md`는 thin alias입니다.
- `.codex/skills/harness-helm/SKILL.md`가 runtime command guidance를 소유합니다.
- `references/`는 compact runtime snapshot을 저장합니다.
- `.harness-helm/h2-cartridge.yml`은 설치되어 있을 때 provider, surface, fallback, routing, output language, registry 값을 소유합니다.

## Boundaries

- Alias 안에서 core h2 semantics를 재정의하지 않습니다.
- Claude Code, gstack, superpowers, compound-engineering을 재구현하지 않습니다.
- 승인 없이 canonical 10/20/30/40/50 docs를 만들지 않습니다.
- Fallback checklist execution을 actual upstream invocation으로 취급하지 않습니다.
