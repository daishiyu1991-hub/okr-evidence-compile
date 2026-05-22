# Routing Write Rules — 每 routing 类型的具体 base 写入

> 详细 payload 规范, 含 base batch-create / batch-update 命令 + 字段映射. 配合 SKILL.md Step 7 用.

---

## 共享前置

```bash
BASE=GxaobEQtqaOwFZsB5wTcC33Rnl7
ME=$(lark-cli auth status --format json | jq -r '.userOpenId')
TODAY_MS=$(python3 -c "import time; print(int(time.time() * 1000))")
THIS_WEEK_FRIDAY_MS=$(python3 -c "
import datetime, time
today = datetime.datetime.now()
days_until_friday = (4 - today.weekday()) % 7  # Friday = 4
friday = today + datetime.timedelta(days=days_until_friday)
friday_end = datetime.datetime(friday.year, friday.month, friday.day, 23, 59, 59)
print(int(friday_end.timestamp() * 1000))
")
```

---

## 7.1 routing = `task`

### Base 表

`🚦每周任务` (`tblrduPxvdifLm62`)

### Payload schema

```json
{
  "fields": [
    "任务",
    "执行人",
    "任务进度",
    "优先级",
    "任务开始日期",
    "任务结束日期",
    "关联KR",
    "所属项目",
    "最近更新原因",
    "最近更新来源",
    "最近更新时间",
    "AI编译摘要",
    "待人工确认"
  ],
  "rows": [
    [
      "<事项文本>",
      [{"id": "<ME>"}],
      "0-未开始",
      "<P0/P1/P2/P3>",
      <today_ms>,
      <≤ this_week_friday_ms>,
      [{"id": "<KR_rec_id>"}] OR [],
      [{"id": "<project_rec_id>"}] OR [],
      "auto from amazon-daily-sync: 来源 <source>",
      "<source_url>",
      <today_ms>,
      "<≤80 字摘要>",
      true
    ]
  ]
}
```

### 关键规则

- **执行人 强制 = ME**，不能替别人建 task
- **任务进度 必须** `"0-未开始"` (新建默认)
- **优先级** 从 evidence 抽 (含 P0-P3 字样) 或默认 P1
- **关联KR / 所属项目** 从 candidate.mentioned_records 解析, 缺则空数组 `[]`
- **待人工确认 = true** (owner 在 base UI 二次确认)

### 命令

```bash
cd /tmp && \
lark-cli base +record-batch-create \
  --base-token $BASE \
  --table-id tblrduPxvdifLm62 \
  --as user \
  --json @task-payload.json
```

---

## 7.2 routing = `project_activity`

### 前置检查

mentioned_records 必须含某 `🧮团队项目清单` record_id (作为父项目). 如无 → 转 `team_project_draft`.

### Base 表

`📊项目活动管理` (`tblf54mtW07iPCRL`)

### Payload schema

```json
{
  "fields": [
    "项目活动",
    "所属项目",
    "负责人",
    "执行人",
    "项目阶段",
    "任务进度",
    "优先级",
    "任务开始日期",
    "任务计划结束日期",
    "AI编译摘要",
    "待人工确认"
  ],
  "rows": [
    [
      "<事项文本>",
      [{"id": "<project_rec_id>"}],
      [{"id": "<ME>"}],
      [{"id": "<ME>"}],
      "1-确定目标",
      "0-未开始",
      "P1",
      <today_ms>,
      <today + 4_weeks_ms>,
      "auto from amazon-daily-sync: 来源 <source>; 阶段默认 1, owner 后续手动改",
      true
    ]
  ]
}
```

### 关键规则

- **所属项目 必填** (link to 父项目 record_id)
- **项目阶段** 默认 `"1-确定目标"`, owner 后续手动改
- **执行人 + 负责人** 都 = ME (项目活动有 2 个 owner 字段)
- **任务计划结束日期** 默认 4 周后 (跨周特征)
- **优先级 select 字段值** 注意活动表是 `PO/P1/P2/P3` (注意 P0 写成 PO 是 base 笔误, 原样匹配)

---

## 7.3 routing = `team_project_draft`

### ⚠️ 不直接写 base record!

cron 自动模式下, 不直接 `record-batch-create` 到 `🧮团队项目清单`. 改为:

### 步骤 1: 写 wiki 草稿

位置: 「01 目标与项目管理 / OKR 巡检与草稿区」节点下 (如节点不存在则用 `lark-cli wiki nodes create` 建).

doc title: `团队项目草稿 · <事项前 30 字> · YYYY-MM-DD`

内容 markdown:

```markdown
# 团队项目草稿: <事项>

> 由 amazon-daily-sync 自动起草 (<YYYY-MM-DD HH:MM>). 等 owner 到 base 「🧮团队项目清单」手动建 record.

## 来源 evidence

- <source 1 ref / link>
- <source 2>

## 拟项目方案

### 项目名: <从事项+context 起草>

### 项目目标

<2-3 句描述, 从 evidence 抽: 想达成什么 / 为什么做 / 影响范围>

### 候选关联 KR

- <KR record_id> "<KR text>" (如 mentioned_records 含)
- 或 候选: 看着像 KR-X "..." (低 confidence, 让 owner 确认)

### 候选成员

- 戴时雨 (默认 ME)
- 其他 mentioned in evidence

### 项目计划结束日期 (拟)

- <today + 3 months> 或基于 evidence 推断

### 拟拆解项目活动

1. 阶段 1-确定目标: <活动名>
2. 阶段 2-确认需求: <活动名>
3. 阶段 3-方案设计与规划: <活动名>
4. 阶段 4-实施并上线: <活动名>
5. 阶段 5-汇报总结: <活动名>

(可选, 让 owner 决定要不要拆)
```

### 步骤 2: 写 wiki

`lark-cli docs +create --as user --wiki-node <草稿区 node_token> --title "<doc_title>" --markdown @<草稿_file>`

记录新 doc 的 URL.

### 步骤 3: DM owner

```bash
lark-cli im +send --as user \
  --receive-id <ME> \
  --receive-id-type open_id \
  --msg-type text \
  --content '{"text": "📋 今天 evidence 出现项目级 candidate: <事项简称>. 已起草 wiki 草稿: <wiki_url>. 请到 🧮团队项目清单 base 手动建 record (含项目名/目标/关联KR/负责人=你 等字段). 草稿仅供参考, 你可调整后再建. base 入口: https://wg9k4pnk2o.feishu.cn/base/...?table=tblOHGg4IA2pY7uh"}'
```

记录 message_id.

---

## 7.4 routing = `audit_only`

### 目标

仅更新 ME-owned record (KR / 项目 / 项目活动 / 任务) 的 audit 字段, **不动正式状态字段**.

### 字段范围 (仅这 5 个)

- `最近更新原因`
- `最近更新时间`
- `最近更新来源`
- `AI编译摘要`
- `待人工确认`

### Payload (举例: 刷新 KR audit)

```json
{
  "record_id_list": ["<KR_rec_id>"],
  "patch": {
    "最近更新原因": "群中提 KR 进度变化 (auto from amazon-daily-sync)",
    "最近更新时间": <today_ms>,
    "最近更新来源": "<source link>",
    "AI编译摘要": "<≤80 字摘要 + 含 group msg 引用>",
    "待人工确认": true
  }
}
```

### 命令

```bash
lark-cli base +record-batch-update \
  --base-token $BASE \
  --table-id tblxM7ZfxJt2P4Fl \  # KR 表; 项目表 / 项目活动表换 table_id
  --as user \
  --json @audit-payload.json
```

### 关键规则

- **禁止动 KR.状态 / KR.进度 / KR.输出结果** (formal 字段)
- **禁止动 项目.进度** (正式 helper 字段)
- **可动 项目.本周更新 / 下一步 / 阻塞 / 下次检查点** (这些是 helper, OK)
- 如 evidence 含 high confidence 的 KR formal 字段变化信号, 在 audit 段 surface "建议 owner 下次 manual 跑或 base UI 手动改 KR.状态 = 已完成"

---

## 7.5 routing = `skip`

不写任何 record, 不输出 audit. candidate 仅在 evidence read 阶段被记入 audit log (本次扫的 chat / meeting), 不留 base trace.

---

## 共享 Failure Handling

- batch-create / update 失败 → surface raw stderr, 让用户决定 retry / skip
- ownership check fail on a record → 该 record 跳过, 不 abort 整 run, 记 audit_log
- wiki 节点不存在 → 自动创建后重试
- DM 失败 → 不阻断主流程, 在 [WRITE DONE] 段 flag "DM 未发送, 草稿 wiki 已写"
