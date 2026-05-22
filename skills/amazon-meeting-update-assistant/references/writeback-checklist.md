# Writeback Checklist (v2 — ownership-scoped)

## Identity prerequisite

- `ME = lark-cli auth status .userOpenId` resolved before any preview / write
- abort if missing

## Before writing (per target record)

- **Ownership check passes** (v2 hard rule):
  - KR layer → `record.执行人[0].id == ME`
  - Project layer → `record.负责人[0].id == ME`
  - Task layer (update) → `record.执行人[0].id == ME`
  - Task layer (create) → forced `执行人 = [{"id": ME}]`
  - Mismatch → write SKIPPED (not just preview-blocked, actually refused)
- source is traceable
- target record is uniquely identified
- field is on the allowed write list
- before/after diff is explicit
- confidence is not low for formal writes
- named owners/assignees have been resolved to Feishu `open_id`
- user fields are written as `[{ "id": "ou_xxx" }]`, not as plain text names
- linked KR/project fields have been resolved to Base `record_id`
- link fields are written as `[{ "id": "recxxx" }]`, not as plain text titles

## After writing

- write `最近更新原因`
- write `最近更新来源`
- write `最近更新时间`
- write `AI编译摘要`
- set `待人工确认` according to confidence/conflict

## Never do

- write to a record where `ME != owner` (no exception except `force_ownership_bypass=true`)
- create tasks for other people (force `执行人 = ME`)
- overwrite KR/project formal state from vague discussion alone
- write two conflicting target records from the same source without user choice
- silently drop cross-owner action items — list them in preview as "cross-owner (not synced)"
