---
schema_version: 1
id: "CONV-20260531-013"
type: convention
status: stable
owner: tw.jang
security: internal
confidence: medium
target_runtime: included
source_references:
  - cookbooks/0500-enforcement/0503-h2-runtime-folder-structure.md
module:
  - docs
  - workflow
tags:
  - harness-helm
  - runtime-folder
  - staging
---

# h2 runtime folder structure

`.harness-helm/`은 target project에 설치되는 h2 runtime substrate다. `docs/`가 장기 지식이라면 `.harness-helm/`은 검증, 실행 설정, run staging을 담당한다.

## 주요 파일

- `.harness-helm/h2-schema.yml`: docs frontmatter와 validation 정책
- `.harness-helm/h2-cartridge.yml`: provider/surface/fallback/routing/output language mapping
- `.harness-helm/h2-compound.yml`: compound write boundary와 review gate
- `.harness-helm/bin/harness`: target-local Go harness runtime binary
- `.harness-helm/scripts/harness`: target-local Go harness runtime binary wrapper
- `.harness-helm/runs/_templates/`: run artifact template
- `docs/_templates/runs-summary.md`: archive root `runs-summary.md`의 Markdown template. 타이틀, 섹션명, 컬럼명 같은 사람이 읽는 문구는 이 template에서 관리하고, renderer는 summary row block만 주입한다.

## Run staging

```text
.harness-helm/runs/{feature}/{run-id}/
├── context-pack.md
├── manifest.json
├── raw/
├── normalized/
├── promotion-candidates/
├── snapshots/
└── restore-backups/
```

- `raw/`: upstream 원본 출력이나 실행 로그
- `normalized/`: h2 output contract로 정리한 초안
- `promotion-candidates/`: 승인 전 canonical 후보
- `snapshots/`: `h2-autorun` rewind용 pre-step snapshot. Snapshot manifest는 rewind evidence이면서 autorun child stage timing source 역할도 한다.
- `restore-backups/`: `h2-rewind` 복원 전 현재 파일 backup

## Run manifest

`manifest.json`은 run folder 단위의 timing metadata다. 공식 docs가 아니라 run staging 증거이며, `h2-archive`가 이 파일과 autorun snapshot timing manifest를 읽어 임시 `runs/stage-runtime-summary.json`과 archive root `runs-summary.md`를 생성한다. 최종 archive에서는 Markdown summary를 남기고 임시 JSON과 manifest를 제거한다. `harness run-stats`는 active run 조회 또는 legacy summary JSON이 남은 archive에서 구조화 stats를 제공한다.

```json
{
  "schema_version": 1,
  "type": "run-manifest",
  "feature": "h2-run-stats",
  "run_id": "20260601-133811-h2-design",
  "command": "h2-design",
  "status": "completed",
  "started_at": "2026-06-01T13:38:11+09:00",
  "completed_at": "2026-06-01T13:42:03+09:00",
  "autorun_id": null,
  "invoked_surface": "compound-engineering:ce-plan",
  "invocation_mode": "actual",
  "artifact_paths": [
    "docs/02_design/h2-run-stats.md"
  ]
}
```

- `started_at`과 `completed_at`은 KST 기준 timezone-aware ISO-8601 문자열을 사용한다.
- `status`는 `running`, `completed`, `failed`, `incomplete`를 사용한다.
- `status: running`이고 `completed_at`이 없으면 아직 완료 marker가 기록되지 않은 상태다. `run-stats`는 total 계산에서 제외한다.
- `manifest.json`이 없는 기존 run folder는 `run-stats`에서 `missing-manifest`로 표시하고, run-id timestamp를 시작 시각 fallback으로 사용한다. 기존 run-level `manifest.md`는 자동 마이그레이션하지 않고 무시한다.
- `autorun_id`는 `h2-autorun` child 단계들을 묶기 위한 optional parent run-id다.
- `invoked_surface`는 해당 stage가 기록한 machine-readable surface string이다. Actual 또는 recorder surface는 `<provider>:<surface>` 형태를 쓰고, fallback은 `fallback:<fallback_label>` 형태를 쓴다. `fallback:` 뒤의 나머지 문자열 전체가 fallback label이며 label 내부 `:`는 다시 분해하지 않는다.
- `invocation_mode`는 `actual`, `fallback`, `recorder`, `unknown` 중 하나다. Fallback checklist를 실제 upstream invocation처럼 기록하지 않는다.
- legacy manifest처럼 invocation metadata가 없으면 summary에서는 `invoked_surface: null`, `invocation_mode: unknown`으로 처리한다.
- `h2-rewind` 후 같은 run-id의 단계가 다시 실행되면 `run-mark start`는 이전 `started_at`/`completed_at`을 보존하지 않고 새 실행 timing으로 갱신한다.

## Runtime summary

`h2-archive`는 완료된 feature의 archive root에 사용자 확인용 `runs-summary.md`를 생성한다. 생성 과정에서 `runs/stage-runtime-summary.json`을 임시로 쓸 수 있지만 최종 archive pruning 후에는 보존하지 않는다.

```text
docs/_archive/{month}/{timestamp}_{feature}/
├── runs-summary.md
└── runs/
    ├── plan-context-pack.md
    ├── design-context-pack.md
    ├── autorun-context-pack.md
    ├── archive-plan.md
    ├── autorun-summary.md
    ├── build.md
    ├── test.md
    └── compound-candidates.md
```

`runs-summary.md`는 archive 시점의 timing summary다. 생성 직전의 임시 JSON summary는 다음 값을 기반으로 Markdown을 렌더링한다.

- `runs`: 단계별 `run_id`, `command`, `status`, `started_at`, `completed_at`, `elapsed_seconds`, `invoked_surface`, `invocation_mode`, 그리고 autorun 반복 증거(`iteration_index`, `stage_attempt`, `back_edge_from`, `back_edge_reason`, `back_edge_reason_key`, `autorun_resolution`)
- `total_elapsed_seconds`: 단계별 elapsed 합계. Autorun child stage snapshot entry가 있으면 direct `h2-autorun` parent elapsed는 중복 합산하지 않고 wall-clock evidence로만 둔다.
- `archive_wall_clock_seconds`: archive에 포함된 첫 started_at부터 마지막 completed_at까지의 wall-clock
- `autorun_groups`: 동일 `autorun_id`로 묶인 child stage의 pipeline total과 반복 요약
- `warnings`: legacy archive fallback, run-id timestamp mismatch, snapshot stage timing 누락 등 조회자가 알아야 할 조건

Archive root의 `runs-summary.md`는 `docs/_templates/runs-summary.md`를 읽어 생성한다. Template은 사람이 읽는 타이틀, 섹션명, 컬럼명을 담고, Go harness renderer는 다음 placeholder에 동적 값을 주입한다.

- `{{feature}}`
- `{{generated_at}}`
- `{{archive_path}}`
- `{{totals_rows}}`
- `{{runs_rows}}`
- `{{autorun_group_rows}}`
- `{{autorun_iteration_rows}}`
- `{{warnings_block}}`

Target runtime에 template이 없으면 renderer의 built-in fallback template으로 같은 기본 구조를 출력한다. Summary JSON은 machine-readable source of truth이고, Markdown template은 human-readable presentation layer다.

Autorun child stage는 normal run folder가 아니라 `runs/{autorun_run_id}/snapshots/{step}/manifest.json`에서 수집된다. 이 summary entry의 `run_id`는 `{autorun_run_id}/{step}` 형태의 표시용 synthetic id일 수 있으며, filesystem run-id validator 대상이 아니다.

Legacy JSON summary가 있는 archive path에 대해 `harness run-stats <archive-path>`를 실행하면 manifest를 재계산하지 않고 summary JSON을 읽는다. 새 summary가 없고 legacy root `runtime-summary.json`이 있으면 이를 읽되 warning에 `legacy runtime-summary.json fallback`을 추가한다. 두 summary가 모두 없는 archive는 `runs/**/manifest.json`을 스캔한다. 최종 pruning이 끝난 archive에서는 `runs-summary.md`가 사람이 확인하는 timing source다. `manifest.md`만 있는 legacy run dir는 run-level JSON manifest가 없는 것으로 보고 `missing-manifest`로 표시한다.

`runs-summary.md` 생성이 완료된 archive에서는 `runs/` 아래에 flatten된 Markdown 산출물(`plan-context-pack.md`, `design-context-pack.md`, `autorun-context-pack.md`, `archive-plan.md`, `autorun-summary.md`, `build.md`, `test.md`, `compound-candidates.md` 등)만 장기 보존한다. Run `manifest.json`, 임시 `stage-runtime-summary.json`, `snapshots/`, `restore-backups/`, `raw/`, `normalized/`, `promotion-candidates/`와 run-id 디렉터리는 summary 생성 후 제거된다. 이름 충돌이 있으면 deterministic suffix를 붙인다.

`runs-summary.md` 생성이 완료된 feature의 active `.harness-helm/runs/{feature}/` 폴더는 더 이상 stats source가 아니다. 필요한 runtime evidence는 archive root의 `runs-summary.md`와 archive-local `runs/*.md` 산출물에 남아야 하며, active run folder는 삭제할 수 있다. 테스트 fixture도 active `.harness-helm/runs/` 아래에 남기지 않는다.

## Run timing helper

Agent-driven h2 단계는 `harness run-mark`로 동일 manifest 계약을 기록한다.

```text
harness run-mark start --feature <feature> --run-id <run-id> --command <h2-command>
harness run-mark complete --feature <feature> --run-id <run-id> --artifact <path> --invoked-surface <surface> --invocation-mode <mode>
```

`run-mark start`도 `--invoked-surface`와 `--invocation-mode`를 받을 수 있지만, 생략하면 해당 field를 쓰지 않는다. 최종 source of truth는 `run-mark complete` 시점의 값이다. Complete에서 invocation option을 생략하면 기존 값을 보존한다.

`h2-autorun` child stage는 pre-step snapshot manifest에 timing을 남긴다. `--run-id`는 child step id가 아니라 parent autorun run-id다.

```text
harness h2-snapshot save --feature <feature> --run-id <autorun-run-id> --step <h2-step>
harness h2-snapshot complete --feature <feature> --run-id <autorun-run-id> --step <h2-step> --artifact <path> --invoked-surface <surface> --invocation-mode <mode>
```

`h2-snapshot save`도 invocation options를 받을 수 있지만, 생략하면 해당 field를 쓰지 않는다. Child stage의 최종 invocation metadata는 `h2-snapshot complete`가 기록한다.

`h2-archive` child stage도 timing/source evidence를 위해 snapshot manifest는 유지한다. 다만 archive 자체가 `docs/_archive/`에 plan/design/review/report 원문을 보존하므로, 신규 `h2-archive` snapshot은 active docs를 `snapshots/h2-archive/files/docs/**`로 다시 복사하지 않는다. Manifest의 `files`는 빈 list일 수 있으며, `h2-snapshot complete`가 archive artifact path와 completed timing을 기록한다. 기존 legacy `h2-archive` snapshot manifest가 있는 경우 `h2-snapshot list`와 `h2-snapshot restore --dry-run`은 계속 허용하고, archive residue는 자동 삭제하지 않고 경고만 남긴다.

`harness run-stats [feature-or-archive-path]`는 feature별 run elapsed time을 출력한다. feature 인자를 생략하면 active run folder의 feature별 최신 run summary를 출력한다. Archive path를 넘기면 legacy summary JSON 또는 남아 있는 manifest를 사용한다. 최종 pruning이 끝난 archive의 사람이 읽는 timing 기록은 `runs-summary.md`다.

## 금지

- `.harness-helm/runs/**`를 official docs로 취급하지 않는다.
- secret, token, 개인정보가 포함된 raw output을 canonical docs로 그대로 옮기지 않는다.
- archive residue를 자동 삭제하지 않는다.
