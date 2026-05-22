## 拟更新预览 (v2 — ownership-scoped)

- 来源：{{source_title}}
- 链接：{{source_url}}
- 识别层级：{{layer}}
- 识别记录：{{record_title}}
- 当前 owner：{{record_owner_name}} ({{record_owner_open_id}})
- 我的身份：{{me_name}} ({{me_open_id}})
- **ownership**：{{ownership_status}}  ← `✅ own (will write)` / `❌ not own (write blocked)` / `🆕 will create with me as owner`
- 置信度：{{confidence}}
- 建议人工复核：{{needs_review}}

### 字段变更

| 字段 | 当前值 | 拟写入值 | 原因 |
|---|---|---|---|
{{field_rows}}

### 留痕

- 最近更新原因：{{audit_reason}}
- 最近更新来源：{{audit_source}}
- AI编译摘要：{{audit_summary}}

### Cross-owner action items (not synced)

> 来源内提及但 owner 不是我的行动项：列出来供透明 / 协调，但**不**写入 base。让对方在自己的 codex 跑 skill 同步。

| 行动项 | 来源 | rightful_owner |
|---|---|---|
{{cross_owner_rows}}

---

**请确认是否写入。** 如果 ownership=`❌ not own`，写入会被拒绝（即便你确认）。

