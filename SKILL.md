---
name: okr-evidence-compile
version: 0.1.0
description: Evidence-based OKR compiler for 86lux 团队管理 Base. Each owner runs this skill on their own machine to compile their own KR records. Reads a 👤个人OKR record's linked projects/tasks/meetings/weeklies, classifies each evidence by path alignment to the KR description (directly_contributes / tangentially_related / off_path), computes path_alignment_score, detects path drift, then writes a compiled summary into the OKR record's 5 AI maintenance fields AND appends a structured entry to the KR's dedicated Feishu wiki doc (1 doc per KR, append history). Doc includes both a 👤 human-readable conclusion section and machine-readable structured data. Strict ownership safety — aborts if current lark-cli user != KR 执行人 (unless force_ownership_bypass=true). Never invents progress numbers — if evidence missing or path drifts, reports honestly and flags 待人工确认.
metadata:
  requires:
    bins: ["lark-cli", "jq", "python3", "date"]
  cliHelp: "lark-cli base --help"
  agents: ["codex", "claude-code"]
  tenant: "86lux"
  base_token: "GxaobEQtqaOwFZsB5wTcC33Rnl7"
  wiki_space_id: "7639331686206999770"
  wiki_parent_node: "Q7aGwCUvciF0lMknHo7cUEMOnAh"
---

# OKR Evidence-Based Compile

## Purpose

Each owner runs this skill on their own machine to compile their own KR records evidence-based. The compiler reads only the linked evidence (projects / tasks / team-KR / meetings / weekly reports in the 86lux 团队管理 Base), classifies each by path alignment to the KR description, writes back the 5 AI maintenance fields 戴时雨 pre-built on the table, AND appends a structured entry to the KR's dedicated Feishu wiki doc (in wiki space 7639331686206999770, parent node `Q7aGwCUvciF0lMknHo7cUEMOnAh` "OKR AI 编译记录"). Never invents progress numbers; if evidence is insufficient or drifts off the KR description, reports honestly and flags 「待人工确认」=true.

Reference plan: `/Users/daishiyu/.claude/plans/obsidian-open-vault-obsidian-20vault-fil-quizzical-waffle.md` (v4.3)

## Default Behavior

- **Identity**: `--as user` (each owner authenticates lark-cli with own Feishu account; Feishu audit log naturally captures who ran)
- **Ownership check is mandatory** (Step 1.5): current lark-cli user_id must equal record `执行人` open_id, otherwise abort. CEO audit case can pass `force_ownership_bypass=true`.
- **Never write 「状态」or「进度」fields** — those require owner cross-check
- Only write the 5 AI maintenance fields: `AI编译摘要 / 最近更新原因 / 最近更新时间 / 最近更新来源 / 待人工确认`
- **Long compile content goes to a Feishu wiki doc**, NOT to the AI编译摘要 field. AI编译摘要 = abstract (≤80 字), 最近更新来源 = doc URL.
- Writeback is **approval-gated** by default: surface the Step 4 JSON output to caller, wait for explicit OK before Step 5/4.5. Skip the gate only when called with `auto_approve=true`.
- `path_drift=true` OR `confidence=low` → 待人工确认 = true
- Read `references/anti-hallucination.md` before invocation — strict evidence integrity + ownership rules
- Read `references/okr-compile-flow.md` for the exact lark-cli commands + Claude prompt + writeback shell snippet
- Read `references/doc-template.md` for the wiki doc markdown structure + abstract extraction rule

## Workflow

1. **Locate** the target record: search 👤个人 OKR (`tblxM7ZfxJt2P4Fl`) by KR text or record_id → get `record_id` + linked record_ids
2. **Ownership check** (Step 1.5): assert current lark-cli user open_id == record `执行人` open_id; otherwise abort unless `force_ownership_bypass=true`. **All subsequent write actions depend on this check passing.**
3. **Pull evidence**: get linked 🧮团队项目清单 + 🚦每周任务 + 👪团队OKR records
4. **Scan context**: search 📖会议纪要 + 📅周报 within `evidence_lookback_weeks` window for KR keyword
5. **Compile**: feed evidence to Claude API with the 3-task prompt (classify / score / summarize). Receive JSON.
6. **Approve gate**: present Step 5 JSON to caller; wait OK. Skip if `auto_approve=true`.
7. **Doc write** (Step 4.5 logical step): determine branch by reading record's `最近更新来源` field:
   - Empty/null → create new doc with 1 entry
   - Contains plan path (v3.3 historical) → create new doc with entry #0 (v3.3 retro) + entry #1 (current)
   - Contains doc URL → fetch doc, prepend new entry, update doc
   See `references/doc-template.md` for exact branch logic and the markdown template.
8. **Base writeback** via `lark-cli base +record-batch-update`: 5 AI fields only. `AI编译摘要` = abstract (≤80 字); `最近更新来源` = doc URL (replaces v3.3 plan path).
9. **Verify** via `lark-cli base +record-get`, confirm 5 fields written + 「状态」/「进度」untouched.

## Params

| param | required | default | semantics |
|---|---|---|---|
| `record_id` | yes | — | 👤个人 OKR record_id to compile |
| `auto_approve` | no | `false` | If true, skip approval gate (only for Hermes cron) |
| `evidence_lookback_weeks` | no | `4` | How far back to scan 会议纪要 / 周报 for KR keyword |
| `force_ownership_bypass` | no | `false` | If true, skip Step 1.5 ownership check (only for CEO audit / Hermes cron) |

## Failure Handling

- `token_exists` fail → ask user to run/approve `lark-cli auth login`. Abort.
- **Ownership mismatch + `force_ownership_bypass=false`**: print clear message + abort. Do NOT write anything.
- Permission errors on a sub-table → record `permission_blocked` for that source, continue with accessible sources. Reflect in 缺失警示.
- Empty linked records → valid result B. Report 「evidence 缺失：...」 honestly. Do not invent.
- Claude API timeout → retry once. If still fails → abort writeback, surface error.
- Pre-existing 待人工确认=true on the record → still proceed. The new write overwrites with current run's reasoning.
- Doc create/update error → do NOT proceed to base writeback (avoids dangling abstract pointing to invalid doc URL). Surface lark-cli error, ask user.
- Base writeback error → do not retry blindly. Surface lark-cli error, ask user. Note: doc may have been written successfully even if base failed — caller should reconcile.

## Don't

- Don't write 「状态」or「进度」fields
- Don't write to other records, even if linked
- Don't fabricate evidence not present in raw lark-cli outputs (see `references/anti-hallucination.md`)
- Don't pick a 进度推断 number when path_drift=true — output null
- Don't bypass the approval gate unless `auto_approve=true` is explicitly set
- **Don't bypass Step 1.5 ownership check** unless `force_ownership_bypass=true` is explicitly set
- Don't try to write base abstract longer than 80 字 — strict limit
- Don't write long compile content into the base AI编译摘要 field — it goes to the wiki doc, base only gets abstract
