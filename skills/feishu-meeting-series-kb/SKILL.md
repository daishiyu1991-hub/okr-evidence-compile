---
name: feishu-meeting-series-kb
description: Build and maintain cross-session knowledge bases for recurring Feishu/Lark meeting series. Use when the user asks to use feishu/lark-cli, Feishu Minutes, meeting notes, training meetings, weekly meetings, review meetings, topic-selection meetings, or recurring company meetings to collect past sessions, analyze decisions/topics/follow-ups/patterns, onboard new people, or create/update a durable Feishu doc/wiki/Markdown knowledge base across many meeting instances.
---

# Feishu Meeting Series KB

## Purpose

Turn a repeated meeting series into a durable knowledge base. The unit is the series, not one meeting: collect multiple sessions, preserve decisions and reasons, track recurring topics and dropped follow-ups, and produce a knowledge base that can be updated later.

Prefer `lark-cli` / `feishu` as the data path. When the task needs exact Feishu command patterns, read [feishu-cli-workflow.md](references/feishu-cli-workflow.md). When creating the final artifact, read [kb-output-contract.md](references/kb-output-contract.md).

## Default Behavior

- If the user gives a series name but no date range, search the last 90 days first.
- If the user gives no target output, create a local Markdown draft first; ask before publishing into a team-visible Feishu doc/wiki.
- Use `--as user` for personal-visible docs, minutes, and drive search. Use `--as bot` only for app-owned resources or when the user explicitly asks for bot identity.
- Treat write, delete, member/permission, broad message-history, and team-visible publication actions as approval gates.
- Do not store raw transcripts, private chat history, secrets, access tokens, or broad personal data in durable knowledge. Summarize into compact, useful operating knowledge.
- For the `🚀亚马逊攻坚小分队` daily meeting flow, the authoritative daily conclusion source is the group chat. Copy the daily conclusion artifacts into the knowledge base completely before synthesis: preserve conclusion text, source links, files, images, and Excalidraw/whiteboard artifacts. Then add structured compilation below the copied source block. Still redact secrets, tokens, credentials, and passwords; record them only as sensitive-content risks.

## Workflow

1. Define the series boundary.
   - Capture series name, aliases, owner/participants if known, date range, source type (`minutes`, `docs`, `wiki`, `drive`, `calendar/vc`), and output target.
   - For ambiguous repeated meetings, start with read-only discovery and list candidate sessions before synthesis.

2. Verify Feishu access.
   - Run `lark-cli doctor` and `lark-cli auth status`.
   - If user identity is missing or expired, request user authorization before continuing.

3. Discover candidate sessions.
   - Search Feishu Minutes when the source is meeting recordings or "妙记".
   - Search Drive/docs/wiki when the source is written meeting notes or meeting docs.
   - Search calendar/vc first when the user names a calendar meeting and asks for the related minute.
   - Deduplicate by stable token or URL.

4. Fetch source content.
   - Fetch only the fields needed for synthesis: title, date, participants/owner when available, summary, agenda, decisions, action items, transcript snippets needed for evidence, and source URL/token.
   - For daily meeting conclusions posted in `🚀亚马逊攻坚小分队`, treat the posted conclusion bundle as a source artifact, not merely evidence for summary. Mirror it into the target knowledge page as a "原始结论区" with full text and attachments/whiteboards first, then compile it.
   - If a conclusion includes Excalidraw, Feishu whiteboard, image, file, or linked drawing asset, preserve the original artifact link and, when supported by Feishu APIs, copy or upload the artifact into the target wiki/doc rather than replacing it with a text placeholder.
   - For long transcripts, pre-aggregate by session before feeding semantic synthesis. Do not paste huge raw transcripts into the main response.

5. Build the cross-session ledger.
   - One row per meeting session.
   - Track topics, decisions, reasons, action items, unresolved items, later outcomes, repeated patterns, and onboarding lessons.
   - Mark missing data as `not_collected`, `not_available`, or `permission_blocked`; do not invent details.

6. Synthesize the knowledge base.
   - Create sections for meeting inventory, decision map, topic conversion/follow-through, meeting rhythm, decision mechanism, recurring phenomena, onboarding guide, reusable rules, open loops, and maintenance plan.
   - Separate evidence from judgment. Use source links for traceability.

7. Publish or update.
   - For local review, write Markdown into the requested workspace/run folder.
   - For Feishu publication, use the relevant official lark skill docs (`lark-doc`, `lark-wiki`, `lark-drive`) and ask before creating/updating team-visible docs.
   - For recurring maintenance, propose an automation or Hermes-owned recurring path only after the first manual run proves the data path and output shape.

## Analysis Rules

- Optimize for longitudinal memory: what changed across sessions, what was decided, what was forgotten, and what should inform future meetings.
- Preserve the distinction between "discussed", "decided", "assigned", "completed", "dropped", and "still open".
- For topic-selection meetings, explicitly track topic lifecycle: proposed -> accepted/rejected/deferred -> converted into output/project -> outcome if known.
- For training meetings, extract reusable onboarding modules, recurring questions, tacit standards, examples, and "what good looks like".
- For review/retro meetings, extract failure patterns, corrective actions, owner commitments, and whether the same issue recurs.
- Prefer concise evidence snippets over long transcript quotes.

## Expected Outputs

For a full run, produce:

- `meeting-series-ledger`: structured table or JSON with one row per session.
- `knowledge-base-draft`: Feishu-ready Markdown/XML or local Markdown.
- `source-index`: source URL/token list with fetch status.
- `open-loops`: unresolved promises, deferred ideas, and follow-up checks.
- `maintenance-plan`: how to update this series next time.

## Feishu Skill Handoff

When operating live Feishu resources, use installed official Lark skills if available:

- `lark-minutes` for `minutes +search` and minute metadata.
- `lark-vc` for locating meetings and fetching notes from `minute_token`.
- `lark-doc` for creating, fetching, or updating docs.
- `lark-drive` for resource discovery.
- `lark-wiki` for placing the final doc in a knowledge space.

Read the relevant official skill file before running write operations.
