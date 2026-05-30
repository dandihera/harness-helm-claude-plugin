---
schema_version: 1
id: "LEARN-20260527-001"
type: learning
status: stable
owner: "harness-helm"
security: public
confidence: medium
related: []
source_references:
  - https://github.com/mattpocock/skills
  - https://raw.githubusercontent.com/mattpocock/skills/main/README.md
tags:
  - external-reference
  - agent-skills
  - codex
  - claude-code
---

# 외부 참고자료: Matt Pocock Skills

## Context

이 문서는 Matt Pocock의 `skills` repository를 compact reference note로 보관한다.

이 source repository는 harness-helm의 직접적인 product dependency가 아니며 operational runbook도 아니다. 가치는 비교 참고에 있다. 다른 agent-skill system이 installation, skill organization, setup, engineering failure mode를 어떻게 설명하는지 보여준다.

Source 확인일: 2026-05-27

- Repository: <https://github.com/mattpocock/skills>
- README raw source: <https://raw.githubusercontent.com/mattpocock/skills/main/README.md>
- GitHub contents API 기준 README blob SHA: `2f4a38d7bbb0eeb61da626124a719e420ce7d42f`

## Summary

이 repository는 실제 software engineering 작업을 위한 agent skill 모음을 제시한다. 핵심 positioning은 agent skill이 전체 development process를 소유하기보다 작고, 수정 가능하고, 조합 가능하며, 여러 model에서 사용할 수 있어야 한다는 것이다.

README는 skill을 일반적인 agent failure mode를 기준으로 설명한다.

1. Agent가 사용자의 의도를 제대로 이해하지 못한다.
2. Shared project language가 없어 agent의 설명이 지나치게 장황해진다.
3. Feedback loop가 약해서 생성된 code가 제대로 동작하지 않는다.
4. Agent-assisted development가 entropy를 가속해 codebase가 변경하기 어려워진다.

제안하는 해결책은 skill-driven workflow다.

- implementation 전에 interview 또는 "grilling" skill로 의도를 정렬한다.
- documentation-aware planning을 통해 shared language와 ADR을 갱신한다.
- TDD와 diagnosis loop로 feedback을 강화한다.
- architecture-improvement와 zoom-out skill로 system design을 계속 보이게 유지한다.

## Installation Model

Public README는 `skills.sh` installer를 통한 설치를 설명한다.

```bash
npx skills@latest add mattpocock/skills
```

원하는 skill과 대상 coding agent를 선택한 뒤, setup skill이 issue tracker, triage label, documentation location 같은 repository별 선택 사항을 설정한다.

README는 Claude Code, Codex, 기타 coding agent를 target environment로 명시한다. Repository에는 `.claude-plugin/plugin.json`도 있어 Claude plugin packaging surface가 존재함을 보여준다. 이번 capture에서 repository tree 안에 Codex 전용 plugin manifest는 찾지 못했다. Codex와의 관련성은 installer의 agent-selection model과 skill의 일반적인 agent compatibility에서 나온 것으로 보인다.

## Skill Organization

Repository는 skill을 bucket으로 나눈다.

- `skills/engineering/`: 일상적인 code-work skill
- `skills/productivity/`: 일반 workflow skill
- `skills/misc/`: 가끔 쓰는 utility
- `skills/personal/`: 작성자 개인 환경에 묶인 skill
- `skills/in-progress/`: draft skill
- `skills/deprecated/`: retired skill

Repository guidance는 `engineering`, `productivity`, `misc`에 있는 promoted skill이 top-level README와 `.claude-plugin/plugin.json` 양쪽에 모두 나타나야 한다고 설명한다. Personal, draft, deprecated skill은 양쪽에 포함하지 않는다.

## 원문 Reference 섹션 번역

이 섹션은 원문 README의 `Reference` 섹션을 한국어로 옮긴 것이다. Link target은 원문 repository 기준 상대 경로를 유지한다.

### Engineering

매일 code work에 사용하는 skill이다.

- **[diagnose](https://github.com/mattpocock/skills/blob/main/skills/engineering/diagnose/SKILL.md)**: 까다로운 bug와 performance regression을 위한 disciplined diagnosis loop. Reproduce, minimise, hypothesise, instrument, fix, regression-test 순서로 진행한다.
- **[grill-with-docs](https://github.com/mattpocock/skills/blob/main/skills/engineering/grill-with-docs/SKILL.md)**: 기존 domain model을 기준으로 plan을 압박 검토하고, terminology를 날카롭게 다듬으며, `CONTEXT.md`와 ADR을 inline으로 갱신하는 grilling session.
- **[triage](https://github.com/mattpocock/skills/blob/main/skills/engineering/triage/SKILL.md)**: triage role state machine을 통해 issue를 triage한다.
- **[improve-codebase-architecture](https://github.com/mattpocock/skills/blob/main/skills/engineering/improve-codebase-architecture/SKILL.md)**: `CONTEXT.md`의 domain language와 `docs/adr/`의 decision을 참고해 codebase에서 deepening opportunity를 찾는다.
- **[setup-matt-pocock-skills](https://github.com/mattpocock/skills/blob/main/skills/engineering/setup-matt-pocock-skills/SKILL.md)**: 다른 engineering skill이 사용하는 per-repo config를 만든다. Issue tracker, triage label vocabulary, domain doc layout을 설정하며, `to-issues`, `to-prd`, `triage`, `diagnose`, `tdd`, `improve-codebase-architecture`, `zoom-out` 사용 전에 repository마다 한 번 실행한다.
- **[tdd](https://github.com/mattpocock/skills/blob/main/skills/engineering/tdd/SKILL.md)**: red-green-refactor loop를 사용하는 test-driven development skill. Feature나 bugfix를 vertical slice 단위로 만든다.
- **[to-issues](https://github.com/mattpocock/skills/blob/main/skills/engineering/to-issues/SKILL.md)**: plan, spec, PRD를 vertical slice 기준의 독립 실행 가능한 GitHub issue로 나눈다.
- **[to-prd](https://github.com/mattpocock/skills/blob/main/skills/engineering/to-prd/SKILL.md)**: 현재 conversation context를 PRD로 바꾸고 GitHub issue로 제출한다. 별도 interview 없이 이미 논의한 내용을 종합한다.
- **[zoom-out](https://github.com/mattpocock/skills/blob/main/skills/engineering/zoom-out/SKILL.md)**: 익숙하지 않은 code section에 대해 agent가 더 넓은 context나 higher-level perspective를 설명하게 한다.
- **[prototype](https://github.com/mattpocock/skills/blob/main/skills/engineering/prototype/SKILL.md)**: design을 구체화하기 위한 throwaway prototype을 만든다. State/business-logic 질문을 위한 runnable terminal app이나, 하나의 route에서 toggle 가능한 여러 UI variation을 만들 수 있다.

### Productivity

Code-specific하지 않은 일반 workflow tool이다.

- **[caveman](https://github.com/mattpocock/skills/blob/main/skills/productivity/caveman/SKILL.md)**: filler를 제거해 token usage를 크게 줄이면서 technical accuracy는 유지하는 ultra-compressed communication mode.
- **[grill-me](https://github.com/mattpocock/skills/blob/main/skills/productivity/grill-me/SKILL.md)**: plan이나 design에 대해 decision tree의 모든 branch가 정리될 때까지 집요하게 interview한다.
- **[handoff](https://github.com/mattpocock/skills/blob/main/skills/productivity/handoff/SKILL.md)**: 다른 agent가 작업을 이어갈 수 있도록 현재 conversation을 handoff document로 압축한다.
- **[write-a-skill](https://github.com/mattpocock/skills/blob/main/skills/productivity/write-a-skill/SKILL.md)**: proper structure, progressive disclosure, bundled resource를 갖춘 새 skill을 만든다.

### Misc

자주 쓰지는 않지만 보관해 두는 tool이다.

- **[git-guardrails-claude-code](https://github.com/mattpocock/skills/blob/main/skills/misc/git-guardrails-claude-code/SKILL.md)**: Claude Code hook을 설정해 `push`, `reset --hard`, `clean` 같은 위험한 git command가 실행되기 전에 막는다.
- **[migrate-to-shoehorn](https://github.com/mattpocock/skills/blob/main/skills/misc/migrate-to-shoehorn/SKILL.md)**: test file의 `as` type assertion을 `@total-typescript/shoehorn`으로 migrate한다.
- **[scaffold-exercises](https://github.com/mattpocock/skills/blob/main/skills/misc/scaffold-exercises/SKILL.md)**: section, problem, solution, explainer를 갖춘 exercise directory structure를 만든다.
- **[setup-pre-commit](https://github.com/mattpocock/skills/blob/main/skills/misc/setup-pre-commit/SKILL.md)**: lint-staged, Prettier, type checking, test를 포함한 Husky pre-commit hook을 설정한다.

## Relevant Patterns For harness-helm

### Small Composable Skills

README는 전체 process를 소유하는 큰 system에 반대하고, 작고 조합 가능한 skill을 강조한다. 이는 harness-helm의 cartridge approach와 잘 맞는다. Upstream tool과 agent skill은 교체 가능하게 두고, h2는 artifact contract와 lifecycle을 소유한다.

### Setup As A First-Class Skill

`setup-matt-pocock-skills` skill은 다른 skill이 의존하기 전에 project-specific configuration을 묻는다. 이는 h2 runtime installation에도 참고할 만하다. Target project에는 local issue tracker, docs location, label vocabulary를 수집하는 명시적인 setup 또는 smoke command가 필요할 수 있다.

### Shared Language As Token Compression

Repository는 shared domain language를 verbosity를 줄이고 naming을 개선하는 방법으로 다룬다. 이는 harness-helm의 `docs/40_knowledge/conventions`와 `docs/10_domain` 분리와 맞닿아 있다. Durable terminology는 session마다 다시 만들기보다 canonical docs로 승격해야 한다.

### Feedback Loops Before Confidence

Engineering skill은 TDD, diagnosis, browser/static/test feedback loop를 강조한다. 이는 h2가 `h2-build`, `h2-test`, `h2-review`를 분리하는 이유를 보강한다. Implementation evidence는 completion claim과 분리해서 기록해야 한다.

### Architecture Maintenance As A Repeated Workflow

Architecture 관련 skill은 design quality를 일회성 planning artifact가 아니라 반복되는 maintenance로 다룬다. 이는 review finding이나 compound knowledge가 design 또는 architecture improvement work를 촉발할 수 있는 h2 follow-up loop와 잘 맞는다.

## Apply When

- harness-helm의 skill/workflow design을 외부 agent-skill system과 비교할 때.
- h2 setup, installation, target-project onboarding flow를 설계할 때.
- Claude Code, Codex, skill/plugin ecosystem에 익숙한 사용자에게 h2의 가치를 어떻게 설명할지 검토할 때.
- 어떤 behavior가 작은 adapter skill, cartridge route, canonical h2 workflow contract 중 어디에 속해야 하는지 판단할 때.

## Do Not Apply When

- harness-helm source of truth를 정의할 때. 이 문서는 authority가 아니라 external reference다.
- harness-helm command semantics를 정할 때. 그 경우 `cookbooks/`, `.harness-helm/h2-cartridge.yml`, `.harness-helm/h2-schema.yml`을 기준으로 삼는다.
- Source repository를 다시 확인하지 않고 현재 upstream installer behavior에 대해 단정할 때.

## References

- Matt Pocock skills repository: <https://github.com/mattpocock/skills>
- Top-level README: <https://github.com/mattpocock/skills/blob/main/README.md>
- Claude plugin package directory: <https://github.com/mattpocock/skills/tree/main/.claude-plugin>
- 2026-05-27에 확인한 GitHub API contents endpoint: <https://api.github.com/repos/mattpocock/skills/contents>
