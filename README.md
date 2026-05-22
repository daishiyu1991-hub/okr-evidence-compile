# okr-evidence-compile

> 86lux internal codex skill for **evidence-based OKR compile**.

Each KR owner runs this skill on their own machine to compile their own KR records, based on real-world evidence in the 86lux 团队管理 Base (projects / tasks / meetings / weekly reports). The skill detects when KR field values (like a self-reported "60% progress") **lack supporting evidence**, flags `path_drift`, and refuses to invent progress numbers. Output goes to both the base record's 5 AI-maintenance fields AND a dedicated Feishu wiki doc.

**This skill is private and internal to 86lux**: hard-coded with 86lux Base token, wiki space, and node IDs.

---

## Install

### Option A — via `npx skills` (recommended)

```bash
# install for both codex + claude-code
npx skills add daishiyu1991-hub/okr-evidence-compile -y

# or scope to current project
npx skills add daishiyu1991-hub/okr-evidence-compile -p
```

This puts the skill under `~/.agents/skills/okr-evidence-compile/`. Both codex and Claude Code will discover it automatically.

### Option B — manual clone (fallback)

```bash
git clone https://github.com/daishiyu1991-hub/okr-evidence-compile.git ~/.codex/skills/okr-evidence-compile
```

### Required tools on your machine

- `lark-cli` (≥ 1.0.29) — install: `npm install -g @larksuite/cli`
- `jq` — install: `brew install jq`
- `python3` — usually preinstalled on macOS
- `date` — usually preinstalled

Verify with:

```bash
lark-cli doctor
jq --version
python3 --version
```

---

## One-time onboarding (per employee)

```bash
# 1. authenticate lark-cli with your own Feishu account
lark-cli auth login

# verify your identity is captured correctly
lark-cli auth status | jq -r '.userName + " · " + .userOpenId'
# expected: <your name> · ou_xxxxxxxxxxxxxxx

# 2. confirm the skill is installed (run after Option A or B above)
ls ~/.agents/skills/okr-evidence-compile/    # or ~/.codex/skills/okr-evidence-compile/
# expected: SKILL.md  references/  README.md  LICENSE
```

---

## Use

### Basic run

```bash
codex exec --skill okr-evidence-compile \
  --params '{"record_id":"<your KR record_id>"}' \
  --skip-git-repo-check
```

The skill will:

1. Locate the KR record in the 86lux 👤个人 OKR table (`tblxM7ZfxJt2P4Fl`)
2. **Ownership check**: verify the current `lark-cli` user is the KR's 执行人. **Aborts** if mismatch (unless `force_ownership_bypass=true`).
3. Pull all linked evidence (projects / tasks / team KR / meetings / weekly reports)
4. Compile via Claude API → output: path alignment classification + path drift detection + abstract + raw JSON
5. Approval gate (CEO manual mode): present the compile JSON, wait for OK
6. Create or update the KR's dedicated Feishu wiki doc under the `OKR AI 编译记录` node
7. Write back 5 AI maintenance fields to the base record
8. Verify by reading back

### How to find your KR record_id

```bash
lark-cli base +record-search \
  --base-token GxaobEQtqaOwFZsB5wTcC33Rnl7 \
  --table-id tblxM7ZfxJt2P4Fl \
  --as user \
  --json '{"keyword":"<keyword from your KR text>","search_fields":["KR-关键结果"],"limit":5}' \
  --format json | jq '.data.record_id_list'
```

### Common params

| param | required | default | semantics |
|---|---|---|---|
| `record_id` | yes | — | 👤个人 OKR record_id to compile |
| `auto_approve` | no | `false` | Skip approval gate (only for Hermes cron) |
| `evidence_lookback_weeks` | no | `4` | How far back to scan 会议纪要 / 周报 |
| `force_ownership_bypass` | no | `false` | Skip ownership check (CEO audit / Hermes only) |

---

## What gets written

### Base table `tblxM7ZfxJt2P4Fl` (👤个人 OKR) — 5 fields per run

| 字段 | what skill writes |
|---|---|
| AI编译摘要 | ≤80 字 abstract |
| 最近更新原因 | `evidence-based compile. confidence=... path_drift=... off_path_ratio=...` |
| 最近更新时间 | execution timestamp |
| 最近更新来源 | URL to the KR's wiki compile doc |
| 待人工确认 | `true` if `path_drift=true` or `confidence=low` |

**Never written**: 状态, 进度, 优先级, 执行人, 关联字段, 其他.

### Wiki doc per KR — created or appended

Located under `亚马逊目标管理与会议沟通沉淀 / 01 目标与项目管理 / OKR AI 编译记录 / <auto-named doc>`.

Doc structure:
- **Header** (KR / base record source link)
- **👤 当前结论** (human-readable conclusion, snapshot)
- **当前状态 snapshot (latest)** (semi-structured metadata)
- **Compile history**, sorted by time descending:
  - Each entry has **👤 结论 (人读版)** (现状 / 怎么办 / 为什么)
  - And **机器读结构** (摘要 / Evidence classifications 表 / 缺失警示 / Raw JSON)

---

## Result types (3 honest outcomes)

The skill returns one of three result classes — each is a valid, honest output:

- **A · evidence 充足 + path 对齐**: AI returns an evidence-cited progress inference (`path_alignment_score` high, `path_drift=false`).
- **B · evidence 缺失**: linked records empty / weeklies empty / meetings have no relevant content. Skill reports the gap honestly and refuses to invent. **This is high-signal output** — it surfaces "no underlying evidence" as the root cause of empty AI fields.
- **C · evidence 有但 path drift**: linked records exist but most are off-topic (off_path_ratio > 30%). Skill prefixes summary with `⚠️ path drift warning` and lists the off_path record_ids.

---

## Anti-hallucination rules (strict)

See `references/anti-hallucination.md` for the 6 hard rules. Key ones:

1. AI cannot cite any `record_id` not in the raw lark-cli evidence pool
2. No invented numbers / progress / decisions / status
3. If evidence missing: must output `缺失警示` honestly, no padding
4. If `path_drift=true`: must output `进度推断=null`, no specific %
5. abstract ≤ 80 字 (base field), full version ≤ 200 字 (doc)
6. Ownership mismatch → ABSOLUTE write gate (no doc create, no base writeback)

---

## File layout

```
okr-evidence-compile/
├── SKILL.md                                # frontmatter + Purpose + Workflow
├── references/
│   ├── okr-compile-flow.md                  # exact lark-cli commands + Claude prompt + writeback schema
│   ├── doc-template.md                      # wiki doc markdown template + 👤 结论 generation rule
│   └── anti-hallucination.md                # 6 hard rules + self-check checklist
├── README.md                                 # this file
├── LICENSE                                   # MIT
└── .gitignore
```

---

## License

MIT — see [LICENSE](LICENSE).

This skill is part of 86lux's internal toolkit. The skill itself (lark-cli command templates, prompt engineering, doc structure) is MIT-licensed and reusable. The hard-coded base / wiki / node IDs are specific to 86lux's Feishu tenant; forks intending other tenants must replace these constants.
