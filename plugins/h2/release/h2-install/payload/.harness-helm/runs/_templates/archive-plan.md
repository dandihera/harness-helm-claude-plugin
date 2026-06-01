---
command: h2-archive
feature: "<TODO: feature-slug>"
status: draft
next:
  recommended_h2_step: null
---

<!-- harness-helm h2-archive staging output. 실제 archive 처리는 harness archive script에 위임한다.
     이 파일은 dry-run 출력과 archive 전 boundary check 결과를 담는다.
     See 0501 Enforcement Policy, 0502 Enforcement Implementation, 0303 Workflow Lifecycle Commands. -->

# h2-archive — <TODO: feature title>

## Context Pack

### primary_docs
- <TODO: 관련 01_plan, 02_design, 03_review, 04_report 경로>

## Archive Plan

### Source Files (이동 대상)

- <TODO: docs/01_plan/{feature}.md 또는 docs/01-plan/{feature}.md>
- <TODO: docs/02_design/{feature}.md>
- <TODO: docs/03_review/**/{feature}.md>
- <TODO: docs/04_report/{feature}.md>

### Target Path

```text
docs/_archive/<TODO: YYYY-MM>/<TODO: feature>/
├── 01_plan/
├── 02_design/
├── 03_review/
└── 04_report/
```

### Manifest Metadata (예상)

- feature: <TODO>
- archived_at (Asia/Seoul): <TODO: YYYY-MM-DD HH:MM>
- source_trace: <TODO>
- source_pr: <TODO>
- phase_docs_present: <TODO: 01_plan, 02_design, 03_review, 04_report 중 어떤 것이 존재하는지>
- purpose: <TODO: archive 사유>

## Dry-run Output

```text
<TODO: .harness-helm/scripts/harness archive {feature} --dry-run 출력 붙여넣기>
```

## Boundary Checks

- frontmatter status가 `done` 또는 `archived`로 업데이트되는지: <TODO: ok/issue>
- archive 본문이 _indexes 입력에서 제외되는지: <TODO: ok/issue>
- manifest metadata가 허용 범위(feature, archived_at, archive_path, source_trace, source_pr, phase_docs_present, purpose)만 포함하는지: <TODO: ok/issue>
- `.harness-helm/runs/{feature}` cleanup이 dry-run 또는 실제 archive output에 표시되는지: <TODO: ok/issue>

## Artifacts

### created
- <TODO: archive dry-run 계획 또는 manifest 후보>

### updated
- <TODO: archive 준비 중 갱신된 문서>

### suggested
- <TODO: close 전 필요한 archive 후속 조치>

## Routing

- target_docs:
  - <TODO: docs/_archive/{YYYY-MM}/MMdd-HHMMSS_{feature}/...>
- archive_candidate: true
- promotion_candidates: []

## Verification

### required
- <TODO: archive 전 확인 사항>

### completed
- <TODO>

### not_verified
- <TODO: 사람 검토 대기>

## Next

- recommended_h2_step: null
