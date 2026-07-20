# 电商零售 RFM 用户分层与经营分析项目

这是一个面向数据分析、商业分析、BI 分析、用户增长分析实习岗位的作品集项目。

项目从电商交易明细数据出发，完成数据生成、数据清洗、SQL 指标计算、RFM 用户分层和运营策略输出，展示从“原始订单数据”到“可执行业务建议”的完整分析流程。

本项目参考了 GitHub 上公开的电商 RFM 用户分层项目思路，但代码、模拟数据生成逻辑、SQL 查询、分析流程和输出结果均为原创实现。

## 项目亮点

很多数据分析实习岗位会要求 SQL、Python、用户行为分析、指标体系、看板思维和业务建议能力。本项目覆盖这些核心要求：

1. 使用 Python 生成模拟电商客户与订单数据。
2. 使用 SQLite 构建轻量级分析数据库。
3. 计算 GMV、订单量、客单价、活跃用户数、复购率和月度趋势。
4. 基于 Recency、Frequency、Monetary 构建客户 RFM 指标。
5. 将客户划分为高价值用户、忠诚用户、潜力用户、流失风险用户等群体。
6. 输出可接入 Excel、Power BI、Tableau 或 Streamlit 的分析结果表。

## 项目结构

```text
ecommerce-rfm-customer-analytics/
  README.md
  .gitignore
  data/
    README.md
    sample_customers.csv
    sample_orders.csv
  docs/
    resume_bullets_zh.md
  outputs/
    README.md
    monthly_kpi.csv
    segment_summary.csv
    customer_segments.csv
  sql/
    analysis_queries.sql
  src/
    generate_sample_data.py
    run_analysis.py
```

## 快速运行

本项目只依赖 Python 标准库，不需要额外安装第三方包。

```bash
python src/generate_sample_data.py
python src/run_analysis.py
```

运行后会在 `outputs/` 目录生成：

- `monthly_kpi.csv`：月度 GMV、订单量、活跃用户、客单价和复购率
- `segment_summary.csv`：用户分群规模、GMV 贡献和运营建议
- `customer_segments.csv`：客户级 RFM 指标、评分和分群标签

## 分析逻辑

### 经营指标

- GMV：有效订单实付金额总和
- 订单量：已支付订单数量
- 活跃用户数：当月至少产生一笔有效订单的客户数
- 客单价：GMV / 订单量
- 复购率：当月下单超过 1 次的客户数 / 当月活跃客户数

### RFM 指标

- Recency：距离最近一次购买的天数
- Frequency：有效购买次数
- Monetary：累计消费金额

客户会根据 RFM 三个维度分别打 1 到 5 分。购买越近，R 分越高；购买频次越高，F 分越高；消费金额越高，M 分越高。

### 用户分群规则

- 高价值用户：近期活跃、购买频次高、消费金额高
- 忠诚用户：购买频次高，消费贡献稳定
- 潜力用户：近期活跃，但购买频次和消费金额仍有提升空间
- 流失风险用户：历史价值较高，但近期未购买
- 沉睡用户：活跃度和消费贡献均较低
- 新用户：近期新增，尚未形成稳定复购

## 可回答的业务问题

- 哪些用户群体贡献了最多 GMV？
- 哪些用户应该优先做召回或留存运营？
- 收入增长主要来自订单量提升，还是客单价提升？
- 哪些用户适合发会员权益、门槛券、品类推荐或限时召回券？

## 简历适配方向

这个项目适合用于投递：

- 数据分析实习生
- 商业分析实习生
- BI 分析实习生
- 用户/产品数据分析实习生
- 增长分析/数据运营实习生

中文简历项目描述见：`docs/resume_bullets_zh.md`

## 参考项目

以下公开项目帮助确定了 RFM 分析主题和业务分析框架：

- https://github.com/yulianthyho/Olist-Ecommerce-RFM-Customer-Segmentation
- https://github.com/rppradhan08/rfm-segmentation
- https://github.com/mustafaa7med/RFM-Based-Customer-Segmentation

