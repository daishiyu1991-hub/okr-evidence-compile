---
name: amazon-daily-sync
version: 0.4.0
description: Per-owner daily Feishu evidence → Base sync. Each teammate runs this on their own codex (cron at evening) to scan today's group-chat + meetings + minutes, extract candidate items, route each via turn-based REVIEW QUEUE into 5 destinations (task / project-activity / team-project draft / audit-only / skip), then write to Base under strict ownership scope. Merges previous `amazon-daily-kb-sync` (daily auto task creation) + `amazon-meeting-update-assistant` (KR/project formal writes) into one skill. Group-chat coverage filtered by 3-layer allowlist + auto-discover + per-message ME-relevance.
metadata:
  requires:
    bins: ["lark-cli", "jq", "python3", "date"]
  cliHelp: "lark-cli base --help; lark-cli im --help"
  agents: ["codex", "claude-code"]
  tenant: "86lux"
  base_token: "GxaobEQtqaOwFZsB5wTcC33Rnl7"
  group_chat_id_allowlist:
    - "oc_eeed0bff3e18355ab5ae3e3e2d20107f"  # 🚀亚马逊攻坚小分队
  merged_from:
    - "amazon-daily-kb-sync@v0.3.0"
    - "amazon-meeting-update-assistant"
---

# Amazon Daily Sync (v0.4.0 — merged)

## Purpose

每天扫**当前 owner** 在飞书的 evidence（**群聊 + 会议**），从中抽 candidate 行动项 / 状态变更 / 立项信号，**turn-based 引导 owner 把每条 candidate 路由到 5 个目的地之一**：

- 🚦 `task` → `🚦每周任务` Base (单点本周内)
- 📊 `project_activity` → `📊项目活动管理` Base (跨周阶段)
- 🧮 `team_project_draft` → wiki 草稿 + DM owner (大事，cron 不自动建)
- 📝 `audit_only` → 仅刷新 ME-owned KR/项目 audit 字段
- ⏭️ `skip` → 不写

**Merges** prior 2 skills:
- `amazon-daily-kb-sync@v0.3.0` — 之前每天 cron 自动建 task，不动 KR/项目 formal
- `amazon-meeting-update-assistant` — 之前 owner 手动调用，preview-confirm 改 KR/项目 formal

合并后**单一 skill**，运行模式：cron 触发 + turn-based 对话，跟 `okr-weekly-ritual` 模式一致。

## Default Behavior

- **Identity 必须**: `ME = lark-cli auth status .userOpenId`；fallback chain `.userOpenId // .data.user_open_id // .data.users[0].userOpenId`；为空 abort
- **ME 预期** = 戴时雨 `ou_ce0e16bb55bcde24078f9a551db3740d`（其他 owner 跑前改成自己的 open_id）
- **全部 ownership-scoped**：只写 ME-owned records；新建 task 强制 `执行人=ME`；cross-owner action items 仅 list 不写
- **绝对不写飞书 wiki / docs**（除 team_project_draft 起草到「OKR 巡检与草稿区」节点）：wiki 日会沉淀由 CEO 账号 wiki sinking automation 独立维护，不在本 skill 范围
- **新建 record 强制** `待人工确认=true`（owner 在 base UI 二次确认）

## Scope 边界（v0.4 硬规则）

- ✅ 可读：飞书所有群聊 (lark-im) + 会议 (lark-vc / lark-minutes) + Base 4 表
- ✅ 可写：
  - `🚦每周任务` (新建 + 更新, 执行人=ME)
  - `📊项目活动管理` (新建 + 更新, 执行人=ME, 待人工确认=true)
  - `🧮团队项目清单` 字段 (`本周更新` / `下一步` / `阻塞` / `下次检查点`) — 仅 helper 字段
  - `👤个人OKR` 字段 (`状态` / `进度` / `输出结果`) — 仅 high confidence + ME-owned
  - 所有 ME-owned record 的 audit 字段 (`最近更新原因` / `最近更新时间` / `最近更新来源` / `AI编译摘要` / `待人工确认`)
- ❌ 禁写：
  - 任何 wiki / docs (草稿区 doc 除外)
  - non-ME-owned base records
  - `🧮团队项目清单` 新建 (高风险, 改 team_project_draft → wiki 起草 + DM owner)
  - `👤个人OKR.状态/进度/输出结果` 在 low/medium confidence 下（仅 high confidence + ME 明确说"已完成"等 才能动）

## Step 0 — Identity + 时间窗

- `ME = lark-cli auth status` 取 `userOpenId`，缺则 abort
- `today = Asia/Shanghai date`，`week_num = ISO week`
- `today_start_ms` / `today_end_ms` = today 00:00:00 ~ 23:59:59 Asia/Shanghai UTC ms epoch

## Step 1 — 3-layer 群聊 filter（确定要扫哪些群）

### Layer 1: hardcoded allowlist (必扫)

```
must_scan_chat_ids:
  - "oc_eeed0bff3e18355ab5ae3e3e2d20107f"  # 🚀亚马逊攻坚小分队
  # 可扩展添加其他核心业务群
```

### Layer 2: auto-discover ME 加入的群 + 过滤

`lark-cli im +list-chats --as user --page-size 100 --format json` 拉所有群，jq filter：

- **包含** if 群名 match `(OKR|项目|亚马逊|Amazon|选品|PRD|运营)` 且 成员数 ≤ 30
- **排除** if 群名 match `(通知|机器人|财务|HR|公告|活动|生日)` 或 成员数 > 50
- **保留** if 在 Layer 1 allowlist 里 (优先级最高)

### Layer 3: 候选群拉今天消息 + ME-relevance filter

对每个 Layer 1+2 通过的群：

```bash
lark-cli im +list-messages --as user \
  --container-id $chat_id --container-id-type chat \
  --start-time $today_start_ms --end-time $today_end_ms \
  --format json
```

每条 msg 保留 if 任一为 true：
- `msg.sender.id == ME`（ME 自己发的）
- `f"@{ME_name}" in msg.text`（ME 被 @）
- `msg.text` 含 **ME-owned 关键词**（从 base 动态拉 ME-owned KR/项目/项目活动 文本抽，加上业务通用词 `PRD / OKR / Action item / 立项 / 决策`）

## Step 2 — 拉今天会议 evidence

- `lark-cli minutes +search --as user --participant-ids me --start <today> --end <today> --page-size 20 --format json`
- `lark-cli minutes +search --as user --owner-ids me --start <today> --end <today> --page-size 20 --format json`
- `lark-cli vc +search --as user --participant-ids me --start <today> --end <today>`（如可用）
- 对会议 minute 拉 notes / transcript（如有 scope）

如果会议 minute notes API 限权（缺 `minutes:minutes.artifacts:read` 等 scope），在 evidence pool 里 flag `permission_blocked` 继续，不阻断。

## Step 3 — 拉 ME-owned base 当天变更

- KR：`lark-cli base +record-list --base-token GxaobEQtqaOwFZsB5wTcC33Rnl7 --table-id tblxM7ZfxJt2P4Fl --as user --limit 200 --format json` filter `执行人[0].id == ME`，对每条找最近 24h 字段变化
- 长期项目：同上 `tblOHGg4IA2pY7uh` filter `负责人[0].id == ME`
- 项目活动：同上 `tblf54mtW07iPCRL` filter `执行人[0].id == ME OR 负责人[0].id == ME`
- 每周任务：同上 `tblrduPxvdifLm62` filter `执行人[0].id == ME`

## Step 4 — Extract candidates from evidence

每条 candidate 包含：
- `事项` (文本动作描述)
- `source` (link / msg_id / minute_token)
- `mentioned_records` (evidence 里提到的 base record_id 集合，用于关联)
- `mentioned_keywords` (提到的 KR/项目/项目活动名)
- `signals` (用于 routing 推断的关键词集合)

并为每条 candidate 计算 **AI 建议 routing**，按以下规则（按优先级）：

| 信号 | AI 建议 | 理由示例 |
|---|---|---|
| 含 "做一个 X 工具 / 平台 / 系统" + 跨周词 ("设计 / 开发 / 实施 / 上线 / 阶段") | `team_project_draft` | "做一个 X 工具 → 跨周多阶段建设" |
| 含 "X 项目的 Y 阶段" / "完成 X 的 Z 部分" + 既有项目 id 在 mentioned_records | `project_activity` | "对应已有项目 X 的阶段" |
| 含 "跟 X 同步 / 发 / 写 / review / 整理 / 调研 / 跟进" + 单点 | `task` | "本周内单点动作" |
| 含 "KR X 完成了" / "进度到 N%" / "状态改 Y" | `audit_only` | "KR 状态/进度变更, 不需新 record" |
| 闲聊 / 跑题 / 玩笑 / 跟业务无关 | `skip` | "evidence 不构成 actionable" |

## Step 5 — 输出 [REVIEW QUEUE] + 等用户

输出消息（必含 `[REVIEW QUEUE]` 标记），格式：

```
[REVIEW QUEUE] amazon-daily-sync W<weeknum> 2026-MM-DD

ME = 戴时雨 (ou_ce0e16bb55bcde24078f9a551db3740d)
扫描范围: <扫了的群数> 群 + <参与会议数> 个会议
今天 base 自更 records: <count>
candidates 总数: <N>

══════════════════════════════════════════════════════════
📚 引导: 5 个归属选项怎么选
══════════════════════════════════════════════════════════

🚦 task: ≤1 周单点动作 → 写 🚦每周任务 (执行人=ME)
  例: "跟林军 sync X" / "发 PRD 给 Y" / "调研 3 个竞品"

📊 项目活动: 2-4 周阶段, 属于既有项目 → 写 📊项目活动管理
  5 阶段: 1确定目标 / 2确认需求 / 3方案设计 / 4实施上线 / 5汇报总结
  例: "ai 唤醒灯 · 阶段 2 PRD 设计"

🧮 团队项目: 1-6 个月大事, 跨多阶段 → ⚠️ cron 不自动建
  → 起草方案到 wiki「OKR 巡检与草稿区」 + DM owner 明天手动建
  例: "ai 唤醒灯产品研发" / "完成目标管理 AI 化"

📝 仅 audit: 状态/进度变更, 不建新 record → 写 ME-owned 字段 audit
  例: 群里 mention "KR1 实际进度 50%" → 刷新 KR.audit + 标 待人工确认

⏭️ skip: 闲聊 / 跑题 / 误抓 → 不写

💡 三层关系: 团队项目 (书) → 项目活动 (章节) → 每周任务 (段落)
💡 简单项目走两层 (团队项目 → 任务, skip 项目活动); ≥3 月大事才用三层

══════════════════════════════════════════════════════════
候选列表
══════════════════════════════════════════════════════════

候选 #1: "<事项文本>"
  来源: <源类型> #<msg_id> 或 <minute_token>
  AI 建议: <🚦 task | 📊 项目活动 | 🧮 团队项目 | 📝 仅 audit | ⏭️ skip>
  理由: <1 句>

候选 #2: ...

...

══════════════════════════════════════════════════════════

下一步选择 (回复一个):

[1] 全部按 AI 建议接受 → 一次写完
[2] 逐条 review → codex 一条条问你 routing
[3] 改部分 → 你说 "#1 改 task, #3 改 skip" 等具体改动
[4] 全部 skip → 今天不写
[5] 解释 X → 不懂某个选项就问 (如 "解释项目活动")
```

[run 此处结束, 等用户回复]

### REVIEW QUEUE 输出硬规则

- **目标长度 ≤ 2500 字符**（含引导段 + 候选列表）
- **每条候选最多 4 行**（事项 / 来源 / AI 建议 / 理由）—— 不展开 3 个 候选方案
- candidates 总数 > 10 时只 list top 10 + 末尾 "另有 X 条简略, 回 'show all' 看全部"
- **不要列已完成 task** / 已存在 record（避免噪声）
- **0 candidates** 时输出 "今天 evidence 干净, 无 actionable 候选" + 直接 surface "skip 推群?" 选项

## Step 6 — 用户回复处理

按用户回复路由：

### [1] 全部按 AI 建议接受

对每条 candidate 按其 AI 建议 routing 执行（详见 Step 7 各 routing 类型的写法）。
执行完输出 `[WRITE DONE]` 汇总。

### [2] 逐条 review

对每条 candidate 依次输出 `[PHASE-#<index>]`：

```
[PHASE-#<index>] candidate (<index>/<total>):

事项: "<text>"
来源: <ref>

选项:
[1] 🚦 task
[2] 📊 项目活动 (需指定父项目, 我列你 own 的项目候选)
[3] 🧮 团队项目 (起草草稿, 不立刻建)
[4] 📝 仅 audit (我问你具体改哪个 KR/项目 字段)
[5] ⏭️ skip

回复数字 (1-5)。
```

用户回复 → 执行该 routing → 进下一条。

### [3] 改部分

解析用户回复（如 "#1 改 task, #3 改 skip"），update 内存 routing 决策，再输出更新版 REVIEW QUEUE + "现在接受吗 [1]?"

### [4] 全部 skip

不写任何 record，输出 "今天 0 写入, 仅 evidence 已 read"。

### [5] 解释 X

按 X 类型展开详细说明（参考 references/routing-guidance.md），含定义 / 何时用 / 何时不用 / 当前 ME-base 状况，再回 REVIEW QUEUE 等用户选。

## Step 7 — 按 routing 类型写 base

### 7.1 routing = `task`

`lark-cli base +record-batch-create --base-token GxaobEQtqaOwFZsB5wTcC33Rnl7 --table-id tblrduPxvdifLm62 --as user --json '<payload>'`

字段:
- 任务 = `事项`
- 执行人 = `[{"id": ME}]` **强制**
- 任务进度 = `"0-未开始"`
- 任务开始日期 = today ms epoch
- 任务结束日期 = ≤ this_week_friday ms epoch
- 关联KR = `[{"id": <kr_rec_id>}]` (如 mentioned_records 含)
- 所属项目 = `[{"id": <project_rec_id>}]` (如 mentioned_records 含)
- 最近更新原因 = "auto from amazon-daily-sync: 来源 <source>"
- 最近更新来源 = source link
- 最近更新时间 = now ms epoch
- AI编译摘要 = ≤80 字摘要
- 待人工确认 = `true`

### 7.2 routing = `project_activity`

先确认有父项目（mentioned_records 含某 🧮项目 record_id）。如无 → 转 team_project_draft.

`lark-cli base +record-batch-create --table-id tblf54mtW07iPCRL`:
- 项目活动 = `事项`
- 所属项目 = `[{"id": <project_rec_id>}]`
- 负责人 = `[{"id": ME}]`
- 执行人 = `[{"id": ME}]`
- 项目阶段 = `"1-确定目标"` (默认, owner 后续手动改)
- 任务进度 = `"0-未开始"`
- 优先级 = `"P1"` (默认)
- 任务计划结束日期 = 4 周后 ms epoch (默认)
- 待人工确认 = `true`

### 7.3 routing = `team_project_draft`（**起草, 不直接建 base record**）

不 batch-create 项目！而是：

1. 写 wiki 草稿 doc 到「01 目标与项目管理 / OKR 巡检与草稿区」节点下
   - title: `团队项目草稿 · <候选事项前 30 字> · YYYY-MM-DD`
   - 内容: 项目名 / 项目目标 / 候选关联KR / 候选成员 / 拟拆活动 / 来源 evidence
2. lark-im DM owner 到 ME 本人:
   - "今天 evidence 出现项目级 candidate: <事项简称>. 已起草 wiki: <link>. 请去 🧮团队项目清单 base UI 手动建 record."

### 7.4 routing = `audit_only`

仅更新 ME-owned 相关 record 的 audit 字段（最近更新原因 / 时间 / 来源 / AI编译摘要 / 待人工确认）。**不动正式状态字段**（KR.状态/进度, 项目.正式进度）。

如 candidate 含 high confidence 的"完成了" / "进度到 N%" → 在 audit 段 surface 给 owner，让他下次 manual 跑或 base UI 手动改 formal 字段。

### 7.5 routing = `skip`

不写任何 record，不输出 audit。

## Step 8 — 写入完毕，输出 [WRITE DONE]

```
[WRITE DONE] amazon-daily-sync 完成

写入汇总:
- 🚦 task: <N> 条 → [list record_ids]
- 📊 项目活动: <N> 条 → [list]
- 🧮 团队项目草稿: <N> 个 wiki doc + DM → [list links]
- 📝 仅 audit: <N> records → [list]
- ⏭️ skip: <N> 条

cross-owner items (未写, 仅 list):
  1. <事项>: assignee=<other>, source=<ref>
  ...

base UI 入口:
- 🚦每周任务: https://wg9k4pnk2o.feishu.cn/base/GxaobEQtqaOwFZsB5wTcC33Rnl7?table=tblrduPxvdifLm62
- 📊项目活动管理: https://wg9k4pnk2o.feishu.cn/base/GxaobEQtqaOwFZsB5wTcC33Rnl7?table=tblf54mtW07iPCRL

边界检查:
- 0 cross-owner records 被写
- 全部新 task / 项目活动 待人工确认=true
- 0 wiki/doc 写入（除 team_project_draft 起草到「OKR 巡检与草稿区」）
- KR/项目正式状态字段未动 (仅 audit)

下次运行: 明天 22:00 cron 自动触发, 同一 thread 继续 / 新 thread (取决于客户端行为)
```

## 阶段状态机

每轮 codex 唤醒时，看 thread 历史最后一条 bot output 的标记，识别当前状态：

- thread 空 + cron 触发 → 跑 Step 0-5（auto），输出 [REVIEW QUEUE]，等用户
- 最后是 `[REVIEW QUEUE]` + 用户回 "1" → 进 Step 6.1 (全部接受) → Step 7 写 → Step 8 [WRITE DONE]
- 最后是 `[REVIEW QUEUE]` + 用户回 "2" → 进 Step 6.2 [PHASE-#1]
- 最后是 `[PHASE-#N]` + 用户回数字 → 处理该 candidate 的 routing → 进 [PHASE-#N+1] 或 [WRITE DONE]
- 最后是 `[REVIEW QUEUE]` + 用户回 "3 ..." → 重新分类 + 输出更新版 REVIEW QUEUE
- 最后是 `[REVIEW QUEUE]` + 用户回 "5 解释 X" → 输出该选项的详细说明 (见 references/routing-guidance.md)，然后回 [REVIEW QUEUE] 等用户选
- 最后是 `[WRITE DONE]` → 本次仪式结束

## Failure Handling

- `lark-cli auth` 失败 → abort, 提示 `lark-cli auth login`
- 群聊 API limit / permission_blocked → flag in evidence, 继续不阻断
- 会议 minute notes scope 缺 → 同上, flag
- base batch write 失败 → surface raw stderr, 让用户决定 retry / skip
- ownership check fail → 该 record 跳过 + 记 audit, 不 abort 整 run
- 写 wiki 草稿 doc 失败 (草稿区节点不存在) → 自动创建节点，重试

## Don't

- ❌ 不要替别人写 base records (cross-owner 仅 list)
- ❌ 不要在 cron 模式下自动建 🧮团队项目清单 record (高风险, 改 team_project_draft)
- ❌ 不要 shell out `claude` CLI 推理 (codex 自己就是 LLM)
- ❌ 不要硬编 evidence (缺就老实报告 "evidence 不足")
- ❌ 不要发明 base 表不存在的字段 (如 "预估投入 X 天")
- ❌ 不要写飞书日会 wiki / 决策台账等（CEO 账号 wiki sinking automation 的活）
- ❌ 不要给 task 起"模糊动词"名 (如 "看看 X")
- ❌ 不要批量提问 N 个 candidates 让用户一次回 N 答案 — 走 [REVIEW QUEUE] 全貌 dump 或 [PHASE-#N] 逐条

## References

- [references/chat-filter.md](references/chat-filter.md) — 3-layer chat filter 详细规则
- [references/routing-guidance.md](references/routing-guidance.md) — 5 个 routing 选项的展开说明 (用户回 "解释 X" 时输出)
- [references/routing-write-rules.md](references/routing-write-rules.md) — 每 routing 类型的具体 base 写入 payload
- [templates/review-queue-template.md](templates/review-queue-template.md) — REVIEW QUEUE 输出格式模板
- [`libraries/amazon-base-kb-bridge/`](../../libraries/amazon-base-kb-bridge/) — 共享 ownership 规则 + field-map + Python scripts
