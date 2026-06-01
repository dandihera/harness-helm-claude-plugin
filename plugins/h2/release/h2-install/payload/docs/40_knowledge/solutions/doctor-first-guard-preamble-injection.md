---
schema_version: 1
id: SOL-20260530-002
type: solution
status: verified
owner: 장태욱
security: internal
confidence: medium
related:
  - docs/_archive/2026-05/0530-004105_h2-plugin-claude-code/h2-plugin-claude-code.design.md
  - docs/40_knowledge/learnings/plugin-target-command-collision-single-scope.md
  - docs/40_knowledge/learnings/multi-target-guard-single-signal.md
module:
  - workflow
tags:
  - guard
  - first-run
  - preamble
  - idempotent
tests:
  - .harness-helm/runs/h2-plugin-claude-code/20260530-001146-h2-test/test.md Smoke 7·8·9
human_verified_by: 장태욱
---

# Solution: payload staging 후처리로 doctor-first guard preamble 주입 (`apply_guard_preambles`)

## Problem

Plugin install로 target에 펼쳐지는 `.claude/commands/<namespace>/*.md` 명령들이 "사전 조건이 충족되지 않으면 자동으로 중단하고 안내"하는 first-run gate를 가져야 한다. install 엔진(`harness.py install`)이나 manifest schema를 수정해 처리할 수도 있지만 release 도구의 "engine 재구현 금지" 원칙과 충돌하며, 한 번 install된 target 명령에 일관되게 guard를 적용하기 어렵다.

## Solution

manifest 기반 payload staging이 끝난 직후에 후처리 함수로 guard preamble을 inject한다. helper는 staging 디렉터리만 받아 frontmatter 직후에 한정된 markdown 본문을 끼워 넣고, 이미 inject된 파일은 idempotent skip한다. zip builder와 plugin builder가 같은 helper를 호출하므로 두 배포면 모두 일관된 guard를 받는다.

```python
# release/_payload_lib.py
GUARD_PREAMBLE = """## doctor-first guard

`/h2:doctor`가 target에 install-manifest를 만들기 전에는 이 command를 실행하지 않는다.

1. `Read` 또는 `Bash`로 `<target>/.harness-helm/install-manifest.json` 존재를 확인한다.
2. 파일이 없으면 다음 한 줄만 출력하고 즉시 중단한다 (skill·tool 호출 금지):

```text
/h2:doctor를 먼저 실행하세요.
```

3. 파일이 있으면 아래의 원래 command 본문으로 진행한다.

---

"""

GUARD_TARGET_DIR = ".claude/commands/h2"
GUARD_TARGET_EXCLUDE = ("doctor.md",)


def apply_guard_preambles(payload_root: Path) -> tuple[int, list[str]]:
    """Inject GUARD_PREAMBLE between frontmatter and body.

    - GUARD_TARGET_EXCLUDE에 속한 파일은 skip
    - frontmatter 없는 파일은 skip + reason 기록
    - 이미 preamble이 있으면 idempotent skip
    - 위 조건을 통과한 파일만 inject
    Returns (injected_count, skipped_reasons).
    """
    ...
```

build 마지막 단계에서 호출:

```python
copied, missing = stage_payload_entries(entries, src_root, payload)
# ...missing 처리...
injected, _skipped = apply_guard_preambles(payload)
```

## Why This Works

- 후처리이므로 manifest schema·install 엔진을 수정하지 않는다 → "engine 재구현 금지" 원칙 충족
- frontmatter 직후에 inject해 명령의 YAML 메타데이터(allowed-tools 등)는 그대로 유지
- idempotency 검사로 같은 staging 디렉터리에 두 번 호출해도 중복 inject 없음
- zip builder와 plugin builder가 같은 helper를 호출하므로 두 배포면이 byte-equal guard를 받음
- LEARN-20260530-002의 "per-target source-of-truth 단독" 원칙을 preamble 본문에서 직접 명시 (install-manifest만 확인) → multi-target false-pass 방지

## When NOT to Use

- guard 본문이 명령마다 달라야 하는 경우 (이 함수는 단일 preamble 가정. 다중 preamble은 별도 dispatcher 필요)
- frontmatter 없는 markdown 명령을 사용하는 plugin (현 helper는 frontmatter 부재 시 skip)
- guard signal이 per-target이 아니라 전역인 경우 (이 패턴은 per-target source-of-truth와 짝)
- 모델이 markdown instruction을 무시할 수 있는 환경에서 hard gate가 필요한 경우 (preamble은 advisory에 가까움. 정말 강제하려면 wrapper script 단위 차단 필요)

## Verification

- tests: smoke 7 (target apply 후 plan.md preamble 존재), smoke 8 (idempotency — 재실행 시 헤딩 count = 1), smoke 9 (multi-target false-pass 회귀 정적 검증). 모두 `.harness-helm/runs/h2-plugin-claude-code/20260530-001146-h2-test/test.md`에 기록
- `build-zip-payload.py`와 `build-claude-plugin.py` 두 builder 모두 helper 호출 후 12 h2 command에 일관 inject 확인
- human_verified_by: 장태욱

## Supersedes

- 없음 (기존 release 도구는 guard preamble을 다루지 않았음)

## References

- design §6 (Bootstrap Helper Boundary) / §7 (h2 Command Guard) / §2 (Plugin Package Layout)
- LEARN-20260530-001 (plugin/target command collision 옵션 A 패턴)
- LEARN-20260530-002 (multi-target guard 판정 신호 단일화)
- build round 2 Step 6 결정 (옵션 b payload staging 후처리)
