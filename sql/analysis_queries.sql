-- SQLite-compatible analytical SQL for the synthetic retail dataset.
-- The Python analysis script executes equivalent SQL and exports the results.

-- 1. Monthly KPI
WITH valid_orders AS (
    SELECT
        order_id,
        customer_id,
        substr(order_date, 1, 7) AS order_month,
        paid_amount
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
        1.0 * SUM(CASE WHEN m.order_count > 1 THEN 1 ELSE 0 END)
        / COUNT(DISTINCT m.customer_id),
        4
    ) AS repeat_purchase_rate
FROM valid_orders v
JOIN monthly_customer_orders m
    ON v.order_month = m.order_month
   AND v.customer_id = m.customer_id
GROUP BY v.order_month
ORDER BY v.order_month;

-- 2. Customer-level RFM base table
WITH valid_orders AS (
    SELECT
        order_id,
        customer_id,
        order_date,
        paid_amount
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

-- 3. Segment summary is produced in src/run_analysis.py after score assignment.

