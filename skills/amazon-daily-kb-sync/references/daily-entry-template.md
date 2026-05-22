# Daily Entry Template (v2 — per-owner)

每个 owner 在 `02 日会沉淀` 下有 1 个 doc，名为 `日会同步日志 · <执行人 name>`。本文件定义 doc 的 markdown 结构 + 每次 daily run 如何 prepend new entry。

## Doc 标题命名约定

```
日会同步日志 · <执行人 name>
```

例：

```
日会同步日志 · 戴时雨
日会同步日志 · 罗国华
```

- 1 doc per owner，**永远不再建第二个**（即便跨年）
- 用 `·` (U+00B7 中点) 分隔，跟 `okr-evidence-compile` doc 一致
- 飞书 wiki node list 按 title 排序时，4 个 owner 的 daily log 自动聚成连续区域

## Doc 完整模板（markdown）

```markdown
# 日会同步日志 · <执行人 name>

> 此 doc 由 codex skill `amazon-daily-kb-sync` 自动累积维护。**Only the named owner writes to this doc** — multi-user safe by design.
>
> **不要直接编辑此 doc**——任何手工编辑会在下次 skill 运行时被新 entry 覆盖（顶部插入）。

## 👤 当前结论（latest snapshot · 扫一眼）

> <一段大白话总结本周节奏 + 最近 open loops + 最近 inconsistency 警示。30-100 字。回答：本周我做了啥 / 哪些 KR 在动 / 哪些卡住了 / 下一个动作是什么。>
>
> <如果是周会日：说明 7-day summary 是否完整、有几个 inconsistency 需要 review。>

---

## 当前状态 snapshot (latest)

- **执行人**: <name> (open_id ou_xxx)
- **最新 sync 截至**: <ISO 周, 如 2026-W21> · <YYYY-MM-DD HH:MM> · trigger="..."
- **持有 KR 数**: <N>
- **持有 项目 数**: <N>
- **持有 进行中 任务 数**: <N>
- **本周累计 inconsistency**: <N> (仅周会日填，非周会日填 "-")
- **最新 entry**: #<N>

---

## Sync history（按时间倒序）

### #<N> · <ISO 周> · <YYYY-MM-DD> · <周几> · trigger="daily" · meetings=<count>

#### 👤 当天结论（人读版）

- **现状**：<1-2 句话讲清今天我做了啥 / KR & 项目状态如何 / 关键 evidence record_id 引用>
- **怎么办**：
  1. <具体可执行动作 1，引用 record_id>
  2. <具体可执行动作 2>
  3. <可选：跟谁同步 / 需要谁配合>
- **为什么**：<1-2 句说明 evidence 来源 + AI 判定依据>

#### 机器读结构

**原始群结论区** (mirrored from 🚀亚马逊攻坚小分队 if ME participated today)

> 完整 copy 群里的日会结论原文（包含 attachments / Excalidraw / 白板）。
> 如果 ME 不在今天的日会群结论里，本段省略。

**当天会议 / minutes** (where ME is participant or owner)

| record_id | source_type | title | link |
|---|---|---|---|
| <token> | minutes | <title> | <url> |
| <token> | vc | <title> | <url> |

**当天 base 变更（ME 持有的 records）**

KR (`👤个人OKR`):

| record_id | KR | what changed | link |
|---|---|---|---|
| <recXXX> | <KR text> | 状态: A→B / 进度: 0.4→0.5 / ... | <base://...> |

项目 (`🧮团队项目清单`):

| record_id | 项目名称 | what changed | link |
|---|---|---|---|
| ... | ... | ... | ... |

任务 (`🚦每周任务`):

| record_id | 任务 | what changed | link |
|---|---|---|---|
| ... | ... | ... | ... |

**新建 / 更新 task 同步 (assignee == ME)**

| action_item | source | new_record_id (in 🚦每周任务) | confidence |
|---|---|---|---|
| "<action text>" | <meeting/chat ref> | <recXXX created OR existing updated> | high/medium/low |

**Cross-owner action items (not synced — for transparency only)**

| action_item | source | rightful_owner | note |
|---|---|---|---|
| "<action text>" | <ref> | <other name> | left for them to sync from their own machine |

**Weekly compile (7-day · own records only)** — 仅周会日填

> 按 `weekly-compile-contract.md` 规范填。

**来源索引**

| source_id | url_or_token | fetch_status |
|---|---|---|
| ... | ... | fetched / permission_blocked / not_available |

---

### #<N-1> · ... (上次 sync)

（依此类推。每个 entry 之间用 `---` 分隔。）
```

## 「👤 当天结论」生成规则

每次 sync 必须额外生成一段大白话「👤 当天结论」，服务 owner 一眼读懂：

- **长度**：30-100 字
- **必含 3 段**：
  - **现状**：1 句话讲清当前 KR / project / task 是什么状态，引用 record_id 增加 traceability
  - **怎么办**：1-3 步具体动作（不是"建议..."这种空话，要明确"加 X 字段"/"link 到 Y record"/"补 evidence 后 rerun"）
  - **为什么**：1-2 句讲清 AI 判定依据，可引用 evidence count / inconsistency count 等

例（戴时雨周一日会）：

> **现状**：本周日会决定了 O1-KR1 转向"先做 wiki doc 工具再做面板"。我持有的 2 个项目（recA1 / recB2）已更新本周更新；2 个任务（recT1 / recT2）已分配给自己。
> **怎么办**：1. 跟林军同步 recA1 项目变更影响他的 KR；2. 跑 okr-evidence-compile 验证 O1-KR1 path drift 是否解除；3. 周五前完成 recT1。
> **为什么**：今天会议 minutes recM1 明确变更方向；当前 base 进度 0.6 与新 path 不一致，待人工确认。

## 与「机器读结构」的分工

- 「👤 结论」：服务 owner 自己 / CEO 巡检。先放、先看。
- 「机器读结构」：服务 audit / debug / 未来自动化。后放、按需展开。

## 创建 vs 更新分支判定

skill 跑前在 wiki 节点 `02 日会沉淀` 下搜 `日会同步日志 · <ME.userName>`：

| 搜索结果 | 行为 |
|---|---|
| 0 hit | doc 不存在 → **创建** new doc with 1 entry |
| 1 hit | doc 存在 → **fetch + prepend new entry** |
| > 1 hit | 异常 → abort，要求人工 cleanup（不应该出现 2 个同标题的 owner doc） |

## append 机制（doc 已存在分支）

1. `lark-cli docs +fetch --doc <token> --as user --api-version v1 --format json`
2. parse 现有 markdown content，定位：
   - `## 当前状态 snapshot (latest)` 段
   - `## Sync history（按时间倒序）`
   - 第一个 `### #N · ...` entry header（取最大 N）
3. 计算新 entry 号 = max_N + 1
4. 重写"当前状态 snapshot"整段为新数据
5. 重写"👤 当前结论"整段为新数据
6. 在 "## Sync history" 之后、第一个 `### #N` 之前 prepend 新 entry（用 `---` 分隔）
7. `lark-cli docs +update --doc <token> --as user --markdown <new markdown>`
