---
name: amazon-meeting-update-assistant
description: Use when a teammate wants AI to turn Amazon meeting notes, Feishu links, daily-page links, chat summaries, or manual project updates into structured Base field changes with a preview-first confirmation flow, source traceability, and audit writes across KR, long-term project, and task layers.
---

# Amazon Meeting Update Assistant

## Purpose

This is the teammate-facing skill. It takes meeting or update content and turns it into a preview of Base changes. Only after confirmation should it write the target records.

Always load `amazon-base-kb-bridge` first for field mapping, confidence, and conflict rules.

## Accepted Inputs

- Meeting-notes text
- Feishu meeting or minute link
- Daily-page link from the Amazon knowledge base
- Group-chat summary
- Manual project update text
- Optional direct target hints:
  - specific `KR`
  - specific `长期项目`
  - specific `任务`

## Required Output Shape

Always return a two-step flow:

1. `拟更新预览`
2. `确认后写入`

The preview must include:
- target layer
- matched record
- field-by-field before/after
- reason
- source link or source page
- confidence
- whether manual review is recommended

## Execution Flow

1. **Identity** (v2): resolve `ME = lark-cli auth status .userOpenId` (with fallback chain). Abort if missing.
2. Parse the input into a `source_packet`
3. Resolve whether the input is meeting-driven or manually targeted
4. Resolve the layer and candidate records
5. **Ownership check** (v2): for each resolved target record, call `amazon-base-kb-bridge.assert_ownership(record, layer)`:
   - `kr` layer → `record.执行人[0].id == ME`
   - `project` layer → `record.负责人[0].id == ME`
   - `task` layer (update) → `record.执行人[0].id == ME`
   - mismatch → drop that target from preview, surface in preview as `❌ ownership_mismatch (owned by <other>)`, **do not** write
6. Use `scripts/build_update_preview.py` from `amazon-base-kb-bridge`
7. Present the preview (must mark each target's ownership status: `✅ own` / `❌ not own`)
8. Only write after explicit confirmation. **Refuse** to write any target marked `❌ not own` even after confirmation
9. After writing, backfill audit fields

## Write Boundaries

- **Ownership scope (v2, hard rule)**:
  - KR write: only when `KR.执行人 == ME`
  - Project write: only when `项目.负责人 == ME`
  - Task update: only when `任务.执行人 == ME`
  - Task create: force `任务.执行人 = [{"id": ME}]`. If source action item is for another person → skip create (let them sync from their own machine)
  - Audit fields obey the same ownership scope as formal fields
- KR layer formal fields: only `状态`, `进度`, `输出结果`
- Project layer formal/helper fields: only `进度`, `本周更新`, `下一步`, `阻塞`, `下次检查点`
- Task layer formal/helper fields: only `执行人`, `关联KR`, `任务进度`, `本周完成结果`, `输出结果`, `任务结束日期`
- Task assignee resolution: when the source explicitly names an owner (other than ME),
  resolve the person with `lark-contact`, but **only emit a write if that owner == ME**.
  Otherwise add to "cross-owner action items (not synced)" section of preview.
- Task KR link: when the source maps to a KR, resolve the KR record first and
  include `关联KR` as `[{ "id": "recxxx" }]`.

If confidence is low:
- do not write formal state
- write `AI编译摘要` and `待人工确认` only, or stay preview-only

If ownership mismatch:
- **never** write (even audit fields)
- surface in preview so caller knows that target is owned by someone else
- recommend the other owner runs the skill on their own machine

## Multi-User Safety (v2 notes)

This skill runs concurrently on multiple teammates' codex laptops. Because every
write is scoped by ownership, two teammates can run the skill at the same time
without conflicting on the same record:

- 戴时雨 can only write to records where `执行人/负责人 == 戴时雨.open_id`
- 罗国华 can only write to records where `执行人/负责人 == 罗国华.open_id`
- Same source content (e.g., a shared meeting note) processed by 4 owners produces 4 disjoint write sets

No shared lock needed. Action item dedup happens naturally because each item has at most one owner who can sync it.

## References

- [references/interaction-contract.md](references/interaction-contract.md)
- [references/writeback-checklist.md](references/writeback-checklist.md)
- [templates/confirmation_preview.md](templates/confirmation_preview.md)
