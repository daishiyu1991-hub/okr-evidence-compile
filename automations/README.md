# automations/

> 每个员工在自己 codex 客户端上跑的 automation 集合。全部 ownership-scoped（只动自己 own 的 records）。

---

## 当前 4 个 automation

| 名称 | 触发 | 用途 | 安装方式 |
|---|---|---|---|
| **`okr-evidence-compile`** | owner 手动或 cron 触发，针对单条 KR | KR evidence-based compile（含 path drift 检测） | `npx skills add ... --skill okr-evidence-compile` |
| **`amazon-meeting-update-assistant`** | owner 拿到 1 份会议纪要时手动触发 | 会议讨论 → preview → 写 KR/项目/任务 base 字段 | `npx skills add ... --skill amazon-meeting-update-assistant` |
| **`amazon-daily-kb-sync`** | 每天晚上 cron 自动跑 | 扫今天自己的行动项 → 写 `🚦每周任务` base | `npx skills add ... --skill amazon-daily-kb-sync` |
| **`okr-weekly-ritual`** | 每周一 9:00 cron | OKR 4-phase 周仪式（复盘 / 补建 / 规划 / 推群） | **手动复制 prompt.md** 到 codex 客户端 |

---

## 两种安装方式

| 方式 | 适用 | 怎么装 |
|---|---|---|
| **npx skills add**（推荐）| 前 3 个 automation（有 SKILL.md frontmatter，npx skills 工具能识别）| `npx skills add daishiyu1991-hub/okr-evidence-compile --skill <name> -y` 装到 `~/.agents/skills/<name>/`，codex 自动发现 |
| **手动复制 prompt**（cron 用）| 第 4 个 `okr-weekly-ritual`（纯 prompt 文本，没 SKILL.md frontmatter）| 复制 prompt.md → codex 客户端"自动化"功能 → 新建 → 粘贴 → 设 cron |

为什么 `okr-weekly-ritual` 不用 npx skills 装？
- 它是 **codex cron prompt**，本质上是给 codex 客户端的 automation 配置。
- 没有 SKILL.md frontmatter（不是 skill 格式），无法被 `npx skills add` 识别。
- 只能通过 codex 客户端 UI 手动添加。

---

## 全部 ownership-scoped

每个员工跑自己的 automation，只能动 `执行人/负责人 == ME` 的 records。详见 [root README](../README.md#ownership-安全模型全部-automation-共享)。

---

## 依赖

- `okr-evidence-compile` / `okr-weekly-ritual` — **独立**，无 library 依赖
- `amazon-meeting-update-assistant` / `amazon-daily-kb-sync` — 依赖 [`libraries/amazon-base-kb-bridge/`](../libraries/amazon-base-kb-bridge/)，需要同时装：

```bash
npx skills add daishiyu1991-hub/okr-evidence-compile --skill amazon-base-kb-bridge -y
```

---

## 86lux 推广 onboarding

```bash
# 一次装全部 (4 automation + 1 library)
npx skills add daishiyu1991-hub/okr-evidence-compile --all -y

# lark-cli 装 + 授权 (用自己飞书账号)
npm install -g @larksuite/cli
lark-cli auth login --domain minutes,vc,im,docs,base,wiki,contact,calendar

# okr-weekly-ritual 单独到 codex 客户端配置
# 见 automations/okr-weekly-ritual/README.md
```

每个 owner 30-45 分钟可完成 onboarding。
