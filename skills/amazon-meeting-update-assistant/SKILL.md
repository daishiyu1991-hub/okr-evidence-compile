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

1. Parse the input into a `source_packet`
2. Resolve whether the input is meeting-driven or manually targeted
3. Resolve the layer and candidate records
4. Use `scripts/build_update_preview.py` from `amazon-base-kb-bridge`
5. Present the preview
6. Only write after explicit confirmation
7. After writing, backfill audit fields

## Write Boundaries

- KR layer: only `状态`, `进度`, `输出结果`
- Project layer: only `进度`, `本周更新`, `下一步`, `阻塞`, `下次检查点`
- Task layer: only `执行人`, `关联KR`, `任务进度`, `本周完成结果`, `输出结果`, `任务结束日期`
- Task assignee: when the source explicitly names an owner, resolve the person
  with `lark-contact` and include `执行人` as a user field in the preview/write.
- Task KR link: when the source maps to a KR, resolve the KR record first and
  include `关联KR` as `[{ "id": "recxxx" }]`.

If confidence is low:
- do not write formal state
- write `AI编译摘要` and `待人工确认` only, or stay preview-only

## References

- [references/interaction-contract.md](references/interaction-contract.md)
- [references/writeback-checklist.md](references/writeback-checklist.md)
- [templates/confirmation_preview.md](templates/confirmation_preview.md)
