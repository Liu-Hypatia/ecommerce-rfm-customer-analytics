# E-commerce RFM Customer Analytics

This repository is a portfolio-ready retail analytics project built for data analyst,
business analyst, BI analyst, and growth analytics internship applications.

The project turns transaction-level e-commerce data into business metrics, customer
segments, and actionable retention recommendations. It is inspired by public RFM
customer segmentation projects on GitHub, but the code, sample data generator, SQL
queries, and analysis outputs in this repository are original.

## Why This Project

Many data analyst internship job descriptions ask for SQL, Python, customer behavior
analysis, dashboard thinking, and business recommendations. This project demonstrates
those skills through a complete workflow:

1. Generate realistic retail order and customer data.
2. Build a SQLite analytical database.
3. Calculate GMV, orders, AOV, repeat purchase rate, and monthly trends.
4. Build customer-level RFM metrics.
5. Segment users into actionable groups.
6. Export analysis tables that can feed Excel, Power BI, Tableau, or Streamlit.

## Repository Structure

```text
ecommerce-rfm-customer-analytics/
  README.md
  .gitignore
  data/
    README.md
  docs/
    resume_bullets_zh.md
  outputs/
    README.md
  sql/
    analysis_queries.sql
  src/
    generate_sample_data.py
    run_analysis.py
```

## Quick Start

This project only uses the Python standard library.

```bash
python src/generate_sample_data.py
python src/run_analysis.py
```

The analysis script writes these files to `outputs/`:

- `monthly_kpi.csv`
- `segment_summary.csv`
- `customer_segments.csv`

## Analysis Logic

### Business Metrics

- GMV: total paid amount
- Orders: valid order count
- Active customers: customers with at least one valid order
- AOV: GMV divided by order count
- Repeat purchase rate: customers with more than one order divided by active customers

### RFM Metrics

- Recency: days since the customer's latest order
- Frequency: number of valid orders
- Monetary: total customer spend

Customers are assigned score bands from 1 to 5. Higher frequency and monetary scores
mean stronger customer value; lower recency means more recent activity and therefore
a higher recency score.

### Segment Rules

- Champions: high recent activity, high frequency, and high monetary value
- Loyal Customers: frequent buyers with solid spending
- Potential Loyalists: recent buyers with moderate frequency
- At Risk: valuable customers who have not purchased recently
- Hibernating: low activity and low value customers
- New Customers: recently acquired but not yet proven

## Example Business Questions

- Which customer segments contribute the most GMV?
- Which segments need retention campaigns first?
- Is revenue growth driven by more orders or higher average order value?
- Which users should receive loyalty benefits, threshold coupons, or win-back offers?

## Resume Positioning

This project is designed to support applications for:

- Data Analyst Intern
- Business Analyst Intern
- BI Analyst Intern
- Growth/Data Operations Intern
- User/Product Analytics Intern

See `docs/resume_bullets_zh.md` for Chinese resume bullet points.

## Reference Projects

These public projects helped shape the project idea and analytical framing:

- https://github.com/yulianthyho/Olist-Ecommerce-RFM-Customer-Segmentation
- https://github.com/rppradhan08/rfm-segmentation
- https://github.com/mustafaa7med/RFM-Based-Customer-Segmentation

