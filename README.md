# 86lux internal codex skills

> 86lux 内部使用的 codex skill 集合。本仓库 hosts multi-skill collection；每个 skill 在 `skills/<name>/` 自含 `SKILL.md` + `references/` + 必要文件。

仓库名 `okr-evidence-compile` 是历史命名（首个 skill 名同名）。现在内含多个 skill，名字会暂时不动；将来如果再加 skill 会考虑改名或者迁移。

---

## Skills 清单

| skill | 用途 | 路径 | 文档 |
|---|---|---|---|
| **okr-evidence-compile** | Evidence-based OKR compiler for 86lux 团队管理 Base. KR owner 自跑、自动从飞书 base 拉关联 evidence (projects / tasks / meetings / weeklies)、做 path 对齐分类、检测 path drift、写回 5 个 AI 字段 + 飞书 wiki doc append history。**严格 ownership 安全**（仅本人能跑自己的 KR）+ anti-hallucination。 | [`skills/okr-evidence-compile/`](skills/okr-evidence-compile/) | [README](skills/okr-evidence-compile/README.md) |
| **amazon-meeting-update-assistant** | 把 Amazon 会议纪要 / 飞书链接 / daily-page 链接 / chat 摘要 / 手工 project update 转成 Base 字段变更，含 preview-first 确认流、source traceability、跨 KR + 长期项目 + 任务 三层 audit 写入。 | [`skills/amazon-meeting-update-assistant/`](skills/amazon-meeting-update-assistant/) | (SKILL.md 内嵌) |

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
