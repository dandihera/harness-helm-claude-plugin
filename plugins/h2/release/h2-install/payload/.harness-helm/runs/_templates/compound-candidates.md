---
command: h2-compound
feature: "<TODO: feature-slug>"
status: draft
next:
  recommended_h2_step: h2-archive
---

<!-- harness-helm h2-compound output.
     low-risk learning/solution은 overlap/schema/lint 확인 후 docs/40_knowledge에 작성/갱신할 수 있다.
     governed canonical 목적지는 owner/verifier 또는 Tech Lead 승인 전까지 staging한다.
     See 0202 Operations Ownership, 0301 Core Workflow Spec, 0303 Workflow Lifecycle Commands,
     and docs/40_knowledge/conventions/guidelines/h2-canonical-promotion-flow.md. -->

# h2-compound — <TODO: feature title>

## Context Pack

### primary_docs
- <TODO: 관련 04_report, 01~04 산출물>

## Routing

- target_docs: []
- archive_candidate: false
- promotion_candidates:
  - <TODO: 후보 1 경로 또는 요약>
  - <TODO: 후보 2>

## Knowledge Candidates (low-risk)

이 섹션은 `compound-candidates.md` 안의 template-local 기록이다. 공통 h2 output field를 새로 추가하지 않는다.

```yaml
knowledge_candidates:
  - target: docs/40_knowledge/solutions/<topic>.md
    governance_level: low-risk
    overlap:
      score: low | moderate | high
      matched_docs: []
    action: create | update | suggest
    evidence: []
    status: ready-to-write | written | skipped
```

Low-risk 작성/갱신 결과는 공통 output의 `artifacts.created` 또는 `artifacts.updated`에 기록한다. 쓰지 않은 제안은 `artifacts.suggested`에 둔다.

## Promotion Candidates (상세)

이 섹션은 governed canonical 목적지의 승인 전 staging 영역이다.

### Candidate 1

- target_route: <TODO: docs/10_domain/... | 20_specs | 30_decisions | 40_knowledge | 50_operations>
- proposed_type: <TODO: domain | spec | decision | solution | convention | learning | runbook | incident | release>
- rationale: <TODO: 왜 canonical 영역으로 승격할 만한지>
- evidence: <TODO: tests, source_pr, human_verified_by 후보>
- owner_or_verifier: <TODO: 검토할 owner/verifier>
- security_level: <TODO: internal | confidential | regulated>

### Candidate 2

- <TODO: 동일 형식>

## Approval Metadata (승인 후 작성)

승인 입력 형태: 자연어("이 후보 승인", "이 후보를 canonical 문서로 만들어도 됨") 또는 alias(`$h2 compound approve <candidate-path>`). 승인 입력은 별도 canonical command id가 아니라 h2-compound input form이다. 자세한 절차는 `docs/40_knowledge/conventions/guidelines/h2-canonical-promotion-flow.md` 또는 0304 cookbook을 따른다.

Low-risk `docs/40_knowledge/solutions/**`와 `docs/40_knowledge/learnings/**` 작성은 approval 없이 가능하다. 다만 기본값은 `status: draft`, `confidence: medium`이며, `verified`, `stable`, `confidence: high`는 schema가 요구하는 검증 근거가 있을 때만 사용한다.

승인 기록 예:

```yaml
approval:
  status: approved
  approved_by: <TODO: owner-id 또는 verifier-id>
  approved_at: <TODO: YYYY-MM-DD>
  scope:
    - <TODO: docs/{canonical-route}/candidate-name.md>
  evidence:
    - <TODO: docs/01_plan/{feature}.md>
    - <TODO: docs/04_report/{feature}.md>
  notes:
    - <TODO: Candidate approved for canonical promotion.>
```

승인 status enum: `approved | pending | rejected`. ambiguous 또는 사람 검토 필요면 `pending` 유지. rejected 항목은 docs/30_decisions/{NNNN}-{topic}.rejected.md로 별도 기록 가능.

## Verification

### required
- <TODO: 승격 전 필요한 검증>

### completed
- <TODO: 이미 수행된 검증>

### not_verified
- <TODO: owner/verifier 또는 Tech Lead 검토 대기>

## Artifacts

### created
- <TODO>

### updated
- <TODO>

### suggested
- <TODO>

## Next

- recommended_h2_step: h2-archive
