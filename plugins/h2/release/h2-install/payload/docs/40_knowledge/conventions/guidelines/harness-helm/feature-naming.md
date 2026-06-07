---
schema_version: 1
id: "CONV-20260603-132"
type: convention
status: stable
owner: "장태욱"
security: internal
confidence: medium
target_runtime: included
related:
  - https://github.com/dandihera/harness-helm/issues/132
  - docs/01_plan/issue-derived-feature-suffix_132.md
  - docs/02_design/issue-derived-feature-suffix_132.md
  - docs/02_design/issue-derived-feature-suffix_132.analysis.md
module:
  - docs
  - workflow
tags:
  - harness-helm
  - h2
  - feature-naming
  - issue-trace
source_trace: "GitHub Issue #132"
---

# Convention: h2 feature naming

## Rule

GitHub/GitLab 이슈에서 시작한 h2 workflow의 feature slug는 기본적으로 다음 형식을 사용한다.

```text
<kebab-case-feature>_<issue-number>
```

GitHub/GitLab 이슈에서 시작하지 않은 workflow는 issue suffix 없이 kebab-case feature slug만 사용한다.

## Applies To

- `docs/01_plan/{feature}.md`
- `docs/02_design/{feature}.md`
- `docs/03_review/{type}/{feature}.md`
- `docs/04_report/{feature}.md`
- `.harness-helm/runs/{feature}/{run-id}/`
- `docs/_archive/YYYY-MM/MMdd-HHMMSS_{feature}/`
- h2 command/skill 안내의 issue-derived feature 예시

## Rationale

`docs/`, `.harness-helm/runs/`, `docs/_archive/`에는 h2 workflow 산출물이 오래 남는다. 이슈에서 시작한 작업은 파일명과 archive 경로만 보아도 원천 이슈를 추적할 수 있어야 한다.

Issue number separator는 `_`를 사용한다. 기능명 본문은 kebab-case 하이픈을 계속 사용하므로, issue number suffix까지 하이픈으로 붙이면 기능명 일부와 추적용 suffix의 경계가 흐려진다. `_`는 의미 있는 feature slug와 issue trace suffix를 시각적으로 분리한다.

## Examples

### GitHub-only 또는 single-provider

```text
snapshot-archive-scope_124
runtime-summary-stage-evidence_131
rewind-archive-residue_98
```

GitHub Issues가 주된 backlog/source trace인 project에서는 provider를 파일명에 넣지 않는다. Provider 구분은 frontmatter의 `related` 또는 `source_trace`에 남긴다.

### Multi-provider

GitHub/GitLab을 함께 쓰고 번호 충돌을 파일명 단계에서 피해야 하는 target project는 provider suffix를 사용할 수 있다.

```text
snapshot-archive-scope_gh_124
snapshot-archive-scope_gl_124
```

Provider suffix는 다음 조건을 모두 만족할 때만 사용한다.

- 같은 target project에서 GitHub와 GitLab issue를 모두 backlog/source trace로 사용한다.
- 두 provider의 numeric issue id가 파일명 또는 archive path에서 충돌할 수 있다.
- 사용자가 issue source를 명시했거나, issue URL/source_trace에서 provider가 확인된다.

### No issue source

GitHub/GitLab 이슈에서 시작하지 않은 feature는 suffix 없는 일반 feature slug를 그대로 쓴다.

```text
h2-run-stats
guard-version-drift
cartridge-output-normalization
```

## Avoid

이슈에서 시작하지 않은 작업에 임의 issue suffix를 만들지 않는다.

```text
h2-run-stats_0
guard-version-drift_unknown
```

GitHub-only project에서 provider suffix를 기본값으로 강제하지 않는다.

```text
snapshot-archive-scope_gh_124
```

## Migration

기존 feature명과 archive 경로에는 소급 적용하지 않는다. 완료된 workflow 산출물과 archive manifest link를 유지하기 위해 rename하지 않는다.

진행 중인 draft workflow는 아직 archive되지 않았고 cross-reference를 함께 갱신할 수 있을 때만 새 naming rule에 맞게 정리할 수 있다.

## Verification

- `rg -n "feature slug|feature명|issue-number|이슈 번호" cookbooks/0300-workflow-contract/0301-core-workflow-spec.md cookbooks/0500-enforcement/0503-h2-runtime-folder-structure.md cookbooks/0100-knowledge-base-foundation/0101-docs-folder-structure.md`
- `rg -n "feature-naming.md|Feature naming|h2 feature naming" docs/40_knowledge/conventions/guidelines/harness-helm/README.md`
- `.harness-helm/scripts/harness kb-lint`
- `.harness-helm/scripts/harness kb-index`

## References

- GitHub Issue #132
- `docs/01_plan/issue-derived-feature-suffix_132.md`
- `docs/02_design/issue-derived-feature-suffix_132.md`
- `docs/02_design/issue-derived-feature-suffix_132.analysis.md`
