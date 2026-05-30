---
schema_version: 1
id: LEARN-20260530-001
type: learning
status: pending
owner: 장태욱
security: internal
confidence: medium
related:
  - docs/02_design/h2-plugin-claude-code.md
  - docs/04_report/h2-plugin-claude-code.md
module:
  - workflow
tags:
  - claude-code
  - plugin
  - distribution
  - guard
human_verified_by: 장태욱
---

# Learning: Claude Code plugin/target command collision은 발생 자체를 제거하라

## Context

Claude Code plugin은 `commands/<namespace>/<name>.md` 형태로 user scope 명령을 노출한다. harness-helm처럼 plugin install이 동시에 target project에 같은 namespace의 명령(`.claude/commands/<namespace>/<name>.md`)을 설치하는 모델이면 한 명령이 두 곳에 동시에 존재하게 된다. Claude Code의 plugin vs project scope precedence rule은 명문화되지 않았고 실측도 비용이 큰 시점에서, 가장 안전한 해결은 collision 자체를 만들지 않는 것이다.

## Learning

plugin scope에는 first-run command 하나만 ship하고, 다른 모든 namespace 명령은 target install 단계에서 target 측 `.claude/commands/<namespace>/*.md`에 직접 배치한다. plugin이 ship하는 first-run command는 `harness.py install` 같은 기존 설치 계약을 호출해 target에 명령 파일을 펼치고, guard preamble(있다면)은 target 측 파일에 build 단계에서 주입한다. 이렇게 하면:

- plugin scope와 project scope가 동일 명령을 동시 노출하지 않으므로 precedence rule에 의존하지 않는다
- plugin update가 plugin cache만 갱신하고, target 측 명령은 사용자의 명시적 재실행이 있어야 갱신되어 mutation 동의 모델이 일관된다
- guard 신호도 target 측 install-manifest 같은 per-target source-of-truth만 참조하면 multi-target 환경에서 false-pass가 발생하지 않는다 (LEARN-20260530-002 참조)

## Evidence

- tests: `.harness-helm/runs/h2-plugin-claude-code/20260530-001146-h2-test/test.md` smoke #3·#4·#7·#9
- human_verified_by: 장태욱

## Apply When

- Claude Code plugin이 target project 파일도 함께 mutate해야 하는 경우
- plugin과 target에 같은 namespace의 명령이 동시에 존재할 가능성이 있는 경우
- plugin install이 user home cache 변경에 그치고 target mutation은 별도 consent 흐름이 필요한 경우

## Do Not Apply When

- plugin이 target project 파일을 전혀 변경하지 않는 단순 user-scope plugin
- plugin과 target 명령의 namespace가 의도적으로 분리되어 collision 가능성이 0인 경우
- 두 surface에 같은 명령을 두는 것이 의도된 redundancy 패턴인 경우 (drift 추적 비용을 받아들일 수 있는 경우)

## References

- design §2 (Plugin Package Layout) / §7 (h2 Command Guard) — 옵션 A 채택 근거
- docs/04_report/h2-plugin-claude-code.md — Promotion Candidates (40_knowledge/learnings)
- ce-doc-review round-1의 P0 finding 두 건 (plugin/target collision + multi-target false-pass)
