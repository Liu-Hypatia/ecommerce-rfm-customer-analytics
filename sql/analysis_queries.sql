-- 适用于 SQLite 的电商零售分析 SQL。
-- Python 分析脚本会执行等价 SQL，并将结果导出为 CSV。

-- 1. 月度经营指标
WITH valid_orders AS (
    SELECT
        order_id,
        customer_id,
        substr(order_date, 1, 7) AS order_month,
        paid_amount
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
        1.0 * SUM(CASE WHEN m.order_count > 1 THEN 1 ELSE 0 END)
        / COUNT(DISTINCT m.customer_id),
        4
    ) AS 复购率
FROM valid_orders v
JOIN monthly_customer_orders m
    ON v.order_month = m.order_month
   AND v.customer_id = m.customer_id
GROUP BY v.order_month
ORDER BY v.order_month;

-- 2. 客户级 RFM 基础表
WITH valid_orders AS (
    SELECT
        order_id,
        customer_id,
        order_date,
        paid_amount
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

-- 3. 用户分群汇总在 src/run_analysis.py 中完成评分后生成。
