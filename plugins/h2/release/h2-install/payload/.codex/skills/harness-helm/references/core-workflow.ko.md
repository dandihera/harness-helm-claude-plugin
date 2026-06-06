# Core Workflow Spec Reference

`0301 Core Workflow Spec`의 압축 runtime snapshot입니다.

## 목적

`harness-helm`은 agent 작업을 h2 lifecycle command, 공통 output contract, staging artifact, docs routing으로 표준화합니다. Claude Code, Codex, gstack, superpowers, compound-engineering을 대체하지 않고 감쌉니다.

## Command Lifecycle

- `h2-context`: primary, supporting, excluded docs를 선택하고 run context pack을 생성 또는 갱신합니다.
- `h2-plan`: goal, scope, non-goals, done criteria, risk, verification을 담아 `docs/01_plan/{feature}.md`를 생성 또는 갱신합니다.
- `h2-design`: plan을 기준으로 implementation design을 `docs/02_design/{feature}.md`에 작성합니다.
- `h2-analysis`: plan과 design을 비교하고 gap과 alignment work를 `docs/02_design/{feature}.analysis.md`에 기록합니다.
- `h2-autorun`: design 이후 `h2-analysis`를 실행하고, test/review back-edge가 있으면 `h2-build -> h2-test -> h2-review`를 반복한 뒤 최신 test와 review가 forward 진행을 허용할 때만 report/compound/archive를 실행합니다. 단계와 반복 status를 `.harness-helm/runs/{feature}/{run-id}/autorun-summary.md`에 요약합니다.
- `h2-rewind`: 특정 `h2-autorun` pre-step snapshot을 복원하고 evidence를 `.harness-helm/runs/{feature}/{run-id}/snapshots/{step}/restore.md`에 기록합니다.
- `h2-build`: 구현 작업, 변경 파일, risk, blocked item을 기록합니다.
- `h2-test`: test command, result, skipped check, failure, remaining verification을 기록합니다.
- `h2-review`: code, QA, security, cross-review findings를 `docs/03_review/{type}/{feature}.md`에 기록합니다.
- `h2-report`: plan, design, analysis, build, test, review를 `docs/04_report/{feature}.md`에 요약합니다.
- `h2-compound`: 재사용 가능한 지식을 축적합니다. low-risk `40_knowledge` learning/solution 문서는 검증 후 작성할 수 있고, governed canonical 후보는 승인 전까지 staging합니다.
- `h2-archive`: 완료된 01-04 workflow artifact를 archive로 이동하고 완료된 feature run-root도 archive tooling으로 이동합니다. dry-run은 사용자가 preview-only 동작을 명시적으로 요청한 경우에만 사용합니다.
- `h2-ops`: runbook, release, incident, branch cleanup 같은 운영 follow-up을 기록합니다.
- `h2-cartridge`: provider, surface, fallback, routing, output language mapping을 점검 또는 갱신합니다.

## 공통 출력

모든 h2 command는 다음 구조를 보존해야 합니다.

```yaml
command: h2-command
feature: feature-slug-or-null
status: draft | updated | skipped | blocked
context_pack:
  primary_docs: []
  supporting_docs: []
  canonical_knowledge: []
  excluded_by_policy: []
  assumptions: []
artifacts:
  created: []
  updated: []
  suggested: []
routing:
  target_docs: []
  archive_candidate: false
  promotion_candidates: []
verification:
  required: []
  completed: []
  not_verified: []
next:
  recommended_h2_step: null
```

## Routing Rules

- PDCA workflow docs는 `docs/01_plan`, `docs/02_design`, `docs/03_review`, `docs/04_report`에 둡니다.
- Canonical knowledge는 `docs/10_domain`, `docs/20_specs`, `docs/30_decisions`, `docs/40_knowledge`, `docs/50_operations`에 둡니다.
- Run-local staging은 `.harness-helm/runs/{feature}/{run-id}/`에 둡니다.
- `_archive`는 historical record이며 default retrieval에서 제외합니다.

## Guardrails

- 다른 upstream tool을 사용했다는 이유로 command semantics를 바꾸지 않습니다.
- raw upstream output을 canonical h2 output으로 저장하지 않습니다.
- 승인 없이 governed canonical docs를 작성하지 않습니다. Low-risk `40_knowledge/solutions`와 `40_knowledge/learnings` 작성은 overlap, schema, lint 확인 후 허용됩니다.
- `h2-context`에서 `_indexes`를 생성하지 않습니다. `kb-index`를 사용합니다.
