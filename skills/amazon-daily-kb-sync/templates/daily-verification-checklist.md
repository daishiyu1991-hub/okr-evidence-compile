# Daily Verification Checklist (v2 — per-owner)

## Identity & Ownership

- [ ] `ME = lark-cli auth status .userOpenId` 已解析成功
- [ ] 所有写入的 base records 都满足 `owner == ME`
- [ ] 所有新建 task 强制 `执行人 = [{"id": ME}]`
- [ ] Cross-owner action items 已列入 "not synced" 段而不是被强制同步

## Daily Log Doc

- [ ] 找到 / 创建了 ME 自己的 doc：`日会同步日志 · <ME.userName>`
- [ ] 没动到其他 owner 的 doc
- [ ] doc 顶部新 entry 已 prepend（不是 overwrite）
- [ ] 老 entry 完整保留
- [ ] doc 顶部 "👤 当前结论" + "当前状态 snapshot" 已替换为最新值
- [ ] 来源索引在 entry 内可回溯（每个 reference 有 url 或 token）

## Base Writes

- [ ] KR / project 的 `状态` / `进度` 字段未被强行覆盖（除非有 strong evidence）
- [ ] 仅写了 audit fields + 行动项 task 表
- [ ] task 表新建记录 `执行人 == ME`
- [ ] 已写 records 的 `最近更新原因` / `最近更新时间` / `最近更新来源` audit 字段都已 backfill

## Weekly-Meeting Day Only

- [ ] 7-day 汇总仅 scope 到 own records
- [ ] inconsistency 检测仅 scope 到 own records
- [ ] Weekly compile 段已 append 进当日 entry（不是新建 doc）

## 来源 / 安全

- [ ] 群结论 / 妙记 / minutes 引用都有原始 link，不替换为占位
- [ ] Excalidraw / 白板 / 文件附件保留原物或原 link
- [ ] 没把 secrets / tokens / 私聊原文写进持久 KB
