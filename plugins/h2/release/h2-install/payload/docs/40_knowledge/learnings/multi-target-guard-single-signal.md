---
schema_version: 1
id: LEARN-20260530-002
type: learning
status: pending
owner: 장태욱
security: internal
confidence: medium
related:
  - docs/02_design/h2-plugin-claude-code.md
  - docs/40_knowledge/learnings/plugin-target-command-collision-single-scope.md
module:
  - workflow
tags:
  - guard
  - state
  - multi-target
human_verified_by: 장태욱
---

# Learning: multi-target 환경의 guard는 per-target source-of-truth 단독으로 좁혀라

## Context

Plugin이 사용자 home에 단일 진단 결과 파일(`~/.claude/plugins/data/<plugin>/<key>/latest.json` 등)을 남기고 다른 명령들이 이 파일을 보조 신호로 쓰면, 사용자가 여러 project에서 plugin을 쓸 때 false-pass가 발생한다. project A에서 first-run 진단을 한 번 통과시키면 project B에서도 진단 결과 파일이 발견되어 명령이 차단되지 않고 도중에 깨지거나 잘못된 상태를 보여주는 실패 모드다.

## Learning

guard 판정 신호는 per-target source-of-truth 하나만 사용한다. harness-helm에서는 `<target>/.harness-helm/install-manifest.json`이 그 역할을 맡고, 진단 결과 파일은 같은 target 디렉터리(`<target>/.harness-helm/doctor/latest.json`) 또는 log 용도로만 남기되 guard 흐름에는 절대 참조하지 않는다. guard preamble을 작성할 때도 본문에서 명시적으로 per-target 경로만 확인하도록 강제한다.

핵심 규칙:
- guard signal = per-target source-of-truth (install-manifest, lockfile, marker 등)
- 진단/log/cache 파일은 plugin data dir 또는 per-target dir에 자유롭게 두되 guard 판정에서는 제외
- preamble·wrapper 본문에서 "이 파일을 확인한다"가 보이도록 명시 (모델·코드 reviewer 모두 추적 가능)

## Evidence

- tests: `.harness-helm/runs/h2-plugin-claude-code/20260530-001146-h2-test/test.md` smoke #9 (multi-target false-pass 회귀 정적 검증)
- human_verified_by: 장태욱

## Apply When

- 하나의 plugin이 사용자 home에 작성한 파일과 target project에 작성한 파일을 둘 다 만들고, target 측 명령이 양쪽 모두를 참조할 가능성이 있는 경우
- 사용자가 같은 plugin을 다수의 target project에서 운영하는 경우
- guard·gate·prerequisite check가 명령 실행 흐름에 포함되는 경우

## Do Not Apply When

- plugin이 target project를 mutate하지 않거나 target이 하나뿐인 single-project tool인 경우
- guard 자체가 user-scope 전역 정책이고 per-target 의미가 없는 경우 (예: 사용자 license check)
- per-target source-of-truth가 만들어지기 전에 실행되어야 하는 부트스트랩 명령 (이 경우 guard 자체에서 제외해야 한다)

## References

- design §7 (h2 Command Guard 단일 source-of-truth) / §8 (State Model)
- LEARN-20260530-001 (plugin/target command collision 옵션 A 패턴)
- ce-doc-review round-1 P0 finding (doctor 결과 파일이 전역 단일이라 false-pass)
