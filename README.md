# 86lux internal codex tools

> 86lux 内部使用的 codex automation + library 集合，覆盖 KR / 项目 / 任务三层在飞书 Base 上的协同写入。
>
> 仓库名 `okr-evidence-compile` 是历史命名（首个 automation 同名），现在范围比当初大了，名字暂时不动。

---

## 仓库分两类

```
daishiyu1991-hub/okr-evidence-compile/
│
├── automations/     ← 每个员工在自己 codex 客户端跑的东西（owner self-run / cron）
│   ├── okr-evidence-compile/
│   ├── amazon-daily-sync/       (v0.4 merged: daily-kb-sync + meeting-update-assistant)
│   └── okr-weekly-ritual/
│
├── skills/          ← 业务运营脚本型 skill
│   └── 06_inventory/
│
└── libraries/       ← 给 automations 调用的共享库 / 决策规则，不直接跑
    └── amazon-base-kb-bridge/
```

---

## Automations 清单（3 个）

每个员工各自在自己电脑 codex 客户端跑，**全部 ownership-scoped**（只能动 `执行人/负责人 == ME` 的 records；新建 task 强制 `执行人=ME`）。

| automation | 触发模式 | 干什么 | 写哪 |
|---|---|---|---|
| **`okr-evidence-compile`** | KR owner 手动或 cron 触发 | 对单条 KR 做 evidence-based compile，分析它有没有 path drift（KR 字段写的 60% 进度是不是真的有 evidence 支撑）| 写 base.KR 的 5 个 audit 字段 + 每 KR 1 个 wiki compile doc append history |
| **`amazon-daily-sync`** (v0.4) | 每天晚上 cron 自动跑 + turn-based 对话 | 扫今天 Feishu 群聊 (3-layer filter) + 会议/妙记 → 抽 candidates → REVIEW QUEUE 引导 owner 决策 → 5 个 routing 之一: 🚦task / 📊项目活动 / 🧮团队项目草稿 / 📝仅audit / ⏭️skip | base 三层 (含 task / 项目活动) + 仅 audit 字段 + wiki 草稿 (team_project_draft) |
| **`okr-weekly-ritual`** | 每周一 9:00 cron | OKR 4-phase 周仪式：复盘上周 + 补建 gap + 规划本周 + 推群 | 写 base 三层 + wiki final 报告 |

> Note: 旧 `amazon-meeting-update-assistant` + `amazon-daily-kb-sync` 已合并到 `amazon-daily-sync` v0.4。两个原 skill 在 commit `3f62398` 之后移除，历史可 git log 看。合并理由：日常每天都有会议+群讨论，分两个 skill 必然重合；合并后单一 skill 走 turn-based routing review，owner 直接决定每条 evidence 归哪个 base 表。

---

## Libraries 清单（1 个）

| library | 干什么 |
|---|---|
| **`amazon-base-kb-bridge`** | base 写入的"决策中枢"（详见下） |

## Skills 清单（1 个）

| skill | 干什么 |
|---|---|
| **`06_inventory`** | 86lux 亚马逊库存日报：读取积加 FBA 库存，计入 FBA 可售 + 在途 + 亚马逊调仓，写库存预警 / 月度补货建议两张飞书 Base，并向亚马逊电商部群发送日报。 |

### `amazon-base-kb-bridge` 是啥？

**它不是自动化、也不直接被 owner 跑**。它是 `amazon-daily-sync` 调用的**底层逻辑库**。

名字有点误导——「kb」容易让人以为它跟 wiki 知识库相关。其实 **kb-bridge 全部跟"飞书 Base 表的写入决策"有关**，跟 wiki 完全无关。

它存了**所有 base 写入相关的规则**，避免 2 个 automation 各自硬编同一套规则：

| 它提供的 | 解决什么问题 |
|---|---|
| **field-map** | 哪个层（KR / 项目 / 任务）能写哪些字段？哪些是 formal（不允许 AI 改）/ audit（AI 可写）/ owner（用来 ownership check）。3 张表共 ~30 个字段的分类规则 |
| **ownership 规则** | 怎么判断 "这条 record 是 ME 的"？KR 看 `执行人[0].id`、长期项目看 `负责人[0].id`、任务看 `执行人[0].id`。新建任务强制 `执行人=ME`。统一在这一处定义 |
| **confidence 规则** | source 证据强弱不同时怎么写？high=直接写 formal 字段；medium=只写辅助字段；low=只写 audit + 标 `待人工确认=true` |
| **conflict 规则** | source 说 "X 已完成" 但 base 里 X.状态 = 未开始，证据又不够强，怎么办？→ 不覆盖 formal 字段，写 audit 注明矛盾，标 `待人工确认=true` |
| **2 个 Python 脚本** | • `build_update_preview.py`：把 source packet + 候选 record → 标准化的 "拟更新预览 JSON" <br>• `detect_state_inconsistencies.py`：跨表跑不一致检测（KR 推进但项目没动 / 项目动了但 KR 没改 / 任务逾期但项目无阻塞 etc）|

### 谁在用它

```
amazon-daily-sync ──→ amazon-base-kb-bridge (ownership / field-map / 脚本)

okr-evidence-compile ──→ 不依赖 (独立运行, 自带 ownership check)
okr-weekly-ritual    ──→ 不依赖 (prompt 自包含全部规则)
```

### 你需不需要装？

| 你是谁 | 要不要装 kb-bridge |
|---|---|
| 用 `okr-evidence-compile` / `okr-weekly-ritual` 的人 | ❌ 不需要——它们独立运行 |
| 用 `amazon-daily-sync` 的人 | ✅ 需要——它会调用 kb-bridge 的 Python 脚本和 field-map |
| 想自己写 base 写入逻辑的人 | ✅ 装它复用规则，避免重新发明 |

---

## Install

### 安装 automations

```bash
# 装单个 (推荐根据需要安装)
npx skills add daishiyu1991-hub/okr-evidence-compile --skill okr-evidence-compile -y
npx skills add daishiyu1991-hub/okr-evidence-compile --skill amazon-daily-sync -y
npx skills add daishiyu1991-hub/okr-evidence-compile --skill amazon-base-kb-bridge -y
npx skills add daishiyu1991-hub/okr-evidence-compile --skill 06_inventory -y

# 一次装所有 automation + library + skill
npx skills add daishiyu1991-hub/okr-evidence-compile --all -y
```

> 装完会到 `~/.agents/skills/<name>/`。codex 自动发现。
> `okr-weekly-ritual` 不用 npx 装（无 SKILL.md frontmatter），见下方"设置 cron"段。

### 设置 `okr-weekly-ritual` cron

不通过 npx skills，是手动复制 prompt 到 codex 客户端"自动化"功能：

📄 [`automations/okr-weekly-ritual/`](automations/okr-weekly-ritual/) 看 README.md

复制 `prompt.md` 整段 → codex 客户端 → 新建 automation → 粘贴 → 设 cron + 保存。

---

## ownership 安全模型（全部 automation 共享）

```
每个员工的 codex 用自己的飞书账号 lark-cli auth
→ ME = lark-cli auth status .userOpenId
→ 所有 base 写入: 必须 record.执行人/负责人 == ME 才允许
→ 新建 task: 强制 执行人 = ME（不能给别人建任务）
→ 跨 owner action item: preview 列出但不写
→ 新建 record: 标 待人工确认=true（owner 在 base UI 二次确认）

→ 4 个 owner 同时跑自己的 automation，写入集自然 disjoint，无冲突
```

---

## License

[MIT](LICENSE)。

skill / automation 本身可复用（lark-cli 命令模板、ownership 检查模式、字段映射）。**hardcoded 的 base / wiki / chat 等 ID 是 86lux 飞书租户专用**——他人 fork 用必须替换。
