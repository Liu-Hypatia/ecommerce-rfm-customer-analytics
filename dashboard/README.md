# BI 看板说明

该目录包含一个纯前端静态 BI 看板，用于展示电商零售经营指标、品类贡献、用户分群和运营建议。

## 打开方式

推荐在项目根目录启动本地服务：

```bash
python -m http.server 8000
```

然后访问：

```text
http://localhost:8000/dashboard/
```

也可以将仓库开启 GitHub Pages 后直接在线访问。

## 数据来源

看板数据由 `src/build_dashboard_data.py` 从以下文件生成：

- `data/sample_orders.csv`
- `data/sample_customers.csv`
- `outputs/monthly_kpi.csv`
- `outputs/segment_summary.csv`
- `outputs/customer_segments.csv`

重新生成完整数据和看板数据：

```bash
python src/generate_sample_data.py
python src/run_analysis.py
python src/build_dashboard_data.py
```

