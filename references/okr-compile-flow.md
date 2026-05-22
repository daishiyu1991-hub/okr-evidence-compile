# OKR Compile Flow — lark-cli Commands + Claude Prompt + Writeback

## 常量

```bash
BASE=GxaobEQtqaOwFZsB5wTcC33Rnl7
WIKI_SPACE=7639331686206999770
WIKI_PARENT_NODE=Q7aGwCUvciF0lMknHo7cUEMOnAh   # OKR AI 编译记录 root

PERSONAL_OKR=tblxM7ZfxJt2P4Fl   # 👤个人 OKR
TEAM_OKR=tblIql9R1iIgXZZi        # 👪团队 OKR
PROJECT=tblOHGg4IA2pY7uh         # 🧮团队项目清单
ACTIVITY=tblf54mtW07iPCRL        # 📊项目活动管理
TASK=tblrduPxvdifLm62            # 🚦每周任务
MEETING=tblur61KITUciwt0         # 📖会议纪要
WEEKLY=tblqaeNSZ73cmGHi          # 📅周报
```

## Step 1：定位 record（只读）

如果调用者已知 record_id，直接 +record-get。否则用关键词搜：

```bash
# 关键字搜（注意 lark-cli base +record-search 用 --json 而非 --data，schema 是 keyword/search_fields）
lark-cli base +record-search \
  --base-token $BASE --table-id $PERSONAL_OKR --as user \
  --json '{"keyword":"<关键词>","search_fields":["KR-关键结果"],"limit":5}' \
  --format json

# 已知 record_id 直接读
lark-cli base +record-get \
  --base-token $BASE --table-id $PERSONAL_OKR --as user \
  --record-id <record_id> --format json
```

提取关键字段：
- `record_id` (本 KR)
- `KR-关键结果`、`O-目标`、`所属周期`、`开始日期`、`截止日期`、`进度`
- `执行人` → list of `{id: open_id, name}` ← **Step 1.5 用**
- `关联团队项目` (link) → list of project record_ids
- `每周任务` (link) → list of task record_ids
- `关联团队KR` (link) → list of team KR record_ids
- `AI编译摘要 / 最近更新原因 / 最近更新时间 / 最近更新来源 / 待人工确认` ← 当前 5 个 AI 字段值（用于判断 doc 分支 + v3.3 retro 数据源）

## Step 1.5：Ownership check（强制，除非 force_ownership_bypass=true）

```bash
# 拿当前 lark-cli 认证用户的 open_id
ME=$(lark-cli auth status --format json 2>&1 | jq -r '
  .data.user_open_id //
  (.data.users[0].userOpenId) //
  (.data.apps[].users[0].userOpenId) //
  empty
')

if [ -z "$ME" ]; then
  echo "❌ 无法拿到当前 lark-cli user open_id, 请先 lark-cli auth login"
  exit 1
fi

# 从 Step 1 record 字段抽 执行人 open_id（如多个执行人，取首位）
OWNER=$(echo "$STEP1_RECORD_JSON" | jq -r '
  .data.data[0].fields[].执行人[0].id //
  empty
')

if [ "${FORCE_OWNERSHIP_BYPASS:-false}" != "true" ] && [ "$ME" != "$OWNER" ]; then
  echo "❌ ownership mismatch."
  echo "   current lark-cli user: $ME"
  echo "   record 执行人 open_id: $OWNER"
  echo "   如果你确认要替他/她跑（如 CEO 审计），用 codex exec --params 加 'force_ownership_bypass=true'"
  exit 1
fi
```

**所有后续写操作（Step 4.5 doc / Step 5 base writeback）都依赖本 step 通过。** 一旦 abort，禁止任何 write。

## Step 2：拉 linked evidence（只读）

For each linked project record_id：

```bash
lark-cli base +record-get \
  --base-token $BASE --table-id $PROJECT --record-id <pid> --as user \
  --field-id 项目名称 --field-id 项目目标 --field-id 进度 --field-id 本周更新 --field-id 阻塞 --field-id 下一步 --field-id 下次检查点 --field-id 最近更新时间 --field-id AI编译摘要 \
  --format json
```

For each linked task record_id：

```bash
lark-cli base +record-get \
  --base-token $BASE --table-id $TASK --record-id <tid> --as user \
  --field-id 任务 --field-id 任务进度 --field-id 本周完成结果 --field-id 输出结果 --field-id 所属周 --field-id 执行人 --field-id AI编译摘要 --field-id 最近更新时间 \
  --format json
```

For each linked team KR record_id：

```bash
lark-cli base +record-get \
  --base-token $BASE --table-id $TEAM_OKR --record-id <kid> --as user \
  --field-id KR-关键结果 --field-id O-目标 --field-id 进度 --field-id 优先级 --field-id 周期开始日期 --field-id 周期结束日期 \
  --format json
```

## Step 3：扫近 N 周会议纪要 / 周报（只读）

```bash
# 会议纪要 ── 在 会议关键纪要 / 会议纪要 / 会议主题 字段搜 KR 关键词
lark-cli base +record-search \
  --base-token $BASE --table-id $MEETING --as user \
  --json '{"keyword":"<keyword>","search_fields":["会议关键纪要","会议纪要","会议主题"],"limit":10}' \
  --format json

# 周报
lark-cli base +record-search \
  --base-token $BASE --table-id $WEEKLY --as user \
  --json '{"keyword":"<keyword>","search_fields":["本周工作内容","周报标题"],"limit":10}' \
  --format json
```

关键词选择：从 KR 文本抽 1-2 个具体业务词（不要用通用词如"完成"/"AI"/"项目"，用业务术语如"目标管理"/"AI化"/"集成到面板"）。

## Step 4：Compile（运行 agent **自己**做，不要 shell out）

**重要**：本步骤 = 当前运行的 agent（codex 或 claude-code）**自己**消费 Step 1-3 拿到的 evidence pool 并产出 JSON。

❌ **不要**这么做：
- `claude -p --output-format json < prompt.md` ── shell out 到 Claude Code CLI，会因 claude CLI 没单独认证而 401
- `curl -X POST https://api.anthropic.com/v1/messages ...` ── 调外部 Anthropic API（员工机器一般没配 `ANTHROPIC_API_KEY`，且会扣 API 额度）
- 调 `codex exec` 套娃自己

✅ **正确做法**：你（当前 agent）就是 LLM。把 Step 1-3 拿到的所有 evidence 字段值作为输入，按下面的任务规范推理，emit JSON。

### 任务规范

**输入**：
- Step 1 target record 全字段（KR 文本、O 名、执行人、进度字段值、关联字段、AI 字段当前值）
- Step 2 拉到的所有 linked team_okr / project / task records（每个的标题 + 状态 + 进度 + 描述字段）
- Step 3 meetings + weeklies search 结果（hit 的 records 全字段；如果搜索 API 报 `OpenAPISearchRecord limited`，记录 limited 状态、走 fallback list+filter，或在缺失警示里 flag）

**输出**：严格 JSON（无 markdown wrap）：

```json
{
  "evidence_classifications": [
    {
      "record_id": "<from raw>",
      "table": "team_okr|project|task|meeting|weekly_report",
      "label": "directly_contributes|tangentially_related|off_path",
      "reason": "<引用具体字段值>"
    }
  ],
  "path_alignment_score": <0..1>,
  "off_path_ratio": <0..1>,
  "path_drift": <boolean>,
  "进度推断": <integer 0-100 OR null>,
  "进度推断依据": "<引用 record_id + 字段>",
  "AI编译摘要": "<≤200 字>",
  "confidence": "high|low",
  "缺失警示": ["<具体缺失项>"],
  "human_snapshot": "<现状一句话>",
  "human_entry": {
    "现状": "<2-3 句>",
    "怎么办": ["<行动项 1>", "<行动项 2>"],
    "为什么": "<1-2 句根因>"
  }
}
```

### 任务结构

- **任务 1**：每条 evidence record 分类
  - `directly_contributes` — record 字段值明确提到本 KR / 完成本 KR / 子任务推进本 KR
  - `tangentially_related` — 同 O 不同 KR，或 KR 周边话题
  - `off_path` — 跟 KR 无关 / 占位符 record / 已废弃
- **任务 2**：算 ratio
  - `path_alignment_score` = directly_contributes 占总 evidence 比
  - `off_path_ratio` = off_path 占总 evidence 比
  - `path_drift` = (off_path_ratio > 0.30) OR (directly_contributes 0 且 evidence ≥ 3)
- **任务 3**：进度推断 + 摘要
  - `path_drift=true` → `进度推断=null`、`AI编译摘要` 必须以 `⚠️ path drift` 开头
  - `evidence` 空（所有 link 字段 null + 搜索 0 hit） → `进度推断=null`、`confidence=low`、`AI编译摘要` 报告"evidence 缺失"
  - `evidence` 充足 + path 对齐 → `进度推断` = integer 0-100，依据必须引用具体 record_id 字段值
- **任务 4（human-readable）**：填 `human_snapshot` + `human_entry`，给真人读，用大白话写"现状/怎么办/为什么"

### 严格遵守 anti-hallucination

详见 `references/anti-hallucination.md` 6 条规则。要点：

1. `evidence_classifications[].record_id` 必须出现在 Step 1-3 raw 输出里，禁止编
2. 不允许凭空生成进度数字（要么有 evidence 支持，要么 null）
3. `缺失警示` 必须列出实际缺失项（关联字段空 / 搜索 0 hit / 间接关联全占位 / API limited），不要省略
4. `AI编译摘要` 长度 ≤ 200 字（base 字段会再截到 80 字，见 Step 5）
5. 不允许编 `reason` 内容——只能引用 raw record 的字段值原文

## Step 4.5：Doc 写入（按分支判定）

读 Step 1 record 的 `最近更新来源` 字段值，决定分支：

### 分支 A：doc 不存在（字段 空 或 null）

```bash
# 生成 markdown (按 references/doc-template.md 模板渲染单 entry)
DOC_TITLE="OKR Compile · <执行人 name> · <O 名> · <KR 文本前 30 字>"

# 用临时文件传 markdown，避免 shell 转义灾难
echo "<markdown content>" > /tmp/okr-doc-md-$$.md

lark-cli docs +create --as user \
  --wiki-space $WIKI_SPACE \
  --wiki-node $WIKI_PARENT_NODE \
  --title "$DOC_TITLE" \
  --markdown @/tmp/okr-doc-md-$$.md \
  --format json
```

返回的 doc token / URL 用于 Step 5 写回 base。

### 分支 B：doc 已存在 + 是 v3.3 历史路径（字段值是 `skill://...@/Users/...plans/...md`）

跟分支 A 一样新建 doc，但 markdown 含 **2 个 entry**：

- entry #1：本次 v4.0 fresh compile（按 Step 4 输出 JSON 渲染）
- entry #0：v3.3 retro（按 references/doc-template.md "v3.3 retro 数据来源" 节反推）

```bash
# 同分支 A 的 docs +create，markdown 包含 2 个 entry
```

### 分支 C：doc 已存在 + 字段值是 doc URL（`https://wg9k4pnk2o.feishu.cn/wiki/<token>`）

```bash
# 解析 doc token
DOC_URL="<字段值>"
DOC_TOKEN=$(echo "$DOC_URL" | sed -E 's|.*/wiki/([A-Za-z0-9]+).*|\1|')

# Fetch 现有 markdown
lark-cli docs +fetch --as user --doc "$DOC_TOKEN" --api-version v1 --format json > /tmp/okr-doc-current-$$.json

# Parse 出当前最大 entry 号 N → 新 entry 号 = N+1
# 替换 "当前状态 snapshot" 整段 + 在 "## Compile history" 之后 prepend 新 entry
# 详细 markdown 操作见 references/doc-template.md "append 机制" 节

NEW_MD=$(...)  # 在临时文件生成新 markdown

lark-cli docs +update --as user --doc "$DOC_TOKEN" --markdown @/tmp/okr-doc-new-$$.md --format json
```

注：`lark-cli docs +update` 的具体 flag 可能不同，调用前 `lark-cli docs +update --help` 确认。

## Step 5：写回 KR record 5 个 AI 字段（写 — Step 1.5 ownership 必通过）

```bash
RECORD_ID=<step1 取>
NOW_MS=$(date +%s000)

# 拼 abstract（≤80 字，按 doc-template.md "abstract 抽取规则"）
ABSTRACT="<step4 摘要缩到 ≤80 字>"

# 拼 「最近更新原因」
REASON="evidence-based compile. confidence=<step4 confidence>. path_drift=<step4 path_drift>. off_path_ratio=<step4 off_path_ratio>"

# 拿 step 4.5 拿到的 doc URL
DOC_URL="<step 4.5 输出 / fetched URL>"

# 待人工确认 逻辑
if [ "<step4 path_drift>" = "true" ] || [ "<step4 confidence>" = "low" ]; then
  NEED_CONFIRM=true
else
  NEED_CONFIRM=false
fi

# 写 JSON 到临时文件防 shell 转义
cat > /tmp/okr-writeback-$$.json <<EOF
{
  "record_id_list": ["$RECORD_ID"],
  "patch": {
    "AI编译摘要": "$ABSTRACT",
    "最近更新原因": "$REASON",
    "最近更新时间": $NOW_MS,
    "最近更新来源": "$DOC_URL",
    "待人工确认": $NEED_CONFIRM
  }
}
EOF

lark-cli base +record-batch-update \
  --base-token $BASE --table-id $PERSONAL_OKR --as user \
  --json "$(cat /tmp/okr-writeback-$$.json)" \
  --dry-run   # 先 dry-run 一次

# 看 dry-run OK 后真跑：
lark-cli base +record-batch-update \
  --base-token $BASE --table-id $PERSONAL_OKR --as user \
  --json "$(cat /tmp/okr-writeback-$$.json)"
```

**注意**：
- 不写 `状态` 字段（owner 复核）
- 不写 `进度` 字段（owner 复核）
- 不写 record 中其他任何字段
- `AI编译摘要` 必须 ≤80 字，超出截断 + 末尾 `…`

## Step 6：读回验证（只读）

```bash
lark-cli base +record-get \
  --base-token $BASE --table-id $PERSONAL_OKR --record-id $RECORD_ID --as user --format json
```

期望：
- 5 个 AI 字段值已写入
- `AI编译摘要` ≤ 80 字
- `最近更新来源` 是 wiki doc URL（不是 plan path 不是空）
- 「状态」「进度」字段未变
- 如 path_drift=true 或 confidence=low → 待人工确认=true
