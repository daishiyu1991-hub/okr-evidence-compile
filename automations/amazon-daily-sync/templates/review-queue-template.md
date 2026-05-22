# REVIEW QUEUE 输出模板

> 标准 [REVIEW QUEUE] 输出格式 (codex 在 Step 5 用). 长度目标 ≤ 2500 字符.

---

```
[REVIEW QUEUE] amazon-daily-sync W<weeknum> <YYYY-MM-DD>

ME = <name> (<open_id>)
扫描范围: <chat_count> 群 + <meeting_count> 会议
今天 base 触及 records: <count>
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
  来源: <类型> <ref>
  AI 建议: <emoji> <routing>
  理由: <1 句>

候选 #2: "<事项文本>"
  来源: <类型> <ref>
  AI 建议: <emoji> <routing>
  理由: <1 句>

... (max 10 条, 超过时末尾加 "另有 X 条简略, 回 'show all' 看全部")

══════════════════════════════════════════════════════════

下一步选择 (回复一个):

[1] 全部按 AI 建议接受 → 一次写完
[2] 逐条 review → codex 一条条问你 routing
[3] 改部分 → 你说 "#1 改 task, #3 改 skip" 等具体改动
[4] 全部 skip → 今天不写
[5] 解释 X → 不懂某个选项就问 (如 "解释项目活动")
```

---

## 实例 (戴时雨今天 5/22 evidence)

```
[REVIEW QUEUE] amazon-daily-sync W21 2026-05-22

ME = 戴时雨 (ou_ce0e16bb55bcde24078f9a551db3740d)
扫描范围: 3 群 + 1 会议
今天 base 触及 records: 1 (KR recvcU53W4hH0e)
candidates 总数: 6

══════════════════════════════════════════════════════════
📚 引导: ...
══════════════════════════════════════════════════════════

候选 #1: "做一个自动跑会议纪要的工具"
  来源: 群聊 #6814 (🚀亚马逊攻坚小分队 15:32)
  AI 建议: 🧮 团队项目
  理由: "做一个 X 工具" + 跨周建设, 属于"目标管理 AI 化"方向

候选 #2: "跟林军同步 Sorftime 子账号注册问题"
  来源: 群聊 #6816
  AI 建议: 🚦 task
  理由: 单点 sync 动作, 本周内完

候选 #3: "完成自动周报自动化"
  来源: 群聊 #6813
  AI 建议: 🧮 团队项目
  理由: skill 设计 + 测试 + 部署, 跨多周

候选 #4: "本周内 follow up 罗国华 KR2 进展"
  来源: 会议 minute #recXXX
  AI 建议: 🚦 task
  理由: 单点 follow up 动作

候选 #5: "KR1 进度实际到 50% (群里 mention)"
  来源: 群聊 #6820
  AI 建议: 📝 仅 audit
  理由: 不需要新 record, 刷新 KR.audit + 标 待人工确认

候选 #6: "周末聊聊乡村振兴"
  来源: 群聊 #6800
  AI 建议: ⏭️ skip
  理由: 闲聊跑题, 不构成 actionable

══════════════════════════════════════════════════════════

下一步选择 (回复一个): ...
```

---

## 配套 [PHASE-#N] 输出 (用户选 [2] 逐条 review 时)

```
[PHASE-#<index>] candidate (<index>/<total>):

事项: "<text>"
来源: <ref>
AI 建议: <emoji> <routing> (理由: <1 句>)

选项:
[1] 🚦 task → 写 🚦每周任务
[2] 📊 项目活动 → 写 📊项目活动管理 (需指定父项目)
[3] 🧮 团队项目 → 起草 wiki 草稿 + DM (不立即建 base)
[4] 📝 仅 audit → 刷 KR/项目 audit 字段 (我会问改哪个 record 的 audit)
[5] ⏭️ skip → 不写

回复数字 (1-5).
```

如用户选 [2] 但 candidate 无父项目 → codex 提示 "此候选无对应既有项目, 建议改 [3] 起草新团队项目? 或选 [1] task 临时挂".

如用户选 [4] 但 candidate 涉及多个 record → codex 列具体 records 让用户选改哪个的 audit.

---

## 配套 [WRITE DONE] 输出

```
[WRITE DONE] amazon-daily-sync 完成

写入汇总:
- 🚦 task: <N> 条
  · <task name> (rec_id) → <base url>
  ...
- 📊 项目活动: <N> 条
  ...
- 🧮 团队项目草稿: <N> 个 wiki doc + DM
  · "<draft title>" wiki: <url>
  ...
- 📝 仅 audit: <N> records 刷新
  ...
- ⏭️ skip: <N> 条

cross-owner items (未写, 仅 list):
  1. <事项>: assignee=<other>, source=<ref>
  ...

base UI 入口:
- 🚦每周任务: https://wg9k4pnk2o.feishu.cn/base/.../tblrduPxvdifLm62
- 📊项目活动管理: https://wg9k4pnk2o.feishu.cn/base/.../tblf54mtW07iPCRL

边界检查:
- 0 cross-owner records 写入
- 全部新 task/项目活动 待人工确认 = true
- 0 wiki 写入 (除 team_project_draft 起草到草稿区)
- 0 KR/项目正式状态字段变更
- 0 个人 DM (除 team_project_draft 给 ME 自己)

下次运行: 明天 22:00 cron 自动触发
```
