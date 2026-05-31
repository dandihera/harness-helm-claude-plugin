---
schema_version: 1
id: "CONV-20260531-013"
type: convention
status: stable
owner: tw.jang
security: internal
confidence: medium
target_runtime: included
source_references:
  - cookbooks/0500-enforcement/0503-h2-runtime-folder-structure.md
module:
  - docs
  - workflow
tags:
  - harness-helm
  - runtime-folder
  - staging
---

# h2 runtime folder structure

`.harness-helm/`은 target project에 설치되는 h2 runtime substrate다. `docs/`가 장기 지식이라면 `.harness-helm/`은 검증, 실행 설정, run staging을 담당한다.

## 주요 파일

- `.harness-helm/h2-schema.yml`: docs frontmatter와 validation 정책
- `.harness-helm/h2-cartridge.yml`: provider/surface/fallback/routing mapping
- `.harness-helm/h2-compound.yml`: compound write boundary와 review gate
- `.harness-helm/scripts/harness.py`: validation과 workflow helper 구현
- `.harness-helm/runs/_templates/`: run artifact template

## Run staging

```text
.harness-helm/runs/{feature}/{run-id}/
├── context-pack.md
├── raw/
├── normalized/
├── promotion-candidates/
├── snapshots/
└── restore-backups/
```

- `raw/`: upstream 원본 출력이나 실행 로그
- `normalized/`: h2 output contract로 정리한 초안
- `promotion-candidates/`: 승인 전 canonical 후보
- `snapshots/`: `h2-autorun` rewind용 pre-step snapshot
- `restore-backups/`: `h2-rewind` 복원 전 현재 파일 backup

## 금지

- `.harness-helm/runs/**`를 official docs로 취급하지 않는다.
- secret, token, 개인정보가 포함된 raw output을 canonical docs로 그대로 옮기지 않는다.
- archive residue를 자동 삭제하지 않는다.

