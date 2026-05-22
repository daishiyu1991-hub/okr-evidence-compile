# Daily Sync Contract (v2 — per-owner)

## Date Boundary

- Use `Asia/Shanghai`
- Only process 2026+ data

## Identity Requirement (v2)

- Resolve `ME = lark-cli auth status .userOpenId` first
- Abort if missing; instruct user to run `lark-cli auth login`

## Read Sources

Filter all reads to ME's scope:

- `🚀亚马逊攻坚小分队` same-day messages (skill reads all, but compiles only what's ME-relevant — ME mentioned, ME's action items, ME's projects)
- Shared docs / images / files / whiteboards from chats ME participated in
- Same-day meetings / minutes / notes where ME is `participant-ids me` or `owner-ids me`
- Same-day Base deltas filtered by owner field:
  - KR (`👤个人OKR`): `执行人 == ME`
  - Project (`🧮团队项目清单`): `负责人 == ME`
  - Task (`🚦每周任务`): `执行人 == ME`

## Write Targets

Per-owner only:

- ME's own daily log doc under `02 日会沉淀`:
  - Title: `日会同步日志 · <ME.userName>`
  - Append entry (prepend new at top of Sync history)
- `🚦每周任务` records where `执行人 == ME` (update existing OR create new with `执行人 = [{"id": ME}]`)
- Audit fields on ME-owned KR/project records that were touched this day

## Forbidden Write Targets

- Daily page shared across team (v1 deprecated model)
- Any KR/project record where ME != owner
- Tasks created with `执行人 != ME`
- `04 决策与行动项追踪` shared page (use individual daily log doc instead)

## Validation

Before finishing, verify (via readback):

- Own daily log doc exists and the new entry is at top of Sync history
- Old entries preserved (no overwrite, no drop)
- Page title contains `<ME.userName>` (not someone else's name)
- Synced task records all have `执行人 == ME`
- Audit fields touched only on ME-owned records
- Source index in entry is traceable (each citation has a link back to source)

## Concurrency Model

Multiple owners running concurrently is the **expected** mode. Each owner writes to:

- Their own (different) daily log doc
- Tasks they own (force `执行人 = ME`)
- KR/project records they own (ownership check)

These write sets are disjoint by design. No locking required.
