# 86lux internal codex skills

> 86lux 内部使用的 codex skill 集合。本仓库 hosts multi-skill collection；每个 skill 在 `skills/<name>/` 自含 `SKILL.md` + `references/` + 必要文件。

仓库名 `okr-evidence-compile` 是历史命名（首个 skill 名同名）。现在内含多个 skill，名字会暂时不动；将来如果再加 skill 会考虑改名或者迁移。

---

## Skills 清单 (v2 — ownership-scoped, multi-user safe)

5 个 skill 一起构成 86lux 在飞书 Base + 知识库上做"OKR 落地 + 项目同步 + 任务追踪"的完整工具链。**全部都是 ownership-scoped**：每个员工只能在 codex 上写自己持有的 record / 自己的页面。

| skill | 类型 | 用途 | 路径 |
|---|---|---|---|
| **okr-evidence-compile** | 用户向 | KR owner 自跑、evidence-based OKR compile，写自己 KR 的 5 个 AI 字段 + 每 KR 1 个 wiki doc append history。严格 ownership 安全（仅本人能跑自己的 KR）+ anti-hallucination + 跨 entry 警示。 | [`skills/okr-evidence-compile/`](skills/okr-evidence-compile/) |
| **amazon-meeting-update-assistant** | 用户向 | 把会议纪要 / 飞书链接 / daily-page / chat 摘要 / 手工 update 转成 Base 字段变更，preview-first 确认流。**v2 加 ownership check**：只能改自己持有的 KR / 项目 / 任务。Cross-owner action items 列出但不写入。 | [`skills/amazon-meeting-update-assistant/`](skills/amazon-meeting-update-assistant/) |
| **amazon-daily-kb-sync** | 用户向 (每日自跑) | 每天扫自己参与的会议 / 群结论 / Base 变更，append 1 entry 到自己专属的 `日会同步日志 · <owner>` doc。同步自己的行动项到 🚦每周任务。周会日附加 7 天自有记录汇总。**v2 per-owner doc，多人并发安全。** | [`skills/amazon-daily-kb-sync/`](skills/amazon-daily-kb-sync/) |
| **amazon-base-kb-bridge** | 底层库 | 共享决策层：field map / ownership check 规则 / confidence rules / inconsistency detection。被 meeting-update-assistant + daily-kb-sync 共用，不直接调。**v2 加 ownership scoping** spec。 | [`skills/amazon-base-kb-bridge/`](skills/amazon-base-kb-bridge/) |
| **feishu-meeting-series-kb** | 底层库 | 通用：处理任何 Feishu 周期性会议系列（周会 / 培训 / 选题 / review）→ 跨 session ledger + 持续维护的 KB。被 daily-kb-sync 用作 meeting discovery 底座。 | [`skills/feishu-meeting-series-kb/`](skills/feishu-meeting-series-kb/) |

### 依赖关系

```
okr-evidence-compile  (独立，仅依赖 lark-cli)
                          
amazon-meeting-update-assistant ─┐
                                  ├──→ amazon-base-kb-bridge  ★ 共享决策 + Python 脚本
amazon-daily-kb-sync ─────────────┘            
                                  │
                                  └──→ feishu-meeting-series-kb  ★ 通用 Feishu 会议底座
```

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
