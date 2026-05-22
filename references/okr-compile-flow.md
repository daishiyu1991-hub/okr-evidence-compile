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

## Step 4：Claude API compile（外部调用）

Prompt 详见 v3.3 plan 文件（见 plan 文件 Step 4 完整 prompt 体）。任务结构：

- 任务 1：path alignment 分类（directly_contributes / tangentially_related / off_path）
- 任务 2：path_alignment_score + off_path_ratio + path_drift（off_path > 0.30）
- 任务 3：进度推断 + 摘要（path_drift=true → 进度 null + 摘要前置 ⚠️ 警示）

输出严格 JSON。

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
