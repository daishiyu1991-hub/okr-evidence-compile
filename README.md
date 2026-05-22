# 86lux internal codex skills

> 86lux 内部使用的 codex skill 集合。本仓库 hosts multi-skill collection；每个 skill 在 `skills/<name>/` 自含 `SKILL.md` + `references/` + 必要文件。

仓库名 `okr-evidence-compile` 是历史命名（首个 skill 名同名）。现在内含多个 skill，名字会暂时不动；将来如果再加 skill 会考虑改名或者迁移。

---

## Skills 清单 (v3 — 职责清晰分离：wiki vs base)

5 个 skill 构成 86lux 在飞书 Base + 知识库上的工具链。**核心设计原则：feishu-meeting-series-kb 独占 wiki 写入，其他 amazon-* skills 独占 base 表写入**。

| skill | 类型 | wiki 写 | base 写 | 用途 |
|---|---|---|---|---|
| **feishu-meeting-series-kb** | wiki 沉淀 | ✅ **唯一负责** | ❌ | 总结日会/周会 + 跨 session KB → 飞书 wiki |
| **okr-evidence-compile** | 用户向 (KR owner self-run) | ✅ per-KR compile doc | ✅ KR 自己的 5 AI 字段 | KR evidence-based compile + 跨 entry 警示 |
| **amazon-meeting-update-assistant** | 用户向 (单次手动) | ❌ | ✅ KR / 项目 / 任务 三层 | 会议纪要 → base 字段变更，preview-confirm |
| **amazon-daily-kb-sync** | 用户向 (每日自跑) | ❌ | ✅ 自己的 🚦每周任务 + KR/项目 audit | 扫今天 evidence → 同步自己的行动项到 base |
| **amazon-base-kb-bridge** | 底层库 | ❌ | ❌ | ownership 规则 / field map / 决策层 (被 amazon-* 调用) |

### 全部 ownership-scoped

每个员工只能在 codex 上写自己持有的 record：

- `KR.执行人 == ME` 才允许写
- `项目.负责人 == ME` 才允许写
- `任务.执行人 == ME` 才允许更新；新建任务强制 `执行人 = ME`
- 跨 owner action item → preview 列出但不真写

### 依赖关系

```
feishu-meeting-series-kb   (独立，wiki only)
                                 ↑ read-only by daily-kb-sync if accessible

okr-evidence-compile  (独立，KR-specific wiki doc + base)

amazon-meeting-update-assistant ─┐
                                  ├──→ amazon-base-kb-bridge  (ownership + scripts)
amazon-daily-kb-sync ─────────────┘
```

### 一句话决策树（怎么选 skill）

- 要把今天日会 / 周会的内容**沉淀到飞书 wiki 文档** → **`feishu-meeting-series-kb`**
- 要把自己 KR 的进度做 evidence-based compile（含 path drift 检测） → **`okr-evidence-compile`**
- 拿到一份会议纪要 / 链接，想**手动**把它转成 base 字段变更 → **`amazon-meeting-update-assistant`**
- 每天**自动**扫自己的 action items 同步到 🚦每周任务 → **`amazon-daily-kb-sync`**
- 写自己的脚本想复用 ownership / field 决策规则 → **`amazon-base-kb-bridge`** (库)

---

## Automations（codex 客户端定时自动化）

跟 skills 不同——这是直接复制粘贴到 codex 客户端 "自动化" 功能里的 prompt 文本，**不通过 `npx skills add` 安装**。详见 [`automations/`](automations/)。

| Automation | 触发 | 用途 |
|---|---|---|
| **okr-weekly-ritual** | 每周一 09:00 Asia/Shanghai cron | OKR 4-phase 周仪式：复盘上周 → 补建 gap → 规划本周 → 推群同步 |

部署方式：进 [`automations/okr-weekly-ritual/`](automations/okr-weekly-ritual/) 看 `README.md`，复制 `prompt.md` 粘到 codex 客户端。

---

## Install

### 装单个 skill（推荐）

```bash
# okr-evidence-compile（KR owner 用）
npx skills add daishiyu1991-hub/okr-evidence-compile --skill okr-evidence-compile -y

# amazon-meeting-update-assistant（会议 / 项目 update 用）
npx skills add daishiyu1991-hub/okr-evidence-compile --skill amazon-meeting-update-assistant -y
```

### 一次装所有

```bash
npx skills add daishiyu1991-hub/okr-evidence-compile --all -y
```

### 项目本地装（不全局）

加 `-p` flag：

```bash
npx skills add daishiyu1991-hub/okr-evidence-compile --skill okr-evidence-compile -p
```

### 手动 clone（fallback）

```bash
git clone https://github.com/daishiyu1991-hub/okr-evidence-compile.git /tmp/oec
# 任选其一拷贝
cp -R /tmp/oec/skills/okr-evidence-compile ~/.agents/skills/
cp -R /tmp/oec/skills/amazon-meeting-update-assistant ~/.agents/skills/
rm -rf /tmp/oec
```

---

## Repo 结构

```
okr-evidence-compile/
├── README.md                                # this file (collection 入口)
├── LICENSE                                  # MIT，全仓适用
├── .gitignore
└── skills/
    ├── okr-evidence-compile/
    │   ├── SKILL.md                         # 含 frontmatter (name / version / metadata)
    │   ├── README.md                        # install / onboarding / 字段写入说明
    │   └── references/
    │       ├── okr-compile-flow.md          # exact lark-cli 命令 + Step 4 compile spec + 写回 schema
    │       ├── doc-template.md              # wiki doc markdown 模板 + 跨 entry 警示规则
    │       └── anti-hallucination.md        # 6 条 anti-hallucination 硬规则
    └── amazon-meeting-update-assistant/
        ├── SKILL.md
        ├── agents/openai.yaml
        ├── references/
        │   ├── interaction-contract.md
        │   └── writeback-checklist.md
        ├── templates/
        │   └── confirmation_preview.md
        └── scripts/
```

---

## 共同前提条件

两个 skill 都要求：

- `lark-cli` (≥ 1.0.29) — `npm install -g @larksuite/cli`
- `jq` — `brew install jq`
- `python3` — 一般 macOS 自带
- 自己飞书账号 `lark-cli auth login` 登录

---

## License

[MIT](LICENSE) — 见根目录 LICENSE。

skill 本身可复用（lark-cli 命令模板、prompt engineering、文档结构）。**hardcoded 的 base / wiki / node ID 是 86lux 飞书租户专用**，他人 fork 用必须替换。
