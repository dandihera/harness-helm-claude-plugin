# Workflow Lifecycle Commands Reference

Source cookbook: `cookbooks/0300-workflow-contract/0303-workflow-lifecycle-commands.md`.

Claude Code와 Codex h2 command meaning을 위한 compact runtime snapshot입니다.

이 파일은 command meaning과 routing을 정의합니다. Upstream provider를 선택하거나, agent tool을 구현하거나, test를 실행하거나, canonical docs를 승격하지 않습니다. Provider/surface/fallback mapping은 `.harness-helm/h2-cartridge.yml`과 `references/cartridge-command-mapping.md`에 속합니다.

## Commands

- `h2-context`: run context를 생성 또는 갱신합니다.
- `h2-plan`: 작업을 계획하고 `docs/01_plan/{feature}.md`로 route합니다.
- `h2-design`: implementation design을 작성하고 `docs/02_design/{feature}.md`로 route합니다.
- `h2-analysis`: plan/design gap을 점검하고 alignment note를 `docs/02_design/{feature}.analysis.md`에 기록합니다.
- `h2-autorun`: design 이후 `h2-analysis`를 실행한 뒤, test 또는 review가 `next.recommended_h2_step: h2-build`를 반환하면 `h2-build -> h2-test -> h2-review` state machine을 반복합니다. 최신 test와 review가 forward 진행을 허용한 뒤에만 `h2-report`, `h2-compound`, `h2-archive`를 실행하며, `status: blocked`, 반복된 unresolved reason, review 미실행, max iteration 초과에서 중단합니다.
- `h2-rewind`: 특정 `h2-autorun` pre-step snapshot을 복원합니다. Snapshot이 없으면 `blocked:no-snapshot`으로 중단합니다.
- `h2-build`: implementation work와 changed files를 기록합니다.
- `h2-test`: test execution, skipped check, remaining verification을 기록합니다.
- `h2-review`: review finding을 기록하고 `docs/03_review/{type}/{feature}.md`로 route합니다.
- `h2-report`: lifecycle result를 요약하고 `docs/04_report/{feature}.md`로 route합니다.
- `h2-compound`: reusable knowledge를 축적하고 governed canonical promotion candidate를 staging합니다.
- `h2-harvest`: `docs/_harvest-inbox/**` 메모를 canonical docs로 정리하고 report를 `.harness-helm/runs/_unscoped/{run-id}/harvest-report.md`로 route합니다.
- `h2-harvest-tag`: `docs/_harvest-inbox/raw/**` 파일을 prefixed raw suggestion 또는 typed inbox folder로 분류하고 report를 `.harness-helm/runs/_unscoped/{run-id}/harvest-tag-report.md`로 route합니다.
- `h2-archive`: preflight에서 h2-compound 실행 여부를 확인합니다(미실행이면 자동 트리거). 이후 완료된 01-04 workflow artifact와 완료된 feature run-root를 archive tooling으로 이동합니다. dry-run은 사용자가 preview-only 동작을 명시적으로 요청한 경우에만 사용합니다.
- `h2-ops`: operational follow-up candidate를 기록합니다.
- `h2-cartridge`: cartridge mapping을 점검 또는 갱신합니다.

## Runtime Note

Claude Code는 `/h2:{command}` slash command를 노출할 수 있습니다. Codex는 `$h2 {command}` skill alias를 노출할 수 있습니다. 둘 다 같은 h2 semantics를 보존해야 합니다.
