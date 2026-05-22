# OKR 周复盘+规划仪式 · codex automation

> 每周一 09:00 Asia/Shanghai 自动触发，跟 owner 在同一 thread 里跑完 4-phase 周仪式：复盘上周 → 补建 gap → 规划本周 → 推群同步。

---

## 用途

把"每周一上午回顾上周 + 规划本周"这个 OKR 仪式自动化：

| Phase | 干啥 |
|---|---|
| **Step 0 (cron 自动)** | 拉 base 4 表 ME-owned 数据 → 输出 `[GAP REPORT]` 极简报告（≤1500 字）|
| **Phase 1 复盘** | 上周未完成 task / 逾期项目活动 / 长期无动 KR 逐条引导决策（5 选 1：续做/推迟/取消/标完成/拆细）|
| **Phase 2 补建** | KR 缺项目 / 项目缺拆解 / 活动逾期 / 项目缺文档 4 类 gap，AI 起草候选方案让 owner 选 |
| **Phase 3 规划本周** | AI 推荐 5-7 个候选 task（含关联 KR / 截止日 / 优先级），owner review → 批量写 `🚦每周任务` 表 |
| **Phase 4 推群** | 生成"本周计划"DM 草稿 → owner confirm → 推到 `🚀亚马逊攻坚小分队` 群 |

全程**单 thread**，turn-based 对话。cron 触发首次执行，之后每次 owner 输入触发 codex 进下一步。

---

## 关键设计原则

1. **base 是 source of truth**——所有 task / 项目 / 项目活动 写入 base 表，wiki 只做 view 和归档
2. **per-owner ownership scoped**——只动 ME 名下的 records（执行人/负责人 = ME），不替别人写
3. **新建 record 标 `待人工确认=true`**——owner 在 base UI 二次确认
4. **不发明 AI 抽象指标**——只用 base 已有字段（优先级 / 任务进度 / 任务结束日期 / 关联KR 等）；禁止 "预估 X 天" / "load %" 这种 AI 拍脑袋估算
5. **群 DM 仅 Phase 4 用户 explicit 确认后发 1 次**——其余 phase 无任何 IM 推送

---

## codex 客户端配置

在 codex 客户端 → 自动化 → 新建（或编辑现有），按下表填：

| 字段 | 值 |
|---|---|
| **name** | `OKR 周复盘+规划 · <你的名字> (4-phase single-thread)` |
| **kind** | `cron` |
| **rrule (Asia/Shanghai 周一 09:00)** | `FREQ=WEEKLY;BYDAY=MO;BYHOUR=9;BYMINUTE=0;BYSECOND=0` |
| **rrule (本机 America/Chicago 等 UTC-6 / DST UTC-5)** | DST: `BYDAY=SU;BYHOUR=20`；非 DST: `BYDAY=SU;BYHOUR=19` |
| **model** | `gpt-5.5` |
| **reasoning_effort** | `high` |
| **execution_environment** | `local` |
| **cwd** | `/Users/<your_name>/Documents/<some_project_dir>`（任何已有目录，cron 不依赖具体内容）|
| **status** | `ACTIVE` |
| **prompt** | 复制 [`prompt.md`](prompt.md) 全文粘贴 |

---

## 部署步骤

### 第 1 次部署

1. 打开 codex 客户端 → 自动化功能 → 新建
2. 按上表填字段
3. **prompt 框**：复制 [`prompt.md`](prompt.md) 整段（~13K 字符）粘贴
4. 保存
5. 立即运行 1 次手动验证：
   - 客户端 → automation 详情页右上角点 "立即运行"
   - 预期：Step 0 拉 base 数据后输出 `[GAP REPORT]`（约 1000-1500 字符）
   - 你在 thread 里回复（如 `go` / `重点 A-3` / `skip 推群`）→ codex 进对应 phase

### 之后每周一

cron 自动跑，不用动。每周一上午打开 codex 客户端那个 thread → 看 `[GAP REPORT]` → 回复推进。

---

## Prompt 替换占位符（仅当推广到其他 owner）

如果你不是戴时雨而是别的 owner（如罗国华 / 林军 / 谢静雯），用 prompt 前**只需改 1 处**：

```
ME 预期 = 戴时雨 `ou_ce0e16bb55bcde24078f9a551db3740d`
```

改成你的 open_id。其他全部用 `lark-cli auth status` 实时获取 ME，自动适配你的身份。

> 找你自己 open_id 的方法：
> ```
> lark-cli auth status | jq .userOpenId
> ```

---

## 前置依赖

- ✅ macOS / Linux 终端
- ✅ codex CLI（desktop app 已装）
- ✅ `lark-cli` ≥ 1.0.29
- ✅ `lark-cli auth login --domain minutes,vc,im,docs,base,wiki,contact,calendar` 已授权（用你自己的飞书账号）
- ✅ jq + python3

**不需要装任何 npx skills**——prompt 自包含全部 workflow。

---

## 验证 cron 跑通的 4 个标志

第一次手动 trigger 后：

1. ✅ thread 里看到 `[GAP REPORT]` 段落（约 1000-1500 字，含 ME 身份 + 没做好 + 需要补 + 本周拟做 + 4 个下一步选项）
2. ✅ ME = 你的名字（lark-cli auth status 拿到的 open_id 跟 ME 预期值一致或不一致都会 surface）
3. ✅ `boundary 检查`：本轮没有写 base / 没有发 DM（cron 触发的 Step 0 是纯读 + 准备数据 + 输出报告）
4. ✅ codex automation 客户端 "运行历史记录" 里这次跑标记完成

如果某条不符 → 回到 prompt 检查或反馈给上游（戴时雨）。

---

## 一周后的二次运行

下周一 09:00 cron 自动触发时，**它会在原 thread 继续追加**还是开新 thread？目前 codex 客户端行为：每次 cron 触发是**新 session（同 automation 配置）**，会出现在"运行历史记录"列表里。

**实际工作流建议**：

- 本周一你跟 codex 走了完整 Phase 1 → 4 → done
- 下周一 cron 又触发 → 新的 thread / session
- 你打开新 session，看新 GAP REPORT，又走一遍 4 phase
- 周复一周

如果上周 thread 还没走完（你只回了 Phase 1 就忘了），下周新 thread 是独立的——不会自动续上周的未完决议。要么你抓紧本周内走完，要么手动跨 thread 整理。

---

## 故障 / 反馈

- prompt 里有 hardcoded base/wiki token / chat_id，仅 86lux 飞书租户可用
- 跑出来 GAP REPORT 字符数 ≫ 1500 → prompt 里 0.6 规则没生效，反馈调 prompt
- codex 在 Phase 2/3 直接写 base record 但没等 owner confirm → ownership 规则没生效，反馈

反馈直接找戴时雨 / 群里说。
