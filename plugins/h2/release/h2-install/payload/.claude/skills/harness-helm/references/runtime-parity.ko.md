# Runtime Parity Report

Claude Code와 Codex parity를 위한 압축 runtime snapshot입니다.

## 규칙

Claude Code와 Codex는 서로 다른 command surface를 제공하지만, h2 command meaning, output field, routing, staging rule, verification semantics는 같아야 합니다.

## Runtime Surfaces

| Runtime | Entrypoint | Fixture |
|---|---|---|
| Claude Code | `/h2:{command}` slash command | `.claude/skills/harness-helm/references/claude-entrypoint.md` |
| Codex | `$h2 {command}` skill alias | `.codex/skills/harness-helm/references/codex-entrypoint.md` |

## Parity Requirements

- Common input meaning: `command`, `feature`, `task`, optional `source_request`, `references`, `constraints`.
- Common output meaning: `context_pack`, `artifacts`, `routing`, `verification`, `next`.
- Routing은 `.harness-helm/h2-cartridge.yml`이 설치되어 있으면 그 파일과 일치해야 합니다.
- `.harness-helm/h2-cartridge.yml`이 없으면 `references/upstream-tool-invocation.md`를 compact runtime mapping으로 사용합니다.
- Fallback-only check를 actual upstream invocation으로 기록하지 않습니다.

## Upstream Invocation Parity

두 runtime은 h2 command에 대해 같은 provider/surface intent를 사용합니다. Runtime별 문구 차이는 허용하지만 semantic drift는 허용하지 않습니다.

Upstream을 실제 호출했을 때만 `actual:<provider>:<surface>`를 사용합니다. Fallback checklist만 적용했다면 `verified-fallback:<label>`을 사용합니다.
