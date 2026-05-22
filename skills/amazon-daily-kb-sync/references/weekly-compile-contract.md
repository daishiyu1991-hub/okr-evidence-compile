# Weekly Compile Contract (v2 — per-owner)

## Trigger

Append a weekly compile section to ME's daily entry when:

- the day contains the weekly meeting (configurable; default Monday), OR
- the day's meeting set clearly includes the weekly review / planning meeting

The weekly section lives **inside the same daily entry**, not in a separate doc. The owner's daily log doc accumulates both daily entries and (on weekly days) entries that include a weekly compile block.

## Scope

All 7-day analysis is scoped to ME's own records:

- Own KRs: changes to KRs where `执行人 == ME` over the past 7 days
- Own projects: changes to projects where `负责人 == ME` over the past 7 days
- Own tasks: tasks where `执行人 == ME`, completed / in-progress / overdue in the past 7 days

Do not compile other owners' state changes — they run this skill on their own machines.

## Required Weekly Sections

Inside the daily entry (under `机器读结构`):

```
**Weekly compile (7-day · own records only)**

- 7-day own-KR change summary
  - <KR record_id>: <state change> (evidence: <link>)
- 7-day own-project change summary
  - <project record_id>: ...
- 7-day own-task change summary
  - <task record_id>: completed / overdue / blocked ...
- Own-record inconsistency reminders (from amazon-base-kb-bridge detect_state_inconsistencies)
  - <inconsistency type>: <record refs>
- Pending decisions (open items I owe)
  - ...
```

## Required Inconsistency Types (scoped to own records)

Run `amazon-base-kb-bridge/scripts/detect_state_inconsistencies.py` with `--scope own --user $ME`:

- Own-KR active but linked own-projects show no recent movement
- Own-project moving but linked own-KR has no recent status/progress change
- Own-overdue task without project blocker
- Own-task moved repeatedly but linked own-project's `本周更新` stale

Do not raise inconsistency for cross-owner relationships (e.g., my project linked to someone else's KR) — let them handle it.

## Output Discipline

- Weekly section is part of the daily entry. Do not create a separate weekly doc.
- Use evidence links (`base://...` or `https://feishu.cn/...`); never invent record IDs.
- Mark inconsistency items with action recommendations (e.g., `→ check linked project recXXX 本周更新`).
- If 0 own-record activity over 7 days, still emit the weekly section with `evidence_count=0` and a "low activity" note — silence is also signal.
