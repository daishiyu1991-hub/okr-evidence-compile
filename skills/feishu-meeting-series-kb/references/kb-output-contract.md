# Knowledge Base Output Contract

Use this reference when producing the meeting-series knowledge base.

## Source Index

Track every candidate source:

| field | meaning |
|---|---|
| `source_id` | stable token or generated id |
| `title` | source title |
| `date` | meeting/session date |
| `source_type` | minutes, doc, wiki, drive, calendar, vc |
| `url_or_token` | traceable source ref |
| `fetch_status` | fetched, skipped, permission_blocked, not_available |
| `notes` | short caveat |

## Meeting-Series Ledger

One row per meeting/session:

| field | meaning |
|---|---|
| `session_date` | meeting date |
| `session_title` | source title |
| `participants_or_owner` | people if available |
| `agenda_or_context` | why the meeting happened |
| `topics_discussed` | normalized topic list |
| `decisions` | concrete decisions only |
| `decision_reasons` | why the decision was made |
| `action_items` | owner + action + deadline if available |
| `open_loops` | deferred or unresolved items |
| `outcome_if_known` | later conversion/completion status |
| `evidence_ref` | source id and brief evidence pointer |

## Raw Daily Conclusion Mirror

For `🚀亚马逊攻坚小分队` daily meeting conclusions, include a source-preserving section before synthesis:

| field | meaning |
|---|---|
| `date` | daily conclusion date |
| `source_chat` | group name and chat id if available |
| `source_message_ref` | message id / timestamp / source link if available |
| `conclusion_text` | complete daily conclusion text copied from the group |
| `attached_artifacts` | files, images, links, Excalidraw, Feishu whiteboards, or drawing assets |
| `artifact_copy_status` | copied, linked, permission_blocked, unsupported, or redacted_sensitive |
| `redaction_notes` | only for secrets, tokens, credentials, passwords, or privacy-sensitive material |

Rule: daily conclusions should be copied completely into the KB before analysis. The structured summary is additive and must not replace the original conclusion block. Secrets, tokens, credentials, and passwords are never copied verbatim.

## Knowledge Base Sections

Use these sections unless the user asks for another format:

1. Overview
2. Meeting Inventory
3. Topic / Decision Conversion Analysis
4. Meeting Rhythm and Process
5. Decision Mechanism
6. Recurring Phenomena
7. Onboarding Guide for New Members
8. Reusable Experience and Rules
9. Open Loops and Follow-Up Queue
10. Maintenance Plan
11. Source Index

For daily conclusion pages, add:

- 原始结论区（完整复制）
- Excalidraw / 画板 / 附件区
- 结构化编译区
- 待追踪事项

## Writing Style

- Write in Chinese by default when the user's workflow is Chinese.
- Make the doc useful for a teammate who did not attend the meetings.
- Keep source references close to claims.
- Use `not_collected`, `not_available`, or `permission_blocked` instead of guessing.
- Do not include raw full transcripts unless explicitly requested and approved.
- For `🚀亚马逊攻坚小分队`, raw daily conclusions and their Excalidraw/whiteboard artifacts are explicitly requested source artifacts and should be preserved completely, subject only to sensitive-secret redaction.

## Publication Rules

Before creating or updating a team-visible Feishu doc/wiki, summarize:

- target space/folder/doc
- write action: create, append, overwrite, or update
- source count
- privacy-sensitive content excluded

Then ask for approval unless the user already explicitly authorized that exact write action.
