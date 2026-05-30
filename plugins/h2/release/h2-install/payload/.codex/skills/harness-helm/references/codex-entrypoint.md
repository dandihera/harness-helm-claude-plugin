# Codex Entrypoint Smoke

This fixture records the Codex side of runtime parity checks.

## Expected Surface

Codex uses the `$h2 ...` alias that delegates to `.codex/skills/harness-helm/SKILL.md`.

Example:

```text
$h2 plan harness-helm-review-followups
```

## Expected Meaning

The command should resolve to `h2-plan`, preserve the common h2 output fields, and route plan artifacts to `docs/01_plan/{feature}.md`.

## Parity Requirement

The Codex result must be semantically equivalent to the Claude Code `/h2:plan` result even though the invocation surface differs.
