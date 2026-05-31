# Runtime Folder Structure Reference

`0503 h2 Runtime Folder Structure`의 압축 runtime snapshot입니다.

## Rule

`.harness-helm/`은 설치된 h2 runtime substrate입니다. 실행 정책, schema, cartridge mapping, staging template, run-local evidence를 담습니다.

`docs/`는 장기 지식입니다. `.harness-helm/runs/`는 staging이며 canonical docs가 아닙니다.

## Runtime Roots

- `.harness-helm/h2-schema.yml`: docs frontmatter와 validation 설정
- `.harness-helm/h2-cartridge.yml`: provider, surface, fallback, routing mapping
- `.harness-helm/h2-compound.yml`: compound destination과 review gate 정책
- `.harness-helm/scripts/`: validation과 workflow helper 구현
- `.harness-helm/runs/`: run-local context, raw output, normalized draft, snapshot, restore backup

## Runs Layout

```text
.harness-helm/runs/{feature}/{run-id}/
├── context-pack.md
├── raw/
├── normalized/
├── promotion-candidates/
├── snapshots/
└── restore-backups/
```

feature가 아직 없으면 `{feature}` 대신 `_unscoped`를 사용합니다.

## Avoid

- `.harness-helm/runs/**`를 official KB로 취급하지 않습니다.
- secret이나 raw log를 canonical docs로 그대로 옮기지 않습니다.
- rewind 또는 archive review 중 archive residue를 자동 삭제하지 않습니다.

