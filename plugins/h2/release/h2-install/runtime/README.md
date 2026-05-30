# runtime/

Claude Code, Codex, 인접 agent 도구를 수동 설치할 때 사용하는 asset이다.

`h2-install.sh` installer는 `runtime/` 아래 파일을 자동으로 복사하지 않는다. 이 파일들은 harness-helm runtime adapter를 local agent home directory에 설치할 때 참고하는 안내 자료다.

## Claude Code

Claude Code에서 `h2-*` skill을 repository별이 아니라 global scope로 노출하려면 다음 경로를 복사한다.

- `claude/skills/harness-helm/` → `~/.claude/skills/harness-helm/`
- `claude/commands/h2/` → `~/.claude/commands/h2/`

`.claude/`를 통한 repository별 설치는 standard payload로 이미 자동 수행되며, 이 방식을 권장한다. 특정 repository 밖에서도 skill이 필요할 때만 `runtime/claude/**`를 사용한다.

## Codex

Codex `h2` skill을 global scope에서 사용하려면 다음 경로를 복사한다.

- `codex/skills/harness-helm/` → `~/.agents/skills/harness-helm/`
- `codex/skills/h2/` → `~/.agents/skills/h2/`

대부분의 project에서는 `.codex/`를 통한 repository별 설치를 권장한다.

## 외부 integration

`harness-helm`은 gstack, superpowers, compound-engineering 또는 다른 agent 도구를 설치하지 않는다. 각 도구의 공식 문서에 따라 별도로 설치한다. 설치 후 harness-helm cartridge(`.harness-helm/h2-cartridge.yml`)가 사용 가능한 upstream tool로 `h2-*` command를 routing한다.
