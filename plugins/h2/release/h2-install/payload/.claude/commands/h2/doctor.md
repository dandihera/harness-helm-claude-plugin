---
name: doctor
description: harness-helm plugin의 first-run command. plugin install 직후 사용자가 실행하면 환경 사전점검 → Go bootstrap dry-run preview → 사용자 승인 → target runtime 설치까지 한 흐름으로 처리합니다. 사용자가 별도로 /h2:bootstrap 같은 명령을 알 필요가 없습니다.
user-invocable: true
argument: optional
allowed-tools: [Bash, Read]
---

# h2:doctor

`/h2:doctor`는 `h2` Claude Code plugin의 first-run command입니다. plugin install 직후 첫 호출은 사용자 환경을 점검하고 target project에 h2 runtime surface를 부트스트랩합니다.

## Inputs (optional)

```text
/h2:doctor
/h2:doctor --dry-run
/h2:doctor --target <path>
/h2:doctor --backup
/h2:doctor --allow-non-git
/h2:doctor --plugin-root <path>
```

기본값:

- `--target`: 지정하지 않으면 현재 위치에서 `git rev-parse --show-toplevel`로 repository root를 자동 감지하고, 실패하면 현재 working directory
- `--dry-run`: false (false면 사용자 승인 후 실제 적용)
- `--backup`: false (managed block 외부 수정이 있는 파일에 권장)
- `--allow-non-git`: false (`.git` 없으면 중단)

## Execution Sequence

이 command는 prompt template이며, 모델이 다음 순서로 `Bash`·`Read` tool을 호출해 진행한다.

1. **Target resolution**
   - `--target`이 있으면 그 경로를 target으로 결정.
   - `--target`이 없으면 `Bash`로 `git rev-parse --show-toplevel`을 실행해 현재 위치가 속한 git repository root를 target으로 결정.
   - `git rev-parse --show-toplevel`이 실패하면 `pwd`를 target으로 결정.
   - `Bash`로 `test -d <target>/.git`을 확인. `.git`이 없고 `--allow-non-git`도 없으면 안내 후 중단.

2. **Plugin root resolution (다음 우선순위)**
   1. `--plugin-root <path>`가 주어지면 그 경로.
   2. 환경변수 `CLAUDE_PLUGIN_ROOT`가 설정되어 있으면 그 경로.
   3. `Read`로 `~/.claude/plugins/installed_plugins.json`을 읽고 `h2@dandisoft-harness-helm` entry의 `installPath`를 사용.
   4. `Bash`로 `ls -d ~/.claude/plugins/cache/dandisoft-harness-helm/h2/*` 중 최신 version을 선택.
   - 모두 실패하면 사용자에게 `--plugin-root <path>`를 제공하도록 안내 후 중단.

3. **Preflight**
   - **IMPORTANT**: h2 runtime은 Go binary(`harness`)다. `python3`, `harness.py`, `harness_lib/` 는 v0.20.0에서 완전히 제거됐다. Python 버전 체크를 실행하거나 `harness.py`를 호출하지 말 것.
   - `Bash`로 `test -f <plugin-root>/release/h2-install/MANIFEST.txt` 확인. 없으면 plugin payload 누락 FAIL.
   - `Bash`로 `<plugin-root>/release/h2-install/h2-install-v*.txt` marker 중 최고 version을 확인.
   - host platform이 `darwin/arm64`, `darwin/amd64`, `linux/amd64`, `linux/arm64`, `windows/amd64` 중 하나인지 확인. Windows ARM64 등 unsupported platform이면 remediation과 함께 FAIL.
   - `H2_HARNESS_RELEASE_BASE`가 주어졌으면 해당 release base에서 선택된 Go binary asset과 `<asset>.sha256`이 접근 가능한지 확인. 주어지지 않았으면 plugin/public release asset base를 사용한다.
   - 권장 plugin (`superpowers`, `gstack`, `compound-engineering`) 설치 여부를 `~/.claude/plugins/installed_plugins.json`에서 확인. 누락은 WARN으로 안내(bootstrap 차단하지 않음).

4. **Bootstrap dry-run preview**
   - `Bash`로 다음을 실행하여 변경 사항을 미리 보여준다:

```text
h2-install.sh \
  --target <target> \
  --dry-run \
  [--backup] [--allow-non-git]
```

   Windows target에서는 PowerShell equivalent를 사용한다:

```text
h2-install.ps1 \
  --target <target> \
  --dry-run \
  [--backup] [--allow-non-git]
```

   - dry-run 결과를 그대로 사용자에게 출력하고, target path / package version / 변경 파일 / backup 여부를 명시.

5. **User approval gate**
   - `--dry-run` flag가 주어진 경우는 여기서 종료.
   - 그렇지 않으면 사용자에게 "Apply / Cancel" 응답을 명시적으로 요청한다. Cancel 시 변경 없이 종료.

6. **Apply**
   - 사용자가 Apply를 선택하면 같은 명령을 `--dry-run` 없이 실행한다:

```text
h2-install.sh \
  --target <target> \
  [--backup] [--allow-non-git]
```

   Windows target에서는 `h2-install.ps1`을 같은 argument로 실행한다.

7. **Post-apply result**
   - `<target>/.harness-helm/install-manifest.json` 경로를 출력.
   - `<target>/.harness-helm/bin/harness(.exe)` 경로와 `install-manifest.json.runtime_binary` evidence를 출력.
   - `<target>/.harness-helm/scripts/bin/harness(.exe)`가 존재하면 stale legacy path로 보고하고, `/h2:doctor` 또는 `h2-install` 재실행으로 새 `.harness-helm/bin/harness(.exe)` 경로를 복구하도록 안내.
   - 다음 권장 명령(`/h2:plan` 또는 `/h2:context`)을 한 줄 안내.
   - 진단 결과는 `<target>/.harness-helm/doctor/latest.json`에 log 용도로 남긴다 (guard 판정에는 사용하지 않음).

## Failure Handling

- 4단계 dry-run이 비정상 종료(non-zero)하면 그 출력을 그대로 사용자에게 보이고 중단한다.
- 6단계 apply가 도중 실패하면:
  - `install-manifest.json`은 작성되지 않은 상태로 둔다.
  - `--backup`이 사용되었으면 backup으로 자동 rollback을 시도.
  - backup이 없으면 `<target>/.harness-helm/install-partial.json`에 partial 상태를 기록하고, 사용자에게 "partial detected — 다시 `/h2:doctor`를 실행하거나 정리 후 재시도"를 안내한다.

## Re-run / Idempotency

- 같은 version으로 재실행 시 `unchanged`가 유지되어야 한다.
- plugin이 update된 후 정상 bootstrap target은 plugin hook 또는 target command guard가 자동 apply를 시도한다.
- 자동 apply가 실패하거나 manifest가 partial/invalid이면 `/h2:doctor`가 수동 복구 command로 동작한다.
- 수동 재실행은 `install-manifest.json.package_version`과 plugin payload marker `h2-install-v{version}.txt`를 SemVer로 비교하여 upgrade가 필요한 경우에만 변경을 적용한다.
- 낮은 version payload로 높은 version target을 덮는 downgrade는 기본 차단한다.

## Notes

- `/h2:doctor`는 `h2` plugin scope의 유일한 h2 command다. 다른 `/h2:*` 명령은 target install 단계에서 doctor-first guard preamble이 주입된 상태로 target 측 `.claude/commands/h2/*.md`에 위치한다.
- guard 판정 기준은 `<target>/.harness-helm/install-manifest.json` 단독이다. doctor 결과 파일은 진단/log 용도로만 사용된다.
- 자동 apply 진단 결과는 `<target>/.harness-helm/doctor/auto-apply-latest.json`에 남긴다. 이 파일도 guard 판정에는 사용하지 않는다.
- `/h2:doctor` 진단 규칙의 전체 카탈로그(스키마·세분화된 PASS/WARN/FAIL 정책)는 별도 plan 소관이며, 본 command는 first-run에 필요한 최소 체크만 수행한다.
