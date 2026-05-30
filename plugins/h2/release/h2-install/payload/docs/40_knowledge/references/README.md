# 40_knowledge/references

외부 repository, tool, skill ecosystem을 compact하게 정리한 비교 참고자료를 보관한다.

이 폴더의 문서는 harness-helm의 command semantics, governance, schema, runtime routing을 직접 정의하지 않는다. 그런 기준은 `cookbooks/`, `.harness-helm/*.yml`, `docs/40_knowledge/conventions/`, runtime skill references를 따른다.

## 파일 패턴

```text
docs/40_knowledge/references/{topic}.md
```

## 사용 기준

- 외부 자료의 요약, 비교 관찰, 적용 가능한 pattern을 보관한다.
- frontmatter `source_references`에 원문 repository, raw 문서, 확인한 API endpoint 같은 재검증 경로를 남긴다.
- 외부 자료가 바뀔 수 있으면 문서 본문에 확인일이나 확인한 source revision을 명시한다.
- 이 폴더의 문서를 기준 문서로 인용하지 않는다. 기준 변경이 필요하면 별도 convention, spec, decision, cookbook 변경으로 승격한다.
