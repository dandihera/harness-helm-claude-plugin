---
schema_version: 1
id: "LEARN-20260529-002"
type: learning
status: draft
owner: "tw-jang"
security: internal
confidence: medium
related:
  - "docs/04_report/h2-install-powershell.md"
  - "docs/02_design/h2-install-powershell.md"
  - "docs/40_knowledge/learnings/powershell-path-combine-portability.md"
module:
  - workflow
tags:
  - powershell
  - process
  - splatting
  - launcher
human_verified_by: "tw-jang"
---

<!-- harness-helm learning template. status enum: draft|pending|verified|stable|deprecated. See 0102 Frontmatter Schema. -->

# Learning: launcher가 selector 인자를 요구할 때 `@{ Command; PrefixArgs }` 구조체 + splatting으로 호출한다

## Context

`release/install-package/h2-install.ps1`의 `Resolve-Python`을 작성하면서 Windows의 `py` launcher가 Python 3을 선택하기 위해 `py -3` 형태의 selector 인자를 요구한다는 점을 다뤘다. 초기 설계 검토에서 \"`py -3`\"를 단일 string으로 합쳐 반환하면 호출 시 splatting이 깨진다는 우려가 나왔고, design 단계에서 `@{ Command; PrefixArgs }` 구조체 반환 방식으로 수렴했다.

## Learning

PowerShell에서 external executable을 호출할 때, launcher가 prefix selector 인자(예: `py -3`, `dotnet run --`, `python -m foo`)를 요구하면:

1. **금지**: `'py -3'`처럼 selector를 명령어 이름에 합쳐 string으로 반환. 호출 시 `& 'py -3' ...` 또는 `& $cmd ...`에서 PowerShell이 `py -3`를 단일 실행 파일 이름으로 해석해 ENOENT가 발생하거나, 합쳐진 string이 그대로 첫 인자로 전달되어 의도와 다르게 동작.
2. **권장**: 구조체로 분리해 반환.

   ```powershell
   function Resolve-Python {
       $candidates = @(
           @{ Command = 'python';  PrefixArgs = @()       },
           @{ Command = 'python3'; PrefixArgs = @()       },
           @{ Command = 'py';      PrefixArgs = @('-3')   }
       )
       foreach ($c in $candidates) {
           if (Get-Command $c.Command -ErrorAction SilentlyContinue) {
               return $c
           }
       }
       return $null
   }
   ```

3. **호출**: `& $resolved.Command @($resolved.PrefixArgs) <script-path> @Args` 한 형태로 통일. `@(...)` splatting은 빈 배열이면 인자 0개로 전개되고, 비어 있지 않으면 각 토큰이 독립 인자로 전달된다.

핵심: prefix selector는 \"argument\"이지 \"executable name의 일부\"가 아니다. 데이터 모델을 그렇게 표현하면 호출 코드는 모든 launcher를 동일한 한 줄로 다룰 수 있다.

## Evidence

- tests:
  - `.harness-helm/runs/h2-install-powershell/20260529-004048-h2-test/test.md` T5 — design step mapping에서 호출 형식 일관성 확인
  - `.harness-helm/runs/h2-install-powershell/20260529-004906-h2-test/test.md` T5 — S1 패치 후에도 위임 호출 contract 불변 확인
  - 실 호출은 `release/install-package/h2-install.ps1:76`에 단일 형태로 작성됨
- human_verified_by: tw-jang
- 발견/검증 출처: DESIGN-20260529-001 Resolve-Python contract, 외부 review 피드백

## Apply When

- PowerShell wrapper에서 다수 후보 launcher 중 첫 번째 사용 가능한 것을 선택해 호출해야 할 때.
- launcher가 wrapped command 선택을 위해 prefix 인자를 요구할 때 (예: `py -3`, `python -m`, `dotnet run --`, `node --experimental-modules`).
- 호출 형식을 한 곳으로 통일해 prefix-arg 있는 케이스와 없는 케이스를 같은 코드 경로로 다루고 싶을 때.

## Do Not Apply When

- 단일 고정 executable만 호출하는 단순 경우 — `& $exe @Args` 한 줄로 충분.
- launcher selection 자체를 PATH 변경, alias 등 외부 환경으로 위임하는 경우.
- POSIX shell wrapper처럼 splatting 개념이 없는 환경 (이 경우 `exec`나 `$@` 사용).

## References

- Report: `docs/04_report/h2-install-powershell.md`
- Design Resolve-Python contract: `docs/02_design/h2-install-powershell.md` (Interfaces / Data Flow)
- 실 wrapper 호출: `release/install-package/h2-install.ps1` (L37-47 helper, L76 호출)
- 관련 learning: `docs/40_knowledge/learnings/powershell-path-combine-portability.md` (같은 wrapper에서 도출된 portability 패턴)
