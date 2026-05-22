# libraries/

> 共享 library，被 [`automations/`](../automations/) 里的 automation 调用。**不直接由员工跑**，是底层逻辑层。

---

## 1 个 library: `amazon-base-kb-bridge`

详细说明见 [root README 的"Libraries 清单"](../README.md#libraries-清单1-个)。

简单说：

- **它是什么**：飞书 Base 表写入的"决策中枢"，集中存放 field-map / ownership 规则 / confidence 规则 / conflict 规则 + 2 个 Python 脚本
- **名字误导**：「kb」容易让人以为是 wiki 知识库，实际跟 wiki 完全无关，只跟 base 表的写入有关
- **谁在用**：`amazon-meeting-update-assistant` + `amazon-daily-kb-sync`
- **谁不用**：`okr-evidence-compile` + `okr-weekly-ritual` 都是独立运行的，不依赖它

### 安装

```bash
npx skills add daishiyu1991-hub/okr-evidence-compile --skill amazon-base-kb-bridge -y
```

装到 `~/.agents/skills/amazon-base-kb-bridge/`。一般跟着 `amazon-meeting-update-assistant` 或 `amazon-daily-kb-sync` 一起装就行。
