# Cartridge Surface Map Reference

Source cookbook: `0603 Cartridge Surface Map`.

Compatibility marker: Source cookbook: `0603 Upstream Surface Map`.

이 reference는 upstream surface recommendation의 runtime snapshot입니다. Provider, fallback label, routing의 기준인 `.harness-helm/h2-cartridge.yml` 또는 `references/cartridge-command-mapping.md`를 대체하지 않습니다.

## Recommended Strengths

- `gstack`: planning review, QA, docs, ops 중심 surface.
- `superpowers`: design discipline, TDD, systematic debugging, verification gate.
- `compound-engineering`: plan, work, review, doc review, compound learning, PR workflow surface.

## Selection Rule

Adapter default를 사용할 수 없거나, 사용자가 run-level upstream override를 요청하거나, permanent mapping change의 alternative를 평가할 때 이 map을 사용합니다.

예: `h2-design`은 결과 산출물이 여전히 h2 design document로 정규화되는 경우에만 gstack, superpowers, compound-engineering surface를 사용할 수 있습니다.

## Boundaries

- Command semantics는 h2에서 옵니다.
- Fallback label과 routing target은 `.harness-helm/h2-cartridge.yml`과 `references/cartridge-command-mapping.md`에 속합니다.
- Upstream raw output은 `references/cartridge-output-normalization.md`를 통해 정규화해야 합니다.
- Upstream surface를 실제 호출하지 않았다면 actual invocation이라고 기록하지 않습니다.
