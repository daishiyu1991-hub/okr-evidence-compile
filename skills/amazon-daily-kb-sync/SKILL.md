---
name: amazon-daily-kb-sync
version: 0.2.0
description: Per-owner daily knowledge-base sync for 86lux Amazon target-management. Each teammate runs this on their own codex laptop to compile their own day — read same-day Feishu meeting/chat/doc artifacts, filter Base deltas to their own KR/project/task records, append a dated entry to their own owner-scoped daily log doc, and sync only their own action items to the 🚦每周任务 table. On weekly-meeting day, adds 7-day own-record compilation and inconsistency reminders. Strict ownership safety — every write is scoped to the current lark-cli user.
metadata:
  requires:
    bins: ["lark-cli", "jq", "python3", "date"]
  cliHelp: "lark-cli base --help"
  agents: ["codex", "claude-code"]
  tenant: "86lux"
  base_token: "GxaobEQtqaOwFZsB5wTcC33Rnl7"
  wiki_space_id: "7639331686206999770"
  wiki_parent_node_label: "02 日会沉淀"
---

# Amazon Daily KB Sync (v2 — per-owner)

## Purpose

Each teammate runs this on their own codex laptop. The skill compiles **their own** day:

- Read same-day Feishu artifacts (meetings, group messages, daily-page input, docs)
- Filter Base deltas to their own KR / project / task records (where they are 执行人 / 负责人)
- Append a dated entry to **their own owner-scoped daily log doc** under `02 日会沉淀`
- Sync only **their own** action items into `🚦每周任务`
- On weekly-meeting day, add 7-day own-record compilation + inconsistency reminders for own records

**Multi-user safe by design**: 4 owners can run concurrently. Each writes only to:
1. Their own daily log doc (`日会同步日志 · <执行人>`)
2. Their own Base records (ownership-gated)
3. Tasks they assign to themselves (force `执行人 = ME` on create)

No shared daily page, no shared lock needed.

Reuse `feishu-meeting-series-kb` for meeting discovery, raw-material copying, and entry structure. Reuse `amazon-base-kb-bridge` for ownership check, field mapping, and inconsistency logic.

## Default Behavior

- **Identity** (Step 0): resolve `ME = lark-cli auth status .userOpenId` (fallback chain). Abort if missing.
- **All Base writes ownership-gated** via `amazon-base-kb-bridge.assert_ownership(record, layer)`. Records not owned by ME are skipped (not written, but counted in audit log).
- **Action items**: sync to `🚦每周任务` only when `action_item.assignee == ME`. Cross-owner items are listed in the daily entry's "cross-owner action items (not synced)" section but not written.
- **Daily log doc**: 1 doc per owner, name `日会同步日志 · <执行人 name>`, lives under wiki node `02 日会沉淀`. Each daily run **prepends** a new entry (similar to `okr-evidence-compile` doc append model).
- **Approval gate**: dry-run preview by default. Real write only when `auto_approve=true` param is set (Hermes cron pattern). When run by human owner from their own laptop, default to confirm-after-preview.
- **Never overwrite** `👤个人OKR.状态/进度` or `🧮团队项目清单.进度` without explicit strong evidence (per `amazon-base-kb-bridge` confidence rules).

## Inputs

- Shanghai-date day boundary (`Asia/Shanghai`)
- Same-day Amazon group messages and shared artifacts (only for `🚀亚马逊攻坚小分队` or other Amazon-related chats the owner participates in)
- Same-day meetings / minutes / docs (filter by `participant-ids me` for discovery)
- Same-day Base deltas filtered to records owned by ME:
  - `👤个人OKR` where `执行人 == ME`
  - `🧮团队项目清单` where `负责人 == ME`
  - `🚦每周任务` where `执行人 == ME`

## Daily Outputs (Per Owner)

- **Own daily log doc** under `02 日会沉淀`:
  - Create on first run, prepend on subsequent runs
  - Naming: `日会同步日志 · <执行人 name>` (e.g., `日会同步日志 · 戴时雨`)
- Each entry follows `references/daily-entry-template.md` and contains:
  - `### #N · ISO-week · YYYY-MM-DD · trigger="..."`
  - `👤 当天结论 (人读版)` — 现状 / 怎么办 / 为什么
  - `机器读结构`:
    - 原始群结论区（completely mirrored from `🚀亚马逊攻坚小分队` if ME was in any meeting today）
    - 当天会议 / minutes 引用
    - 当天我持有的 base 变更（KR / 项目 / 任务）
    - 当天新建 / 更新 task 同步（assignee == ME 的）
    - cross-owner action items (not synced — listed for transparency)
    - 来源索引
- **`🚦每周任务` writes**: new/updated tasks where `执行人 == ME`
- **Audit fields** on touched own records: `最近更新原因` / `最近更新时间` / `最近更新来源`

## Weekly-Meeting Day Outputs

When the run day hits the weekly meeting (configurable; default: Monday):

- 7-day own-record state-change summary:
  - own KRs that moved (and how)
  - own projects that moved
  - own tasks that completed / overdue
- Run `amazon-base-kb-bridge/scripts/detect_state_inconsistencies.py` **scoped to own records**
- Append "Weekly compile" section to the daily entry, NOT a separate doc
- Surface inconsistency reminders + pending decisions

## Hard Boundaries

- **Ownership**: never write a record not owned by ME (Step 0 strict; bypass only via explicit `force_ownership_bypass=true`)
- **Never** directly overwrite `👤个人OKR.状态/进度` without evidence
- **Never** directly overwrite `🧮团队项目清单.进度` without explicit strong evidence
- Only supplement helper project fields when evidence is sufficient
- New tasks: force `执行人 = ME`; never create tasks for other people
- **No shared daily page**: each owner has their own doc; do not write to a date-shared page (v1 model is deprecated)

## Workflow

1. **Identity** (`ME`)
2. **Resolve own daily log doc**:
   - Compute expected title: `日会同步日志 · <ME.userName>`
   - Search wiki node `02 日会沉淀` for that title
   - If found → branch C (prepend)
   - If not found → branch A (create new doc with 1 entry)
3. **Collect today's evidence**:
   - Meetings where ME is participant: `lark-cli minutes/vc/calendar +search --participant-ids me --start <today> --end <today>`
   - Group conclusions where ME is mentioned in `🚀亚马逊攻坚小分队` (read only ME-relevant excerpts)
   - Same-day Base deltas where ME owns the record
4. **Compile entry** (running agent does this itself; see `references/daily-entry-template.md`):
   - 👤 当天结论 (人读版)
   - 机器读结构 (full evidence)
   - Action items classified: my own (sync) / cross-owner (list-only)
5. **Approval gate**: preview JSON + markdown. If `auto_approve=false` and human is running → wait for OK.
6. **Doc write**: create or prepend the entry to own daily log doc
7. **Task sync**: for each own action item, create/update record in `🚦每周任务` (force `执行人 = ME`, `assert_ownership` on update)
8. **Audit field write** on own records touched (`最近更新原因` etc.)
9. **Weekly-meeting day extension**: if today is weekly meeting day, also append weekly compile section + inconsistencies (scoped to own records)
10. **Verify** via base + docs readback

## Params

| param | required | default | semantics |
|---|---|---|---|
| `date` | no | today (Asia/Shanghai) | ISO date to compile for; default = today |
| `auto_approve` | no | `false` | If true, skip approval gate |
| `force_ownership_bypass` | no | `false` | If true, skip ownership scope check (audit only) |
| `weekly_meeting_day` | no | `"mon"` | which weekday triggers weekly compile |
| `evidence_chats` | no | `["🚀亚马逊攻坚小分队"]` | which group chats to scan for daily conclusions |

## Failure Handling

- `lark-cli auth status` fail → ask user to `lark-cli auth login`. Abort.
- Wiki node `02 日会沉淀` not findable → abort, ask user to confirm node exists or pass node token directly
- Ownership check fail on a record → skip that record's write, surface in audit log; do NOT abort whole run
- Doc create/update error → do NOT proceed to base writeback (avoid orphan audit). Surface error.
- Base writeback partial failure → surface per-record result. Doc entry already written — caller decides whether to retry.

## Don't

- Don't write to records you don't own (ownership check is absolute)
- Don't create tasks for other people
- Don't sync cross-owner action items into `🚦每周任务` (let the rightful owner sync from their own machine)
- Don't write into a shared daily page; v2 uses per-owner docs
- Don't fabricate evidence not present in raw `lark-cli` outputs
- Don't run unattended without `auto_approve=true` set explicitly

## References

- [references/daily-sync-contract.md](references/daily-sync-contract.md)
- [references/daily-entry-template.md](references/daily-entry-template.md)
- [references/weekly-compile-contract.md](references/weekly-compile-contract.md)
- [templates/daily-verification-checklist.md](templates/daily-verification-checklist.md)

## Dependencies (other skills)

- `amazon-base-kb-bridge` (ownership rules, field map, scripts, confidence rules)
- `feishu-meeting-series-kb` (meeting discovery, raw-material preservation, entry structure)
- Official lark-* skills (`lark-base`, `lark-doc`, `lark-wiki`, `lark-vc`, `lark-minutes`, `lark-contact`)
