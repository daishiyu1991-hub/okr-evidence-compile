# Daily Sync Contract (v3 — base-only, per-owner)

## Date Boundary

- Use `Asia/Shanghai`
- Only process 2026+ data

## Identity Requirement

- Resolve `ME = lark-cli auth status .userOpenId` first (with fallback chain)
- Abort if missing; instruct user to run `lark-cli auth login`

## Read Sources (read-only)

Filter all reads to ME's scope:

- ME-relevant excerpts from `🚀亚马逊攻坚小分队` and other Amazon chats ME participates in
- Same-day meetings / minutes / notes where ME is `--participant-ids me` or `--owner-ids me`
- Same-day Base deltas filtered by owner field:
  - KR (`👤个人OKR`): `执行人 == ME`
  - Project (`🧮团队项目清单`): `负责人 == ME`
  - Task (`🚦每周任务`): `执行人 == ME`
- Optional: today's `feishu-meeting-series-kb` wiki output (if accessible, as a starting summary)

## Write Targets (Base only)

Per-owner, ownership-gated:

- `🚦每周任务` table:
  - Update existing records where `执行人 == ME`
  - Create new records with forced `执行人 = [{"id": ME}]`
- Audit fields ONLY on ME-owned KR records (`👤个人OKR`, scoped by `执行人 == ME`):
  - `最近更新原因`, `最近更新时间`, `最近更新来源`, `AI编译摘要`, `待人工确认`
- Audit fields ONLY on ME-owned project records (`🧮团队项目清单`, scoped by `负责人 == ME`):
  - Same 5 audit fields

## Forbidden Write Targets

- ❌ Any Feishu wiki (use `feishu-meeting-series-kb`)
- ❌ Any Feishu doc (use `feishu-meeting-series-kb`)
- ❌ KR / project formal fields (状态/进度) without strong evidence
- ❌ Any Base record where `ME != owner`
- ❌ New tasks with `执行人 != ME`
- ❌ Local file outputs (no per-owner daily log; v0.2.0 design dropped)

## Validation

Before finishing, verify (via readback):

- Synced task records all have `执行人 == ME`
- Audit fields touched only on ME-owned records
- KR / project 状态/进度 fields untouched (unless strong-evidence formal write was explicitly approved)
- No Feishu wiki / doc was written
- Cross-owner action items appear in console preview as "(not synced)" but NOT in any Base write
- Console preview is honest about 0 items if there are 0 items today

## Concurrency Model

Multiple owners running concurrently is the **expected** mode. Each owner writes to:

- Tasks they own (force `执行人 = ME`)
- KR / project records they own (ownership check)

These write sets are disjoint by design. No locking required.

If two owners run at the exact same time:
- They write to different records (disjoint)
- They both might create a new task from the same source action item IF that action item is ambiguous (no clear single assignee)
- Mitigation: only sync action items with **explicit** `assignee == ME`; ambiguous-assignee items are surfaced for human review, not auto-synced

## Wiki Boundary

This skill **never** touches Feishu wiki. If you see code or workflow that writes to wiki here, it's a bug — wiki is `feishu-meeting-series-kb`'s domain. Daily / weekly meeting summaries belong there, not here.
