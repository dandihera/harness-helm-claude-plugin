# Claude Entrypoint Fixture

이 fixture는 runtime parity check의 Claude Code 측 기록입니다.

## Expected Surface

Claude Code는 `.claude/skills/harness-helm/SKILL.md`에 위임하는 `/h2:{command}` slash command를 사용합니다.

예시:

```text
/h2:context feature=harness-helm-review-followups task="review follow-up context"
```

## Expected Meaning

Command는 `h2-context`로 해석되어야 하고, 공통 h2 output field를 보존하며, staging artifact를 `.harness-helm/runs/{feature}/{run-id}/`로 route해야 합니다.

## Parity Requirement

Claude Code 결과는 invocation surface가 달라도 Codex `$h2 context` 결과와 의미상 동등해야 합니다.
