# Daily Verification Checklist (v3 — base-only, per-owner)

## Identity & Ownership

- [ ] `ME = lark-cli auth status .userOpenId` 已解析成功
- [ ] 所有 base 写入的 record 都满足 `owner == ME`
- [ ] 所有新建 task 强制 `执行人 = [{"id": ME}]`
- [ ] Cross-owner action items 已在 preview "(not synced)" 段列出，未真写入

## Base Writes

- [ ] KR 的 `状态` / `进度` 字段未被强行覆盖（除非有 strong evidence 且明确确认）
- [ ] 项目 的 `进度` / `状态` 字段未被强行覆盖
- [ ] 仅写了 audit fields + 行动项 task 表
- [ ] task 表新建记录 `执行人 == ME`
- [ ] 已写 records 的 `最近更新原因` / `最近更新时间` / `最近更新来源` / `AI编译摘要` / `待人工确认` audit 字段都已 backfill

## Wiki Boundary

- [ ] **本次跑没有调用任何 `docs +create` / `docs +update` / `wiki +node-create`**
- [ ] **本次跑没有写入 `02 日会沉淀` / `04 决策与行动项追踪` 任何节点**
- [ ] 如果需要 wiki 沉淀今天的会议摘要，应该单独跑 CEO 账号 wiki sinking automation (不在本仓库)，不是本 skill 的职责

## Weekly-Meeting Day Only

- [ ] 7-day 汇总 + inconsistency 检测仅 scope 到 own records
- [ ] inconsistency 仅在 console / preview 中显示，必要时 append 到对应 own record 的 `AI编译摘要` audit 字段
- [ ] **没有**为 weekly 摘要单独写新 wiki 文档（那是 CEO 账号 wiki sinking automation (不在本仓库) 的活）

## 来源 / 安全

- [ ] 群结论 / 妙记 / minutes 引用都有原始 link
- [ ] 不把 secrets / tokens / 私聊原文写进 base audit 字段
- [ ] preview / console 输出可回溯到原始 evidence
