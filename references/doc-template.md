# Doc Template — OKR Compile Log

每个 KR 在 wiki `「OKR AI 编译记录」` 节点（`Q7aGwCUvciF0lMknHo7cUEMOnAh`）下有 1 个 doc。本文件定义 doc 的精确 markdown 结构。

## 常量

- **wiki space**: `7639331686206999770` (亚马逊目标管理与会议沟通沉淀)
- **parent node**: `Q7aGwCUvciF0lMknHo7cUEMOnAh` (OKR AI 编译记录)

## Doc 标题命名约定

```
OKR Compile · <执行人> · <O 名> · <KR 文本前 30 字>
```

例：

```
OKR Compile · 戴时雨 · O1-O1 ai化 · KR1 完成目标管理AI化，集成到面板
```

- 分隔符用 `·` (U+00B7 中点)：避免飞书 doc title 里 `/` 被识别为路径
- 飞书 wiki node list 按 title 字母 / Unicode 序排序时，同执行人 KR 自动聚成连续区域
- 不建 per-owner 子节点（规模 < 80 doc 前不需要）

## Doc 内容（markdown 完整模板）

> v4.4 新增：doc snapshot 和每条 entry 顶部必含「👤 结论（人读版）」段，把 AI 结构化输出翻成大白话给 owner / CEO 一眼读懂。

```markdown
# OKR Compile Log: <KR 文本>

> 此 doc 由 codex skill `okr-evidence-compile` 自动生成 + 累积维护。
> 飞书 base 源：[👤个人 OKR / <record_id>](https://wg9k4pnk2o.feishu.cn/base/GxaobEQtqaOwFZsB5wTcC33Rnl7?table=tblxM7ZfxJt2P4Fl&view=vewgWHPfVJ)
> **不要直接编辑此 doc**——任何手工编辑会在下次 skill 运行时被新 entry 覆盖（顶部插入）。

## 👤 当前结论（人读版，扫一眼）

> <一段大白话总结当前 KR 真实状态。30-100 字。回答：现状是什么 / KR 字段填的数字与 evidence 一致吗 / 下一步要做什么。>
>
> <如果 path_drift=true，明确点出"path drift 警示"和 owner 应该做的纠偏动作。>
>
> <如果 evidence 缺失（结果 B），直接说"无 evidence 支撑，需要先回填"。>

---

## ⚠️ 跨 entry 警示（latest 比 history 更乐观）

> **本段仅当 latest entry 比某条历史 entry "更乐观" 时渲染。无矛盾则整段省略（不留空标题）。** 详见 §「跨 entry 警示 渲染规则」。

下面警示在 historical entry 里出现过、但 **#<latest_N> 本次没复现**。可能是 evidence 真的变了，也可能是不同 agent compile / 不同 evidence_window 判定不一致——**owner 应手动判断哪个结论正确**。

- **#<old_N>** (<trigger>) 报 `path_drift=true`，但 #<latest_N> 报 `path_drift=false`
- **#<old_N>** (<trigger>) 报 `confidence=low` / `待人工确认=true`，但 #<latest_N> 未维持
- **#<old_N>** (<trigger>) 报 evidence 缺失（<列 1-2 项>），但 #<latest_N> 未维持
- **#<old_N>** (<trigger>) `进度推断=null`（曾 path_drift），但 #<latest_N> 推断进度=<N>%

**行动选项**：
1. 你确认 #<latest_N> 正确 → 手动取消 base 「待人工确认」复选框
2. 你确认 #<old_N> 正确 → 补底层 evidence（关联项目/任务/周报），然后 rerun skill
3. 不确定 → 保持现状，下次 self-run 看趋势

---

## 当前状态 snapshot (latest)

- **KR**: <KR-关键结果 文本>
- **执行人**: <执行人 open_id 对应 name>
- **所属周期**: <所属周期 字段值>
- **关联团队 KR**: <recXXX 或 null>
- **base record 进度字段**: <进度 数值，如 0.6 (60%)> ← 注：这是字段值，非 AI 推断
- **最新 compile 截至**: **<ISO 周, 如 2026-W21>** · <YYYY-MM-DD HH:MM> · trigger="<v4.0 first run / 周度 self-run / CEO 审计 / ...>"
- **evidence 时间窗口**: <N> 周 (lookback_weeks)
- **最新 path_alignment_score**: <0.00-1.00>
- **最新 off_path_ratio**: <0.00-1.00>
- **最新 path_drift**: <true|false>
- **最新 confidence**: <high|low>
- **最新 AI 推断进度**: <0-100 整数> | null
- **最新摘要 abstract** (≤80 字)：<abstract 文本>

## Compile history（按时间倒序）

### #<N> · <ISO 周> · <YYYY-MM-DD HH:MM> · trigger="<...>" · evidence_window=<N>w

#### 👤 结论（人读版）

- **现状**：<一句话讲清当前 KR 是什么状态，引用关键 evidence record_id>
- **怎么办**：
  1. <具体可执行动作 1>
  2. <具体可执行动作 2>
  3. <可选：rerun skill 验证>
- **为什么**：<1-2 句解释 AI 判定的依据，引用 path_alignment_score / off_path_ratio / 缺失警示 等关键数据>

#### 机器读结构

**摘要**
<完整 AI 编译摘要 文本>

**Evidence classifications**

| record_id | table | label | reason |
|---|---|---|---|
| <record_id> | <task|project|team_okr|meeting|weekly_report> | <directly_contributes|tangentially_related|off_path> | <1 句 reason> |
| ... | ... | ... | ... |

**缺失警示**
- <每条 1 行>
- ...

**进度推断**: <0-100 整数> | null
**进度推断依据**: <1-2 句话>

<details>
<summary>Raw JSON</summary>

```json
<完整 Step 4 输出 JSON>
```
</details>

---

### #<N-1> · ... (上一次 compile)

（依此类推，每个 entry 之间用 `---` 分隔）
```

## entry 数据来源映射

| 模板字段 | 数据来源 |
|---|---|
| KR 文本 | Step 1 record `KR-关键结果` |
| 执行人 | Step 1 record `执行人` → open_id 通过 lark-cli contact 解析为 name |
| 所属周期 | Step 1 record `所属周期` |
| 关联团队 KR | Step 1 record `关联团队KR` |
| base record 进度 | Step 1 record `进度` |
| ISO 周 | execution time → `date "+%G-W%V"` |
| trigger | skill 调用 param 或上下文 |
| evidence_window | skill 调用 param `evidence_lookback_weeks`（默认 4） |
| path_alignment_score / off_path_ratio / path_drift / confidence / 进度推断 / 进度推断依据 / AI 编译摘要 / 缺失警示 / evidence_classifications | Step 4 Claude API JSON 输出 |
| Raw JSON | Step 4 完整 JSON（含本次所有 evidence 引用） |

## 「👤 结论」生成规则（v4.4 新增）

每次 compile 必须额外生成两段大白话：

### 1. doc 顶部「👤 当前结论」(snapshot block)

- 长度：30-100 字
- 内容必含 3 点：
  - 当前 KR 真实状态（不重复字段值，要"翻译"成现实含义）
  - KR 字段填的数字与 evidence 是否一致（如有矛盾，明确指出）
  - 下一步具体动作（1-2 个，可执行）
- 风格：直白、不绕弯子，避免 path_alignment_score / off_path_ratio 这种术语
- 例（path_drift 场景）：
  > KR 字段标了 60% 进度，但实际没有任何关联项目、每周任务或会议在做这事，周报承认本周无进展。**60% 是历史数字，无 evidence 支撑。** 下一步：先在 base 给这条 KR 加关联项目和任务，再 rerun。

### 2. 每个 entry 顶部「👤 结论」(3 问)

固定 3 段：

- **现状**：1 句话 + 关键 evidence record_id 引用
- **怎么办**：1-3 步具体动作（不是"建议..."这种空话，要明确"加 X 字段"/"link 到 Y record"/"删 Z 占位项目"）
- **为什么**：1-2 句讲清 AI 判定的依据，可以提术语但要伴随翻译（如 "off_path_ratio = 33% > 30% 阈值 → AI 拒绝推断进度"）

### 与「机器读结构」的分工

- 「👤 结论」段：服务 owner / CEO / 非技术员工。**先放，先看。**
- 「机器读结构」段（摘要 / Evidence classifications 表 / 缺失警示 / Raw JSON）：服务 audit / debug / 自动化。**后放，按需展开。**

## 跨 entry 警示 渲染规则（v4.5 新增）

doc 顶部「⚠️ 跨 entry 警示」section 是 **conditional render**：仅当 latest entry 比某条 historical entry "更乐观" 时才出现。**无矛盾就完全省略整段（不留空标题、不留 "无警示" 占位）**。

### 渲染步骤（每次 prepend new entry 时执行）

1. fetch 现有 doc markdown
2. parse 所有 historical entries 的「机器读结构」段，提取每个 entry 的 key fields：
   - `path_drift` (true|false)
   - `confidence` (high|low)
   - `进度推断` (integer | null)
   - `缺失警示` (list)
   - 从 entry 的「最近更新原因」字段或 trigger 抽 trigger string
3. 跟本次 latest entry 比对
4. 任一矛盾命中 → 渲染本段；全部一致 → 跳过

### 矛盾命中条件（任一 true → render）

| 条件 | latest | history 任一 | 解释 |
|---|---|---|---|
| 1 | `path_drift=false` | `path_drift=true` | AI 不再认为偏离路径，但历史报过 |
| 2 | `confidence=high` | `confidence=low` | AI 这次信心更足，但历史不确定 |
| 3 | `缺失警示=[]` | `缺失警示=[<非空>]` | AI 这次不报缺失，但历史报过 |
| 4 | `进度推断=integer` | `进度推断=null AND path_drift=true` | AI 这次推断了进度，但历史因 drift 拒绝推断 |
| 5 | `待人工确认=false` | `待人工确认=true` | AI 这次降级了确认要求 |

> 条件 5 实际等同于"path_drift OR confidence=low" 触发，所以重叠条件 1+2。但显式列出便于 audit。

### 渲染时只 surface "命中的"那几条

- 比如只有条件 1 命中 → 只渲染 "path_drift=true→false" 那一 bullet
- 多条命中 → 多 bullets
- 每条 bullet 用具体 entry 号（`#<old_N>`）+ trigger string，方便 owner 直接定位到 history 那一段

### 不应该 surface 的情况（保持沉默）

- latest 更**保守**（latest.path_drift=true、history.path_drift=false）── 这是 entry 本身的警示职责，不要重复 surface
- 历史 entry 之间互相矛盾、但 latest 跟所有都一致 ── 不关 latest 的事
- 只有「最新摘要 abstract」文字不同 ── 文字差异不算结构性矛盾

## abstract 抽取规则（≤80 字）

abstract 写入飞书 base 「AI 编译摘要」字段。从 Step 4 输出的「AI 编译摘要」（完整版，可能含 ⚠️ 警示 + record_id 引用）抽取关键信息，缩到 ≤80 字：

- 优先保留：path drift 警示 `⚠️`、最严重 evidence 引用 1 个 record_id、关键判断（如"本周无进展"）
- 删除：完整的 record_id 列表、多个 reason 说明、emoji 装饰
- 长度严格 ≤ 80 字。超长截断 + 末尾加 `…`

例：

完整版（120 字）：
> ⚠️ path drift：6 条 evidence、2 条 off_path（占位项目）。无直接关联项目/任务/会议；周报 recvd4XBO5hEpl 明确 KR 本周无进展、60% 进度与"未开始"状态矛盾。建议回填 evidence 后 rerun。

abstract（≤80 字）：
> ⚠️ path drift。无直接关联项目/任务/会议；周报 recvd4XBO5hEpl 明确本周无进展，60% 进度与"未开始"矛盾。建议回填 evidence。

## doc 创建 vs 更新分支判定

skill 跑前读飞书 base record 的「最近更新来源」字段：

| 字段值形态 | 行为 |
|---|---|
| 空 / null | doc 不存在 → **创建新 doc** |
| `skill://okr-evidence-compile@/Users/...` (plan path) | v3.3 历史 → **创建新 doc 且写 entry #0 (v3.3 retro) + entry #1 (本次)** |
| `https://wg9k4pnk2o.feishu.cn/wiki/...` (doc URL) | doc 已存在 → **fetch + prepend new entry** |

## append 机制（doc 已存在分支）

1. `lark-cli docs +fetch --doc <token from URL> --as user --api-version v1 --format json`
2. parse 现有 markdown content，定位：
   - `## 当前状态 snapshot (latest)` ←→ 下一段 markdown header
   - `## Compile history（按时间倒序）`
   - 第一个 `### #N · ...` entry header（取最大 N）
3. 计算新 entry 号 = max_N + 1
4. 重写 "当前状态 snapshot" 整段为新数据
5. 在 "## Compile history" 之后、第一个 `### #N` 之前 prepend 新 entry（用 `---` 分隔）
6. `lark-cli docs +update --doc <token> --as user --markdown <新完整 markdown>`

## v3.3 retro 数据来源（doc 不存在 + 检测到 v3.3 历史的 case）

entry #0 直接从已写入飞书 base 字段值反推：

| entry #0 字段 | 数据来源 |
|---|---|
| 时间 | record `最近更新时间` 字段 |
| trigger | `"v3.3 demo retro"` 固定字符串 |
| ISO 周 | `最近更新时间` → `date "+%G-W%V"` |
| evidence_window | `1w` 固定 |
| 摘要 | record `AI编译摘要` 字段值（即 v3.3 写入的 120 字版） |
| 进度推断 | null（v3.3 已是 path_drift=true） |
| confidence | low（v3.3 已是 low） |
| Evidence classifications | 用本次 v4.0 跑出来的同 evidence pool（同一 record，evidence 不会变） |
| Raw JSON | 简化版，标注 "v3.3 retro - 真实 raw JSON 已丢失，仅含 base 字段反推" |
