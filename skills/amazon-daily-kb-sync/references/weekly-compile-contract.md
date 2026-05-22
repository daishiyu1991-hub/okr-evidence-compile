# Weekly Compile Contract (v3 — base-only, per-owner)

## Trigger

On weekly-meeting day (configurable; default Monday), run the weekly inconsistency detection in addition to the daily flow.

## Scope

All 7-day analysis is scoped to ME's own records:

- Own KRs: records where `执行人 == ME`, changes in past 7 days
- Own projects: records where `负责人 == ME`, changes in past 7 days
- Own tasks: records where `执行人 == ME`, status changes in past 7 days

Do not compile other owners' state changes — they run this skill on their own machines.

## Required Action

Run `amazon-base-kb-bridge/scripts/detect_state_inconsistencies.py` with ownership scope:

```bash
python3 ~/.agents/skills/amazon-base-kb-bridge/scripts/detect_state_inconsistencies.py \
  --scope own \
  --user $ME
```

Surface results in the console preview / summary. Do NOT auto-write the inconsistencies anywhere — they're for human review.

## Required Inconsistency Types (scoped to own records)

- Own-KR active but linked own-projects show no recent movement
- Own-project moving but linked own-KR has no recent status/progress change
- Own task overdue or incomplete while linked own-project blocker is empty
- Multiple own-tasks moved but linked own-project's `本周更新` is stale

Do not raise inconsistency for cross-owner relationships (e.g., my project linked to someone else's KR) — let them handle it.

## Output

Inconsistencies appear as part of the daily console preview (under a "Weekly inconsistency" section) and are written to audit fields IF the owner confirms:

- `AI编译摘要` on the relevant own KR or project record gets the inconsistency note appended
- `待人工确认 = true` is set
- Formal `状态/进度` field is NOT changed

The full inconsistency analysis (with cross-record references) is shown in the console output only. No wiki write, no separate file.

## Wiki Boundary

Weekly compile detection still doesn't touch wiki. The team's weekly meeting summary on wiki is `feishu-meeting-series-kb`'s job (its weekly-series KB compile).

If the weekly compile flow needs to surface a long-form summary, the right path is:
1. `amazon-daily-kb-sync` produces the JSON / console summary (this skill's output)
2. Owner reads it
3. Owner / `feishu-meeting-series-kb` writes the human-readable summary into the team weekly meeting wiki page (separate skill run)

Do not let the lines blur.
