---
name: amazon-base-kb-bridge
description: Shared bridge for Amazon target-management workflows. Use when a task needs to map meeting or project-update content into the existing Feishu Base and knowledge-base structure, including source packets, target resolution across KR/project/task layers, proposed field changes, audit payloads, confidence rules, and cross-layer inconsistency detection.
---

# Amazon Base KB Bridge

## Purpose

Provide one decision layer for all Amazon target-management writes. This skill does not own user-facing workflow by itself. It exists so `amazon-meeting-update-assistant` and `amazon-daily-kb-sync` use the same mapping rules, source-trace format, write boundary, and inconsistency logic.

Read [references/field-map.md](references/field-map.md) before resolving targets or writing fields. Read [references/confidence-and-conflict-rules.md](references/confidence-and-conflict-rules.md) before deciding whether a change should update a formal status field or only write audit notes.

## Fixed Objects

- Base: `团队管理（OKR&项目&任务)` token `GxaobEQtqaOwFZsB5wTcC33Rnl7`
- KR table: `👤个人OKR` table `tblxM7ZfxJt2P4Fl`
- Long-term project table: `🧮团队项目清单` table `tblOHGg4IA2pY7uh`
- Task table: `🚦每周任务` table `tblrduPxvdifLm62`
- Knowledge space: `亚马逊目标管理与会议沟通沉淀` space `7639331686206999770`
- Homepage: `目标管理首页` wiki `WN1fwFod7imQnQkicIMcZEoQn7d`

## Canonical Models

Use these four shapes throughout:

- `source_packet`
- `target_resolution`
- `proposed_change`
- `audit_payload`

The machine-readable defaults live in [templates/field_map.json](templates/field_map.json) and [templates/proposed_update_preview.json](templates/proposed_update_preview.json).

## Resolution Order

Always follow this order:

1. Build `source_packet`
2. Resolve layer: `kr` / `project` / `task`
3. Resolve exact record or candidate records
4. Compute proposed changes
5. Score confidence
6. Decide write mode
7. Attach audit payload

Do not skip directly from raw text to Base write.

## Write Modes

- `write_formal`
  - Use only when the record is uniquely identified and the evidence is sufficient.
- `write_helper_only`
  - Use when project helper fields can be updated but formal status/progress should not change.
- `preview_only`
  - Use when there are multiple candidates or low confidence.
- `audit_only`
  - Use when the source is useful but too weak to modify the formal state.

## What This Skill Can Decide

- Which layer the source belongs to
- Which fields are writable for that layer
- Whether a change should remain preview-only
- Whether a conflict should become `待人工确认`
- Whether cross-layer inconsistency should be raised
- Whether the current `lark-cli` user has ownership permission to write a target record (v2 — multi-user safety)

## What This Skill Must Not Decide

- Final human approval for a meeting-driven write
- A forced overwrite of `👤个人OKR.状态/进度`
- A forced overwrite of `🧮团队项目清单.进度` when evidence is weak
- Team-visible publication policy outside the existing daily/weekly KB workflow
- Cross-owner writes — see "Ownership Scoping" below

## Ownership Scoping (v2 — codex self-run safety)

This skill runs on every teammate's own codex laptop (not Hermes). To keep the
shared Base safe under concurrent multi-user execution, **all writes must be
scoped to the current `lark-cli` user's own records**. The pattern:

```bash
# 1. Resolve current identity (preferred fallback chain)
ME=$(lark-cli auth status --format json 2>&1 \
  | jq -r '.userOpenId // .data.user_open_id // (.data.users[0].userOpenId) // empty')
[ -z "$ME" ] && abort "no lark-cli identity — run \`lark-cli auth login\` first"
```

### Owner field per layer

| layer | table | owner field | shape |
|---|---|---|---|
| `kr` | `👤个人OKR` | `执行人` | `[{"id":"ou_xxx","name":"..."}]` |
| `project` | `🧮团队项目清单` | `负责人` | `[{"id":"ou_xxx","name":"..."}]` |
| `task` | `🚦每周任务` | `执行人` | `[{"id":"ou_xxx","name":"..."}]` |

### Ownership assertion rule

For any write operation, callers MUST call (conceptually):

```text
assert_ownership(record, layer) →
  OWNER = record.fields[OWNER_FIELD_FOR_LAYER][0].id
  if OWNER != ME:
    abort with "ownership mismatch: ME=<ME> OWNER=<OWNER> layer=<layer> record=<record_id>"
  return ok
```

Implementations:

- `amazon-meeting-update-assistant` calls `assert_ownership` per resolved target record before any write (including audit fields)
- `amazon-daily-kb-sync` calls `assert_ownership` per record it would touch in the 7-day weekly compile; also scopes action-item sync to `assignee == ME` only
- `okr-evidence-compile` already has this (Step 1.5)

### New-record creation (task layer)

When the source justifies creating a **new** task (not updating an existing one):

- Force `执行人 = [{"id": ME}]` — never create tasks for other people
- If the source text indicates the action item belongs to someone else, **skip** the create and let that owner sync from their own machine

### Bypass

- `force_ownership_bypass=true` skill param → caller may skip the check (CEO audit / cross-owner cleanup only)
- Default = strict, never bypass without explicit param

## Scripts

- `scripts/build_update_preview.py`
  - Converts a resolved source packet plus candidate records into a normalized preview JSON
- `scripts/detect_state_inconsistencies.py`
  - Checks KR/project/task snapshots and emits inconsistency items for weekly compilation

