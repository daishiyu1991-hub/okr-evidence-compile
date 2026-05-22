# Chat Filter — 3-layer 群聊过滤规则

> 目的: 戴时雨在飞书加入 30-40 个群, 全部扫太重. 用 3-layer filter 只扫与"今天 OKR/项目"相关的群 + 群内只取 ME-relevant 消息.

---

## Layer 1: hardcoded allowlist (必扫)

无论其他条件如何, 这些群一定扫:

```yaml
must_scan_chat_ids:
  - "oc_eeed0bff3e18355ab5ae3e3e2d20107f"  # 🚀亚马逊攻坚小分队
  # 后续可添加 OKR review / 产品决策等核心群
```

Owner 可在 prompt 里追加自己的核心群 chat_id.

## Layer 2: auto-discover ME 加入的群 + 过滤

`lark-cli im +list-chats --as user --page-size 100 --format json` 拉全部群, 然后 jq 过滤:

### Include 规则 (任一满足则保留)

- 群 chat_id 在 Layer 1 allowlist 里
- 群名 含 OR-regex: `(OKR|项目|亚马逊|Amazon|选品|PRD|运营|周会|日会)`
- AND 成员数 ≤ 30

### Exclude 规则 (任一满足则跳过)

- 群名 含 OR-regex: `(通知|机器人|财务|HR|公告|活动|生日|社交|外联)`
- 成员数 > 50
- chat_type == "p2p" 且非 ME 主动场景 (一对一无效)
- 系统/服务号 chat

## Layer 3: 群内消息 ME-relevance filter

每个 Layer 1+2 通过的群, 拉今天消息:

```bash
lark-cli im +list-messages --as user \
  --container-id <chat_id> \
  --container-id-type chat \
  --start-time <today_start_ms> \
  --end-time <today_end_ms> \
  --format json
```

对每条 message 保留 if 任一 true:

1. `msg.sender.id == ME` (ME 自己发的)
2. msg.text 含 `@<ME_name>` OR mentions[].id == ME (ME 被 @)
3. msg.text 含 **ME-owned keyword** (动态)

### ME-owned keyword 构建

从 base 拉:

```bash
# ME-owned KR 关键词
lark-cli base +record-list --table-id tblxM7ZfxJt2P4Fl --as user | \
  jq '.data.data[] | select(.执行人[0].id == "<ME>") | .["KR-关键结果"]'

# ME-owned 项目关键词
lark-cli base +record-list --table-id tblOHGg4IA2pY7uh --as user | \
  jq '.data.data[] | select(.负责人[0].id == "<ME>") | .项目名称'

# ME-owned 项目活动关键词
lark-cli base +record-list --table-id tblf54mtW07iPCRL --as user | \
  jq '.data.data[] | select(.执行人[0].id == "<ME>") | .项目活动'
```

然后从 KR/项目/项目活动文本里抽核心词 (去停用词后的 2-4 字短语), 加业务通用词 fallback:

```yaml
business_keyword_fallback:
  - "PRD"
  - "OKR"
  - "Action item"
  - "立项"
  - "决策"
  - "方案"
  - "执行"
  - "推进"
  - "review"
  - "同步"
```

## Performance 估算

| 阶段 | 量级 |
|---|---|
| Layer 1 + 2 后候选群数 | 5-10 个 |
| 每群每天消息数 | 10-50 |
| 总消息数 | 100-300 |
| Layer 3 后 ME-relevant | 30-80 |
| API calls | 1 (list_chats) + 5-10 (list_messages) ≤ 15 |
| 总耗时 | 3-5 分钟 |

完全在飞书 rate limit 内.

## Edge cases

- **ME 不在 allowlist 里任何群** → Layer 2 自动发现接手
- **群名变化** (regex 不命中) → include 用 regex, 兼容性好; 仍可手动加 chat_id 到 allowlist
- **新加入的群** → 下次 cron 自然 pick up
- **大群里 ME 被 @** → Layer 2 跳过大群 → 漏. 接受这个 trade-off (大群 @ 通常不 actionable)
- **跨业务的群** (如 "战略+OKR") → Layer 2 命中 include keyword → 扫

## Config 暴露给 owner

prompt 里允许 owner 直接改:

```yaml
chat_filter_config:
  must_scan_chat_ids: [...]
  include_name_patterns: [...]
  exclude_name_patterns: [...]
  max_member_count: 30
  business_keyword_fallback: [...]
```

每个 owner 跑时可调整自己关心的群范围.
