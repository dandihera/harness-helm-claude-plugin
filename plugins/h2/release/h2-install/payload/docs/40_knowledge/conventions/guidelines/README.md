# 40_knowledge/conventions/guidelines

h2 workflow에서 agent나 사용자가 따라야 하는 구체적 운용 지침을 보관한다.

상위 `docs/40_knowledge/conventions/`가 용어와 개념 같은 넓은 규약을 담는다면, 이 폴더는 특정 h2 단계에서 실제로 어떻게 판단하고 기록해야 하는지를 설명한다.

## 파일 패턴

```text
docs/40_knowledge/conventions/guidelines/harness-helm/{topic}.md
```

## 현재 지침

- `harness-helm/README.md`: harness-helm runtime guideline namespace의 진입점.
- `harness-helm/runtime-reference-selection.md`: `cookbooks/`, docs guideline, skill reference snapshot을 나누는 기준.
- `harness-helm/canonical-promotion-flow.md`: `h2-compound`가 만든 승격 후보를 승인 후 canonical 문서로 작성하는 절차.
- `harness-helm/specs-vs-decisions.md`: `20_specs`와 `30_decisions`를 구분하는 기준.
- `harness-helm/provider-surface-selection-and-override.md`: h2 command에서 provider/surface를 선택하거나 run-level override하는 기준.

기존 flat `h2-*.md` guideline은 `harness-helm/` namespace로 이동되었다. 새 canonical path는 위 namespace 아래의 파일이다.
