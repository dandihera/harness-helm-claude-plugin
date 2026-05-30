---
schema_version: 1
id: LEARN-20260530-003
type: learning
status: pending
owner: 장태욱
security: internal
confidence: medium
related:
  - docs/02_design/h2-plugin-claude-code.md
  - .harness-helm/runs/h2-plugin-claude-code/20260529-234747-h2-build/build.md
module:
  - workflow
tags:
  - refactor
  - parity
  - tooling
human_verified_by: 장태욱
---

# Learning: release tooling refactor는 byte-equal parity smoke로 회귀 방지

## Context

release 도구(zip builder, plugin builder 등)가 같은 manifest source를 쓰도록 하려면 monolithic main()에서 manifest parsing과 staging helper를 별도 module로 추출해야 한다. helper 추출은 외부 동작이 변하지 않아야 하지만 release 도구는 다양한 file copy/exclude/template 분기를 가지므로 회귀를 놓치기 쉽다.

## Learning

refactor 전후 builder 두 개를 같은 입력으로 실행하고 출력 디렉터리를 `diff -r`로 비교해 차이가 없음을 회귀 신호로 사용한다. 절차:

1. 추출 전 builder를 `git show HEAD:<path>` 로 별도 임시 위치에 저장
2. refactor 후 builder 작성
3. 같은 인자로 둘 다 실행 (출력 디렉터리만 다르게)
4. `diff -r <old-out> <new-out>` 결과가 비어 있으면 PASS
5. parity 통과 후에야 새 builder가 정식 source가 됨

```text
git show HEAD:release/build-zip-payload.py > /tmp/old/build-zip-payload-old.py
python3 /tmp/old/build-zip-payload-old.py --manifest <m> --source-root . --payload /tmp/old/payload
python3 release/build-zip-payload.py        --manifest <m> --source-root . --payload /tmp/new/payload
diff -r /tmp/old/payload /tmp/new/payload && echo "PARITY OK"
```

`diff -r`는 file content + tree structure + permissions를 모두 검사하므로 빠진 file, 추가된 file, 변경된 file, 그리고 누락된 디렉터리를 한 번에 잡는다. 이 절차를 release 도구 refactor의 표준 입력 검사로 둔다.

## Evidence

- tests: `.harness-helm/runs/h2-plugin-claude-code/20260529-234747-h2-build/build.md` Step 8 smoke (`build-zip-payload.py` refactor 후 133 files, `diff -r` 차이 없음)
- human_verified_by: 장태욱

## Apply When

- 기존 monolithic release script를 helper 추출로 refactor할 때
- 둘 이상의 builder가 같은 source(manifest, template) 공유로 통합되는 경우
- file copy/exclude 분기가 많아 unit test로 모든 path를 cover하기 어려운 경우

## Do Not Apply When

- builder output이 timestamp·random·environment-dependent value를 포함해 두 run이 자연히 다른 경우 (이 때는 helper 추출 단위로 unit test가 필요)
- builder가 외부 API 호출을 동반해 sandbox 격리가 어려운 경우 (mock 필요)
- refactor가 byte-equal을 의도적으로 깨는 경우 (예: format 변경, schema bump). 이 때는 별도 expected-diff 정의 후 비교

## References

- design Verification Strategy의 Package Build Validation regression smoke
- ce-doc-review round-2의 Step 8 confirmation
