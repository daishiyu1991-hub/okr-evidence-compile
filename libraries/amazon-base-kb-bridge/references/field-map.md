# Field Map

## Owner Field Quick Lookup (v2)

| layer | table | owner field name | use this field for `assert_ownership` |
|---|---|---|---|
| `kr` | `👤个人OKR` (tblxM7ZfxJt2P4Fl) | `执行人` | yes |
| `project` | `🧮团队项目清单` (tblOHGg4IA2pY7uh) | `负责人` | yes |
| `task` | `🚦每周任务` (tblrduPxvdifLm62) | `执行人` | yes (for update); force `= ME` when creating new |

All owner fields are Base user-cell shape `[{"id":"ou_xxx","name":"..."}]`. Compare on `[0].id`.

## Layer 1: KR / Target

Table:
- name: `👤个人OKR`
- id: `tblxM7ZfxJt2P4Fl`

Primary identity fields:
- `O-目标`
- `KR-关键结果`
- `执行人`
- `关联团队项目`

Formal writable fields:
- `状态`
- `进度`
- `输出结果`

Audit fields:
- `最近更新原因`
- `最近更新来源`
- `最近更新时间`
- `AI编译摘要`
- `待人工确认`

## Layer 2: Long-Term Project

Table:
- name: `🧮团队项目清单`
- id: `tblOHGg4IA2pY7uh`

Primary identity fields:
- `项目名称`
- `团队OKR`
- `负责人`
- `关联个人OKR`

Formal/helper writable fields:
- `进度`
- `本周更新`
- `下一步`
- `阻塞`
- `下次检查点`

Audit fields:
- `最近更新原因`
- `最近更新来源`
- `最近更新时间`
- `AI编译摘要`
- `待人工确认`

## Layer 3: Task

Table:
- name: `🚦每周任务`
- id: `tblrduPxvdifLm62`

Primary identity fields:
- `任务`
- `所属项目`
- `关联KR`
- `执行人`

Formal/helper writable fields:
- `执行人`
- `关联KR`
- `任务进度`
- `本周完成结果`
- `输出结果`
- `任务结束日期`

Audit fields:
- `最近更新原因`
- `最近更新来源`
- `最近更新时间`
- `AI编译摘要`
- `待人工确认`

## Source Packet Defaults

- `source_type`: `meeting_notes` | `minutes_link` | `daily_page` | `chat_summary` | `manual_update`
- `source_url`: canonical source link when present
- `source_title`: source title or generated label
- `source_date`: ISO date in Asia/Shanghai
- `raw_excerpt`: compact evidence excerpt only

## Target Resolution Rules

- Prefer exact record resolution through explicit link or exact title match
- Fall back to owner + title/keyword + date-window narrowing
- If more than one plausible record remains, return candidates and stop at preview
- If a source names an owner or assignee, resolve the person through `lark-contact`
  before preview/write and use the Base user-cell shape `[{ "id": "ou_xxx" }]`.
  Do not write a plain-text person name into user fields.
- If a source maps to a KR, resolve the target KR record in `👤个人OKR` first and
  write `关联KR` as a Base link-cell value `[{ "id": "recxxx" }]`. Do not write
  the KR title as plain text.
