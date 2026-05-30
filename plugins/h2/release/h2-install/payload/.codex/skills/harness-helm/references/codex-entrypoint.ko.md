# Codex Entrypoint Smoke

이 fixture는 runtime parity check의 Codex 측 기록입니다.

## Expected Surface

Codex는 `.codex/skills/harness-helm/SKILL.md`에 위임하는 `$h2 ...` alias를 사용합니다.

예시:

```text
$h2 plan harness-helm-review-followups
```

## Expected Meaning

Command는 `h2-plan`으로 해석되어야 하고, 공통 h2 output field를 보존하며, plan artifact를 `docs/01_plan/{feature}.md`로 route해야 합니다.

## Parity Requirement

Codex 결과는 invocation surface가 달라도 Claude Code `/h2:plan` 결과와 의미상 동등해야 합니다.
