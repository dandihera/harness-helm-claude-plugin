# h2-rewind Recovery Reference

h2 rewind recovery rules의 압축 runtime snapshot입니다.

## Rule

`h2-autorun`은 child step 실행 직전에 rewind 가능한 pre-step snapshot을 만듭니다. `h2-rewind`는 요청된 step boundary 하나를 그 snapshot에서 복원합니다.

Rewind는 workflow restore이며 destructive git reset이 아닙니다.

## Required Inputs

`h2-rewind`에는 다음 입력이 필요합니다.

- feature
- run-id
- step

snapshot manifest 또는 요청한 step snapshot이 없으면 `blocked:no-snapshot`을 반환합니다.

## Runtime Paths

snapshot은 다음 경로에 둡니다.

```text
.harness-helm/runs/{feature}/{run-id}/snapshots/{step}/
```

restore backup은 다음 경로에 둡니다.

```text
.harness-helm/runs/{feature}/{run-id}/restore-backups/{timestamp}/{step}/
```

restore evidence는 다음 경로로 routing합니다.

```text
.harness-helm/runs/{feature}/{run-id}/snapshots/{step}/restore.md
```

## Archive Residue

`docs/_archive/**` 아래 archive residue가 있으면 보존하고 경고합니다. Rewind 중 archive residue를 자동 삭제하지 않습니다.

## Avoid

- run-id를 추측하지 않습니다.
- `git reset --hard`를 rewind로 사용하지 않습니다.
- 덮어쓸 파일을 `restore-backups`에 보존하지 않고 복원하지 않습니다.
- archive residue를 자동 삭제하지 않습니다.

