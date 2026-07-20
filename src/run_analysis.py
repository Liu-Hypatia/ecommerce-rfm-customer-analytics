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
            "Missing generated data files. Run `python src/generate_sample_data.py` first. "
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
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return rows


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
        return "Champions"
    if f >= 4 and m >= 3:
        return "Loyal Customers"
    if r >= 4 and f >= 2:
        return "Potential Loyalists"
    if r <= 2 and (f >= 4 or m >= 4):
        return "At Risk"
    if r <= 2 and f <= 2 and m <= 2:
        return "Hibernating"
    if r >= 4 and f == 1:
        return "New Customers"
    return "Needs Nurture"


def recommendation(segment: str) -> str:
    mapping = {
        "Champions": "Offer loyalty benefits, early access, and referral rewards.",
        "Loyal Customers": "Use membership points and cross-sell bundles to increase basket size.",
        "Potential Loyalists": "Send personalized coupons and category recommendations.",
        "At Risk": "Launch win-back campaigns with limited-time offers.",
        "Hibernating": "Reduce high-cost campaigns; test low-cost reactivation messages.",
        "New Customers": "Guide first repeat purchase with onboarding and threshold coupons.",
        "Needs Nurture": "Use lifecycle messaging and product preference tagging.",
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
    WHERE order_status = 'paid'
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
    v.order_month,
    ROUND(SUM(v.paid_amount), 2) AS gmv,
    COUNT(DISTINCT v.order_id) AS orders,
    COUNT(DISTINCT v.customer_id) AS active_customers,
    ROUND(SUM(v.paid_amount) / COUNT(DISTINCT v.order_id), 2) AS aov,
    ROUND(
        1.0 * COUNT(DISTINCT CASE WHEN m.order_count > 1 THEN m.customer_id END)
        / COUNT(DISTINCT m.customer_id),
        4
    ) AS repeat_purchase_rate
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
    WHERE order_status = 'paid'
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
    with customer_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(enriched[0].keys()))
        writer.writeheader()
        writer.writerows(enriched)

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
                "segment": item["segment"],
                "customers": item["customers"],
                "gmv": round(item["gmv"], 2),
                "gmv_share": round(item["gmv"] / total_gmv, 4),
                "avg_recency_days": round(item["avg_recency"] / item["customers"], 1),
                "recommendation": recommendation(item["segment"]),
            }
        )
    summary.sort(key=lambda x: x["gmv"], reverse=True)

    summary_path = OUTPUT_DIR / "segment_summary.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary[0].keys()))
        writer.writeheader()
        writer.writerows(summary)

    print(f"Monthly KPI rows: {len(monthly_rows)}")
    print(f"Customer segment rows: {len(enriched)}")
    print(f"Segment summary rows: {len(summary)}")
    print(f"Outputs written to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
