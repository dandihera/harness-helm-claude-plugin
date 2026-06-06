---
name: h2
description: canonical harness-helm skill semantics에 위임해 $h2 context, $h2 plan, $h2 design, $h2 autorun, $h2 rewind, $h2 analysis, $h2 build, $h2 test, $h2 review, $h2 report, $h2 compound, $h2 harvest, $h2 archive, $h2 ops, $h2 cartridge를 처리하는 짧은 alias skill.
---

# h2

사용자에게 보이는 짧은 alias이며, canonical Codex skill은 아래 경로에 있다.

```text
.codex/skills/harness-helm/SKILL.md
```

상세 reference snapshot은 이 alias에서 직접 로드하지 않는다. issue 수준의 context가 필요하면 canonical `harness-helm` skill과 그 `references/` 디렉터리를 사용한다.

이 skill은 독립적인 workflow 규칙을 정의하지 않는다. 간결한 `$h2 ...` 호출을 대응하는 `harness-helm` command semantics로 라우팅한다.

Codex runtime guidance는 root `AGENTS.md`에서 시작한 뒤, h2 전용 semantics를 `.codex/skills/harness-helm/SKILL.md`와 그 bundled `references/`로 위임한다.

## Alias Mapping

| User invocation | Canonical semantics |
|---|---|
| `$h2 context ...` | `harness-helm` `h2-context` |
| `$h2 plan ...` | `harness-helm` `h2-plan` |
| `$h2 design ...` | `harness-helm` `h2-design` |
| `$h2 autorun ...` | `harness-helm` `h2-autorun` |
| `$h2 rewind ...` | `harness-helm` `h2-rewind` |
| `$h2 analysis ...` | `harness-helm` `h2-analysis` |
| `$h2 build ...` | `harness-helm` `h2-build` |
| `$h2 test ...` | `harness-helm` `h2-test` |
| `$h2 review ...` | `harness-helm` `h2-review` |
| `$h2 report ...` | `harness-helm` `h2-report` |
| `$h2 compound ...` | `harness-helm` `h2-compound` |
| `$h2 harvest ...` | `harness-helm` `h2-harvest` |
| `$h2 archive ...` | `harness-helm` `h2-archive` |
| `$h2 ops ...` | `harness-helm` `h2-ops` |
| `$h2 cartridge ...` | `harness-helm` `h2-cartridge` |

## Rules

- `$h2 context`, `$h2 plan`, `$h2 design`, `$h2 autorun`, `$h2 rewind`, `$h2 analysis`, `$h2 build`, `$h2 test`, `$h2 review`, `$h2 report`, `$h2 compound`, `$h2 harvest`, `$h2 archive`, `$h2 ops`, `$h2 cartridge`를 대응하는 canonical `h2-*` command id로 취급한다.
- `harness-helm`의 공통 `context_pack`, `artifacts`, `routing`, `verification`, `next` output 의미를 보존한다.
- `harness-helm` workflow semantics를 중복 정의하거나 override하지 않는다.
- provider, surface, fallback label, routing target 값은 canonical skill을 통해 `.harness-helm/h2-cartridge.yml`을 사용한다.
- 이 alias가 `.codex/skills/harness-helm/SKILL.md`와 충돌하면 canonical `harness-helm` skill이 우선한다.
- 먼저 `AGENTS.md`를 따른다. 없으면 project guidance를 따른다.
