# Writeback Checklist

Before writing:
- source is traceable
- target record is uniquely identified
- field is on the allowed write list
- before/after diff is explicit
- confidence is not low for formal writes
- named owners/assignees have been resolved to Feishu `open_id`
- user fields are written as `[{ "id": "ou_xxx" }]`, not as plain text names
- linked KR/project fields have been resolved to Base `record_id`
- link fields are written as `[{ "id": "recxxx" }]`, not as plain text titles

After writing:
- write `最近更新原因`
- write `最近更新来源`
- write `最近更新时间`
- write `AI编译摘要`
- set `待人工确认` according to confidence/conflict

Never do:
- overwrite KR/project formal state from vague discussion alone
- write two conflicting target records from the same source without user choice
