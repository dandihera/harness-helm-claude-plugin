---
schema_version: 1
id: REL-20260607-001
type: release
status: verified
owner: 장태욱
security: internal
confidence: high
tests:
  - docs/_archive/2026-06/0607-0936_release-build-evidence-verification-scope_178/runs/test.md
  - docs/_archive/2026-06/0607-0936_release-build-evidence-verification-scope_178/04.release-build-evidence-verification-scope_178.report.md
  - https://github.com/dandihera/harness-helm/issues/178#issuecomment-4640915633
related:
  - https://github.com/dandihera/harness-helm/issues/178
  - https://github.com/dandihera/harness-helm/issues/178#issuecomment-4640909078
  - https://github.com/dandihera/harness-helm/issues/178#issuecomment-4640915633
  - https://github.com/dandihera/harness-helm/issues/175
  - https://github.com/dandihera/harness-helm/pull/177
  - docs/_archive/2026-06/0607-0936_release-build-evidence-verification-scope_178/01.release-build-evidence-verification-scope_178.plan.md
  - docs/_archive/2026-06/0607-0936_release-build-evidence-verification-scope_178/02.release-build-evidence-verification-scope_178.design.md
  - docs/_archive/2026-06/0607-0936_release-build-evidence-verification-scope_178/02.release-build-evidence-verification-scope_178.analysis.design.md
  - docs/_archive/2026-06/0607-0936_release-build-evidence-verification-scope_178/03.release-build-evidence-verification-scope_178.code.review.md
  - docs/_archive/2026-06/0607-0936_release-build-evidence-verification-scope_178/04.release-build-evidence-verification-scope_178.report.md
module:
  - workflow
tags:
  - release
  - verification
  - go-cutover
---

# Release Build Verification: 2026-06-07

## Summary

#175와 PR #177 이후 release build 경로를 추적 가능한 운영 증적으로 남긴다. 이 기록은 source release helper Python 제거 이후 실제 build 산출 경로, Go asset matrix, Claude plugin local marketplace sync, payload residual sweep 결과를 한 곳에서 확인하기 위한 문서다.

검증 대상 version은 install marker 기준 `v0.14.0`이다. `/tmp` 아래 산출물은 재현용 임시 경로이며 영구 보관 artifact가 아니다.

## Verification Matrix

| Check | Command | Output | Result | Evidence | Limits |
|---|---|---|---|---|---|
| install zip 실제 빌드 | `sh release/build-zip.sh --output-dir /tmp/hh-release-test-dist` | `/tmp/hh-release-test-dist/h2-install-v0.14.0.zip` | pass | initial run failed because `.harness-helm/bin/harness` was missing; after `go -C src build -o ../.harness-helm/bin/harness ./cmd/harness`, rerun passed and wrote `h2-install-v0.14.0.zip` (247407 bytes). The command also ran Go tests and Go asset matrix. | `/tmp` 산출물은 휘발성 |
| Go asset matrix 직접 빌드 | `sh release/build-go-assets.sh --version v0.14.0 --output-dir /tmp/hh-release-test-dist` | `/tmp/hh-release-test-dist/harness-v0.14.0-*` 및 `.sha256` | pass | wrote 5 assets: darwin-arm64, darwin-amd64, linux-amd64, linux-arm64, windows-amd64.exe; matching `.sha256` files exist. | `build-zip`도 내부에서 같은 matrix를 경유함 |
| Claude plugin non-dry-run local marketplace sync | `sh release/build-claude-plugin.sh --dist /tmp/hh-plugin-test-dist --marketplace-dir /tmp/hh-marketplace-test` | `/tmp/hh-plugin-test-dist/claude-plugin-marketplace-h2-0.14.0*`, `/tmp/hh-marketplace-test/.claude-plugin`, `/tmp/hh-marketplace-test/plugins/h2` | pass | staged payload 169 files, wrote plugin zip, synced `.claude-plugin` and `plugins/h2` into local marketplace dir. | public marketplace push나 GitHub Release publish는 검증하지 않음 |
| install zip runtime Python residual sweep | extract 후 `h2-install/payload/**`에서 `docs/**`를 제외한 negative sweep | `/tmp/hh-release-test-install/h2-install/payload` | pass | file-name sweep output 없음; content sweep with `-g '!docs/**'` output 없음. Broad documentation reference sweep did match historical docs, so docs references are tracked separately from runtime residuals. | `payload/docs/**` historical references are not runtime helper/runtime residuals |
| plugin runtime Python residual sweep | plugin zip extract 후 `release/h2-install/payload/**`에서 `docs/**`를 제외한 negative sweep | `/tmp/hh-plugin-test-unzip/claude-plugin-marketplace-h2-0.14.0` | pass | file-name sweep output 없음; content sweep with `-g '!release/h2-install/payload/docs/**'` output 없음. | `payload/docs/**` historical references are not runtime helper/runtime residuals |

## Residual Sweep Scope

residual sweep은 release payload에 실제 포함되는 파일만 대상으로 한다.

- install zip: extracted `h2-install/payload/**`, runtime residual 판정은 `payload/docs/**` 제외
- plugin package: plugin zip extraction의 `release/h2-install/payload/**`, runtime residual 판정은 `payload/docs/**` 제외

검사 범위에서 제외하는 항목:

- `docs/_archive/**`
- `.harness-helm/runs/**`
- source repository 전체 문서 history

제외 이유는 historical context와 canonical knowledge 문서에 과거 Python helper 이름이 정상적으로 남아 있을 수 있기 때문이다. 실제 broad content sweep은 `docs/40_knowledge/solutions/semver-2-0-0-helper-with-cli.md`, `docs/40_knowledge/solutions/doctor-first-guard-preamble-injection.md`, `docs/50_operations/runbooks/guard-version-drift-runtime-smoke.md`의 historical references를 잡았다. 이 항목들은 runtime helper/runtime 파일 잔존물이 아니므로 release runtime residual 판정에서 제외한다.

## Marketplace Sync Limits

`build-claude-plugin` non-dry-run 검증은 임시 local marketplace tree에 `.claude-plugin`과 `plugins/h2`가 sync되고 metadata validation이 통과했음을 뜻한다.

이 검증은 다음을 보장하지 않는다.

- public marketplace repository에 push됨
- GitHub Release가 생성됨
- 설치된 Claude plugin auto-update가 발생함

## Release Checklist

다음 릴리즈 전에 반복할 최소 checklist:

1. `sh release/build-zip.sh --output-dir /tmp/hh-release-test-dist`
2. `sh release/build-go-assets.sh --version v{version} --output-dir /tmp/hh-release-test-dist`
3. `sh release/build-claude-plugin.sh --dist /tmp/hh-plugin-test-dist --marketplace-dir /tmp/hh-marketplace-test`
4. install zip을 extract하고 `h2-install/payload/**`에서 Python helper/runtime residual sweep을 실행한다.
5. plugin zip을 extract하고 payload tree에서 Python helper/runtime residual sweep을 실행한다.
6. public marketplace publish 여부는 별도 release/publish checklist에서 검증한다.

## Follow-up

- #175 archived report는 수정하지 않는다.
- #178 issue comment로 이 증적 위치를 추적한다: https://github.com/dandihera/harness-helm/issues/178#issuecomment-4640909078
- h2 archive 완료 위치는 후속 #178 issue comment에 기록했다: https://github.com/dandihera/harness-helm/issues/178#issuecomment-4640915633
