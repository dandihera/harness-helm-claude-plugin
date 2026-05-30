---
schema_version: 1
id: "LEARN-20260529-001"
type: learning
status: draft
owner: "tw-jang"
security: internal
confidence: medium
related:
  - "docs/04_report/h2-install-powershell.md"
  - "docs/03_review/code/h2-install-powershell.md"
module:
  - workflow
tags:
  - powershell
  - path
  - cross-platform
  - portability
human_verified_by: "tw-jang"
---

<!-- harness-helm learning template. status enum: draft|pending|verified|stable|deprecated. See 0102 Frontmatter Schema. -->

# Learning: PowerShell 경로 결합은 `[System.IO.Path]::Combine`을 사용해 cross-platform 안전성을 보장한다

## Context

`release/install-package/h2-install.ps1` 작성 중 payload 경로를 `Join-Path $PackageRoot 'payload\.harness-helm\scripts\harness.py'`로 작성했다. Windows에서는 동작했지만 macOS PowerShell 7 환경에서 `Test-Path`가 항상 `$false`를 반환했다. 원인은 child 인자의 `\`가 PowerShell on Unix에서 path separator가 아니라 file name의 literal 문자로 해석되었기 때문이다.

코드 리뷰(REVIEW S1)에서 발견되었고, h2-test 재실행 단계에서 `[System.IO.Path]::Combine`으로 교체하여 해소했다.

## Learning

PowerShell 스크립트에서 다단계 경로를 결합할 때, 다음 우선순위로 cross-platform 안전한 방법을 선택한다.

1. **다단계 경로(3 segment 이상)**: `[System.IO.Path]::Combine($base, 'a', 'b', 'c')` 사용. .NET 표준 라이브러리가 runtime OS의 native separator(`\` on Windows, `/` on macOS/Linux)로 결합한다.
2. **단순 2단계**: `Join-Path $parent $child` 사용. child에는 `\`나 `/` 같은 separator를 포함하지 않는다.
3. **금지**: hardcoded `\` 또는 `/`가 포함된 multi-segment string을 `Join-Path`나 `[IO.Path]::Combine`에 전달.

핵심: hardcoded separator는 Windows-only 환경 가정을 코드에 박는다. 같은 wrapper가 macOS/Linux PowerShell 7에서 사전 검증되거나 향후 cross-platform 사용 가능성이 있다면 처음부터 OS-native 결합을 사용한다.

## Evidence

- tests:
  - `.harness-helm/runs/h2-install-powershell/20260529-004906-h2-test/test.md` T5 + T-portability
  - `python3 -c "import os; print(os.path.join('payload', '.harness-helm', 'scripts', 'harness.py'))"` → POSIX `/` 결합 확인 (`Path.Combine`도 동일 동작)
  - 본 패치 적용 후 zip 재빌드 시 wrapper 크기 +192 bytes, POSIX 회귀 검증 통과
- human_verified_by: tw-jang
- 발견 출처: code review S1 (REVIEW-20260529-001)

## Apply When

- PowerShell 스크립트에서 3단계 이상의 경로를 결합할 때.
- 같은 wrapper가 Windows 외 환경(PowerShell on macOS/Linux)에서 한 번이라도 실행될 가능성이 있을 때 — 회귀 테스트, POSIX parity 사전 점검 등.
- 외부 사용자가 zip artifact로 받아 다양한 환경에서 실행할 가능성이 있는 wrapper.

## Do Not Apply When

- 명시적으로 Windows-only registry 경로(`HKLM:\...`)처럼 `\`가 의미를 갖는 경우.
- PowerShell 1단계 단순 결합(`Join-Path` 한 번이면 충분한 경우).
- 외부 명령에 전달하는 string이 이미 OS-specific 형식을 강제하는 경우 (그 경우는 string 그대로 전달).

## References

- Report: `docs/04_report/h2-install-powershell.md`
- Code review S1: `docs/03_review/code/h2-install-powershell.md`
- 패치 적용 wrapper: `release/install-package/h2-install.ps1` (line 18-22)
- 재검증 test run: `.harness-helm/runs/h2-install-powershell/20260529-004906-h2-test/test.md`
