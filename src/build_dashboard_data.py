import csv
import json
from collections import defaultdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
DASHBOARD_DIR = PROJECT_ROOT / "dashboard"
DASHBOARD_DIR.mkdir(exist_ok=True)


def read_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def money(value: float) -> float:
    return round(value, 2)


def build_dashboard_data():
    monthly = read_csv(OUTPUT_DIR / "monthly_kpi.csv")
    segments = read_csv(OUTPUT_DIR / "segment_summary.csv")
    orders = read_csv(DATA_DIR / "sample_orders.csv")
    customers = read_csv(DATA_DIR / "sample_customers.csv")

    valid_orders = [row for row in orders if row["order_status"] == "已支付"]

    category_map = defaultdict(lambda: {"GMV": 0.0, "订单量": 0})
    channel_map = defaultdict(lambda: {"GMV": 0.0, "客户数": 0})
    region_map = defaultdict(lambda: {"客户数": 0})
    month_category_map = defaultdict(lambda: defaultdict(float))
    customer_spend = defaultdict(float)

    customer_lookup = {row["customer_id"]: row for row in customers}

    for customer in customers:
        region_map[customer["region"]]["客户数"] += 1
        channel_map[customer["signup_channel"]]["客户数"] += 1

    for order in valid_orders:
        amount = float(order["paid_amount"])
        month = order["order_date"][:7]
        category = order["category"]
        customer_id = order["customer_id"]
        customer = customer_lookup.get(customer_id, {})
        channel = customer.get("signup_channel", "未知")

        category_map[category]["GMV"] += amount
        category_map[category]["订单量"] += 1
        channel_map[channel]["GMV"] += amount
        month_category_map[month][category] += amount
        customer_spend[customer_id] += amount

    category_summary = [
        {"品类": key, "GMV": money(value["GMV"]), "订单量": value["订单量"]}
        for key, value in category_map.items()
    ]
    category_summary.sort(key=lambda x: x["GMV"], reverse=True)

    channel_summary = [
        {"注册渠道": key, "GMV": money(value["GMV"]), "客户数": value["客户数"]}
        for key, value in channel_map.items()
    ]
    channel_summary.sort(key=lambda x: x["GMV"], reverse=True)

    region_summary = [
        {"地区": key, "客户数": value["客户数"]}
        for key, value in region_map.items()
    ]
    region_summary.sort(key=lambda x: x["客户数"], reverse=True)

    top_customers = [
        {"客户ID": key, "累计消费金额": money(value)}
        for key, value in customer_spend.items()
    ]
    top_customers.sort(key=lambda x: x["累计消费金额"], reverse=True)
    top_customers = top_customers[:10]

    months = sorted({row["月份"] for row in monthly})
    categories = [row["品类"] for row in category_summary]
    monthly_category = [
        {
            "月份": month,
            **{category: money(month_category_map[month].get(category, 0.0)) for category in categories},
        }
        for month in months
    ]

    data = {
        "monthlyKpi": monthly,
        "segmentSummary": segments,
        "categorySummary": category_summary,
        "channelSummary": channel_summary,
        "regionSummary": region_summary,
        "monthlyCategory": monthly_category,
        "topCustomers": top_customers,
        "meta": {
            "project": "电商零售 RFM 用户分层与经营分析项目",
            "generatedFrom": ["data/sample_orders.csv", "data/sample_customers.csv", "outputs/*.csv"],
        },
    }

    out = DASHBOARD_DIR / "data.js"
    with out.open("w", encoding="utf-8") as f:
        f.write("window.DASHBOARD_DATA = ")
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write(";\n")
    print(f"已生成看板数据：{out}")


if __name__ == "__main__":
    build_dashboard_data()

