const data = window.DASHBOARD_DATA;

const colors = ["#146c94", "#2b8a3e", "#b7791f", "#8f3f71", "#577590", "#c8553d", "#3a7ca5"];

const yuan = new Intl.NumberFormat("zh-CN", {
  style: "currency",
  currency: "CNY",
  maximumFractionDigits: 0,
});

const number = new Intl.NumberFormat("zh-CN");
const pct = new Intl.NumberFormat("zh-CN", { style: "percent", maximumFractionDigits: 1 });

const monthSelect = document.getElementById("monthSelect");
const segmentSelect = document.getElementById("segmentSelect");

function toNum(value) {
  return Number.parseFloat(value || 0);
}

function svgEl(tag, attrs = {}) {
  const el = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const [key, value] of Object.entries(attrs)) {
    el.setAttribute(key, value);
  }
  return el;
}

function mountSvg(targetId, width = 760, height = 270) {
  const target = document.getElementById(targetId);
  target.innerHTML = "";
  const svg = svgEl("svg", { viewBox: `0 0 ${width} ${height}`, role: "img" });
  target.appendChild(svg);
  return svg;
}

function xScale(index, count, left, right) {
  if (count <= 1) return left;
  return left + (index * (right - left)) / (count - 1);
}

function yScale(value, min, max, top, bottom) {
  if (max === min) return bottom;
  return bottom - ((value - min) * (bottom - top)) / (max - min);
}

function initControls() {
  const months = data.monthlyKpi.map((row) => row["月份"]);
  monthSelect.innerHTML = months.map((m) => `<option value="${m}">${m}</option>`).join("");
  monthSelect.value = months[months.length - 1];

  const segments = ["全部用户", ...data.segmentSummary.map((row) => row["用户分群"])];
  segmentSelect.innerHTML = segments.map((s) => `<option value="${s}">${s}</option>`).join("");
}

function selectedMonthRow() {
  return data.monthlyKpi.find((row) => row["月份"] === monthSelect.value) || data.monthlyKpi.at(-1);
}

function selectedSegmentRow() {
  const selected = segmentSelect.value;
  if (selected === "全部用户") return null;
  return data.segmentSummary.find((row) => row["用户分群"] === selected);
}

function renderKpis() {
  const row = selectedMonthRow();
  const segment = selectedSegmentRow();
  const grid = document.getElementById("kpiGrid");
  const segmentNote = segment ? `${segment["用户分群"]}贡献 ${pct.format(toNum(segment["GMV占比"]))}` : "全部用户口径";

  const items = [
    ["GMV", yuan.format(toNum(row["GMV"])), `${row["月份"]} 月度实付金额`],
    ["订单量", number.format(toNum(row["订单量"])), "已支付订单"],
    ["活跃客户数", number.format(toNum(row["活跃客户数"])), "当月至少购买一次"],
    ["客单价", yuan.format(toNum(row["客单价"])), "GMV / 订单量"],
    ["复购率", pct.format(toNum(row["复购率"])), segmentNote],
  ];

  grid.innerHTML = items
    .map(
      ([label, value, note]) => `
        <article class="kpi">
          <div class="label">${label}</div>
          <div class="value">${value}</div>
          <div class="note">${note}</div>
        </article>
      `,
    )
    .join("");
}

function renderTrendChart() {
  const rows = data.monthlyKpi;
  const svg = mountSvg("trendChart", 860, 270);
  const left = 54;
  const right = 830;
  const top = 18;
  const bottom = 218;
  const values = rows.map((row) => toNum(row["GMV"]));
  const max = Math.max(...values) * 1.08;

  for (let i = 0; i <= 4; i += 1) {
    const y = top + ((bottom - top) * i) / 4;
    svg.appendChild(svgEl("line", { x1: left, x2: right, y1: y, y2: y, class: "grid-line" }));
  }

  const points = rows.map((row, index) => [xScale(index, rows.length, left, right), yScale(toNum(row["GMV"]), 0, max, top, bottom)]);
  const linePath = points.map(([x, y], index) => `${index === 0 ? "M" : "L"} ${x} ${y}`).join(" ");
  const areaPath = `${linePath} L ${right} ${bottom} L ${left} ${bottom} Z`;
  svg.appendChild(svgEl("path", { d: areaPath, class: "area" }));
  svg.appendChild(svgEl("path", { d: linePath, class: "line" }));

  points.forEach(([x, y], index) => {
    const row = rows[index];
    svg.appendChild(svgEl("circle", { cx: x, cy: y, r: 4, class: "dot" }));
    if (index % 2 === 0 || index === rows.length - 1) {
      const label = svgEl("text", { x, y: 246, "text-anchor": "middle", class: "chart-label" });
      label.textContent = row["月份"].slice(5);
      svg.appendChild(label);
    }
  });

  const yLabel = svgEl("text", { x: left, y: 12, class: "chart-label" });
  yLabel.textContent = "GMV 趋势";
  svg.appendChild(yLabel);
}

function renderBarChart(targetId, rows, labelKey, valueKey, barClass = "bar") {
  const svg = mountSvg(targetId, 560, 270);
  const left = 120;
  const right = 530;
  const top = 18;
  const rowHeight = 34;
  const max = Math.max(...rows.map((row) => toNum(row[valueKey])), 1);

  rows.slice(0, 7).forEach((row, index) => {
    const y = top + index * rowHeight;
    const width = (toNum(row[valueKey]) / max) * (right - left);
    const label = svgEl("text", { x: 0, y: y + 18, class: "chart-label" });
    label.textContent = row[labelKey];
    svg.appendChild(label);
    svg.appendChild(svgEl("rect", { x: left, y, width: Math.max(width, 2), height: 20, rx: 4, class: barClass }));
    const value = svgEl("text", { x: left + width + 8, y: y + 15, class: "chart-value" });
    value.textContent = valueKey.includes("GMV") || valueKey.includes("金额") ? yuan.format(toNum(row[valueKey])) : number.format(toNum(row[valueKey]));
    svg.appendChild(value);
  });
}

function renderSegmentChart() {
  renderBarChart("segmentChart", data.segmentSummary, "用户分群", "GMV", "bar");
}

function renderCategoryChart() {
  renderBarChart("categoryChart", data.categorySummary, "品类", "GMV", "bar alt");
}

function renderChannelChart() {
  renderBarChart("channelChart", data.channelSummary, "注册渠道", "GMV", "bar warn");
}

function renderTopCustomerChart() {
  renderBarChart("topCustomerChart", data.topCustomers, "客户ID", "累计消费金额", "bar");
}

function renderSegmentTable() {
  const selected = segmentSelect.value;
  const rows = selected === "全部用户" ? data.segmentSummary : data.segmentSummary.filter((row) => row["用户分群"] === selected);
  const body = document.getElementById("segmentTable");
  body.innerHTML = rows
    .map(
      (row) => `
        <tr>
          <td>${row["用户分群"]}</td>
          <td>${number.format(toNum(row["客户数"]))}</td>
          <td>${yuan.format(toNum(row["GMV"]))}</td>
          <td>${pct.format(toNum(row["GMV占比"]))}</td>
          <td>${row["平均最近购买间隔天数"]} 天</td>
          <td>${row["运营建议"]}</td>
        </tr>
      `,
    )
    .join("");
}

function renderAll() {
  renderKpis();
  renderTrendChart();
  renderSegmentChart();
  renderCategoryChart();
  renderChannelChart();
  renderTopCustomerChart();
  renderSegmentTable();
}

initControls();
renderAll();

monthSelect.addEventListener("change", renderAll);
segmentSelect.addEventListener("change", renderAll);

