# Runs Summary: {{feature}}

Generated: {{generated_at}}
Archive: `{{archive_path}}`

## Totals

| result | stage_elapsed | archive_wall_clock | runs | warnings |
|---|---:|---:|---:|---:|
{{totals_rows}}

## Runs

| stage | result | duration | surface | run_id |
|---|---|---:|---|---|
{{runs_rows}}

## Autorun Groups

| autorun_id | stage_count | elapsed | stages | slowest_stage |
|---|---:|---:|---|---|
{{autorun_group_rows}}

## Autorun Iterations

| autorun_id | iteration | stage | attempt | status | back_edge_from | reason | resolution |
|---|---:|---|---:|---|---|---|---|
{{autorun_iteration_rows}}

## Warnings

{{warnings_block}}
