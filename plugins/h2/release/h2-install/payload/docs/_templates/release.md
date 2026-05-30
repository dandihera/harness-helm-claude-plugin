---
schema_version: 1
id: "REL-YYYYMMDD-NNN"
type: release
status: draft
owner: "<TODO: release manager username>"
security: internal
confidence: low
related: []
# Recommended optional fields
# source_pr: "<TODO: release PR number>"
# tests: []
# legal_hold: false
---

<!-- harness-helm release template. status enum: draft|released|superseded. See 0102 Frontmatter Schema. -->

# Release: <TODO: 버전 또는 릴리스 이름>

## Release Date (Asia/Seoul)

<TODO: YYYY-MM-DD>

## Highlights

- <TODO: 주요 변경 사항 1>
- <TODO: 주요 변경 사항 2>

## Changes

### Features
- <TODO>

### Fixes
- <TODO>

### Breaking Changes
- <TODO: 없으면 "없음"으로 명시>

## Migration Notes

<TODO: 배포 전후 수동 절차, schema migration, config 변경.>

## Verification

- tests: <TODO: 실행한 검증>
- canary / staging 결과: <TODO>

## Rollback Plan

<TODO: 문제 발생 시 되돌리는 절차.>

## Affected Modules

- <TODO: bootstrap-system, hera-webapp, ...>

## References

- source PR: <TODO>
- 관련 incident/runbook: <TODO>
