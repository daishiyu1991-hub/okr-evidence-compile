# Interaction Contract

## Default Mode

Use mixed mode by default:
- accept raw meeting/update content
- optionally accept a manually specified target

## Response Contract

When the input is processable, respond in this order:

1. Short summary of what the input appears to update
2. Target candidates
3. `拟更新预览`
4. Explicit confirmation request

## If Multiple Candidates Exist

- list candidates with layer + record title + owner
- do not write
- ask the user to choose one

## If Evidence Is Weak

- say the skill can only produce preview or audit-only output
- mark `待人工确认 = true`
- do not overwrite formal status/progress

