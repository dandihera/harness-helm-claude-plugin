# 0302 Skill Suite Reference

harness-helm skill suite의 압축 runtime snapshot입니다.

## 규칙

`harness-helm`은 h2 workflow semantics를 소유하는 canonical skill입니다. `h2`는 canonical skill에 위임하는 짧은 alias surface입니다.

## 책임

- `harness-helm`: 공통 h2 command semantics, output contract, routing, staging, boundary.
- `h2`: `$h2 ...` 또는 slash command entrypoint를 위한 짧은 user-facing alias.
- Runtime references: command semantics, adapter, upstream mapping, parity, operational guideline을 위한 compact snapshot.
- `.harness-helm/h2-cartridge.yml`: 설치되어 있을 때 provider, surface, fallback label, routing target, registry의 기준.

## Required h2 Commands

`h2-context`, `h2-plan`, `h2-design`, `h2-analysis`, `h2-build`, `h2-test`, `h2-review`, `h2-report`, `h2-compound`, `h2-archive`, `h2-ops`, `h2-cartridge`.

## Boundaries

- Alias skill은 workflow semantics를 재정의하지 않습니다.
- Agent-specific wording은 허용되지만 output meaning과 routing은 동등해야 합니다.
- Runtime references는 compact해야 하며 canonical docs를 대체하지 않습니다.
- Installed target project는 `cookbooks/`를 필요로 하지 않습니다.

## Minimal Runtime Shape

```text
.codex/skills/harness-helm/SKILL.md
.codex/skills/h2/SKILL.md
.codex/skills/harness-helm/references/

.claude/skills/harness-helm/SKILL.md
.claude/commands/h2/*.md
.claude/skills/harness-helm/references/
```
