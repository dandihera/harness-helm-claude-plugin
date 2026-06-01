# Cartridge Output Normalization Reference

Source cookbook: `0604 Cartridge Output Normalization`.

Compatibility marker: Source cookbook: `0604 Upstream Output Normalization`.

이 reference는 upstream raw output을 h2 output으로 변환하는 runtime 요약입니다.

Upstream raw output은 canonical h2 artifact가 아닙니다(`not a canonical h2 artifact`). 공식 문서에 쓰기 전에 Claude Code, Codex, gstack, superpowers, compound-engineering 결과를 h2 output contract로 정규화해야 합니다.

## 흐름

```text
upstream raw output
  -> h2 cartridge normalization
  -> h2 common output shape
  -> official docs or run artifacts
```

`raw/`, `normalized/`, `promotion-candidates/` 폴더 생성은 각 h2 command의 runtime cartridge 책임입니다. `harness.py`는 생성된 staging artifact와 cleanup rule을 검증하며, 이 폴더를 직접 만들지 않습니다.

## 필수 매핑

- Upstream command name이 아니라 h2 `command`를 보존합니다.
- 실제로 존재하는 created/updated file을 `artifacts.created`와 `artifacts.updated`에 매핑합니다.
- Suggested docs, release notes, runbooks, knowledge item은 `artifacts.suggested` 또는 `routing.promotion_candidates`에 매핑합니다.
- 실제 upstream invocation은 `verification.completed`에 `actual:<provider>:<surface>`로 매핑합니다.
- Fallback execution은 `.harness-helm/h2-cartridge.yml`의 fallback label로 매핑합니다.
- 불확실한 claim과 skipped check는 `verification.not_verified`에 매핑합니다.
- Blocked prerequisite은 `verification.required`에 매핑합니다.
- `next.recommended_h2_step`은 upstream tool이 아니라 h2 lifecycle에서 선택합니다.

## Command Notes

- `h2-plan`: goals, scope, non-goals, done criteria, risks를 `docs/01_plan/{feature}.md`로 정규화합니다.
- `h2-design`: implementation flow, module/interface boundary, data flow, verification strategy를 `docs/02_design/{feature}.md`로 정규화합니다.
- `h2-autorun`: child step status, artifact, warning, blocked reason을 `.harness-helm/runs/{feature}/{run-id}/autorun-summary.md`로 정규화합니다.
- `h2-rewind`: restore action, backup path, archive residue warning, no-snapshot blocked reason을 `.harness-helm/runs/{feature}/{run-id}/snapshots/{step}/restore.md`로 정규화합니다.
- `h2-analysis`: plan/design mismatch와 gap을 analysis note 또는 sync section으로 정규화합니다.
- `h2-build`, `h2-test`, `h2-review`: actor result를 run artifact 또는 review docs로 정규화합니다. Actual execution evidence를 upstream suggestion으로 대체하지 않습니다.
- `h2-report`: lifecycle summary와 follow-up need를 `docs/04_report/{feature}.md`로 정규화합니다.
- `h2-compound`: low-risk learning/solution 작성은 `artifacts.created` 또는 `artifacts.updated`로 매핑하고, governed canonical 대상은 승인 전까지 `routing.promotion_candidates`에 유지합니다.
- `h2-archive`, `h2-ops`, `h2-cartridge`: archive 실행 또는 명시적 dry-run preview, ops, mapping validation output을 configured route로 정규화합니다.

Raw output은 sensitive information을 masking하고 core workflow staging cleanup policy를 따라야 합니다.
