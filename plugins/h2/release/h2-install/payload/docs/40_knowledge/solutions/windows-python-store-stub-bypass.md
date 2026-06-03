---
schema_version: 1
id: "SOL-20260529-001"
type: solution
status: pending
owner: "tw-jang"
security: internal
confidence: medium
related:
  - "docs/_archive/2026-05/0529-0104_h2-install-powershell/h2-install-powershell.report.md"
  - "docs/_archive/2026-05/0529-0104_h2-install-powershell/h2-install-powershell.analysis.design.md"
source_references:
  - "cookbooks/0700-runbooks/0701-h2-install-build-and-install.md"
module:
  - workflow
tags:
  - windows
  - python
  - powershell
  - troubleshooting
human_verified_by: "tw-jang"
---

<!-- harness-helm solution template. status enum: draft|pending|verified|stable|deprecated.
     confidence: high은 human_verified_by/tests/source_pr/source_trace 중 하나 이상 필요.
     See 0102 Frontmatter Schema, 0202 Operations Ownership. -->

# Solution: Windows에서 Microsoft Store python stub 매치를 우회한다

## Problem

Windows 10/11 기본 환경에서 `python`이 PATH에 존재하지만 실제로는 `C:\Users\<user>\AppData\Local\Microsoft\WindowsApps\python.exe` (Microsoft Store launcher stub)인 경우가 있다. 비대화형 install script나 wrapper가 `Get-Command python` 또는 `where python`으로 후보 발견에 성공해 stub을 실행하면, Store 설치 페이지가 GUI로 열리면서 script가 사용자 확인을 기다리며 멈춘다. CI나 unattended install에서 hang 또는 timeout으로 이어진다.

`release/install-package/h2-install.ps1`의 `Resolve-Python`은 이 케이스를 사전 판별하지 않는 것으로 설계되었고(ANALYSIS F2), 운영 측 우회 가이드로 처리한다.

## Solution

사용자 또는 운영자 측에서 다음 3가지 중 하나로 우회한다 (우선순위 순).

```text
1. 정식 Python 3.10+ 설치 (권장)
   - https://www.python.org/downloads/ 에서 installer 다운로드
   - 설치 시 "Add python.exe to PATH" 체크
   - 효과: 정식 python.exe가 stub보다 PATH 우선순위가 되어 자동으로 매치됨

2. py launcher 설치 후 사용
   - 정식 Python installer 설치 시 "Install py launcher" 옵션을 함께 선택
   - wrapper가 자동으로 `py -3` (3순위 후보)를 매치하여 호출
   - 효과: `python` PATH가 stub이어도 `py` launcher가 별도 경로로 인식됨

3. Microsoft Store python 별칭 비활성화
   - 설정 → 앱 → 앱 실행 별칭 (Settings → Apps → App execution aliases)
   - "앱 설치 관리자" 항목의 "python.exe" / "python3.exe" 별칭 끄기
   - 효과: stub이 PATH에서 사라져 wrapper가 다음 후보로 fall-through
```

자동화 시나리오(CI/MDM 배포 등)에서는 1번을 표준화하고, 사용자 워크스테이션 ad-hoc 대응에서는 2번 또는 3번을 안내한다.

## Why This Works

- 정식 Python(`python.org`) 설치는 `C:\Program Files\Python3xx\` 또는 `%LOCALAPPDATA%\Programs\Python\Python3xx\`에 실제 interpreter를 배치하고 PATH 우선순위를 stub 앞에 둔다 → `Get-Command python`이 정식 binary를 매치.
- `py` launcher는 `C:\Windows\py.exe`로 설치되며 Store stub과 별도 경로다 → wrapper의 `Resolve-Python`이 3순위 후보로 매치.
- 앱 실행 별칭은 user-level PATH 우회 메커니즘이다. 비활성화 시 stub이 PATH lookup에서 제외된다.

## When NOT to Use

- 사용자가 Microsoft Store python을 의도적으로 사용 중인 경우 (개인 환경 사전 동의 하). 이 경우 stub이 아니라 실제 Store-installed Python을 사용 중이므로 매치 후 정상 동작한다.
- Linux/macOS 환경 — 이 문제는 Windows 10/11에서만 발생.
- Python 외 다른 interpreter(node, ruby 등)는 별도 stub 케이스가 없거나 패턴이 다르다.

## Verification

- tests: 본 wrapper의 `Resolve-Python` 자체는 stub 판별을 하지 않음을 정적 점검(`.harness-helm/runs/h2-install-powershell/20260529-004048-h2-test/test.md` T5)에서 확인. 실 stub 환경 동작은 Windows 검증자 위임 (test.md N5).
- human_verified_by: tw-jang
- 출처: ANALYSIS F2 (`docs/_archive/2026-05/0529-0104_h2-install-powershell/h2-install-powershell.analysis.design.md`), Runbook Section C 트러블슈팅 (`cookbooks/0700-runbooks/0701-h2-install-build-and-install.md`).

## Pending Reason

운영 우회 가이드는 현재 runbook과 wrapper 설계에 맞지만, Microsoft Store python stub이 있는 실제 Windows 10/11 환경에서의 재현 검증은 test.md N5로 위임된 상태다. Windows 검증자가 1번 정식 Python 설치, 2번 `py -3` launcher, 3번 앱 실행 별칭 비활성화 중 최소 하나를 실제 환경에서 확인한 뒤 `verified`로 승격한다.

## Supersedes

- 신규 solution. supersedes 대상 없음.

## References

- Runbook Section C 트러블슈팅: `cookbooks/0700-runbooks/0701-h2-install-build-and-install.md`
- Report: `docs/_archive/2026-05/0529-0104_h2-install-powershell/h2-install-powershell.report.md`
- Analysis F2: `docs/_archive/2026-05/0529-0104_h2-install-powershell/h2-install-powershell.analysis.design.md`
- 관련 wrapper: `release/install-package/h2-install.ps1` (Resolve-Python helper)
- Microsoft 공식 docs: \"Manage app execution aliases\" (설정 → 앱 → 앱 실행 별칭)
