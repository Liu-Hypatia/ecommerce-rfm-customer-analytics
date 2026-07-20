import csv
import sqlite3
from pathlib import Path
from typing import Dict, List


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

CUSTOMERS_CSV = DATA_DIR / "sample_customers.csv"
ORDERS_CSV = DATA_DIR / "sample_orders.csv"


def require_data() -> None:
    missing = [str(p) for p in [CUSTOMERS_CSV, ORDERS_CSV] if not p.exists()]
    if missing:
        raise FileNotFoundError(
            "缺少模拟数据文件，请先运行 `python src/generate_sample_data.py`。"
            + ", ".join(missing)
        )


def load_csv(conn: sqlite3.Connection, table_name: str, csv_path: Path) -> None:
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames or []
        quoted_cols = ", ".join(f'"{c}" TEXT' for c in columns)
        conn.execute(f'DROP TABLE IF EXISTS "{table_name}"')
        conn.execute(f'CREATE TABLE "{table_name}" ({quoted_cols})')
        placeholders = ", ".join("?" for _ in columns)
        conn.executemany(
            f'INSERT INTO "{table_name}" VALUES ({placeholders})',
            ([row[c] for c in columns] for row in reader),
        )
    conn.commit()


def write_query(conn: sqlite3.Connection, query: str, out_path: Path) -> List[Dict]:
    cur = conn.execute(query)
    rows = [dict(zip([col[0] for col in cur.description], row)) for row in cur.fetchall()]
    with out_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return rows


def write_rows(rows: List[Dict], out_path: Path, fieldnames: List[str]) -> None:
    with out_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def rfm_score(values: List[float], value: float, reverse: bool = False) -> int:
    ordered = sorted(values)
    n = len(ordered)
    if n == 0:
        return 1
    rank = sum(1 for v in ordered if v <= value) / n
    score = min(5, max(1, int(rank * 5) + 1))
    return 6 - score if reverse else score


def segment_customer(r: int, f: int, m: int) -> str:
    if r >= 4 and f >= 4 and m >= 4:
        return "高价值用户"
    if f >= 4 and m >= 3:
        return "忠诚用户"
    if r >= 4 and f >= 2:
        return "潜力用户"
    if r <= 2 and (f >= 4 or m >= 4):
        return "流失风险用户"
    if r <= 2 and f <= 2 and m <= 2:
        return "沉睡用户"
    if r >= 4 and f == 1:
        return "新用户"
    return "待培育用户"


def recommendation(segment: str) -> str:
    mapping = {
        "高价值用户": "提供会员权益、新品优先体验和推荐奖励，提升留存与口碑传播。",
        "忠诚用户": "通过会员积分、组合购和交叉销售提升客单价。",
        "潜力用户": "推送个性化优惠券和品类推荐，引导形成稳定复购。",
        "流失风险用户": "设计限时召回活动，优先触达历史消费价值较高的客户。",
        "沉睡用户": "控制高成本投放，测试低成本唤醒消息和基础优惠。",
        "新用户": "通过新客引导、首单后关怀和门槛券促进第二次购买。",
        "待培育用户": "结合生命周期消息和品类偏好标签，提升活跃度和转化率。",
    }
    return mapping[segment]


MONTHLY_KPI_SQL = """
WITH valid_orders AS (
    SELECT
        order_id,
        customer_id,
        substr(order_date, 1, 7) AS order_month,
        CAST(paid_amount AS REAL) AS paid_amount
    FROM orders
    WHERE order_status = '已支付'
),
monthly_customer_orders AS (
    SELECT
        order_month,
        customer_id,
        COUNT(*) AS order_count
    FROM valid_orders
    GROUP BY order_month, customer_id
)
SELECT
    v.order_month AS 月份,
    ROUND(SUM(v.paid_amount), 2) AS GMV,
    COUNT(DISTINCT v.order_id) AS 订单量,
    COUNT(DISTINCT v.customer_id) AS 活跃客户数,
    ROUND(SUM(v.paid_amount) / COUNT(DISTINCT v.order_id), 2) AS 客单价,
    ROUND(
        1.0 * COUNT(DISTINCT CASE WHEN m.order_count > 1 THEN m.customer_id END)
        / COUNT(DISTINCT m.customer_id),
        4
    ) AS 复购率
FROM valid_orders v
JOIN monthly_customer_orders m
    ON v.order_month = m.order_month
   AND v.customer_id = m.customer_id
GROUP BY v.order_month
ORDER BY v.order_month;
"""

RFM_BASE_SQL = """
WITH valid_orders AS (
    SELECT
        order_id,
        customer_id,
        order_date,
        CAST(paid_amount AS REAL) AS paid_amount
    FROM orders
    WHERE order_status = '已支付'
),
max_date AS (
    SELECT MAX(order_date) AS analysis_date
    FROM valid_orders
)
SELECT
    v.customer_id,
    CAST(julianday((SELECT analysis_date FROM max_date)) - julianday(MAX(v.order_date)) AS INTEGER) AS recency_days,
    COUNT(DISTINCT v.order_id) AS frequency,
    ROUND(SUM(v.paid_amount), 2) AS monetary
FROM valid_orders v
GROUP BY v.customer_id;
"""


def main() -> None:
    require_data()
    conn = sqlite3.connect(":memory:")
    load_csv(conn, "customers", CUSTOMERS_CSV)
    load_csv(conn, "orders", ORDERS_CSV)

    monthly_rows = write_query(conn, MONTHLY_KPI_SQL, OUTPUT_DIR / "monthly_kpi.csv")
    rfm_cur = conn.execute(RFM_BASE_SQL)
    rfm_columns = [col[0] for col in rfm_cur.description]
    rfm_rows = [dict(zip(rfm_columns, row)) for row in rfm_cur.fetchall()]

    recency_values = [row["recency_days"] for row in rfm_rows]
    frequency_values = [row["frequency"] for row in rfm_rows]
    monetary_values = [row["monetary"] for row in rfm_rows]

    enriched = []
    for row in rfm_rows:
        r_score = rfm_score(recency_values, row["recency_days"], reverse=True)
        f_score = rfm_score(frequency_values, row["frequency"])
        m_score = rfm_score(monetary_values, row["monetary"])
        segment = segment_customer(r_score, f_score, m_score)
        enriched.append(
            {
                **row,
                "r_score": r_score,
                "f_score": f_score,
                "m_score": m_score,
                "rfm_score": f"{r_score}{f_score}{m_score}",
                "segment": segment,
            }
        )

    customer_path = OUTPUT_DIR / "customer_segments.csv"
    customer_rows = [
        {
            "客户ID": row["customer_id"],
            "最近购买间隔天数": row["recency_days"],
            "购买频次": row["frequency"],
            "累计消费金额": row["monetary"],
            "R评分": row["r_score"],
            "F评分": row["f_score"],
            "M评分": row["m_score"],
            "RFM评分": row["rfm_score"],
            "用户分群": row["segment"],
        }
        for row in enriched
    ]
    write_rows(
        customer_rows,
        customer_path,
        ["客户ID", "最近购买间隔天数", "购买频次", "累计消费金额", "R评分", "F评分", "M评分", "RFM评分", "用户分群"],
    )

    segment_map = {}
    for row in enriched:
        item = segment_map.setdefault(
            row["segment"],
            {"segment": row["segment"], "customers": 0, "gmv": 0.0, "avg_recency": 0.0},
        )
        item["customers"] += 1
        item["gmv"] += row["monetary"]
        item["avg_recency"] += row["recency_days"]

    total_gmv = sum(item["gmv"] for item in segment_map.values())
    summary = []
    for item in segment_map.values():
        summary.append(
            {
                "用户分群": item["segment"],
                "客户数": item["customers"],
                "GMV": round(item["gmv"], 2),
                "GMV占比": round(item["gmv"] / total_gmv, 4),
                "平均最近购买间隔天数": round(item["avg_recency"] / item["customers"], 1),
                "运营建议": recommendation(item["segment"]),
            }
        )
    summary.sort(key=lambda x: x["GMV"], reverse=True)

    summary_path = OUTPUT_DIR / "segment_summary.csv"
    write_rows(
        summary,
        summary_path,
        ["用户分群", "客户数", "GMV", "GMV占比", "平均最近购买间隔天数", "运营建议"],
    )

    print(f"月度 KPI 行数：{len(monthly_rows)}")
    print(f"客户分层行数：{len(enriched)}")
    print(f"分群汇总行数：{len(summary)}")
    print(f"输出目录：{OUTPUT_DIR}")


if __name__ == "__main__":
    main()
