---
schema_version: 1
id: "CONV-20260528-001"
type: convention
status: stable
owner: "장태욱"
security: internal
confidence: high
source_trace: "https://github.com/dandihera/harness-helm/issues/3"
related: []
module:
  - docs
tags:
  - harness-helm
  - release-notes
  - convention
---

# Convention: h2 릴리즈 노트

## 개요

harness-helm 프로젝트의 릴리즈 노트 작성 절차를 정의한다. 버전 변경 이력과 업그레이드 가이드를 `docs/50_operations/releases/`에 일관된 형식으로 기록한다.

## 트리거

다음 시점에 릴리즈 노트를 작성한다.

- Milestone 완료
- Breaking change 발생
- 외부 공개 전

## 버전 형식

```text
v{major}.{minor}.{patch}
```

릴리즈 버전은 semantic version의 major, minor, patch 세 자리만 사용한다. 릴리즈 작성 시각은 버전 문자열에 넣지 않고, 릴리즈 노트 본문의 날짜 필드에 기록한다.

예: `v0.1.0`

## 파일 위치와 이름

```text
docs/50_operations/releases/v{major}.{minor}.{patch}.release-notes.md
```

## frontmatter

```yaml
schema_version: 1
id: "REL-{yyyyMMdd}-{NNN}"       # NNN: 같은 날 릴리즈 순번 (001, 002, ...)
type: release
status: draft                     # draft → released → superseded
owner: "<릴리즈 담당자 username>"
security: internal
confidence: medium
related: []
module:
  - docs
tags:
  - harness-helm
  - v{version}
  - release-notes
```

`status` 전환 규칙:

- `draft`: 작성 중
- `released`: 배포 완료 후
- `superseded`: 다음 릴리즈로 대체 시

## 섹션 구조

```markdown
## Summary
버전, 날짜(Asia/Seoul), commit range, 3줄 요약

## What's Changed
### feat
### fix
### docs
### refactor
### chore

## Breaking Changes
없어도 "없음" 명시 필수

## Upgrade Guide
없어도 "없음" 명시 필수

## Links
```

### 섹션 작성 규칙

- **Summary**: 버전과 날짜, commit range 조회 명령, 3줄 이내 요약을 작성한다.
- **What's Changed**: conventional commit prefix(`feat`, `fix`, `docs`, `refactor`, `chore`)별로 분류한다. 해당 항목이 없는 prefix는 섹션을 생략한다.
- **Breaking Changes**: 없어도 "없음"을 반드시 명시한다.
- **Upgrade Guide**: 없어도 "없음"을 반드시 명시한다.
- **Links**: commit range 조회 명령, 관련 GitHub issue, 이번 사이클의 archived cycle 경로를 포함한다.

## 언어 정책

릴리즈 노트 본문은 **한국어(KO) 단일** 작성한다. 내부 운영 문서이므로 EN parity를 요구하지 않는다.

이 컨벤션 문서 자체는 한국어 단일 원본으로 유지한다. EN parity 파일은 생성하지 않는다.

## 작성자와 검토자

- `owner`: 릴리즈를 주도한 담당자 username.
- 별도 `reviewer` 필드는 두지 않는다. 리뷰가 필요하면 h2-review 사이클을 통해 `docs/03_review/` 산출물로 남긴다.

## Out of Scope

- 루트 `CHANGELOG.md` (v2 재검토)
- `h2-schema.yml`에 `release-notes` 타입 별도 등록 (`type: release` 사용)
- 자동 생성 스크립트
