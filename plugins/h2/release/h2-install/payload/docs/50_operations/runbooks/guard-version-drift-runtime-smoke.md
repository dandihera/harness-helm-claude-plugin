---
schema_version: 1
id: RUNBOOK-20260602-115
type: runbook
status: draft
owner: 장태욱
security: internal
confidence: medium
related:
  - https://github.com/dandihera/harness-helm/issues/187
  - https://github.com/dandihera/harness-helm/issues/115
  - docs/01_plan/guard-version-drift-runtime-smoke_187.md
  - docs/02_design/guard-version-drift-runtime-smoke_187.md
  - docs/02_design/guard-version-drift-runtime-smoke_187.analysis.md
  - docs/50_operations/releases/release-build-verification-2026-06-07.md
  - docs/_archive/2026-06/0602-1404_guard-version-drift/guard-version-drift.report.md
source_references:
  - cookbooks/0500-enforcement/0504-install-package.md
module:
  - workflow
tags:
  - guard
  - plugin
  - runtime-smoke
  - semver
  - go-runtime
  - payload
source_trace: GitHub Issue #187
command: h2-ops
feature: guard-version-drift-runtime-smoke
next: []
---

# Runbook: guard version drift runtime smoke

## 목적

`GUARD_PREAMBLE` 버전 드리프트 차단이 실제 Claude Code target-side command 실행에서 기대대로 동작하는지 확인한다. 현재 기준은 Go-owned release payload flow다. Release payload는 `release/install-package/h2-install/MANIFEST.txt`를 source-of-truth로 삼고, Go release staging이 `.claude/commands/h2/*.md`에 guard preamble을 주입한다.

이 runbook은 두 검증 경계를 분리한다.

- Payload/staging 검증: Go release payload와 target runtime surface가 올바르게 구성됐는지 확인한다.
- Live Claude Code runtime smoke: prompt-level guard가 stale target command 실행을 실제로 차단하는지 확인한다.

## 사전 조건

- 최신 h2 Claude plugin 또는 current h2 install payload가 준비되어 있다.
- target project 하나를 runtime smoke 전용으로 사용할 수 있다.
- target project의 `.harness-helm/install-manifest.json` 파일 안 `package_version` field를 테스트 목적으로 수정하거나 fixture target을 만들 수 있다.
- current payload version source를 확인할 수 있다.
  - Claude plugin install 경로에서는 `~/.claude/plugins/installed_plugins.json`의 `h2@dandisoft-harness-helm` entry와 각 `installPath` 아래 `release/h2-install/h2-install-v*.txt` marker를 확인한다.
  - Zip/direct install 경로에서는 current payload version source가 없을 수 있으며, 이 경우 drift 미검증 경고 후 진행하는 fallback을 확인한다.
- smoke 후 target을 원복할 수 있다.

## Go payload/runtime 기준

| 기준 | Canonical source | 확인 내용 |
|---|---|---|
| Payload mapping | `release/install-package/h2-install/MANIFEST.txt` | target에 설치될 runtime surface와 docs scaffold를 정의한다. |
| Guard injection | `src/internal/harness/release/payload.go` | `.claude/commands/h2/*.md`에 `GuardPreamble`을 주입한다. |
| Target smoke surface | `src/internal/harness/validation/target_smoke.go` | `targetSmokeRequiredPaths` 전체가 target project에 존재해야 한다. |
| Runtime wrapper/binary | `.harness-helm/scripts/harness`, `.harness-helm/bin/harness` | wrapper가 Go harness binary 기준으로 동작해야 한다. |
| Install record | `.harness-helm/install-manifest.json` | `package_version` field를 SemVer로 해석한다. |

## target-smoke required surface

`target-smoke --strict`의 required surface canonical source는 `src/internal/harness/validation/target_smoke.go`의 `targetSmokeRequiredPaths`다. 아래 표는 이 runbook 작성 시점의 snapshot이며, 코드 목록이 바뀌면 코드가 기준이다.

| Group | Required surface |
|---|---|
| Root guide | `AGENTS.md`, `CLAUDE.md` |
| Harness config | `.harness-helm/h2-cartridge.yml`, `.harness-helm/h2-compound.yml`, `.harness-helm/h2-harvest.yml`, `.harness-helm/h2-schema.yml` |
| Harness runtime | `.harness-helm/scripts/harness`, `.harness-helm/bin/harness` |
| Claude adapter | `.claude/commands/h2`, `.claude/skills/harness-helm/SKILL.md`, `.claude/skills/h2-harvest/SKILL.md` |
| Codex adapter | `.codex/skills/h2`, `.codex/skills/harness-helm/SKILL.md`, `.codex/skills/h2-harvest/SKILL.md` |
| Docs runtime | `docs`, `docs/_harvest-inbox`, `docs/40_knowledge/conventions/guidelines/harness-helm` |

`target-smoke --strict`는 cookbooks-less target runtime surface와 wrapper/binary 동작을 확인한다. Prompt-level guard가 실제 Claude Code invocation에서 준수되는지는 아래 live runtime smoke로 별도 확인한다.

## Release payload checklist

Release 전 또는 live smoke 준비 전 다음 checklist를 실행해 payload/runtime surface가 현재 Go 기준에 맞는지 확인한다.

1. Go harness binary를 빌드한다.

Source wrapper bootstrap: source repository에서 `.harness-helm/scripts/harness` 또는 이를 호출하는 release wrapper를 실행하기 전에는 최신 Go harness binary가 필요하다.

```sh
go -C src build -o ../.harness-helm/bin/harness ./cmd/harness
```

Failure mode / Recovery: binary 없이 wrapper를 실행하면 `runtime binary missing at .harness-helm/bin/harness`로 실패할 수 있다. 위 build command를 다시 실행한 뒤 wrapper command를 재시도한다.

2. Target smoke를 실행한다.

```sh
.harness-helm/scripts/harness target-smoke --strict
```

3. Install zip 또는 payload-only build를 실행한다.

이 command는 `.harness-helm/scripts/harness`를 경유하므로 source wrapper bootstrap 이후 실행한다.

```sh
sh release/build-zip.sh --payload-only
```

4. Claude plugin package staging을 수행하는 release flow에서는 staged `release/h2-install/MANIFEST.txt`, `release/h2-install/payload/`, `release/h2-install/h2-install-v*.txt` marker가 함께 존재하는지 확인한다.
5. Payload residual sweep은 release payload에 실제 포함되는 runtime 파일을 대상으로 수행한다. Historical docs reference는 runtime residual로 판정하지 않는다.

## Smoke 1: stale target 차단

1. target project에 h2 runtime을 설치한다.
2. `<target>/.harness-helm/install-manifest.json` 파일의 `package_version` field를 current plugin/payload version보다 낮은 valid SemVer로 설정한다.
   - 예: current payload `v0.14.0`, target `v0.2.0`
3. Claude Code에서 target project를 열고 target-side command를 실행한다.
   - 예: `/h2:plan`
4. 기대 결과:

```text
/h2:doctor를 먼저 실행하세요. target h2 runtime이 현재 plugin보다 오래되었습니다.
```

5. 원래 h2 command 본문이 실행되지 않아야 한다.

## Smoke 2: current target 진행

1. `<target>/.harness-helm/install-manifest.json` 파일의 `package_version` field를 current plugin/payload version과 같게 설정한다.
2. `/h2:plan` 또는 `/h2:context`를 실행한다.
3. 기대 결과:
   - guard가 통과한다.
   - 원래 command 본문이 진행된다.

## Smoke 3: scoped-array installed_plugins.json

1. `~/.claude/plugins/installed_plugins.json`에서 `h2@dandisoft-harness-helm` entry shape를 확인한다.
2. entry가 배열이거나 복수 install 후보가 있으면 current project scope entry를 우선한다.
3. current project scope 판단이 불명확하면 각 entry의 `installPath` 아래 `release/h2-install/h2-install-v*.txt` marker filename SemVer 중 가장 높은 값을 current payload version으로 삼는다.
4. marker가 없으면 entry의 `version` field를 fallback으로 사용한다.
5. 기대 결과:
   - stale target은 차단된다.
   - entry 배열 때문에 current plugin/payload version을 낮게 오판하지 않는다.
   - marker filename과 marker 본문 `version:`이 다르면 filename SemVer를 우선하고 경고만 남긴다.

## Smoke 4: zip/direct install fallback

1. plugin registry entry를 사용하지 않는 zip/direct install target 또는 fixture를 준비한다.
2. `<target>/.harness-helm/install-manifest.json` 파일의 `package_version` field는 valid SemVer로 둔다.
3. target-side command를 실행한다.
4. 기대 결과:
   - current payload version source가 없다는 경고 후 원래 command 본문으로 진행한다.
   - `.harness-helm/install-manifest.json`이 없으면 `/h2:doctor를 먼저 실행하세요.` 안내 후 중단한다.
   - `package_version` field가 missing 또는 invalid이면 `/h2:doctor를 먼저 실행하세요. install-manifest package_version을 확인할 수 없습니다.` 안내 후 중단한다.

## 실패 시 대응

### Payload/staging 실패

- `.claude/commands/h2/*.md`에 guard preamble이 없으면 Go release payload staging 경로와 `GuardPreamble` 주입 조건을 확인한다.
- `release/install-package/h2-install/MANIFEST.txt`가 required surface를 누락하면 manifest mapping을 갱신한 뒤 release payload를 다시 stage한다.

### Target smoke 실패

- `target-smoke: required surface missing in target project: ...`가 나오면 `targetSmokeRequiredPaths`와 install payload destination을 대조한다.
- `.harness-helm/scripts/harness` 또는 `.harness-helm/bin/harness` 누락은 Go runtime install surface 문제로 본다.

### Live command guard 실패

- stale target이 진행되면 `GuardPreamble`의 version 비교 지시를 더 단순화하거나 hard gate 승격을 별도 설계한다.
- scoped-array entry에서 version을 잘못 고르면 `installed_plugins.json` entry 선택 문구를 실제 schema 기준으로 갱신한다.
- prompt-level guard가 반복적으로 무시되면 `/h2:doctor` 또는 wrapper script 수준의 hard check 승격을 별도 설계한다.

## GitHub Follow-up 초안

이 초안은 본문 기록용이다. 이 runbook 갱신만으로 새 GitHub issue를 생성하지 않는다.

제목:

```text
ops: guard version drift live Claude Code runtime smoke
```

본문:

> ## 목적
>
> #187 runbook 갱신 후, Go payload surface 기준의 `GUARD_PREAMBLE` stale runtime 차단이 실제 Claude Code target-side command에서 동작하는지 확인한다.
>
> ## 사전 확인
>
> - [ ] `go -C src build -o ../.harness-helm/bin/harness ./cmd/harness` (source wrapper missing-binary recovery command)
> - [ ] `.harness-helm/scripts/harness target-smoke --strict`
> - [ ] staged payload의 `release/h2-install/MANIFEST.txt`와 `release/h2-install/h2-install-v*.txt` marker 확인
>
> ## Live smoke 항목
>
> - [ ] stale target (`.harness-helm/install-manifest.json`의 `package_version` field가 current payload보다 낮음)에서 `/h2:plan`이 `/h2:doctor` 안내 후 중단
> - [ ] current target에서 command 본문 진행
> - [ ] scoped-array 또는 복수 `installed_plugins.json` entry에서 current project scope와 marker SemVer fallback 선택이 정상
> - [ ] zip/direct install fallback은 valid `package_version`이면 drift 미검증 경고 후 진행
>
> ## 기대 stale 차단 메시지
>
> `/h2:doctor를 먼저 실행하세요. target h2 runtime이 현재 plugin보다 오래되었습니다.`
>
> ## 관련
>
> - #187
> - `docs/50_operations/runbooks/guard-version-drift-runtime-smoke.md`
> - `src/internal/harness/release/payload.go`
> - `src/internal/harness/validation/target_smoke.go`

## h2 Output

```yaml
command: h2-build
feature: guard-version-drift-runtime-smoke_187
status: updated
context_pack:
  primary_docs:
    - docs/01_plan/guard-version-drift-runtime-smoke_187.md
    - docs/02_design/guard-version-drift-runtime-smoke_187.md
    - docs/02_design/guard-version-drift-runtime-smoke_187.analysis.md
    - docs/50_operations/runbooks/guard-version-drift-runtime-smoke.md
  supporting_docs:
    - src/internal/harness/release/payload.go
    - src/internal/harness/validation/target_smoke.go
    - release/install-package/h2-install/MANIFEST.txt
    - docs/50_operations/releases/release-build-verification-2026-06-07.md
  canonical_knowledge:
    - targetSmokeRequiredPaths is the canonical target smoke required surface.
    - MANIFEST.txt drives install/release payload mapping.
    - GuardPreamble is injected by Go release payload staging.
  excluded_by_policy:
    - docs/_archive/** body except cited historical trace.
    - .ko.md translation parity files.
  assumptions:
    - Live Claude Code runtime smoke remains a separate ops/test step.
artifacts:
  created: []
  updated:
    - docs/50_operations/runbooks/guard-version-drift-runtime-smoke.md
  suggested:
    - .harness-helm/runs/guard-version-drift-runtime-smoke_187/20260607-141900-h2-build/build.md
routing:
  target_docs:
    - .harness-helm/runs/guard-version-drift-runtime-smoke_187/20260607-141900-h2-build/build.md
  archive_candidate: false
  promotion_candidates: []
verification:
  required:
    - kb-lint --strict
    - negative runtime helper reference sweep
    - targetSmokeRequiredPaths coverage check
  completed:
    - runbook updated to Go payload/runtime surface baseline
    - GitHub follow-up draft updated without creating an issue
    - install-manifest package_version wording clarified as JSON field
  not_verified:
    - live Claude Code runtime smoke not performed in h2-build
next:
  recommended_h2_step: h2-test
```
