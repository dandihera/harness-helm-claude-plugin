---
schema_version: 1
id: "CONV-20260531-017"
type: convention
status: stable
owner: tw.jang
security: internal
confidence: medium
target_runtime: included
source_references:
  - cookbooks/0300-workflow-contract/0303-workflow-lifecycle-commands.md
  - cookbooks/0500-enforcement/0503-h2-runtime-folder-structure.md
module:
  - docs
  - workflow
tags:
  - harness-helm
  - h2-rewind
  - recovery
---

# h2 rewind recovery

`h2-rewind`는 `h2-autorun`이 남긴 pre-step snapshot으로 특정 step boundary를 복원하는 workflow restore다. Git history를 되돌리는 destructive restore가 아니다.

## Required inputs

`h2-rewind`는 다음 입력을 요구한다.

- feature
- run-id
- step

snapshot manifest 또는 요청 step snapshot이 없으면 `blocked:no-snapshot`으로 막는다.

## Runtime paths

Snapshot:

```text
.harness-helm/runs/{feature}/{run-id}/snapshots/{step}/
```

Restore backup:

```text
.harness-helm/runs/{feature}/{run-id}/restore-backups/{timestamp}/{step}/
```

Restore evidence:

```text
.harness-helm/runs/{feature}/{run-id}/snapshots/{step}/restore.md
```

## Archive residue

`docs/_archive/**` 아래 archive residue가 있으면 보존하고 경고한다. Rewind가 archive residue를 자동 삭제하지 않는다.

## 금지

- run-id를 추측하지 않는다.
- `git reset --hard`를 h2-rewind로 사용하지 않는다.
- 덮어쓸 파일을 `restore-backups`에 보존하지 않고 복원하지 않는다.
- archive residue를 자동 삭제하지 않는다.

