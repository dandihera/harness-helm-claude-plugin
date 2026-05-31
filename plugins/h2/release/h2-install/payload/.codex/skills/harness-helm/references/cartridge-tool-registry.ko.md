# Cartridge Tool Registry Reference

Compatibility marker: 0602 Upstream Tool Registry.

cartridge tool registry의 압축 runtime snapshot입니다.

## 규칙

Upstream tool registry는 `.harness-helm/h2-cartridge.yml`의 `external_tool_registry.tools`에서 관리합니다.

Registry는 h2 command가 호출하거나 참조할 수 있는 upstream tool을 나열합니다. 초기 대상은 `gstack`, `superpowers`, `compound-engineering`입니다.

## Registry Fields

각 tool entry는 다음을 정의해야 합니다.

- `id`: 안정적인 registry id
- `display_name`: 사람이 읽는 이름
- `category`: workflow engine, skill system, engineering plugin 등 분류
- `surfaces`: h2가 사용할 수 있는 command, skill, plugin surface
- `availability`: 필요한 설치 또는 활성화 조건
- `preferred_for`: tool을 우선 사용할 h2 command 또는 workflow stage
- `fallback`: 사용할 수 없을 때의 fallback behavior
- `alternatives`: 같은 목적의 다른 tool
- `source_of_truth`: mapping이 유지되는 위치
- `validation`: smoke 또는 dry-run check
- `notes`: runtime별 주의사항

## 결정

- Provider, surface, fallback, routing 값은 `.harness-helm/h2-cartridge.yml`에 둡니다.
- `references/cartridge-command-mapping.md`는 compact runtime mapping을 기록합니다.
- Claude Code와 Codex는 tool 호출 방식이 달라도 h2 output contract는 동등해야 합니다.
- Upstream tool을 사용할 수 없으면 command fallback label을 유지하고 이유를 `verification.not_verified`에 기록합니다.

## 피해야 할 것

- 이 reference만으로 새 upstream tool을 설치하거나 도입하지 않습니다.
- h2 lifecycle command 순서나 의미를 재정의하지 않습니다.
- gstack, superpowers, compound-engineering을 재구현하지 않습니다.
