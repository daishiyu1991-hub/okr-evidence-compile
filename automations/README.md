# Codex Automations

> 86lux 内部 **codex 客户端 automation prompt** 集合（不是 npx skills add 安装的 skill）。

---

## automations vs skills 区别

| 维度 | `skills/` | `automations/`（本目录）|
|---|---|---|
| **如何安装** | `npx skills add daishiyu1991-hub/okr-evidence-compile --skill <name> -y` 装到 `~/.agents/skills/` | **手动复制粘贴 prompt 到 codex 客户端** "自动化" 功能里 |
| **运行入口** | 通过 `codex exec --skill <name>` 或对话里 invoke | codex cron 自动触发 + thread 内对话 |
| **更新机制** | `npx skills update <name>` 一键拉新版 | 手动复制新 prompt 覆盖 codex 客户端配置 |
| **典型用例** | 一次性任务（如 evidence-compile 单 KR） | 定时周仪式（如每周一 OKR 复盘+规划）|
| **跨员工分发** | npx skills add 命令 | 每个 owner 复制 prompt 到自己 codex 客户端 |

---

## 当前 automation 清单

| 名称 | 触发时间 | 用途 | 路径 |
|---|---|---|---|
| **okr-weekly-ritual** | 每周一 09:00 Asia/Shanghai | OKR 4-phase 周仪式：复盘上周 → 补建 gap → 规划本周 → 推群同步 | [`okr-weekly-ritual/`](okr-weekly-ritual/) |

---

## 如何用

每个 automation 子目录下有 2 个文件：

- **`README.md`** — 用法说明 / codex 客户端配置 / 部署步骤
- **`prompt.md`** — 纯 prompt 文本（直接复制粘贴到 codex 客户端 "自动化" → 新建/编辑 → prompt 框里）

---

## 86lux Onboarding（其他 owner 部署）

每个 owner（罗国华 / 林军 / 谢静雯）在自己 codex 客户端：

1. clone 或浏览本仓库 → 进 `automations/<name>/`
2. 看 `README.md` 知道用法
3. 复制 `prompt.md` 内容
4. codex 客户端 → 自动化 → 新建 → 粘贴 + 改 cron 设置 → 保存
5. 等定时触发，或手动"立即运行"测试

> ⚠️ Prompt 里有 hardcoded `ME 预期 = 戴时雨 ou_ce0e16bb55bcde24078f9a551db3740d`。其他 owner 用前要改成自己的 open_id（运行时其实会用 `lark-cli auth status` 实时取，但预期值用来 sanity check）。

---

## 后续会加进来的 automation（roadmap）

暂未添加，按需补：

- `amazon-daily-kb-sync-owner` —— per-owner 每日 base 写入 task（每个 owner 在自己电脑跑）

如要这个 prompt，可以从主仓库的设计文档（`/Users/daishiyu/Documents/automation-*.md`）拉出。

> Note: **每日日会 wiki 沉淀 + render base view** 是 CEO 账号在自己 codex 客户端独立管理的 automation，**不打包分发**到本仓库——员工不需要跑。
