---
name: rewind
description: harness-helm skill의 h2-rewind workflow를 실행합니다. h2-autorun snapshot을 사용해 특정 단계 실행 직전 상태로 복원합니다.
user-invocable: true
argument: optional
---

## doctor-first guard

`/h2:doctor`가 target에 install-manifest를 만들기 전에는 이 command를 실행하지 않는다.

1. `Read` 또는 `Bash`로 `<target>/.harness-helm/install-manifest.json` 존재를 확인한다.
2. 파일이 없으면 다음 한 줄만 출력하고 즉시 중단한다 (skill·tool 호출 금지):

```text
/h2:doctor를 먼저 실행하세요.
```

3. 파일이 있으면 아래의 원래 command 본문으로 진행한다.

---

# h2:rewind

Source of truth: `.claude/skills/harness-helm/SKILL.md`

Invoke the `h2-rewind` command semantics from the `harness-helm` skill.

Arguments:

```text
$ARGUMENTS
```

Do not duplicate or override the skill semantics in this command file.
