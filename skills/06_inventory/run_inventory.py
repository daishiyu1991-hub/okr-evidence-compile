#!/usr/bin/env python3
"""06 库存与物流检查：积加取数 -> 口径计算 -> 写飞书 Base."""
import argparse
import datetime as dt
import json
import math
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


BASE_TOKEN = "ObmkbXIbSaafOEsD0g9c646XnSc"
ALERT_TABLE_ID = "tbl2KxctwoJPn2OR"
REPLENISH_TABLE_ID = "tbloGDnlR0ajA1hA"
GROUP_CHAT_ID = "oc_02610466b18eb80a04dd4fef06b7c178"  # 亚马逊电商部群（日报/告警）
LARK = os.environ.get("LARK_CLI", os.path.expanduser("~/.npm-global/bin/lark-cli"))
GERP_BASE = "https://mcpgateway.apist.gerpgo.com/mcp/{ep}/streamable"

# 来源：plans/atomic/06_inventory.md §0/§2/§3。
LEAD_TIME_DAYS = 75
REVIEW_PLUS_LEAD_DAYS = 105
SAFETY_FACTOR = 1.1
SLOW_DAYS = 180
NEW_DAYS = 60  # 上架 < 60 天 = 新品，不判滞销/僵尸（用户口径，按 createTime 判断）
AMAZON_TRANSFER_FIELD = "reservedTransfers"  # 亚马逊 FC 调仓/转仓中库存
REPLENISH_EXTRA_FIELDS = [
    {"name": "亚马逊调仓", "type": "number"},
    {"name": "积加可售量", "type": "number"},
    {"name": "站点ASIN映射", "type": "text"},
]
# 手动排除清单（待推广/特殊处理的 ASIN，不判滞销/僵尸，归🆕）。可随时增删。
MANUAL_EXCLUDE = {"B0GVK9NQ92"}  # 挂烫机米黄：上架超60天但还没推广，先手动排除
# 运输方式 lead time：生产+清关入仓上架固定，头程随方式（用户口径：快船20/慢船30）
PROD_TAIL_DAYS = 44   # 生产 ~32 + 清关入仓上架 ~12
SHIP_FAST_DAYS = 20   # 海运快船头程 → 总 lead 64
SHIP_SLOW_DAYS = 30   # 海运慢船头程 → 总 lead 74


def load_gerp_headers():
    cfg = json.load(open(os.path.expanduser("~/.claude.json")))
    h = cfg["mcpServers"]["gerp"]["headers"]
    return h["X-App-Id"], h["X-App-Key"]


AID, AKEY = load_gerp_headers()


def headers(sid=None):
    h = {
        "X-App-Id": AID,
        "X-App-Key": AKEY,
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if sid:
        h["Mcp-Session-Id"] = sid
    return h


def parse(body):
    body = body.strip()
    if body.startswith("{"):
        return json.loads(body)
    res = None
    for ln in body.splitlines():
        ln = ln.strip()
        if ln.startswith("data:"):
            try:
                res = json.loads(ln[5:].strip())
            except Exception:
                pass
    return res


def post(ep, payload, sid=None):
    req = urllib.request.Request(
        GERP_BASE.format(ep=ep),
        data=json.dumps(payload).encode(),
        headers=headers(sid),
        method="POST",
    )
    try:
        r = urllib.request.urlopen(req, timeout=60)
        return parse(r.read().decode()), r.headers.get("mcp-session-id")
    except urllib.error.HTTPError as e:
        return {"_error": e.code, "body": e.read().decode()}, None


def session(ep, retries=4):
    last = None
    for i in range(retries):
        last, sid = post(
            ep,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "inventory-skill", "version": "1.0"},
                },
            },
        )
        if sid:
            post(ep, {"jsonrpc": "2.0", "method": "notifications/initialized"}, sid)
            return sid
        time.sleep(1.5 * (i + 1))
    raise RuntimeError("GERP session init failed: " + json.dumps(last, ensure_ascii=False)[:600])


def call(ep, sid, tool, args, retries=4):
    res = None
    used_retries = 0
    for i in range(retries):
        res, _ = post(
            ep,
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": tool, "arguments": args},
            },
            sid,
        )
        if res and "result" in res:
            txt = res["result"]["content"][0]["text"]
            return json.loads(txt)[0]["data"], used_retries
        used_retries += 1
        time.sleep(1.5 * (i + 1))
    raise RuntimeError("call failed: " + json.dumps(res, ensure_ascii=False)[:600])


def num(v, default=None):
    if v in (None, "", "无限"):
        return default
    try:
        f = float(v)
    except Exception:
        return default
    if math.isnan(f) or math.isinf(f):
        return default
    return f


def qty(v):
    return num(v, 0.0) or 0.0


def fetch_inventory():
    ep = "gerp-inventory"
    sid = session(ep)
    rows = []
    page = 1
    retried_pages = []
    while True:
        data, used_retries = call(
            ep,
            sid,
            "post_purchase_store_fbaInventory_page_V2",
            {"page": page, "pagesize": 100, "hideZeroQuantity": False},
            retries=4,
        )
        if used_retries:
            retried_pages.append(page)
        rows.extend(data["rows"])
        if page * data["pagesize"] >= data["total"]:
            break
        page += 1
        time.sleep(0.6)
    return rows, retried_pages


def normalize(row):
    afn = qty(row.get("afnFulfillableQuantity"))
    available = qty(row.get("availableQty"))
    in_transit = qty(row.get("inTransitQty"))
    amazon_transfer = qty(row.get(AMAZON_TRANSFER_FIELD))
    supply_with_transfer = afn + in_transit + amazon_transfer
    d30 = qty(row.get("avgUnitsOrdered30Days"))
    d7 = qty(row.get("avgUnitsOrdered7Days"))
    obsolete = qty(row.get("obsoleteRate"))
    age181 = sum(
        qty(row.get(k))
        for k in (
            "invAge181To270Days",
            "invAge271To330Days",
            "invAge331To365Days",
            "invAge365PlusDays",
        )
    )
    sellable_days = None if d30 <= 0 else supply_with_transfer / d30
    target = REVIEW_PLUS_LEAD_DAYS * d30 * SAFETY_FACTOR
    suggested = max(0.0, target - supply_with_transfer)
    wh_name = row.get("warehouseName") or ""
    site = wh_name.split(":")[-1].replace("_FBA", "") if wh_name else (row.get("warehouseCountry") or "?")
    parent_asins = row.get("parentAsinList") or []
    if isinstance(parent_asins, list):
        site_asin_map = " / ".join(str(x) for x in parent_asins if x and "未设置" not in str(x))
    else:
        site_asin_map = str(parent_asins or "")
    return {
        "asin": row.get("asin") or "",
        "msku": row.get("msku") or row.get("sku") or "",
        "site": site,
        "productName": row.get("productName") or "",
        "fulfillmentChannel": row.get("fulfillmentChannel") or "",
        "afnFulfillableQuantity": afn,
        "availableQty": available,
        "inTransitQty": in_transit,
        "amazonTransferQty": amazon_transfer,
        "supplyWithTransferQty": supply_with_transfer,
        "avgUnitsOrdered30Days": d30,
        "avgUnitsOrdered7Days": d7,
        "availableSellableDaysWithTransit": sellable_days,
        "leadTimeDays": LEAD_TIME_DAYS,
        "safetyStock": LEAD_TIME_DAYS * d30,
        "targetInventory": target,
        "suggestedReplenishmentQty": suggested,
        "obsoleteRate": obsolete,
        "age181PlusQty": age181,
        "fbaInventoryLevelHealthStatus": row.get("fbaInventoryLevelHealthStatus") or "-",
        "onHandValue": qty(row.get("onHandValue")),
        "createTime": (row.get("createTime") or "")[:10],
        "siteAsinMap": site_asin_map,
        "raw": row,
    }


def listing_days(create_str, today_d):
    try:
        return (today_d - dt.date.fromisoformat((create_str or "")[:10])).days
    except Exception:
        return 9999


def classify(item):
    # 手动排除(待推广等) 或 新品(上架 < NEW_DAYS 天) → 归🆕，不判滞销/僵尸
    if item.get("asin") in MANUAL_EXCLUDE or item.get("listingDays", 9999) < NEW_DAYS:
        return "NEW"
    sellable = item["avgUnitsOrdered30Days"] > 0 or item["avgUnitsOrdered7Days"] > 0
    days = item["availableSellableDaysWithTransit"]
    is_dead = (not sellable) and item["afnFulfillableQuantity"] == 0
    is_red = sellable and days is not None and days < LEAD_TIME_DAYS
    # 来源：plans/atomic/06_inventory.md §3，在途救援降级。
    if (
        is_red
        and item["afnFulfillableQuantity"] == 0
        and item["inTransitQty"] + item["amazonTransferQty"] >= item["targetInventory"]
    ):
        is_red = False
    is_yellow = sellable and (not is_red) and days is not None and LEAD_TIME_DAYS <= days < REVIEW_PLUS_LEAD_DAYS
    is_slow = (
        (not is_red)
        and (not is_dead)
        and item["availableQty"] > 0
        and (
            (days is not None and days > SLOW_DAYS)
            or item["obsoleteRate"] > 0
            or item["age181PlusQty"] > 0
        )
    )
    if is_red:
        return "R1"
    if is_yellow:
        return "R2"
    if is_dead:
        return "R4"
    if is_slow:
        return "R3"
    if sellable:
        return "OK"
    return ""


def round2(v):
    if v is None:
        return None
    return round(float(v), 2)


def ship_advice(days):
    """按含在途可售天数选运输方式（越紧越快越贵）。慢船74/快船64/空运兜底。"""
    if days is None:
        return "🐢海运慢船"
    if days >= PROD_TAIL_DAYS + SHIP_SLOW_DAYS:
        return "🐢海运慢船"
    if days >= PROD_TAIL_DAYS + SHIP_FAST_DAYS:
        return "🚢海运快船"
    return "✈️空运/加急"


def fmt_days(v):
    return "无限" if v is None else str(round2(v))


def detail_line(item):
    return (
        f"ASIN={item['asin']} | 站点={item['site']} | MSKU={item['msku']} | 品名={item['productName']} | "
        f"日均30d={round2(item['avgUnitsOrdered30Days'])} | "
        f"含在途可售天数={fmt_days(item['availableSellableDaysWithTransit'])} | "
        f"现有可售={round2(item['afnFulfillableQuantity'])} | 在途={round2(item['inTransitQty'])} | "
        f"亚马逊调仓={round2(item['amazonTransferQty'])}"
    )


def is_real_site_row(r):
    # 过滤无关站点占位行 + 亚马逊自动库存(plans/atomic/06_inventory.md §站点维度）
    if (r.get("msku") or "").startswith("Amazon.Found"):
        return False
    return (qty(r.get("afnFulfillableQuantity")) > 0 or qty(r.get("availableQty")) > 0
            or qty(r.get("avgUnitsOrdered30Days")) > 0 or qty(r.get("avgUnitsOrdered7Days")) > 0)


def build_outputs(rows, today):
    items = [normalize(r) for r in rows if is_real_site_row(r)]
    today_d = dt.date.fromisoformat(today)
    buckets = {"R1": [], "R2": [], "R3": [], "R4": [], "OK": [], "NEW": []}
    for item in items:
        item["listingDays"] = listing_days(item.get("createTime"), today_d)
        cls = classify(item)
        item["class"] = cls
        if cls:
            buckets[cls].append(item)
    status_label = {"R1": "🔴紧急", "R2": "🟡必补", "R3": "🟣滞销", "OK": "🟢健康", "NEW": "🆕新品"}

    def is_dead_slow(it):
        # 呆滞：可售>365天 或 无动销 或 日均<0.5（用户口径）；其余 R3 为「库存偏厚」
        days = it["availableSellableDaysWithTransit"]
        return days is None or days > 365 or it["avgUnitsOrdered30Days"] < 0.5

    def status_of(it):
        if it["class"] == "R3":
            return "🪦呆滞" if is_dead_slow(it) else "📦偏厚"
        return status_label.get(it["class"], it["class"])

    replenishment = []
    # 有动销品 + 新品（🔴🟡🟢🟣🆕）；⚫无动销僵尸不进明细
    for item in buckets["R1"] + buckets["R2"] + buckets["NEW"] + buckets["OK"] + buckets["R3"]:
        replenishment.append(
            {
                "日期": today,
                "ASIN": item["asin"],
                "站点": item["site"],
                "MSKU": item["msku"],
                "品名": item["productName"],
                "状态": status_of(item),
                "日均30d": round2(item["avgUnitsOrdered30Days"]),
                "含在途可售天数": round2(item["availableSellableDaysWithTransit"]),
                "现有可售": round2(item["afnFulfillableQuantity"]),
                "积加可售量": round2(item["availableQty"]),
                "在途": round2(item["inTransitQty"]),
                "亚马逊调仓": round2(item["amazonTransferQty"]),
                "站点ASIN映射": item["siteAsinMap"],
                "库存货值(RMB)": round2(item["onHandValue"]),
                "补货周期天数": item["leadTimeDays"],
                "安全库存": round2(item["safetyStock"]),
                "目标库存": round2(item["targetInventory"]),
                "建议补货量": round2(item["suggestedReplenishmentQty"]),
                "运输建议": (ship_advice(item["availableSellableDaysWithTransit"])
                            if (item.get("suggestedReplenishmentQty") or 0) > 0 else "—"),
            }
        )
    r3 = buckets["R3"]
    dead = [i for i in r3 if is_dead_slow(i)]
    thick = [i for i in r3 if not is_dead_slow(i)]
    dead_value = round2(sum(i["onHandValue"] for i in dead))
    thick_value = round2(sum(i["onHandValue"] for i in thick))
    alert_fields = {
        "日期": today,
        "今日是否安全": "❌" if buckets["R1"] else "✅",
        "紧急断货数": len(buckets["R1"]),
        "必补数": len(buckets["R2"]),
        "滞销数": len(buckets["R3"]),
        "呆滞数": len(dead),
        "僵尸数": len(buckets["R4"]),
        "新品数": len(buckets["NEW"]),
        "呆滞货值(RMB)": dead_value,
        "偏厚货值(RMB)": thick_value,
        "滞销压货值(RMB)": round2(dead_value + thick_value),
        "紧急断货明细": "\n".join(detail_line(i) for i in buckets["R1"]) or "无",
        "呆滞明细": "\n".join(detail_line(i) for i in dead) or "无",
        "状态码": "DONE",
    }
    return items, buckets, alert_fields, replenishment


def run_lark(args):
    proc = subprocess.run(args, text=True, capture_output=True, check=False)
    try:
        parsed = json.loads(proc.stdout)
    except Exception:
        parsed = None
    if proc.returncode != 0:
        raise RuntimeError(
            json.dumps(
                {
                    "cmd": args,
                    "returncode": proc.returncode,
                    "stdout": proc.stdout,
                    "stderr": proc.stderr,
                },
                ensure_ascii=False,
            )
        )
    return parsed if parsed is not None else proc.stdout


def cleanup_default_table():
    tables = run_lark(
        [
            LARK,
            "base",
            "+table-list",
            "--base-token",
            BASE_TOKEN,
            "--as",
            "user",
        ]
    )
    deleted = []
    for table in tables.get("data", {}).get("items", []) if isinstance(tables, dict) else []:
        name = table.get("name") or table.get("table_name")
        table_id = table.get("table_id") or table.get("id")
        if name == "数据表" and table_id not in (ALERT_TABLE_ID, REPLENISH_TABLE_ID):
            deleted.append(
                run_lark(
                    [
                        LARK,
                        "base",
                        "+table-delete",
                        "--base-token",
                        BASE_TOKEN,
                        "--table-id",
                        table_id,
                        "--as",
                        "user",
                        "--yes",
                    ]
                )
            )
    return deleted


def batch_create_records(table_id, rows):
    if not rows:
        return {"ok": True, "records": []}
    fields = list(rows[0].keys())
    return run_lark(
        [
            LARK,
            "base",
            "+record-batch-create",
            "--base-token",
            BASE_TOKEN,
            "--table-id",
            table_id,
            "--as",
            "user",
            "--json",
            json.dumps(
                {"fields": fields, "rows": [[row.get(field) for field in fields] for row in rows]},
                ensure_ascii=False,
            ),
        ]
    )


def read_records(table_id, limit=200):
    return run_lark(
        [
            LARK,
            "base",
            "+record-list",
            "--base-token",
            BASE_TOKEN,
            "--table-id",
            table_id,
            "--as",
            "user",
            "--format",
            "json",
            "--limit",
            str(limit),
        ]
    )


def ensure_replenish_extra_fields():
    data = run_lark(
        [
            LARK,
            "base",
            "+field-list",
            "--base-token",
            BASE_TOKEN,
            "--table-id",
            REPLENISH_TABLE_ID,
            "--as",
            "user",
        ]
    )
    existing = {
        field.get("name")
        for field in data.get("data", {}).get("fields", [])
        if isinstance(field, dict)
    }
    created = []
    for field in REPLENISH_EXTRA_FIELDS:
        if field["name"] in existing:
            continue
        created.append(
            run_lark(
                [
                    LARK,
                    "base",
                    "+field-create",
                    "--base-token",
                    BASE_TOKEN,
                    "--table-id",
                    REPLENISH_TABLE_ID,
                    "--as",
                    "user",
                    "--json",
                    json.dumps(field, ensure_ascii=False),
                ]
            )
        )
    return created


def print_summary(rows, buckets, alert_fields, replenishment, retried_pages):
    print(f"# 06 库存与物流检查 — {alert_fields['日期']}")
    print(f"数据源：积加 gerp-inventory · 扫描 {len(rows)} 个 SKU")
    print(f"状态码：{alert_fields['状态码']}")
    if retried_pages:
        print(f"重试页：{retried_pages}")
    print(
        "计数："
        f"🔴 {len(buckets['R1'])} · 🟡 {len(buckets['R2'])} · "
        f"🟣 {len(buckets['R3'])} · ⚫ {len(buckets['R4'])}"
    )
    print(f"今日是否安全：{alert_fields['今日是否安全']}")
    print(f"月度补货建议行数：{len(replenishment)}")
    print("\n[库存预警表 payload]")
    print(json.dumps(alert_fields, ensure_ascii=False, indent=2))
    print("\n[月度补货建议表 payload]")
    print(json.dumps(replenishment, ensure_ascii=False, indent=2))


def build_report(buckets, alert_fields):
    """三角色库存日报(管理层/运营/物流)文本。"""
    from collections import defaultdict

    def ohv(i):
        return float((i.get("raw") or {}).get("onHandValue") or 0)

    def unit(i):
        r = i.get("raw") or {}
        q = float(r.get("onHandQty") or 0)
        return ohv(i) / q if q else 0

    def nm(i):
        return (i.get("raw") or {}).get("productName") or i.get("msku") or ""

    def dstr(i):
        d = i["availableSellableDaysWithTransit"]
        return "∞" if d is None else round(d)

    def is_dead(i):
        d = i["availableSellableDaysWithTransit"]
        return d is None or d > 365 or i["avgUnitsOrdered30Days"] < 0.5

    R1, R2, R3 = buckets["R1"], buckets["R2"], buckets["R3"]
    OK, NEW = buckets.get("OK", []), buckets.get("NEW", [])
    dead = [i for i in R3 if is_dead(i)]
    thick = [i for i in R3 if not is_dead(i)]
    restock = [i for i in (R1 + R2 + OK + R3) if (i.get("suggestedReplenishmentQty") or 0) > 0]
    restock_cost = sum(i["suggestedReplenishmentQty"] * unit(i) for i in restock)
    transfer_qty = sum(float(i.get("amazonTransferQty") or 0) for i in (R1 + R2 + NEW + OK + R3))
    cat = defaultdict(float)
    for i in R3:
        cat[(i.get("raw") or {}).get("categoryName") or "其他"] += ohv(i)
    declining = [i for i in (R1 + R2 + OK)
                 if i["avgUnitsOrdered30Days"] > 1
                 and i["avgUnitsOrdered7Days"] < i["avgUnitsOrdered30Days"] * 0.7]
    dead_value = sum(ohv(i) for i in dead)
    thick_value = sum(ohv(i) for i in thick)
    L = [f"📦 86lux 库存日报 · {alert_fields['日期']}", "—" * 14]
    L.append("👔【管理层】")
    L.append(f"今日：{'❌不安全' if R1 else '✅安全'}  🔴紧急{len(R1)} · 🟡必补{len(R2)} · 🪦呆滞{len(dead)} · 📦偏厚{len(thick)}")
    L.append(f"💰滞销压货 ¥{dead_value + thick_value:,.0f}"
             f"（🪦该清 ¥{dead_value:,.0f} / 📦偏厚 ¥{thick_value:,.0f}）")
    L.append(f"💸本月需补 ¥{restock_cost:,.0f}（{len(restock)} 个 SKU）")
    L.append(f"🔁亚马逊调仓已计入可售天数：{transfer_qty:,.0f} 件")
    L.append("📂品类压货 Top3：" + " / ".join(f"{k} ¥{v:,.0f}" for k, v in sorted(cat.items(), key=lambda x: -x[1])[:3]))
    L.append("")
    L.append("🎯【运营】")
    L.append("🪦该清呆滞 Top5：")
    for i in sorted(dead, key=lambda x: -ohv(x))[:5]:
        L.append(f"　· {nm(i)} {i['site']} 压¥{ohv(i):,.0f} 可售{dstr(i)}天")
    if declining:
        L.append("📉动销下滑(7日<30日)：" + " / ".join(f"{nm(i)}{i['site']}" for i in declining[:5]))
    L.append("")
    L.append("📦【物流/采购】")
    L.append(f"本月补货清单（共 {len(restock)} 个，¥{restock_cost:,.0f}）：")
    for i in sorted(restock, key=lambda x: -(x["suggestedReplenishmentQty"] * unit(x)))[:8]:
        ship = ship_advice(i["availableSellableDaysWithTransit"])
        L.append(f"　· {nm(i)} {i['site']} 补 {round(i['suggestedReplenishmentQty'])} 件 {ship}")
    L.append("[👉 全部明细 / 补货清单(飞书今日视图)](https://wg9k4pnk2o.feishu.cn/base/ObmkbXIbSaafOEsD0g9c646XnSc?table=tbloGDnlR0ajA1hA&view=vewmeaHJYi)")
    return "\n".join(L)


def send_feishu(chat_id, text):
    # 用 markdown(飞书转 post 富文本)，[文字](url) 才能点；text 消息里的链接点不动
    return run_lark([LARK, "im", "+messages-send", "--chat-id", chat_id,
                     "--markdown", text, "--as", "user"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-write", action="store_true", help="只取数和生成 payload，不写飞书")
    parser.add_argument("--artifact-dir", default="skills/06_inventory/runs")
    parser.add_argument("--from-artifact", help="从已有 artifact JSON 写飞书，不重新取积加")
    parser.add_argument("--no-report", action="store_true", help="不发飞书日报到群")
    args = parser.parse_args()

    today = dt.date.today().isoformat()
    artifact_dir = Path(args.artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    if args.from_artifact:
        artifact = json.loads(Path(args.from_artifact).read_text())
        today = artifact.get("today") or artifact.get("alert_payload", {}).get("日期") or today
        retried_pages = artifact.get("retried_pages", [])
        rows = [item.get("raw", item) for item in artifact.get("items", [])]
        items, buckets, alert_fields, replenishment = build_outputs(rows, today)
        if retried_pages:
            alert_fields["状态码"] = "DONE_WITH_CONCERNS"
        artifact = {
            "today": today,
            "source_rows_count": artifact.get("source_rows_count", len(rows)),
            "retried_pages": retried_pages,
            "items": items,
            "alert_payload": alert_fields,
            "replenishment_payload": replenishment,
        }
        (artifact_dir / f"{today}.json").write_text(json.dumps(artifact, ensure_ascii=False, indent=2))
    else:
        rows, retried_pages = fetch_inventory()
        items, buckets, alert_fields, replenishment = build_outputs(rows, today)
        if retried_pages:
            alert_fields["状态码"] = "DONE_WITH_CONCERNS"
        artifact = {
            "today": today,
            "source_rows_count": len(rows),
            "retried_pages": retried_pages,
            "items": items,
            "alert_payload": alert_fields,
            "replenishment_payload": replenishment,
        }
        (artifact_dir / f"{today}.json").write_text(json.dumps(artifact, ensure_ascii=False, indent=2))

    print_summary(rows, buckets, alert_fields, replenishment, retried_pages)
    if args.no_write:
        return 0

    try:
        cleanup_result = cleanup_default_table()
        field_create_result = ensure_replenish_extra_fields()
        alert_write = batch_create_records(ALERT_TABLE_ID, [alert_fields])
        repl_write = batch_create_records(REPLENISH_TABLE_ID, replenishment)
        alert_readback = read_records(ALERT_TABLE_ID)
        repl_readback = read_records(REPLENISH_TABLE_ID)
    except Exception as exc:
        alert_fields["状态码"] = "BLOCKED"
        (artifact_dir / f"{today}.write_error.json").write_text(str(exc))
        print("\n[飞书写入失败]")
        print(str(exc))
        print("完成状态码：BLOCKED")
        return 2

    write_result = {
        "cleanup_result": cleanup_result,
        "field_create_result": field_create_result,
        "alert_write": alert_write,
        "replenishment_write": repl_write,
        "alert_readback": alert_readback,
        "replenishment_readback": repl_readback,
        "alert_payload": alert_fields,
        "replenishment_payload": replenishment,
    }
    (artifact_dir / f"{today}.write_result.json").write_text(
        json.dumps(write_result, ensure_ascii=False, indent=2)
    )
    print("\n[库存预警表实际写入记录]")
    print(json.dumps(alert_write, ensure_ascii=False, indent=2))
    print("\n[月度补货建议表实际写入记录]")
    print(json.dumps(repl_write, ensure_ascii=False, indent=2))
    print("\n[库存预警表回读]")
    print(json.dumps(alert_readback, ensure_ascii=False, indent=2))
    print("\n[月度补货建议表回读]")
    print(json.dumps(repl_readback, ensure_ascii=False, indent=2))
    print(f"完成状态码：{alert_fields['状态码']}")

    if not args.no_report:
        try:
            report = build_report(buckets, alert_fields)
            send_feishu(GROUP_CHAT_ID, report)
            print("\n[日报已发飞书群]")
        except Exception as exc:
            print(f"\n[日报发群失败] {exc}")
            try:
                send_feishu(GROUP_CHAT_ID, f"🚨 库存日报发送异常：{exc}")
            except Exception:
                pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
