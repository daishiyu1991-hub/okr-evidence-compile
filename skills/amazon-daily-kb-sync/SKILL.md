---
name: amazon-daily-kb-sync
version: 0.3.0
description: Per-owner daily Base sync for 86lux Amazon target-management. Each teammate runs this on their own codex laptop to identify their own action items from today's Feishu meetings/chats/docs/base-deltas and sync them into the 🚦每周任务 Base table (with assignee=ME), plus audit-field writes on own KR/project records they touched today. On weekly-meeting day, also adds own-record inconsistency detection. STRICT scope — Base writes only, no wiki writes (use `feishu-meeting-series-kb` for daily/weekly meeting wiki summaries).
metadata:
  requires:
    bins: ["lark-cli", "jq", "python3", "date"]
  cliHelp: "lark-cli base --help"
  agents: ["codex", "claude-code"]
  tenant: "86lux"
  base_token: "GxaobEQtqaOwFZsB5wTcC33Rnl7"
---

# Amazon Daily KB Sync (v3 — base-only, per-owner)

## Purpose

Each teammate runs this daily on their own codex laptop. The skill is **Base-table-only**:

- Scan today's Feishu evidence (meetings ME attended, chats with ME-relevant content, daily-page if exists, ME-owned Base deltas)
- Identify ME's own action items
- Write to Base tables ONLY:
  - `🚦每周任务` — create / update tasks where `执行人 = ME`
  - Audit fields on ME-owned KR (`👤个人OKR`) / project (`🧮团队项目清单`) / task records touched today
- On weekly-meeting day, also run own-record inconsistency detection

**This skill does NOT write to Feishu wiki.** Daily / weekly meeting wiki summaries are written by `feishu-meeting-series-kb`. If you need a wiki-side daily summary, run that skill separately.

**Multi-user safe by design**: 4 owners run concurrently with disjoint write sets:
- Each only touches records where `执行人/负责人 == ME`
- New tasks force `执行人 = ME` (no cross-owner task creation)
- No shared wiki page (this skill doesn't write wiki at all)

Reuse `amazon-base-kb-bridge` for ownership rules, field mapping, confidence rules, and inconsistency detection scripts.

## Boundaries

### What this skill DOES write to

- `🚦每周任务` (Base): new / updated tasks where `执行人 = ME`
- `👤个人OKR` (Base): audit fields ONLY (`最近更新原因`, `最近更新时间`, `最近更新来源`, `AI编译摘要`, `待人工确认`) on records where `执行人 == ME`
- `🧮团队项目清单` (Base): audit fields ONLY (same 5 fields) on records where `负责人 == ME`

### What this skill does NOT write to

- ❌ Feishu wiki (any node, any space) — use `feishu-meeting-series-kb`
- ❌ Feishu docs (any) — use `feishu-meeting-series-kb`
- ❌ Per-owner daily log doc — concept dropped from v3 (was an error in v0.2.0)
- ❌ Shared `02 日会沉淀` daily page — that's `feishu-meeting-series-kb`'s job
- ❌ KR / project formal status fields (状态/进度) without strong evidence
- ❌ Records not owned by ME

### Read inputs (read-only)

- `feishu-meeting-series-kb` daily wiki output (if it ran today and ME wants to use it as a starting summary)
- Feishu group chat messages (ME-relevant in `🚀亚马逊攻坚小分队` etc.)
- Feishu minutes / vc records (where ME is participant or owner)
- Same-day Base deltas filtered to ME's owned records

## Default Behavior

- **Identity** (Step 0): resolve `ME = lark-cli auth status .userOpenId` (with fallback chain). Abort if missing.
- **All Base writes ownership-gated** via `amazon-base-kb-bridge.assert_ownership(record, layer)`. Records not owned by ME are skipped (counted in audit log, not written).
- **Action items**: sync to `🚦每周任务` only when `action_item.assignee == ME`. Cross-owner items are surfaced in console preview as "cross-owner (not synced)" but NOT written.
- **Approval gate**: dry-run preview by default. Real write only when `auto_approve=true` param is set.
- **Never overwrite** `👤个人OKR.状态/进度` or `🧮团队项目清单.进度` without explicit strong evidence (per `amazon-base-kb-bridge` confidence rules).

## Workflow

1. **Identity** (`ME = lark-cli auth status .userOpenId`)
2. **Collect today's evidence (read-only)**:
   - Meetings where ME is participant: `lark-cli minutes/vc/calendar +search --participant-ids me --start <today> --end <today>`
   - ME-relevant excerpts from `🚀亚马逊攻坚小分队` group conclusions (read all, compile only what mentions ME or ME's KR/project)
   - Same-day Base deltas where ME owns the record (KR / project / task)
   - Optional: today's `feishu-meeting-series-kb` wiki output, if accessible, as a starting summary
3. **Extract candidate action items**:
   - For each item: try to identify `assignee` (open_id resolved via `lark-contact`)
   - Items where `assignee == ME` → include in "to sync" list
   - Items where `assignee != ME` or unassigned → include in "cross-owner (not synced)" list
4. **For each "to sync" item**: resolve target — match to existing 🚦每周任务 record OR mark as new
5. **For each ME-owned KR / project touched today**: build audit field updates (reason / source / abstract / 待人工确认 based on confidence)
6. **Preview**: print structured summary
   - tasks to create / update (with assignee=ME)
   - KR / project audit field updates
   - cross-owner items (not synced)
   - own-record inconsistencies (only on weekly-meeting day)
7. **Approval gate**: wait for OK unless `auto_approve=true`
8. **Base writes**:
   - `lark-cli base +record-batch-create` for new tasks (force `执行人 = [{"id": ME}]`)
   - `lark-cli base +record-batch-update` for task updates (with `assert_ownership` check)
   - `lark-cli base +record-batch-update` for KR / project audit fields (with `assert_ownership` check)
9. **Weekly-meeting day extension**: if today is weekly meeting day, run `amazon-base-kb-bridge/scripts/detect_state_inconsistencies.py --scope own --user $ME` and add results to the preview / console summary
10. **Verify**: readback all touched records, confirm fields written + ownership preserved

## Params

| param | required | default | semantics |
|---|---|---|---|
| `date` | no | today (Asia/Shanghai) | ISO date to compile for; default = today |
| `auto_approve` | no | `false` | If true, skip approval gate |
| `force_ownership_bypass` | no | `false` | If true, skip ownership scope check (CEO audit only) |
| `weekly_meeting_day` | no | `"mon"` | which weekday triggers weekly inconsistency detection |
| `evidence_chats` | no | `["🚀亚马逊攻坚小分队"]` | which group chats to scan for ME-relevant content |
| `read_meeting_kb` | no | `true` | If true, attempt to read today's `feishu-meeting-series-kb` wiki output as a starting summary |

## Failure Handling

- `lark-cli auth status` fail → ask user to `lark-cli auth login`. Abort.
- Ownership check fail on a record → skip that record's write, surface in audit log; do NOT abort whole run
- Base writeback partial failure → surface per-record result; do not retry blindly
- Inconsistency script fail (weekly-meeting day) → continue with daily flow, report failure separately
- No action items found today → preview shows "0 items to sync"; still emit audit field updates if any KR/project were touched in other ways

## Don't

- Don't write to ANY Feishu wiki / doc (use `feishu-meeting-series-kb` instead)
- Don't write to records you don't own (ownership check is absolute)
- Don't create tasks for other people (force `执行人 = ME`)
- Don't sync cross-owner action items into `🚦每周任务` (let the rightful owner sync from their own machine)
- Don't fabricate evidence not present in raw `lark-cli` outputs
- Don't run unattended without `auto_approve=true` set explicitly

## References

- [references/daily-sync-contract.md](references/daily-sync-contract.md)
- [references/weekly-compile-contract.md](references/weekly-compile-contract.md)
- [templates/daily-verification-checklist.md](templates/daily-verification-checklist.md)

## Dependencies (other skills)

- `amazon-base-kb-bridge` (ownership rules, field map, scripts for preview-build + inconsistency detect, confidence rules)
- `feishu-meeting-series-kb` (READ-ONLY: optionally read its daily wiki output as starting summary; this skill never writes wiki itself)
- Official lark-* skills (`lark-base`, `lark-vc`, `lark-minutes`, `lark-contact`, `lark-im`)

## Relationship to feishu-meeting-series-kb

| Concern | feishu-meeting-series-kb | amazon-daily-kb-sync (this) |
|---|---|---|
| Daily meeting wiki summary | ✅ writes (e.g., `02 日会沉淀/...`) | ❌ doesn't write |
| Weekly meeting wiki summary | ✅ writes | ❌ doesn't write |
| 🚦每周任务 Base table | ❌ read-only / inform-only | ✅ writes (own only) |
| KR / project audit fields | ❌ doesn't touch | ✅ writes (own only) |
| Trigger model | manual (per series / per date) | daily self-run (per owner) |
| Concurrency safety | Single wiki page if multi-owner (use carefully) | Per-owner ownership scope → safe |

**Workflow**: `feishu-meeting-series-kb` summarizes today's meetings into wiki (team-visible). `amazon-daily-kb-sync` then (optionally reading that wiki output) syncs ME's action items to Base. Two skills, two artifacts, no overlap.
