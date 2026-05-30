# docs/_indexes — index guide

이 폴더는 `docs/` 아래 문서 중 index 대상에 포함되는 문서의 frontmatter를 스캔해 만든 **routing hint 인덱스**를 보관한다. 본 폴더의 모든 `.md` 파일(이 guide 제외)은 자동 생성되며 사람이 직접 편집하지 않는다.

## 목적

- 신규 사용자·에이전트가 어떤 docs가 있는지 한 화면으로 훑을 수 있게 한다.
- type / domain / tag 세 축으로 같은 자산을 다르게 색인해 검색 진입점을 늘린다.
- archive로 이동된 plan/design/report 사이클을 한 곳에서 추적한다.

## 기준 위계

```
원본 docs/* (기준)
        ↓ kb-index 스캔
docs/_indexes/* (routing hint, 자동 생성)
```

- 원본 문서의 frontmatter가 기준이다. 인덱스는 그 frontmatter를 읽어 만든 derivative다.
- 인덱스 내용이 원본과 어긋난 것 같으면 **원본을 신뢰**하고 `harness kb-index`를 재실행한다.
- 인덱스에서 어떤 항목을 빼고 싶다면 `.harness-helm/h2-schema.yml` 의 `exclude_paths.lint_index` 패턴을 갱신한다 (직접 인덱스 파일을 편집하지 않는다).

## 파일 구성

### `KB_INDEX.md` — 마스터 색인

`docs/` 아래 문서 중 `.harness-helm/h2-schema.yml`의 `exclude_paths.lint_index`에 걸리지 않는 정합 문서를 단일 리스트로 나열한다.

- 각 항목은 `[제목](상대경로) — type, status` 형식이다.
- 본문 끝 `## Archive Manifest` 섹션은 `docs/_archive/<year-month>/<feature>/manifest.md` 들을 별도로 묶어 archive 이력을 빠르게 훑을 수 있게 한다.
- 신규 사용자가 처음 보는 인덱스로 적합하다.

### `DOMAIN_INDEX.md` — 도메인별 그룹

`docs/10_domain/{domain}/...` 경로 또는 frontmatter `tags`에 들어 있는 domain slug를 기준으로 도메인별 헤더(`## workflow`, `## insurance` 등)로 묶는다.

- 허용 domain slug 목록은 `.harness-helm/h2-schema.yml` 의 `domain_slugs`에 있다 (`insurance`, `commission`, `hrm`, `workflow`, `integration`).
- 특정 도메인 작업에 필요한 자산만 빠르게 추리고 싶을 때 사용한다.
- domain slug가 경로나 태그에서 확인되지 않는 문서는 이 인덱스에 등장하지 않는다.

### `TAG_INDEX.md` — 태그별 그룹

frontmatter `tags` 배열의 각 태그를 별도 헤더(`## harness-helm`, `## review-followups` 등)로 묶는다.

- 한 문서가 여러 태그를 가지면 여러 섹션에 중복으로 등장한다(의도된 동작).
- 태그는 자유 키워드이므로 schema enum 검증이 없다. 일관성 유지는 작성자 책임이다.
- 비슷한 주제의 자산을 cross-cutting하게 모을 때 가장 강력한 진입점이다.

## 생성 절차

### 명령

```bash
.harness-helm/scripts/harness kb-index
```

이 명령은 다음을 수행한다.

1. `docs/` 아래 markdown 파일을 frontmatter 파서로 스캔한다.
2. `.harness-helm/h2-schema.yml` 의 `exclude_paths.lint_index` 패턴에 매칭되는 파일은 건너뛴다.
3. KB / DOMAIN / TAG 세 인덱스를 메모리에서 빌드한 뒤 본 폴더에 덮어쓴다.
4. 각 파일 최상단에 `generated_header` 마커 한 줄을 박는다.

### 자동 갱신 시점

다음 조건에서 본 인덱스가 stale 가능성이 있다.

- 새 문서가 `docs/*` 에 추가됐을 때
- 기존 문서의 frontmatter (`type`, `status`, `tags`, `module`, `title`) 가 바뀌었을 때
- 문서가 archive로 이동됐을 때 (manifest.md 등재)
- schema 정책(`domain_slugs`, `exclude_paths`) 이 갱신됐을 때

위 변경을 동반한 커밋에는 `harness kb-index` 재실행 결과도 함께 포함하는 것이 원칙이다. CI workflow `harness-validate.yml` 가 `kb-index drift` 검증 step으로 이를 강제한다.

## 편집 정책

- 본 guide를 제외한 모든 파일은 **수동 편집 금지**다. 잘못 편집하면 kb-lint가 generated_header 부재 또는 schema 위반으로 hard_error를 낸다.
- 색인 누락이 발견되면:
  1. 원본 docs의 frontmatter가 schema enum을 따르는지 확인 (`harness kb-lint --strict`)
  2. 누락 항목이 schema `exclude_paths.lint_index` 에 우연히 매칭되는지 확인
  3. 위 두 가지가 모두 OK이면 `harness kb-index` 를 다시 실행
- 색인 형식 자체를 바꾸고 싶다면 `.harness-helm/scripts/harness.py` 의 `kb-index` 빌더 함수를 수정한다.

## 관련 문서

- `cookbooks/0100-knowledge-base-foundation/0102-frontmatter-schema.md` — frontmatter 필수 필드·enum 정책 (인덱스 빌더가 따르는 기준)
- `cookbooks/0100-knowledge-base-foundation/0103-retrieval-policy.md` — 검색·인덱싱 정책의 cookbook 기준 정의
- `cookbooks/0100-knowledge-base-foundation/0104-templates-and-skeletons.md` — 인덱스가 색인하는 canonical template 정의
- `.harness-helm/h2-schema.yml` — `exclude_paths.lint_index`, `domain_slugs`, `generated_header` 같은 실행 기준
- `.harness-helm/scripts/harness.py` — `kb-index` subcommand 구현 (라인 604 부근)
- `.github/workflows/harness-validate.yml` — CI에서 인덱스 drift를 blocking으로 검증
