---
name: harness-helm
description: harness-helm h2 워크플로를 위한 Claude Code 어댑터. h2-context, h2-plan, h2-design, h2-autorun, h2-rewind, h2-analysis, h2-build, h2-test, h2-review, h2-report, h2-compound, h2-harvest, h2-archive, h2-ops, h2-cartridge에 사용하며, 0301-core-workflow-spec의 command semantics, output fields, staging rules, docs routing을 보존한다.
---

# harness-helm

`harness-helm`은 HERA AI-native docs lifecycle을 위한 얇은 Claude Code 어댑터다. gstack, superpowers, compound-engineering, Claude Code, Codex를 대체하지 않는다. 이들의 작업을 core reference에서 정의한 공통 `h2-*` workflow, output contract, staging rules, routing으로 감싸는 역할을 한다.

Bundled runtime references:

- `references/skill-suite.md`: `0302 Skill Suite` 경계와 `h2` prefix.
- `references/core-workflow.md`: `0301 Core Workflow Spec`의 `h2-*` core workflow.
- `references/claude-adapter.md`: `0401 Claude Code Adapter` scope와 `h2-*` entrypoint.
- `references/claude-entrypoint.md`: `0403 Runtime Parity Test`를 위한 Claude smoke/parity 예시.
- `references/runtime-parity.md`: Claude Code와 Codex의 `0403 Runtime Parity Test` parity 결과.
- `references/workflow-lifecycle-commands.md`: `0303 Workflow Lifecycle Commands`의 `h2-*` command semantics.
- `references/context-pack-contract.md`: `0305 Context Pack Contract`의 retrieval snapshot 규칙.
- `references/runtime-folder-structure.md`: `0503 h2 Runtime Folder Structure`의 설치 runtime과 run staging layout.
- `references/compound-policy-config.md`: `0306 Compound Policy Config`의 h2-compound write/review gate 정책.
- `references/h2-rewind-recovery.md`: h2-autorun snapshot과 h2-rewind restore boundary 규칙.
- `references/cartridge-command-mapping.md`: `0601 Cartridge Command Mapping`의 invocation recording, fallback handling, routing invariant.
- `references/cartridge-tool-registry.md`: `0602 External Tool Registry`의 integration 대상, 대안, availability, registration rules.
- `references/cartridge-surface-map.md`: `0603 Cartridge Surface Map`의 upstream surface 추천과 drift note.
- `references/cartridge-output-normalization.md`: `0604 Cartridge Output Normalization`의 upstream raw output → h2 template 정규화 규칙.
- `references/canonical-promotion-flow.md`: `h2-compound` 승인 게이트와 canonical 작성 규칙의 runtime snapshot.
- `references/specs-vs-decisions.md`: `20_specs`와 `30_decisions` 사이 목적지 판단의 runtime snapshot.
- `references/provider-surface-selection-and-override.md`: run-level upstream override와 permanent mapping 변경의 runtime snapshot.
- `docs/40_knowledge/conventions/guidelines/harness-helm/runtime-reference-selection.md`: snapshot scope를 정하는 meta guideline. bundled runtime snapshot으로 복제하지 않는다.

문서가 설치되면 canonical runtime convention은 `docs/40_knowledge/conventions/guidelines/*.md` 아래에 보관한다. 해당 문서가 없거나 로딩 비용이 큰 경우 bundled `references/canonical-promotion-flow.md`, `references/specs-vs-decisions.md`, `references/provider-surface-selection-and-override.md`가 compact runtime snapshot을 제공한다.

base `references/*.md` 파일은 Claude/Codex parity와 compact loading을 위해 영문으로 작성한다. 같은 이름의 `references/*.ko.md`는 stakeholder 검토용 한국어 번역이며 default agent context에는 자동으로 로드하지 않는다. 사용자가 명시적으로 한국어 검토를 요청할 때만 읽는다.

설치된 target project에는 `cookbooks/`가 없다. 이 `SKILL.md`, `.claude/commands/h2/*.md`, bundled `references/*.md`, root `CLAUDE.md`/`AGENTS.md`, `docs/`, `.harness-helm/`을 runtime surface로 사용한다.

아래의 간결한 rule만으로 부족하거나 자세한 acceptance criteria를 확인해야 할 때만 bundled reference snapshot을 로드한다.

## Docs Artifact Language

번호가 붙은 user-facing docs 폴더 하위의 Markdown 파일은 기본적으로 한국어로 작성한다. 이 규칙은 `docs/01_plan/**`, `docs/02_design/**`, `docs/03_review/**`, `docs/04_report/**`, `docs/10_domain/**`, `docs/20_specs/**`, `docs/30_decisions/**`, `docs/40_knowledge/**`, `docs/50_operations/**`에 적용된다.

`docs/_indexes/**` 하위의 generated machine-facing index 문서는 예외다. 이 index markdown 파일들은 h2가 retrieval과 routing aid로 주로 소비하므로 영어로 작성한다.

Technical identifier, command name, file path, frontmatter key, proper noun, source quotation은 원문 형태를 유지한다. 사용자가 명시적으로 다른 언어를 요청하거나 정확한 source quote를 보존해야 할 때만 다른 언어를 사용한다.

## Runtime Read Order

1. 먼저 root `AGENTS.md`, root `CLAUDE.md`, 그리고 프로젝트별 지침을 따른다.
2. canonical `h2-*` command semantics, output fields, staging rules, docs routing은 이 `SKILL.md`를 기준으로 한다.
3. `.claude/commands/h2/*.md`는 얇은 slash command alias로만 취급한다.
4. 자세한 criteria, parity evidence, upstream mapping, normalization, promotion rule이 필요할 때만 bundled `references/*.md`를 로드한다.
5. 설치되어 있으면 `.harness-helm/h2-cartridge.yml`을 editable provider, surface, fallback, routing, output language 값의 기준으로 사용한다. 없으면 `references/cartridge-command-mapping.md`는 invocation recording, fallback handling, routing invariant 확인에만 사용한다.
6. 설치되어 있으면 `.harness-helm/h2-compound.yml`을 h2-compound domain refinement, canonical destination, review gate, retrieval hook policy의 기준으로 사용한다. 없으면 built-in conservative default를 사용한다.
7. 설치되어 있으면 `.harness-helm/h2-harvest.yml`을 h2-harvest inbox curation policy의 기준으로 사용한다. 없으면 built-in conservative default를 사용한다.

## Runtime Source Hierarchy

- Source repository의 design record는 `cookbooks/`에 있지만, installed target project에는 `cookbooks/`가 없다.
- Installed runtime command semantics는 이 `SKILL.md`, `references/core-workflow.md`, `references/workflow-lifecycle-commands.md`를 기준으로 한다.
- Runtime provider, surface, fallback, routing, output language mapping은 설치된 `.harness-helm/h2-cartridge.yml`을 기준으로 한다. Bundled upstream reference는 cartridge 값 사본이 아니라 invocation recording, fallback handling, routing invariant fallback guidance다.
- Runtime h2-compound knowledge policy는 설치된 `.harness-helm/h2-compound.yml`을 기준으로 하며, 없으면 built-in conservative default를 fallback으로 사용한다.
- Runtime h2-harvest inbox curation policy는 설치된 `.harness-helm/h2-harvest.yml`을 기준으로 하며, 없으면 built-in conservative default를 fallback으로 사용한다.
- Runtime schema validation은 `.harness-helm/h2-schema.yml`을 기준으로 한다.
- Root `CLAUDE.md`와 `AGENTS.md`는 project-wide entrypoint guidance를 제공하며 full workflow contract를 중복 정의하지 않는다.

## Runtime Parity Boundary

- Claude와 Codex는 invocation syntax와 file layout이 다를 수 있다.
- 두 runtime은 같은 `h2-*` command ids, common output fields, docs routing, staging rules, cartridge mapping semantics를 보존해야 한다.
- skill folder 하위 runtime-specific guide file은 target surface가 아니다. Root guidance, 이 `SKILL.md`, alias, bundled references, `docs/`, `.harness-helm/`을 사용한다.

## Command Surface

Claude Code는 다음 `h2-*` command를 제공해야 한다:

- `h2-context`
- `h2-plan`
- `h2-design`
- `h2-autorun`
- `h2-rewind`
- `h2-analysis`
- `h2-build`
- `h2-test`
- `h2-review`
- `h2-report`
- `h2-compound`
- `h2-harvest`
- `h2-archive`
- `h2-ops`
- `h2-cartridge`

`.harness-helm/h2-cartridge.yml`이 설치되어 있으면 provider, surface, fallback label, routing target, output language 값과 external tool registry entry의 공통 기준으로 사용한다. target project에 이 파일이 없으면 bundled `references/cartridge-command-mapping.md`는 invocation recording, fallback handling, routing invariant 확인에만 사용한다. tool 대안과 registration rule은 `references/cartridge-tool-registry.md`, 자세한 workflow lifecycle command 의미가 필요하면 `references/workflow-lifecycle-commands.md`를 읽는다.

## Common Input

Claude Code invocation이 자연어 형태여도 다음 의미를 보존한다:

```yaml
command: h2-context | h2-plan | h2-design | h2-autorun | h2-rewind | h2-analysis | h2-build | h2-test | h2-review | h2-report | h2-compound | h2-harvest | h2-archive | h2-ops | h2-cartridge
feature: "<feature-slug or null>"
task: "<user request or work summary>"
source_request: "<original request, optional>"
mode: "create | update | inspect"
references:
  docs: []
  prs: []
constraints:
  security: "public | internal | restricted | regulated"
```

Minimum input은 `command`, `feature`, `task`다. `h2-context`는 `feature: null`을 사용할 수 있으며, 이 경우 `.harness-helm/runs/_unscoped/{run-id}/`를 사용한다.

이슈에서 시작한 feature명은 기본적으로 `<kebab-case-feature>_<issue-number>`를 사용한다. 예: `snapshot-archive-scope_124`. GitHub/GitLab 이슈에서 시작하지 않은 workflow는 suffix 없이 kebab-case feature slug만 사용한다. 예: `h2-run-stats`. Multi-provider project는 issue 번호 충돌을 피해야 할 때만 `_gh_` 또는 `_gl_`을 사용할 수 있다.

## Common Output

응답과 artifact는 다음 필드를 보존해야 한다:

```yaml
command: "<h2-command>"
feature: "<feature-slug or null>"
status: "draft | updated | skipped | blocked"
context_pack:
  primary_docs: []
  supporting_docs: []
  canonical_knowledge: []
  excluded_by_policy: []
  assumptions: []
artifacts:
  created: []
  updated: []
  suggested: []
routing:
  target_docs: []
  archive_candidate: false
  promotion_candidates: []
verification:
  required: []
  completed: []
  not_verified: []
next:
  recommended_h2_step: "<h2-command or null>"
```

Recommended Markdown shape:

- frontmatter: `command`, `feature`, `status`, `next.recommended_h2_step`
- sections: `## Context Pack`, `## Artifacts`, `## Routing`, `## Verification`

## Command Semantics

### h2-context

- bundled `references/`의 `0103 Retrieval and Index Policy`와 core workflow rule을 사용해 primary/supporting/excluded docs를 선택한다.
- 적용 가능한 canonical docs를 `context_pack.canonical_knowledge`에 포함해 compounded knowledge 재투입을 보이게 한다.
- `docs/_indexes/index_kb.jsonl`, `index_domain.jsonl`, `index_tag.jsonl`이 있으면 파싱한다. index가 없거나 stale이면 공식 기준 문서를 직접 확인한다.
- index absent/stale freshness warning은 `verification.not_verified`에 기록한다. index는 생성하지 않는다.
- `_indexes`를 생성하지 않는다.
- context pack을 `.harness-helm/runs/{feature}/{run-id}/context-pack.md` 또는 `.harness-helm/runs/_unscoped/{run-id}/context-pack.md`에 생성하거나 갱신한다. 후속 `h2-*` command는 같은 snapshot을 기준으로 시작한다.
- `next.recommended_h2_step`을 `null` 또는 사용자 요청에서 암시되는 첫 command로 설정한다.

### h2-plan

- preflight로 `h2-context` 의미를 실행한다.
- goal, scope, non-goals, done criteria, key risks를 요약한다.
- `docs/01_plan/{feature}.md`로 route한다.
- `next.recommended_h2_step`을 `h2-design`으로 설정한다.

### h2-design

- preflight로 `h2-context` 의미를 실행한다.
- plan을 사용해 implementation flow, interfaces, data flow, verification strategy를 정의한다.
- `docs/02_design/{feature}.md`로 route한다.
- plan이 없으면 `status: blocked`를 사용하고 누락된 plan을 `verification.required`에 설명한다.
- `next.recommended_h2_step`을 `h2-analysis`로 설정한다.

### h2-autorun

- preflight로 `h2-context` 의미를 실행하고 이번 autorun을 위한 새 context pack을 만든다. 기존 context pack은 supporting docs로 참조할 수 있다.
- 시작 전에 `docs/02_design/{feature}.md`가 있어야 한다. design이 없거나 명시적으로 blocked이면 `status: blocked`를 사용한다.
- `h2-analysis`를 한 번 실행한 뒤, 최신 test와 review가 forward 진행을 허용할 때까지 `h2-build -> h2-test -> h2-review` state machine을 실행한다. `h2-test` 또는 `h2-review`가 `next.recommended_h2_step: h2-build`를 반환하면 warning이 아니라 back-edge iteration 요청으로 취급한다.
- 최신 `h2-test` 또는 `h2-review`가 아직 `h2-build`를 요청하거나, review가 한 번도 실행되지 않았거나, iteration guard가 blocked이면 `h2-report`, `h2-compound`, `h2-archive`를 실행하지 않는다.
- 각 child step 실행 직전에 `h2-snapshot save` 의미로 pre-step snapshot을 저장해 `h2-rewind`가 해당 단계 경계를 복원할 수 있게 한다.
- 각 child step 완료 후 `h2-snapshot complete`를 `--invoked-surface <resolved-surface> --invocation-mode <mode>`와 함께 호출해 runs-summary 표가 채워지도록 한다. resolved-surface는 해당 step에서 실제로 사용한 `provider:surface` 문자열(예: `compound-engineering:ce-plan`)이며, primary surface를 사용하지 못한 경우 `fallback:<label>` 형태를 쓴다.
- 가능하면 `autorun-summary.md`와 manifest에 iteration evidence를 기록한다: `iteration_index`, `stage_attempt`, `back_edge_from`, `back_edge_reason`, `back_edge_reason_key`, `autorun_resolution`.
- Project runtime policy가 더 엄격한 값을 제공하지 않으면 max_iterations `5`를 사용한다. 동일 unresolved reason이 반복되거나 max iteration을 초과하면 `status: blocked`로 중단한다.
- 기본 `h2-review` type은 `code`다. 사용자 입력은 `review=code|qa|security|cross`로 override할 수 있으며, `security`, `qa`, `cross`는 design/test evidence 또는 Cross Review policy 기준이 있을 때만 선택한다.
- 하위 단계가 `status: blocked`를 반환하면 즉시 중단한다.
- `verification.not_verified`는 warning으로 요약한다. 단, 사람 review evidence 누락은 summary에서 강조한다.
- `h2-report`가 `h2-archive`를 추천하는 경우는 일반 next-step mismatch보다 먼저 평가한다. 그래도 `h2-archive` 전 `h2-compound`를 명시적으로 실행한다.
- `h2-autorun`이 `h2-archive`에 도달하면 기본적으로 실제 archive를 실행한다. 사용자가 dry-run, preview-only, no archive를 명시적으로 요청하지 않은 한 archive를 `--dry-run`으로 낮추지 않는다.
- `.harness-helm/runs/{feature}/{run-id}/autorun-summary.md`로 route한다.
- `next.recommended_h2_step`을 `null`로 설정한다.

### h2-rewind

- `h2-analysis`, `h2-build`, `h2-test`, `h2-review`, `h2-report`, `h2-compound`, `h2-archive` 중 특정 `h2-autorun` pre-step snapshot을 복원한다.
- `feature`, `run-id`, `step`을 요구한다. run id를 추측하지 않는다.
- snapshot manifest가 없으면 `status: blocked`와 `blocked:no-snapshot`을 사용한다.
- `docs/_archive/**` 잔존 파일은 자동 삭제하지 않고 warning으로 보존한다.
- 복원 evidence는 `.harness-helm/runs/{feature}/{run-id}/snapshots/{step}/restore.md`로 route한다.
- `next.recommended_h2_step`은 복원한 step으로 설정한다.

### h2-analysis

- plan의 goal/scope/done criteria를 design의 implementation과 verification strategy와 비교한다.
- analysis 산출물은 `docs/02_design/{feature}.analysis.md`로 route한다.
- plan/design 불일치, gap, 정확한 alignment 권고를 그 문서에 기록한다.
- 사람의 판단이 필요한 gap은 `verification.not_verified`에 둔다.
- `next.recommended_h2_step`을 `h2-build`로 설정한다.

### h2-build

- design 실행 산출물, changed files, implementation risk, blocked/skipped reason을 harness-helm output shape에 기록한다. 산출물은 code, documentation, workflow record, runtime configuration일 수 있다.
- Claude Code, Codex, superpowers, gstack을 code-editing actor로서 대체하지 않는다.
- actual upstream actor invocation이 검증되기 전까지 current mode는 recorder다.
- `.harness-helm/runs/{feature}/{run-id}/build.md`로 route한다.
- `next.recommended_h2_step`을 `h2-test`로 설정한다.

### h2-test

- test commands, results, skip reasons, failures, remaining verification을 기록한다.
- 실행한 check는 `verification.completed`에 둔다.
- skipped/failed/unverified check는 `verification.not_verified`에 둔다.
- `.harness-helm/runs/{feature}/{run-id}/test.md`로 route한다.
- `next.recommended_h2_step`을 `h2-review`로 설정한다.

### h2-review

- `code`, `qa`, `security`, `cross` review type을 지원한다.
- review candidate를 `docs/03_review/{type}/{feature}.md`로 route한다.
- Cross Review는 Cross Review policy criteria를 만족할 때만 실행한다.
- 생성되는 리뷰 내용은 모두 한글로 작성한다. 기술 식별자, 커맨드명, 파일 경로, 인용 소스는 원문 형태를 유지한다.
- `next.recommended_h2_step`을 `h2-report`로 설정한다.

### h2-report

- preflight로 `h2-context` 의미를 실행한다.
- plan/design/analysis/build/test/review 결과를 요약한다.
- `docs/04_report/{feature}.md`로 route한다.
- build/test/review evidence가 수동으로 또는 upstream tool로 만들어졌다면 기록한다. 그렇지 않으면 누락된 evidence를 `verification.not_verified`에 나열한다.
- 10/20/30/40/50 candidate는 `routing.promotion_candidates` 또는 `artifacts.suggested`에만 둔다. 자동 승격하지 않는다.
- `next.recommended_h2_step`을 `h2-archive` 또는 `h2-compound`로 설정한다.

### h2-compound

- 완료된 작업에서 reusable knowledge를 축적한다.
- `.harness-helm/h2-compound.yml`이 있으면 읽어서 domain refinement mode, canonical destination mapping, review gate, retrieval hook policy를 결정한다. 없으면 conservative built-in default를 사용하고 compound artifact에 fallback을 기록한다.
- `mode=synthesis`, `destination=docs/40_knowledge/solutions` 같은 run-level policy override는 defaults를 바꾸지 않는다. `policy:mode:*`, `policy:destination:*` trace로 기록한다.
- `docs/40_knowledge/solutions/**` 또는 `docs/40_knowledge/learnings/**` 아래의 low-risk learning/solution 문서는 overlap, schema, lint 확인 후 작성하거나 갱신할 수 있다.
- `docs/20_specs/**`, `docs/30_decisions/**.accepted.md`, team/runtime convention, operational policy 같은 governed canonical 대상은 owner/verifier 또는 Tech Lead 승인 기록 전까지 staging한다.
- governed 후보는 `routing.promotion_candidates`에 기록하고, low-risk 작성 결과는 `artifacts.created` 또는 `artifacts.updated`에 기록한다.
- `.harness-helm/runs/{feature}/{run-id}/compound-candidates.md`로 route한다.
- `next.recommended_h2_step`을 `h2-archive` 또는 `null`로 설정한다.

### h2-harvest

- `docs/_harvest-inbox/{solution,convention,domain,spec,decision,ops}/`에 staging된 메모를 정리한다.
- 설치되어 있으면 `.harness-helm/scripts/harness h2-harvest`와 `.harness-helm/h2-harvest.yml`을 사용한다.
- 본문만 보고 `confidence: high`를 추론하지 않는다. 사용자가 선언해야 하며 deterministic evidence metadata가 있어야 한다.
- frontmatter가 type을 명시적으로 override하지 않은 경우 possible body/type mismatch는 warning으로만 처리한다.
- report는 `.harness-helm/runs/_unscoped/{run-id}/harvest-report.md`로 route한다.
- `next.recommended_h2_step`을 `null`로 설정한다.

### h2-archive

- `.harness-helm/runs/{feature}/*/compound-candidates.md`를 확인해 이 feature에 대해 `h2-compound`가 실행됐는지 검사한다. compound 실행 증거가 없으면 archive 진행 전에 `h2-compound` 의미를 자동으로 preflight 실행한다.
- `.harness-helm/scripts/harness archive {feature}`를 실행해 archive를 수행한다. 변경 사항을 적용하지 않고 미리보기만 하려면 `--dry-run`을 사용한다.
- `h2-autorun` 안의 `h2-archive`는 preview 단계가 아니라 execute 단계다. 사용자가 lifecycle 자동 진행을 이미 요청했으므로 기본값은 non-dry-run archive다.
- archive file movement를 재구현하지 않는다.
- `harness archive`는 `.harness-helm/runs/{feature}/`를 `docs/_archive/{archive-folder}/runs/`로 이동하고 임시 `runs/stage-runtime-summary.json`을 쓴 뒤 archive root의 `stage-runtime-summary.md`를 생성한다. 이후 임시 JSON을 제거하고 각 run root의 Markdown 산출물(`context-pack.md`, `archive-plan.md`, `autorun-summary.md`, `build.md`, `test.md`, `compound-candidates.md` 등)만 남긴다. Run manifest, snapshot, raw, normalized, promotion candidate, restore backup은 summary 생성 후 제거된다.
- archive 완료 후 `.harness-helm/scripts/harness kb-index`를 실행해 active docs가 indexed 위치에서 archive로 이동된 상태를 `docs/_indexes/*.md`에 반영한다. 재생성된 index 파일을 archive와 같은 commit/PR에 포함한다. 누락하면 다음 push에서 `harness-validate`(또는 동등한 CI)가 index drift로 실패한다.
- `.harness-helm/runs/{feature}/{run-id}/archive-plan.md`로 route한다.
- `next.recommended_h2_step`을 `h2-ops` 또는 `null`로 설정한다.

### h2-ops

- incident, release, runbook, branch sweep operation candidate를 기록한다.
- operation candidate를 `docs/50_operations/{type}/{topic}.md`로 route한다.
- `next.recommended_h2_step`을 `null`로 설정한다.

### h2-cartridge

- `.harness-helm/`이 설치되어 있으면 `.harness-helm/scripts/harness cartridge-validate`를 실행하고, 없으면 bundled `references/cartridge-command-mapping.md`에서 invocation recording, fallback handling, routing invariant를 확인한다.
- 각 command가 `provider`, `surface`, `fallback_label`, `routing_target`, `output_language`를 정의하는지 확인한다.
- unavailable surface나 invalid surface는 `verification.not_verified` 또는 `verification.required`에 기록한다.
- `.harness-helm/runs/{feature}/{run-id}/cartridge-mapping.md`로 route한다.

## Staging

이 skill과 bundled `references/core-workflow.md`의 staging rule을 사용한다:

```text
.harness-helm/runs/{feature}/{run-id}/
├── context-pack.md
├── raw/
├── normalized/
└── promotion-candidates/
```

- `feature`를 알 수 없으면 `.harness-helm/runs/_unscoped/{run-id}/`를 사용한다.
- `run-id` format은 `Asia/Seoul` 기준 `YYYYMMDD-HHMMSS-h2-{command}`이며 harness script가 검증한다.
- h2 command를 실행하는 runtime adapter가 `raw/`, `normalized/`, `promotion-candidates/`를 생성한다. Go harness는 검증하고 정리하지만 모든 lifecycle command마다 생성하지는 않는다.
- `.harness-helm/runs/**`는 official KB가 아니며 default retrieval input도 아니다. `h2-archive`에서는 feature runs folder를 `docs/_archive/{archive-folder}/runs/`로 이동한 뒤 run별 Markdown 산출물만 남기고, archive root의 `stage-runtime-summary.md`에 사람이 읽는 timing summary를 남긴다.
- official docs로 옮기기 전에 sensitive/raw output을 제거하거나 mask한다.

## Upstream Override Input

사용자는 단일 run에 대해 기본 upstream provider/surface를 override할 수 있다. 사용자 요청을 파싱할 때 다음 두 가지 입력 형태를 인식한다.

- key-value form: `/h2:plan {feature} upstream=<provider> surface=<surface>`. `upstream`과 `surface` key만 인식한다. 중복이 있으면 마지막 값이 우선한다.
- natural language: 예: "이번 plan은 gstack 대신 superpowers writing-plans 기준으로 작성해줘". provider와 surface 이름을 추출한다.

같은 요청에 두 형태가 모두 있으면 key-value가 우선한다.

`references/provider-surface-selection-and-override.md` 또는 canonical docs guideline `docs/40_knowledge/conventions/guidelines/harness-helm/provider-surface-selection-and-override.md`에 정의된 선택 우선순위와 기록 규칙을 사용해 override를 적용한다. override 때문에 command routing을 바꾸지 않는다. 결과는 여전히 command의 `routing_target`으로 route되고 command의 h2 template에 기록한다. 입력 provider/surface만 바뀐다. run-level override는 `verification.completed`에 `actual:<provider>:<surface>` 형태로 기록한다. `.harness-helm/h2-cartridge.yml` default를 바꾸지 않는다.

## Adapter Rules

- 먼저 `AGENTS.md`를 따른 다음 `CLAUDE.md`와 project instruction을 따른다.
- command alias에 core semantics를 복사하거나 변경하지 않는다. 이 skill과 bundled `references/core-workflow.md`를 참조한다.
- Claude-specific wording, file location, invocation detail은 다를 수 있지만 output meaning과 routing은 이 skill, bundled `references/core-workflow.md`, Codex parity expectation과 일치해야 한다.
- gstack, superpowers, compound-engineering, enforcement scripts, `_indexes` generation, canonical promotion을 재구현하지 않는다.
- Compatibility note: 이 저장소에는 오래된 `hera-harness` asset이 있을 수 있다. `harness-helm`은 현재 suite name이며 현재 Claude adapter entrypoint다.

## 외부 스킬 통합: mattpocock/skills

`mattpocock/skills`는 이 저장소에 번들하지 않고 전역으로 설치한다.

- Claude Code: 14개 Engineering+Productivity 스킬을 `~/.claude/skills/`에 설치 (`diagnose`, `grill-with-docs`, `improve-codebase-architecture`, `prototype`, `setup-matt-pocock-skills`, `tdd`, `to-issues`, `to-prd`, `triage`, `zoom-out`, `caveman`, `grill-me`, `handoff`, `write-a-skill`)
- Codex: 동일한 14개에 misc 4개(`git-guardrails-claude-code`, `migrate-to-shoehorn`, `scaffold-exercises`, `setup-pre-commit`)를 추가해 `~/.agents/skills/`에 설치

이 외부 스킬들은 보통 `AGENTS.md`와 `docs/agents/`에 기록하는 저장소별 설정을 가정한다. harness-helm에서는 root `AGENTS.md`/`CLAUDE.md`를 h2 중심으로 유지하고 `docs/`를 workflow 산출물 전용으로 유지하기 위해, 그 설정을 이 섹션에 둔다. 아래 sub-section은 이 저장소 안에서 외부 스킬이 실행될 때 적용된다.

### 이슈 트래커

이슈는 GitHub `dandihera/harness-helm`에 있다. "이슈 트래커에 publish한다" 또는 "관련 ticket을 fetch한다"고 표현하는 스킬(`to-issues`, `triage`, `to-prd` 등)은 `gh` CLI를 사용한다: `gh issue create`, `gh issue view <n> --comments`, `gh issue edit <n> --add-label …`, `gh issue close <n>` 등. `gh`는 `git remote -v`로 저장소를 자동 추론한다. 오래된 GitHub issue 번호는 root `AGENTS.md` 규칙에 따라 `cookbooks/` 제목과 기준 참조에서 제외한다.

### Triage 레이블

다섯 가지 canonical 레이블이 GitHub 저장소에 존재하며 mattpocock role 이름과 1:1로 매핑된다. 적용은 `gh issue edit <number> --add-label <label>`로 한다.

| Role              | Label             | 의미                                       |
| ----------------- | ----------------- | ------------------------------------------ |
| `needs-triage`    | `needs-triage`    | maintainer가 평가해야 하는 이슈            |
| `needs-info`      | `needs-info`      | reporter의 추가 정보를 기다리는 상태       |
| `ready-for-agent` | `ready-for-agent` | 사양이 완비되어 AFK agent가 가져갈 수 있음 |
| `ready-for-human` | `ready-for-human` | 사람의 구현이 필요함                       |
| `wontfix`         | `wontfix`         | 처리하지 않음                              |

### 도메인 문서

harness-helm은 mattpocock 기본값(`CONTEXT.md`와 `docs/adr/`) 대신 HERA workflow 레이아웃을 사용한다. `CONTEXT.md`와 `docs/adr/`는 존재하지 않으며 새로 만들지 않는다. `diagnose`, `tdd`, `improve-codebase-architecture`, `zoom-out` 같은 스킬이 "도메인 컨텍스트" 또는 "ADR"을 요청하면 다음을 읽는다.

- `docs/10_domain/` — 엔티티, 어휘, lifecycle (`CONTEXT.md` 대체)
- `docs/30_decisions/` — 아키텍처/프로세스 결정 (`docs/adr/` 대체)
- `docs/10_domain/harness-helm/concepts.md` — harness-helm 제품 개념과 어휘
- `docs/40_knowledge/conventions/` — naming과 structure convention
- `docs/40_knowledge/references/` — compact external references (`matt-pocock-skills.md` 포함)
- GitHub Issues — backlog, follow-up, issue 단위 workflow tracking

해당 영역의 문서가 없으면 조용히 진행한다. 새로운 도메인 용어나 결정은 일반적인 h2 workflow(`h2-design`, `h2-report`, `h2-compound`)를 통해 점진적으로 추가된다. output에서 harness-helm 제품 개념을 명명할 때는 `docs/10_domain/harness-helm/concepts.md`에 정의된 용어를 사용하고, 더 넓은 도메인 용어는 `docs/10_domain/`, convention은 `docs/40_knowledge/conventions/`를 따른다. `docs/40_knowledge/references/`는 비교 참고자료로만 사용하고 harness-helm 기준으로 취급하지 않는다. `docs/30_decisions/`의 기존 결정과 모순되는 output을 내야 한다면 묵시적으로 override하지 말고 명시적으로 surface한다.
