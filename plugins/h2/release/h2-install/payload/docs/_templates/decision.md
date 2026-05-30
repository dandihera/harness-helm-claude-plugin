---
schema_version: 1
id: "ADR-NNNN"
type: decision
status: draft
owner: "<TODO: git username 또는 team id>"
security: internal
confidence: low
related: []
# Recommended optional fields
# revisit_trigger: "<TODO: 재검토 조건. pending/rejected에서 특히 중요.>"
# ai_avoid_phrases: []     # rejected decision에서 필수
# supersedes: []
# source_trace: "<TODO: historical trace 또는 외부 작업 출처>"
---

<!-- harness-helm decision template. status enum: draft|pending|accepted|rejected.
     파일명 suffix와 frontmatter status가 반드시 일치해야 한다:
       NNNN-{topic}.draft.md    -> status: draft
       NNNN-{topic}.pending.md  -> status: pending
       NNNN-{topic}.accepted.md -> status: accepted
       NNNN-{topic}.rejected.md -> status: rejected   (ai_avoid_phrases 필수)
     See 0102 Frontmatter Schema, 0103 Retrieval Policy. -->

# ADR-NNNN: <TODO: 결정 제목>

## Status

<TODO: draft | pending | accepted | rejected>

## Context

<TODO: 결정이 필요한 배경, 제약, 이해관계자.>

## Decision

<TODO: 채택한 결정을 명확한 단정문으로 작성.>

## Alternatives Considered

- <TODO: 대안 1과 기각/선택 사유>
- <TODO: 대안 2와 기각/선택 사유>

## Consequences

### Positive
- <TODO: 결정으로 얻는 효과>

### Negative / Trade-offs
- <TODO: 감수해야 하는 비용/리스크>

## Revisit Trigger

<TODO: 어떤 조건이 충족되면 이 결정을 재검토하는지.>

## AI Avoid Phrases (rejected decision 전용)

<!-- status: rejected일 때 필수. AI가 같은 제안을 반복하지 않도록 phrase를 나열한다. -->

- <TODO: phrase>

## References

- <TODO: 관련 plans, designs, prior decisions>
