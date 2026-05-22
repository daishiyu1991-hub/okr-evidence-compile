# Confidence And Conflict Rules

## Confidence Bands

- `high`
  - unique record match
  - source clearly states a status/progress/action update
  - no contradiction with current layer ownership
- `medium`
  - likely record match
  - helper-field update is clear
  - formal status change is implied but not explicit
- `low`
  - multiple candidate records
  - source lacks direct state language
  - cross-layer inference is speculative

## Default Actions

- `high`
  - preview and allow formal write after confirmation
- `medium`
  - preview; default to helper-field write only unless user confirms formal write
- `low`
  - do not write formal state; write audit only or stay preview-only

## Conflict Rules

- If source text conflicts with an existing formal state and the evidence is not explicit:
  - do not overwrite the formal field
  - write `AI编译摘要`
  - set `待人工确认 = true`
- If one source affects both KR and project:
  - show a merged preview
  - require one confirmation covering both layers
- If source is enough to create a task but not enough to move KR/project:
  - create or update the task only
  - do not force upstream status movement

## Weekly Inconsistency Rules

Raise an item when:
- KR is active but linked projects show no recent movement
- Project is advancing but linked KR has no recent status/progress change
- Task is overdue or incomplete while project blocker is empty
- Multiple tasks move while project `本周更新` remains stale

