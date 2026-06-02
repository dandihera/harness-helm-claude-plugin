---
schema_version: 1
id: RUNBOOK-20260602-115
type: runbook
status: draft
owner: 장태욱
security: internal
confidence: medium
related:
  - https://github.com/dandihera/harness-helm/issues/115
  - docs/_archive/2026-06/0602-140433_guard-version-drift/guard-version-drift.report.md
module:
  - workflow
tags:
  - guard
  - plugin
  - runtime-smoke
  - semver
source_trace: GitHub Issue #115
command: h2-ops
feature: guard-version-drift-runtime-smoke
next: []
---

# Runbook: guard version drift runtime smoke

## 목적

`GUARD_PREAMBLE` 버전 드리프트 차단 변경이 실제 Claude Code target-side command 실행에서 기대대로 동작하는지 확인한다. Static check와 payload smoke는 완료됐지만, preamble은 prompt-level instruction이므로 실제 Claude Code invocation smoke가 release 전 확인 대상이다.

## 사전 조건

- 최신 h2 Claude plugin이 설치되어 있다.
- target project 하나를 runtime smoke 전용으로 사용할 수 있다.
- target project의 `.harness-helm/install-manifest.json`을 테스트 목적으로 수정하거나 fixture target을 만들 수 있다.
- smoke 후 target을 원복할 수 있다.

## Smoke 1: stale target 차단

1. target project에 h2 runtime을 설치한다.
2. `<target>/.harness-helm/install-manifest.json`의 `package_version`을 현재 plugin보다 낮은 값으로 설정한다.
   - 예: current plugin `0.10.0`, target `v0.2.0`
3. Claude Code에서 target project를 열고 target-side command를 실행한다.
   - 예: `/h2:plan`
4. 기대 결과:

```text
/h2:doctor를 먼저 실행하세요. target h2 runtime이 현재 plugin보다 오래되었습니다.
```

5. 원래 h2 command 본문이 실행되지 않아야 한다.

## Smoke 2: current target 진행

1. `<target>/.harness-helm/install-manifest.json.package_version`을 current plugin/payload version과 같게 설정한다.
2. `/h2:plan` 또는 `/h2:context`를 실행한다.
3. 기대 결과:
   - guard가 통과한다.
   - 원래 command 본문이 진행된다.

## Smoke 3: scoped-array installed_plugins.json

1. `~/.claude/plugins/installed_plugins.json`에서 `h2@dandisoft-harness-helm` entry shape를 확인한다.
2. entry가 배열이면 project scope entry 또는 가장 높은 marker SemVer fallback이 preamble 문구와 충돌하지 않는지 확인한다.
3. 기대 결과:
   - stale target은 차단된다.
   - entry 배열 때문에 current plugin version을 낮게 오판하지 않는다.

## Smoke 4: zip direct install fallback

1. plugin registry entry를 사용하지 않는 zip 직접 설치 target 또는 fixture를 준비한다.
2. `package_version`은 valid SemVer로 둔다.
3. target-side command를 실행한다.
4. 기대 결과:
   - current payload version source가 없다는 경고 후 진행한다.
   - `install-manifest.json`이 없거나 `package_version`이 invalid이면 여전히 차단한다.

## 실패 시 대응

- stale target이 진행되면 `GUARD_PREAMBLE` 문구를 더 단순화한다.
- scoped-array entry에서 version을 잘못 고르면 `installed_plugins.json` entry 선택 문구를 실제 schema 기준으로 갱신한다.
- prompt-level guard가 반복적으로 무시되면 `/h2:doctor` 또는 wrapper script 수준의 hard check 승격을 별도 설계한다.

## GitHub Follow-up 초안

제목:

```text
ops: guard version drift live Claude Code runtime smoke
```

본문:

> ## 목적
>
> Issue #115 수정은 static/payload smoke를 통과했지만, `GUARD_PREAMBLE`은 prompt-level instruction이다. Release 전 실제 Claude Code target-side command에서 stale runtime 차단이 동작하는지 확인한다.
>
> ## 확인 항목
>
> - [ ] stale target (`package_version = v0.2.0`, current plugin `0.10.0`)에서 `/h2:plan`이 `/h2:doctor` 안내 후 중단
> - [ ] current target에서 command 본문 진행
> - [ ] scoped-array `installed_plugins.json` entry에서 current version source 선택이 정상
> - [ ] zip direct install fallback은 valid `package_version`이면 WARN 후 진행
>
> ## 기대 stale 차단 메시지
>
> `/h2:doctor를 먼저 실행하세요. target h2 runtime이 현재 plugin보다 오래되었습니다.`
>
> ## 관련
>
> - #115
> - `docs/50_operations/runbooks/guard-version-drift-runtime-smoke.md`
> - `docs/_archive/2026-06/0602-140433_guard-version-drift/guard-version-drift.report.md`

## h2 Output

```yaml
command: h2-ops
feature: guard-version-drift-runtime-smoke
status: draft
context_pack:
  primary_docs:
    - docs/_archive/2026-06/0602-140433_guard-version-drift/guard-version-drift.report.md
    - release/_payload_lib.py
  supporting_docs:
    - docs/_archive/2026-06/0602-140433_guard-version-drift/runs/20260602-140004-h2-autorun/test.md
  canonical_knowledge:
    - prompt-level guard requires live runtime smoke before release confidence is high
  excluded_by_policy:
    - docs/_archive/** body except the current feature archive cited above
artifacts:
  created:
    - docs/50_operations/runbooks/guard-version-drift-runtime-smoke.md
  updated: []
  suggested:
    - GitHub follow-up issue from the included draft
routing:
  target_docs:
    - docs/50_operations/runbooks/guard-version-drift-runtime-smoke.md
  archive_candidate: false
  promotion_candidates: []
verification:
  required:
    - live Claude Code stale target invocation
    - scoped-array installed_plugins.json runtime check
  completed:
    - runtime smoke runbook drafted
    - GitHub follow-up issue body drafted but not published
  not_verified:
    - live runtime smoke remains pending
next:
  recommended_h2_step: null
```
