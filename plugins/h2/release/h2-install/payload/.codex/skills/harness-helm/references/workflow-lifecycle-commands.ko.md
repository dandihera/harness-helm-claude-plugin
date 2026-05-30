# Workflow Lifecycle Commands Reference

Source cookbook: `cookbooks/0300-workflow-contract/0303-workflow-lifecycle-commands.md`.

Claude Code와 Codex h2 command meaning을 위한 compact runtime snapshot입니다.

이 파일은 command meaning과 routing을 정의합니다. Upstream provider를 선택하거나, agent tool을 구현하거나, test를 실행하거나, canonical docs를 승격하지 않습니다. Provider/surface/fallback mapping은 `.harness-helm/h2-cartridge.yml`과 `references/upstream-tool-invocation.md`에 속합니다.

## Commands

- `h2-context`: run context를 생성 또는 갱신합니다.
- `h2-plan`: 작업을 계획하고 `docs/01_plan/{feature}.md`로 route합니다.
- `h2-design`: implementation design을 작성하고 `docs/02_design/{feature}.md`로 route합니다.
- `h2-analysis`: plan/design gap을 점검하고 alignment note를 기록합니다.
- `h2-build`: implementation work와 changed files를 기록합니다.
- `h2-test`: test execution, skipped check, remaining verification을 기록합니다.
- `h2-review`: review finding을 기록하고 `docs/03_review/{type}/{feature}.md`로 route합니다.
- `h2-report`: lifecycle result를 요약하고 `docs/04_report/{feature}.md`로 route합니다.
- `h2-compound`: reusable knowledge를 축적하고 governed canonical promotion candidate를 staging합니다.
- `h2-archive`: preflight에서 h2-compound 실행 여부를 확인합니다(미실행이면 자동 트리거). 이후 완료된 01-04 workflow artifact의 archive 이동 계획을 만듭니다. 실제 이동은 archive tooling에 위임합니다.
- `h2-ops`: operational follow-up candidate를 기록합니다.
- `h2-cartridge`: cartridge mapping을 점검 또는 갱신합니다.

## Runtime Note

Claude Code는 `/h2:{command}` slash command를 노출할 수 있습니다. Codex는 `$h2 {command}` skill alias를 노출할 수 있습니다. 둘 다 같은 h2 semantics를 보존해야 합니다.
