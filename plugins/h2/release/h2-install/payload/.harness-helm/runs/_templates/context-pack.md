---
command: h2-context
feature: "<TODO: feature-slug 또는 null>"
status: draft
next:
  recommended_h2_step: "<TODO: h2-plan | h2-design | h2-autorun | h2-analysis | h2-report | null>"
---

<!-- harness-helm h2-context staging output. .harness-helm/runs는 임시 staging이며 canonical KB가 아니다.
     status enum: draft|updated|skipped|blocked. 0301 Core Workflow Spec 참고. -->

# h2-context — <TODO: task summary>

## Context Pack

### primary_docs
- <TODO: 작업 근거가 되는 핵심 문서 path 또는 issue>

### supporting_docs
- <TODO: 부수적 근거 문서>

### canonical_knowledge
- <TODO: 이번 run에 재투입되는 canonical knowledge 문서. 없으면 <없음>>

### excluded_by_policy
- <TODO: 0103 Retrieval and Index Policy로 제외한 문서 (예: _archive 본문, draft, regulated)>

### assumptions
- <TODO: 명시적으로 가정한 사실>

## Artifacts

### created
- <TODO: 이 단계에서 생성한 파일>

### updated
- <TODO: 이 단계에서 갱신한 파일>

### suggested
- <TODO: 후속 단계에서 만들면 좋은 산출물 제안>

## Routing

- target_docs: []
- archive_candidate: false
- promotion_candidates: []

## Verification

### required
- <TODO: 권장 검증 항목>

### completed
- <TODO: 이미 수행된 검증>
- <TODO: index freshness 확인 또는 canonical docs 직접 scan 결과>

### not_verified
- <TODO: 사람 검토가 필요한 미검증 항목>
- <TODO: index absent/stale warning이 있으면 기록>

## Next

- recommended_h2_step: <TODO: h2-plan | h2-design | h2-autorun | h2-analysis | h2-report | null>
