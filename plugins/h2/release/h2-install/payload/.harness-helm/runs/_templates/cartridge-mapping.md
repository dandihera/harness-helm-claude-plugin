---
command: h2-cartridge
feature: "<TODO: feature-slug or null>"
status: draft
next:
  recommended_h2_step: null
---

<!-- harness-helm h2-cartridge staging output. .harness-helm/h2-cartridge.yml의 effective mapping을 검증하고
     mismatch/누락을 기록한다. provider/surface/routing 본문은 yml의 source of truth를 가리킨다.
     See 0601 Cartridge Command Mapping. -->

# h2-cartridge — Effective Mapping Validation

## Context Pack

### primary_docs
- `.harness-helm/h2-cartridge.yml`
- <TODO: 관련 references (예: `.claude/skills/harness-helm/references/upstream-tool-invocation.md`)>

## Effective Mapping Snapshot

```yaml
<TODO: .harness-helm/h2-cartridge.yml의 현재 active mapping을 붙여넣기>
```

## Validation Results

### Core Commands

| Command | Provider | Surface | Fallback | Routing Target | Status |
|---|---|---|---|---|---|
| h2-context | <TODO> | <TODO> | <TODO> | <TODO> | <TODO: actual/verified-fallback/cartridge-checklist-fallback/blocked> |
| h2-plan | <TODO> | <TODO> | <TODO> | <TODO> | <TODO> |
| h2-design | <TODO> | <TODO> | <TODO> | <TODO> | <TODO> |
| h2-analysis | <TODO> | <TODO> | <TODO> | <TODO> | <TODO> |
| h2-report | <TODO> | <TODO> | <TODO> | <TODO> | <TODO> |

### Workflow Lifecycle Commands

| Command | Provider | Surface | Fallback | Routing Target | Status |
|---|---|---|---|---|---|
| h2-build | <TODO> | <TODO> | <TODO> | <TODO> | <TODO> |
| h2-test | <TODO> | <TODO> | <TODO> | <TODO> | <TODO> |
| h2-review | <TODO> | <TODO> | <TODO> | <TODO> | <TODO> |
| h2-compound | <TODO> | <TODO> | <TODO> | <TODO> | <TODO> |
| h2-archive | <TODO> | <TODO> | <TODO> | <TODO> | <TODO> |
| h2-ops | <TODO> | <TODO> | <TODO> | <TODO> | <TODO> |

## Artifacts

### created
- <TODO: cartridge mapping validation artifact>

### updated
- <TODO: .harness-helm/h2-cartridge.yml 변경 여부>

### suggested
- <TODO: surface/fallback follow-up>

## Routing

- target_docs:
  - `.harness-helm/h2-cartridge.yml`
- archive_candidate: false
- promotion_candidates: []

## Verification

### required
- yml schema 유효성: <TODO: ok/issue>
- provider/surface 누락 없음: <TODO: ok/issue>
- routing target underscore 경로 준수: <TODO: ok/issue>

### completed
- <TODO>

### not_verified
- <TODO: 실제 upstream invocation smoke가 필요한 command>

## Issues Found (있을 때만)

- <TODO: yml 수정이 필요한 항목>

## Next

- recommended_h2_step: null
