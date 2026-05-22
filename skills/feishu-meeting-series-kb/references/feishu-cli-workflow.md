# Feishu CLI Workflow

Use this reference when the task needs live Feishu/Lark data collection.

## Preflight

```bash
lark-cli doctor
lark-cli auth status
```

Use `--as user` for user-visible minutes, docs, wiki, drive, and search:

```bash
lark-cli docs +search --as user --query "<series keyword>" --page-size 20 --format json
```

Prefer `drive +search` over legacy `docs +search` when the installed `lark-drive` skill is available and the target could be a sheet, folder, base, or mixed drive object.

## Minutes Discovery

For "妙记", recurring meetings, training sessions, weekly meetings, or meetings the user attended:

```bash
lark-cli minutes +search --query "<series keyword>" --start YYYY-MM-DD --end YYYY-MM-DD --page-size 20 --format json
lark-cli minutes +search --owner-ids me --start YYYY-MM-DD --end YYYY-MM-DD --page-size 20 --format json
lark-cli minutes +search --participant-ids me --start YYYY-MM-DD --end YYYY-MM-DD --page-size 20 --format json
```

When the user says "我参与的妙记", run owner and participant searches separately, merge by `token`, and dedupe.

If a time range is longer than one month, split it into monthly windows.

## Meeting First, Minute Second

When the user names a specific calendar/video meeting and asks for its minute:

1. Locate the meeting with `calendar` or `vc`.
2. Get the recording/minute token.
3. Fetch minute metadata and notes.

Do not jump straight to broad minute keyword search when the calendar meeting identity is the real anchor.

## Fetching Content

Docs:

```bash
lark-cli docs +fetch --api-version v2 --as user --doc "<doc url or token>" --format json
```

Minutes metadata:

```bash
lark-cli minutes minutes get --params '{"minute_token":"<token>"}' --format json
```

Minute notes/transcript/summaries usually go through the `lark-vc` skill path using `vc +notes --minute-tokens <token>`. Read the installed `lark-vc` skill before using it.

Group daily conclusions:

For `🚀亚马逊攻坚小分队`, daily meeting conclusions are usually posted in the group chat and may include Excalidraw/whiteboard assets. Search the group first, then fetch the source message bundle and attachments before compiling. Preserve the original conclusion text and artifacts in the target knowledge page, then add the synthesis below it.

Use the installed `lark-im` skill for chat search, message retrieval, and attachment/file download. If the artifact is a Feishu whiteboard, use `lark-whiteboard` / `lark-doc` media paths to preserve or link it. If the artifact is an external Excalidraw file/link, keep the original link and, when possible, upload the exported file/image into the target wiki/doc.

Never copy secrets, tokens, credentials, or passwords verbatim from group chat. Replace them with a sensitive-risk note.

## Pagination

Always inspect `has_more` and `page_token`. Do not assume one page is complete.

If total candidates exceed 50, report the count and ask before fetching all raw sessions unless the user explicitly requested a full historical run.

## Failure Handling

- `token_exists` fail: ask the user to run/approve `lark-cli auth login`.
- Permission errors: record `permission_blocked` with the exact resource and continue with accessible sources.
- Empty search: broaden aliases, owners/participants, or date windows before concluding no records exist.
- Mixed duplicates: dedupe by token first, then URL, then normalized title + date.
