# Anti-Hallucination Rules — okr-evidence-compile

为什么有这份文件：之前 codex 在 86lux Base inventory 报告里曾把母 plan 的期望投射成事实（说"📖会议纪要 已有关联 OKR / 关联项目 / 关联周报"——实测都没有）。本 skill 写回飞书生产 OKR 表，幻觉成本太高，必须有硬规则。

参考 memory：`/Users/daishiyu/.claude/projects/-Users-daishiyu/memory/feedback_codex_no_inference.md`

## 六条硬规则

### 规则 1：evidence 引用闭环

AI 输出的任何 `record_id` 引用、项目名引用、任务名引用、会议主题引用、人名引用，**必须**出现在 Step 1-3 的 lark-cli 原始 JSON 响应中。如果原始响应里没有，禁止编造。

违反示例：
- ❌ "基于 rec123XYZ（OKR 表 AI 化项目）..."——但 evidence pool 里没 rec123XYZ
- ❌ "戴时雨在 3 月 5 日会议确认..."——但相关会议纪要里没"戴时雨"和"3 月 5 日"
- ✅ "基于 recvcUavxBq6oH（任务 X 已完成）..."——record_id 确认在 evidence pool 中

### 规则 2：数字不准编

进度、百分比、时间、参与人数等**任何数字**都必须有 evidence 原文支持。不能"看起来 50% 左右就写 50%"。

如果 evidence 中只有定性描述（如"进展顺利"），输出的进度推断 = null + 缺失警示「数字基础缺失」。

### 规则 3：evidence 缺失时禁止脑补

如果某个 source 类别（项目 / 任务 / 会议 / 周报）的 evidence 为空，**必须**：
1. 在 `缺失警示` 列出，如 `"关联团队项目 = 空"`
2. AI 编译摘要 中明确指出此类缺失
3. 不准编造该类别的内容来"凑齐"摘要

违反示例：
- ❌ Evidence pool 里没有项目，但摘要写"项目正在推进中"——脑补
- ✅ Evidence pool 里没有项目，摘要写"无关联项目可参考，进度推断 = null"

### 规则 4：path_drift=true 时进度推断 = null

只要 path_drift=true，**禁止**给一个具体进度数字。即使有 directly_contributes evidence 也不行。

理由：path drift 说明 KR 文本与团队实际方向不一致，此时任何"X%"都误导 owner。该让 owner 先决定"重审 KR 文本"还是"归档旧 evidence"，再 rerun skill。

### 规则 5：摘要长度 + 必含引用（v4.3 修订）

**Base 表 `AI编译摘要` 字段（abstract 版）**：
- 长度 ≤ **80 字**（含 emoji 与标点，v4.3 从 120 收紧到 80）
- 必含至少 1 个 evidence record_id 引用（除非结果是 B：evidence 全空）
- 如 path_drift=true，前置 ⚠️
- 不用 markdown（飞书 base text 字段不渲染 markdown）
- 超长**截断 + 末尾 `…`**

**Wiki doc `摘要` 段（完整版）**：
- 不限长度，但建议 ≤ 200 字
- 必含完整 path drift 警示 + off_path record_ids 列表 + evidence 引用

### 规则 6：ownership 闸门（v4.3 新增）

skill 的 Step 1.5 ownership check 是**绝对写权限闸门**：

- 一旦 Step 1.5 abort（current user ≠ KR 执行人 + force_ownership_bypass=false），后续 **任何 write 操作都禁止**：
  - 禁止 `docs +create / +update`
  - 禁止 `base +record-batch-update / +record-upsert`
  - 禁止任何对 wiki node 的 mutation

违反示例：
- ❌ Step 1.5 abort 后仍然写 doc 或 base record
- ❌ 把 force_ownership_bypass 默认设为 true 来"绕过麻烦"

**理由**：员工 A 在自己电脑跑 skill 时，应只能写自己的 KR。误写他人 record 会污染他人数据 + 飞书 audit log 显示错乱（A 的认证身份写了 B 的 record）。force_ownership_bypass 仅用于 CEO 显式审计或 Hermes cron。

## 自检 checklist（Claude 输出前自验）

输出 JSON 前，AI 必须按以下顺序自检：

1. [ ] Step 1.5 ownership check 已通过（或显式 force_ownership_bypass=true）？
2. [ ] `evidence_classifications` 中所有 `record_id` 都在 Step 1-3 原始响应里出现过吗？
3. [ ] `进度推断` 如果非 null，对应的依据 record_id 在 evidence pool 里吗？
4. [ ] 如果 `path_drift=true`，`进度推断`==null 了吗？
5. [ ] 如果 `evidence_classifications`==[] 或全 off_path，`AI编译摘要` 是"evidence 缺失"模式吗？
6. [ ] base 字段 `AI编译摘要` (abstract 版) 长度 ≤ **80 字** 吗？
7. [ ] doc 中的"摘要"段（完整版）含 evidence record_id 引用吗（除非结果 B）？
8. [ ] `confidence`==low 当 path_drift=true / evidence<3 条 / 最新时间>14 天 之一成立吗？

任一不满足 → 修正 → 再输出。

## 调用者侧的额外护栏

skill 调用方（codex exec / Hermes / 飞书 Bot）在 Step 4 拿到 JSON 后，**写回 Step 5 之前**还要二次校验：

1. parse JSON 成功？
2. 必填字段全部存在？
3. `evidence_classifications` 中 record_id 全部 ∈ Step 1-3 已知 record_id 集合？
4. `进度推断` 类型为 int 或 null？范围 [0, 100]？

任一失败 → 不写回 → surface error + 让 owner 决定 retry 还是 abort。
