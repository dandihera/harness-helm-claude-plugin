---
name: h2-harvest
description: docs/_harvest-inbox에 임시로 둔 Markdown 또는 text 메모를 harness h2-harvest CLI로 공식 docs에 정리한다. inbox 메모 harvest, staged knowledge 파일 promote/reject, h2-harvest 동작 확인 요청에 사용한다.
---

# h2-harvest

`h2-harvest`는 feature lifecycle 밖에서 inbox 기반 지식을 정리할 때 사용한다.

Runtime command:

```bash
.harness-helm/scripts/harness h2-harvest [--promote <path> | --reject <path>] [--dry-run] [--force] [--skip-raw]
```

입력은 `docs/_harvest-inbox/{solution,convention,domain,spec,decision,ops}/` 아래에 있어야 하며 `.md` 또는 `.txt`만 허용한다. `.txt` 입력은 공식 목적지에 `.md`로 저장한다.

`docs/_harvest-inbox/raw/`에 prefix-free 파일이 있으면 `h2-harvest`는 warning을 출력하고 먼저 `h2-harvest-tag` 실행을 안내한다. raw inbox 파일을 의도적으로 무시할 때만 `--skip-raw`를 사용한다.

Phase 1은 LLM 또는 embedding 분류를 사용하지 않는다. `.harness-helm/h2-harvest.yml`의 deterministic policy를 적용하고, frontmatter를 검증하며, 의미상 type mismatch 가능성은 warning으로만 남긴다. Governed 목적지는 workflow가 명시적으로 승인하기 전까지 pending으로 둔다.

Low-risk `solution`, `convention` 항목은 `confidence: high`와 evidence metadata가 있을 때만 auto-write할 수 있다. Governed 항목(`domain`, `spec`, `decision`, `ops`)은 pending으로 유지한다. `--reject` 또는 `status: rejected`는 run report 작성 후 inbox 원본을 hard-delete한다. 미리 보려면 `--dry-run`을 사용한다.

Report는 `.harness-helm/runs/_unscoped/{run-id}/harvest-report.md`에 기록한다.
