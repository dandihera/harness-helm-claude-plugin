# Compound Policy Config Reference

`0306 Compound Policy Config`의 압축 runtime snapshot입니다.

## Rule

`.harness-helm/h2-compound.yml`은 `h2-compound`가 완료된 작업을 재사용 지식으로 바꾸는 방식을 제어합니다.

파일이 없으면 conservative built-in default를 사용하고 compound artifact에 fallback을 기록합니다.

## Policy Areas

- domain refinement mode와 허용되는 run-level override
- 재사용 지식의 canonical destination mapping
- learning과 solution의 low-risk write 정책
- spec, decision, convention, operational policy의 governed review gate
- 생성 지식에 필요한 retrieval hook field

## Write Boundary

Low-risk knowledge는 overlap, schema, lint check 후 작성할 수 있습니다.

Governed canonical target은 owner, verifier, Tech Lead 승인 근거가 기록될 때까지 promotion candidate로 staging해야 합니다.

## Avoid

- governed approval을 피하려고 write를 low-risk로 부르지 않습니다.
- `h2-compound.yml`로 command provider나 routing을 바꾸지 않습니다.
- review evidence 없이 architecture나 policy 변경을 canonical docs에 직접 쓰지 않습니다.

