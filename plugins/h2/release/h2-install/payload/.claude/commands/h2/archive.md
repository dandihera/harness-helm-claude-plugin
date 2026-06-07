---
name: archive
description: harness-helm skill의 h2-archive workflow를 실행합니다. #256 harness archive와 연결하여 01~04 산출물 archive를 준비합니다.
user-invocable: true
argument: optional
---

## doctor-first guard

`/h2:doctor`가 target에 install-manifest를 만들기 전에는 이 command를 실행하지 않는다.
Target h2 runtime이 현재 plugin payload보다 오래된 경우에는 먼저 plugin auto-apply를 시도한다.

1. `Read` 또는 `Bash`로 `<target>/.harness-helm/install-manifest.json` 존재를 확인한다.
2. 파일이 없으면 다음 한 줄만 출력하고 즉시 중단한다 (skill·tool 호출 금지):

```text
/h2:doctor를 먼저 실행하세요.
```

3. 파일이 있으면 `status`와 `package_version`을 읽는다. `status`가 `ok`가 아니거나 `package_version`이 missing/invalid이면 다음 한 줄만 출력하고 즉시 중단한다:

```text
/h2:doctor를 실행해 h2 runtime 상태를 복구하세요.
```

4. 가능하면 `~/.claude/plugins/installed_plugins.json`에서 `h2@dandisoft-harness-helm` entry를 확인한다.
   entry가 배열이면 현재 project scope entry를 우선하고, 판단이 불명확하면 각 `installPath`의 marker 중 SemVer가 가장 높은 항목을 사용한다.
   current payload version은 `<installPath>/release/h2-install/h2-install-v*.txt` marker의 SemVer 최고값을 우선하고, marker가 없으면 entry의 `version`을 사용한다.
   marker filename과 본문 `version:`이 다르면 filename을 우선하고 경고만 남긴다.
5. current payload version을 찾을 수 없으면 zip 직접 설치 환경일 수 있으므로 version drift 미검증 경고를 남기고 아래의 원래 command 본문으로 진행한다.
   entry나 marker가 있으나 version이 invalid SemVer이면 다음 한 줄만 출력하고 즉시 중단한다:

```text
/h2:doctor를 먼저 실행하세요. 현재 plugin version을 확인할 수 없습니다.
```

6. target version과 current payload version을 SemVer 기준으로 비교한다.
   - target < current: `Bash`로 `<installPath>/scripts/h2-auto-apply.sh`를 실행한다. 성공하면 `install-manifest.json.package_version`을 다시 읽어 current payload version 이상인지 확인한 뒤 아래의 원래 command 본문으로 진행한다. 실패하거나 version이 여전히 오래되었으면 다음 한 줄만 출력하고 즉시 중단한다:

```text
h2 자동 업데이트에 실패했습니다. /h2:doctor를 실행해 복구하세요.
```

   - target == current: 아래의 원래 command 본문으로 진행한다.
   - target > current: rollback/newer target 경고를 남기고 아래의 원래 command 본문으로 진행한다.
7. 위 guard를 통과하면 아래의 원래 command 본문으로 진행한다.

---

# h2:archive

Source of truth: `.claude/skills/harness-helm/SKILL.md`

Invoke the `h2-archive` command semantics from the `harness-helm` skill.

Arguments:

```text
$ARGUMENTS
```

Do not duplicate or override the skill semantics in this command file.
