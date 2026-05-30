---
schema_version: 1
id: SOL-20260530-001
type: solution
status: pending
owner: 장태욱
security: internal
confidence: medium
related:
  - docs/02_design/h2-plugin-claude-code.md
  - .harness-helm/runs/h2-plugin-claude-code/20260530-000047-h2-build/build.md
module:
  - workflow
tags:
  - semver
  - version
  - downgrade
  - cli
tests:
  - .harness-helm/runs/h2-plugin-claude-code/20260530-001146-h2-test/test.md Smoke 5
human_verified_by: 장태욱
---

# Solution: SemVer 2.0.0 normalize·compare·downgrade detection helper (`release/_semver.py`)

## Problem

Release 도구에서 version을 단순 문자열로 비교하면 `0.10.0 < 0.9.0`(string sort) 같은 오판이 발생한다. plugin payload version·marker·target install-manifest의 `package_version` 등 여러 곳에서 같은 schema로 정렬·비교·downgrade 차단이 필요한데 외부 lib(semver, packaging) 도입은 release 도구의 의존성 노출을 늘리는 비용이 든다.

## Solution

SemVer 2.0.0 regex parser + 비교 함수 + downgrade 판정 + CLI를 단일 module(`release/_semver.py`)에 두고 release 도구·doctor command·smoke 전부가 같은 helper를 호출한다.

```python
# release/_semver.py
class SemVer(NamedTuple):
    major: int; minor: int; patch: int
    prerelease: tuple[str, ...]; build: str
    def normalized(self) -> str: ...

def parse(s: str) -> SemVer: ...     # SEMVER_RE 검증, invalid는 ValueError
def normalize(s: str) -> str: ...    # canonical 형식 (v prefix strip 포함)
def compare(a, b) -> int: ...        # -1 / 0 / 1, build metadata 무시
def is_downgrade(target: str, payload: str) -> bool: ...   # equal != downgrade
```

CLI:

```text
python3 release/_semver.py normalize v1.0.0          # -> "1.0.0"
python3 release/_semver.py compare 0.10.0 0.9.0      # -> "1"  (exit 0)
python3 release/_semver.py is-downgrade 1.0.0 0.9.0  # -> "true"  (exit 0)
python3 release/_semver.py is-downgrade 0.9.0 1.0.0  # -> "false" (exit 1)
```

`is-downgrade`는 shell guard 패턴 호환:

```sh
if python3 release/_semver.py is-downgrade "$TARGET_V" "$PAYLOAD_V"; then
  echo "downgrade blocked"
  exit 1
fi
```

## Why This Works

- SemVer 2.0.0 regex로 입력을 엄격 검증해 invalid에 `ValueError` + CLI exit 2를 던지므로 호출자가 잘못된 version을 silent하게 받지 않는다
- spec의 prerelease·build metadata 분기를 정확히 구현 (numeric vs alphanumeric identifier 비교, shorter prerelease 낮음, build metadata는 precedence 무시)
- module + CLI를 한 파일에 두어 Python 호출자(builder)와 shell 호출자(doctor.md Bash) 모두가 같은 검증을 통과
- 외부 의존 없음 → release 도구의 supply chain surface 미증가

## When NOT to Use

- 이미 `semver` PyPI lib 같은 검증된 외부 의존을 받아들이는 프로젝트
- SemVer가 아닌 version schema(CalVer, integer sequence 등)를 쓰는 도구
- prerelease·build metadata가 필요 없는 단순 정수 version compare

## Verification

- tests: 26건 unit smoke + 4건 CLI smoke (`.harness-helm/runs/h2-plugin-claude-code/20260530-001146-h2-test/test.md` Smoke 5)
- design Verification Strategy 명시 케이스 3건 (`0.10.0 > 0.9.0`, `1.0.0-rc.1 < 1.0.0`, `v1.0.0 == 1.0.0`) 모두 통과
- spec 준수 케이스(`1.0.0-alpha < 1.0.0-alpha.1`, `1.0.0-beta.2 < 1.0.0-beta.11`, `1.0.0+build == 1.0.0`) 통과
- invalid input 5건(`'1'`, `'1.0'`, `'foo'`, `'1.0.0.0'`, `'01.0.0'`) 모두 ValueError
- human_verified_by: 장태욱

## Supersedes

- 없음 (이전에는 release 도구가 version을 직접 다루지 않았음)

## References

- design §9 (Update / Reinstall Policy의 Version 비교 규약)
- design Verification Strategy의 Version Compare Validation
- build round 2 Step 13 결정 (`release/_semver.py` 신규)
