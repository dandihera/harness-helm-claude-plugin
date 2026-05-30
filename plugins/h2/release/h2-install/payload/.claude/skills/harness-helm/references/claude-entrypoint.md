# Claude Entrypoint Fixture

This fixture records the Claude Code side of runtime parity checks.

## Expected Surface

Claude Code uses `/h2:{command}` slash commands that delegate to `.claude/skills/harness-helm/SKILL.md`.

Example:

```text
/h2:context feature=harness-helm-review-followups task="review follow-up context"
```

## Expected Meaning

The command should resolve to `h2-context`, preserve the common h2 output fields, and route staging artifacts through `.harness-helm/runs/{feature}/{run-id}/`.

## Parity Requirement

The Claude Code result must be semantically equivalent to the Codex `$h2 context` result even though the invocation surface differs.
