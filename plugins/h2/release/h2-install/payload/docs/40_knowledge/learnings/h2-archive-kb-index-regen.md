---
schema_version: 1
id: "LEARN-20260529-003"
type: learning
status: draft
owner: "tw-jang"
security: internal
confidence: medium
related:
  - ".claude/skills/harness-helm/SKILL.md"
  - ".codex/skills/harness-helm/SKILL.md"
  - "https://github.com/dandihera/harness-helm/pull/20"
  - "https://github.com/dandihera/harness-helm/pull/21"
module:
  - workflow
tags:
  - h2-archive
  - kb-index
  - ci
  - drift
human_verified_by: "tw-jang"
---

<!-- harness-helm learning template. status enum: draft|pending|verified|stable|deprecated. See 0102 Frontmatter Schema. -->

# Learning: h2-archive 후 `harness kb-index` 재생성을 같은 PR에 포함한다

## Context

PR #20 (`feat(release): h2-install-powershell`) merge 직후 `harness-validate` CI job이 `docs/_indexes` drift로 FAILURE 처리됐다. 원인은 h2-archive 단계에서 `docs/_archive/2026-05/0529-010432_h2-install-powershell/manifest.md`를 생성했지만 `docs/_indexes/KB_INDEX.md`가 새 manifest 항목을 등록하지 않은 상태로 push되었기 때문이다. 사후에 PR #21로 `harness kb-index` 결과 1줄을 추가하여 해결했다.

`harness-validate` CI는 `harness kb-index` 실행 → `git diff --exit-code -- docs/_indexes`로 작동하므로, archive 등으로 index 입력이 변경되면 PR에 regenerated index가 함께 포함되어야 한다.

## Learning

h2-archive를 수행했다면, 같은 commit 또는 같은 PR 안에 `harness kb-index` 결과를 함께 포함한다. 구체적으로:

1. `harness archive {feature}` 실행으로 새 archive manifest 생성.
2. 곧바로 `harness kb-index` 실행으로 `docs/_indexes/KB_INDEX.md`, `DOMAIN_INDEX.md`, `TAG_INDEX.md`를 재생성.
3. 재생성된 index 파일도 같은 commit/PR에 stage.
4. 그 후 push.

archive와 index 갱신을 분리하면 `harness-validate` CI가 첫 push에서 drift를 잡고 PR이 FAILURE 상태로 merge되거나 추가 fix PR이 필요해진다. archive와 같은 단위로 묶으면 한 PR로 끝난다.

본 학습은 archive뿐 아니라 index 입력(주로 frontmatter, 신규/이동된 canonical doc, archive manifest)을 바꾸는 모든 작업에 적용 가능하지만, 가장 빈번한 누락 지점이 archive이므로 SKILL.md의 h2-archive 절차에 명시했다.

## Evidence

- tests:
  - 사례: PR #20 → CI FAILURE → PR #21 fix.
  - CI 로그: `kb-index: wrote ... KB_INDEX.md` + `+- [Archive Manifest: h2-install-powershell] ...` + `Process completed with exit code 1`.
  - 재발 방지 PR: 본 학습과 함께 SKILL.md 4개(`.claude/skills/harness-helm/SKILL.{md,ko.md}`, `.codex/skills/harness-helm/SKILL.{md,ko.md}`) h2-archive 섹션에 kb-index 단계 명시 bullet 추가.
- human_verified_by: tw-jang
- 출처: PR #20, #21 사이클의 실 경험.

## Apply When

- harness archive로 docs/_archive에 새 manifest를 생성한 직후.
- canonical doc의 frontmatter 변경(`status`, `tags`, `module` 등)으로 index 텍스트가 바뀌는 경우.
- 신규 canonical doc(`docs/10_domain`, `docs/20_specs`, `docs/30_decisions`, `docs/40_knowledge`, `docs/50_operations`) 작성/이동.
- 자기 자신 또는 다른 사람이 마지막 push 후 archive/index 입력 영역을 만진 모든 PR.

## Do Not Apply When

- run staging 파일(`.harness-helm/runs/**`)만 만진 경우 — runs/는 index 입력이 아님.
- source code(`release/`, scripts 등)만 만진 경우.
- `docs/_indexes/INDEX_GUIDE.md`처럼 generated index가 아닌 가이드 문서를 만진 경우.

## References

- PR #20: https://github.com/dandihera/harness-helm/pull/20 (h2-install-powershell feature, CI FAILURE)
- PR #21: https://github.com/dandihera/harness-helm/pull/21 (KB_INDEX drift fix)
- SKILL.md h2-archive 섹션: `.claude/skills/harness-helm/SKILL.md`, `.codex/skills/harness-helm/SKILL.md` (영문), `.ko.md` 짝 (한국어)
- kb-index 스크립트: `.harness-helm/scripts/harness kb-index`
- CI: `.github/workflows/harness-validate.yml` (`Check generated index drift` step)
