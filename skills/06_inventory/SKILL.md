---
name: 06_inventory
version: 0.2.0
description: 86lux Amazon inventory daily. Pulls GERP FBA inventory, counts FBA fulfillable + inbound + Amazon FC transfer stock, writes Feishu Base inventory alert and replenishment detail tables, and sends the group daily report.
metadata:
  requires:
    bins: ["python3", "lark-cli", "jq"]
  tenant: "86lux"
  base_token: "ObmkbXIbSaafOEsD0g9c646XnSc"
  alert_table_id: "tbl2KxctwoJPn2OR"
  replenish_table_id: "tbloGDnlR0ajA1hA"
  group_chat_id: "oc_02610466b18eb80a04dd4fef06b7c178"
---

# 06 库存与物流检查

把积加 `gerp-inventory` 的 FBA 库存全量分页数据，按 `plans/atomic/06_inventory.md`
锁定口径生成两张飞书表：

- 库存预警表 `tbl2KxctwoJPn2OR`：每天 1 行汇总。
- 月度补货建议表 `tbloGDnlR0ajA1hA`：每个 🔴/🟡/🟢/🟣/🆕 MSKU 1 行；⚫僵尸不进明细。

## 口径锁定

- 补货周期 `L = 75` 天，禁止使用积加 `productDeliveryDays`。
- 月度 review + lead time = `105` 天。
- 安全系数 = `1.1`。
- 亚马逊调仓 = 积加 raw 字段 `reservedTransfers`。
- 含在途可售天数 = `(afnFulfillableQuantity + inTransitQty + reservedTransfers) / avgUnitsOrdered30Days`。
- 🔴：有动销且含在途可售天数 `< 75`。
- 🟡：有动销且 `75 <= 含在途可售天数 < 105`。
- 🟣：有货且可售天数 `> 180`，或 `obsoleteRate > 0`，或 180 天以上库龄 `> 0`。
- ⚫：无动销且 `afnFulfillableQuantity == 0`。
- 新品 = 上架 `createTime` < 60 天，或手动排除清单中的待推广 ASIN；不判滞销/僵尸。
- 呆滞 = 可售天数 > 365，或无动销，或日均 30 天 < 0.5；其余 🟣 为库存偏厚。
- 目标库存 = `105 * avgUnitsOrdered30Days * 1.1`。
- 建议补货量 = `max(0, 目标库存 - afnFulfillableQuantity - inTransitQty - reservedTransfers)`。

以上口径来源只允许追溯到 `plans/atomic/06_inventory.md`。

## 运行

```bash
python3 skills/06_inventory/run_inventory.py
```

默认会先用 `+table-list` 查找并删除名为「数据表」且不是两张目标表的默认表壳。
脚本会写两张飞书 Base 表，并向「亚马逊电商部」群发送三角色日报。

只生成 payload、不写飞书：

```bash
python3 skills/06_inventory/run_inventory.py --no-write
```

从已有取数 artifact 重新尝试飞书写入：

```bash
python3 skills/06_inventory/run_inventory.py --from-artifact skills/06_inventory/runs/YYYY-MM-DD.json
```

`--from-artifact` 会使用 artifact 里的 raw rows 按当前脚本口径重新计算 payload，
适合口径修正后回填历史日期。只回填 Base、不发群时加 `--no-report`。

运行 artifact 写入 `skills/06_inventory/runs/YYYY-MM-DD.json`。写飞书成功时还会生成
`YYYY-MM-DD.write_result.json`；写入失败时生成 `YYYY-MM-DD.write_error.json`。

## 外部依赖

- 积加 MCP 认证从 `~/.claude.json` 读取。
- 飞书写入使用 `~/.npm-global/bin/lark-cli base +record-batch-create --as user --json`。
- lark-cli 认证必须能读取本机 keychain。
- 月度补货建议表写入时会确保补充字段存在：
  `亚马逊调仓`（number，已建）、`积加可售量`（number，对应 raw `availableQty`）、
  `站点ASIN映射`（text，对应 raw `parentAsinList`，用于 EU 共享仓映射 DE/FR/ES 等站点）。
- `现有可售` 保持锁定补货口径，对应 raw `afnFulfillableQuantity`；不要把它和
  `availableQty` 混用进补货公式。
