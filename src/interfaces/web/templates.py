from __future__ import annotations


def build_index_page() -> str:
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>肥胖风险预测系统 · 全流程实验面板</title>
    <style>
        :root {
            --bg: #f5f7fb;
            --card: #ffffff;
            --line: #dbe4f0;
            --text: #0f172a;
            --muted: #475569;
            --primary: #2563eb;
            --primary-soft: #dbeafe;
            --success: #059669;
            --shadow: 0 16px 40px rgba(15, 23, 42, 0.08);
        }
        * { box-sizing: border-box; }
        body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: var(--bg); color: var(--text); }
        .hero { background: linear-gradient(135deg, #0f172a, #1d4ed8); color: #fff; padding: 40px 24px; }
        .hero-inner, .container { max-width: 1280px; margin: 0 auto; }
        .hero p { color: rgba(255,255,255,.84); max-width: 880px; }
        .container { padding: 24px; }
        .card { background: var(--card); border-radius: 18px; box-shadow: var(--shadow); padding: 22px; margin-bottom: 22px; }
        .card h2, .card h3 { margin-top: 0; }
        .grid { display: grid; gap: 16px; }
        .grid.cols-4 { grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); }
        .grid.cols-3 { grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); }
        .metric { padding: 18px; border: 1px solid var(--line); border-radius: 16px; background: #f8fbff; }
        .metric .label { font-size: 13px; color: var(--muted); }
        .metric .value { font-size: 28px; font-weight: 700; margin-top: 8px; }
        .badge { display: inline-block; padding: 6px 10px; border-radius: 999px; background: var(--primary-soft); color: var(--primary); font-size: 12px; font-weight: 700; }
        .section-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
        .subtle { color: var(--muted); font-size: 14px; }
        .table-wrap { overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; min-width: 720px; }
        th, td { border-bottom: 1px solid var(--line); padding: 12px 10px; text-align: left; vertical-align: top; }
        th { background: #f8fafc; font-size: 13px; color: #334155; }
        td { font-size: 14px; }
        .figure-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px; }
        .figure-card { border: 1px solid var(--line); border-radius: 16px; padding: 14px; background: #fff; }
        .figure-card img { width: 100%; border-radius: 12px; background: #fff; }
        .figure-card a { color: var(--primary); text-decoration: none; font-size: 13px; }
        .split { display: grid; grid-template-columns: 1.15fr .85fr; gap: 20px; }
        .form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; }
        label { display: flex; flex-direction: column; gap: 6px; font-size: 14px; color: #334155; }
        input, select, button { font: inherit; }
        input, select { border: 1px solid var(--line); border-radius: 12px; padding: 10px 12px; background: #fff; }
        button { border: none; border-radius: 12px; padding: 12px 18px; background: var(--primary); color: #fff; font-weight: 600; cursor: pointer; }
        button:hover { background: #1d4ed8; }
        pre { background: #0f172a; color: #e2e8f0; border-radius: 14px; padding: 16px; overflow: auto; min-height: 180px; }
        .kv-list { display: grid; gap: 10px; }
        .kv-item { padding: 12px 14px; border-radius: 14px; background: #f8fafc; border: 1px solid var(--line); }
        .empty { padding: 18px; border: 1px dashed #cbd5e1; border-radius: 16px; color: var(--muted); }
        @media (max-width: 980px) { .split { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
<header class="hero">
  <div class="hero-inner">
    <span class="badge">课程设计 · 全流程可视化</span>
    <h1>肥胖风险预测系统实验面板</h1>
    <p>本界面将数据分析、sklearn 训练链路、手搓模型训练链路、参数对比、图表产物和单样本预测整合到同一页面，便于课程演示、答辩汇报和实验复现。</p>
  </div>
</header>
<div class="container">
  <section class="card">
    <div class="section-head">
      <div>
        <h2>一、项目总览</h2>
        <div class="subtle" id="summary-status">正在加载训练摘要...</div>
      </div>
      <div class="badge" id="recommended-badge">等待训练摘要</div>
    </div>
    <div class="grid cols-4" id="summary-metrics"></div>
  </section>

  <section class="card">
    <div class="section-head">
      <div>
        <h2>二、sklearn 与手搓模型总对比</h2>
        <div class="subtle">统一展示四类模型的测试集关键指标，避免训练路线混在一起。</div>
      </div>
    </div>
    <div class="table-wrap">
      <table>
        <thead>
          <tr><th>模型家族</th><th>模型名称</th><th>Accuracy</th><th>Macro Precision</th><th>Macro Recall</th><th>Macro F1</th></tr>
        </thead>
        <tbody id="comparison-body"></tbody>
      </table>
    </div>
  </section>

  <section class="split">
    <div class="card">
      <div class="section-head"><h2>三、优化后参数对比</h2><span class="subtle">按训练家族分开列出最终参数</span></div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>家族</th><th>模型</th><th>参数</th></tr></thead>
          <tbody id="parameter-body"></tbody>
        </table>
      </div>
    </div>
    <div class="card">
      <div class="section-head"><h2>四、训练产物状态</h2><span class="subtle">报告、模型、日志、图表一页汇总</span></div>
      <div class="kv-list" id="artifact-list"></div>
    </div>
  </section>

  <section class="card">
    <div class="section-head"><h2>五、关键图表展示</h2><span class="subtle">自动读取训练产物中的 EDA / 训练曲线 / 总对比图</span></div>
    <div class="figure-grid" id="figure-grid"></div>
  </section>

  <section class="split">
    <div class="card">
      <div class="section-head"><h2>六、单样本预测</h2><span class="subtle">同时输出 sklearn 与手搓模型预测结果</span></div>
      <div class="form-grid">
        <label>性别<select id="gender"><option>Female</option><option>Male</option></select></label>
        <label>年龄<input id="age" type="number" step="0.1" value="24" /></label>
        <label>身高（米）<input id="height_m" type="number" step="0.01" value="1.70" /></label>
        <label>体重（千克）<input id="weight_kg" type="number" step="0.1" value="72" /></label>
        <label>家族肥胖史<select id="family_history_with_overweight"><option value="1">Yes</option><option value="0">No</option></select></label>
        <label>高热量饮食偏好<select id="high_calorie_food_frequency"><option value="1">Yes</option><option value="0">No</option></select></label>
        <label>蔬菜摄入评分<input id="vegetable_intake_score" type="number" step="0.1" value="2.5" /></label>
        <label>每日正餐次数<input id="main_meals_per_day" type="number" step="0.1" value="3" /></label>
        <label>加餐频率<select id="snacking_frequency"><option>Never</option><option selected>Sometimes</option><option>Frequently</option><option>Always</option></select></label>
        <label>是否吸烟<select id="smokes"><option value="0">No</option><option value="1">Yes</option></select></label>
        <label>饮水量（升）<input id="water_intake_liters" type="number" step="0.1" value="2.0" /></label>
        <label>是否进行热量监测<select id="calorie_monitoring"><option value="0">No</option><option value="1">Yes</option></select></label>
        <label>运动评分<input id="physical_activity_score" type="number" step="0.1" value="1.5" /></label>
        <label>电子设备使用评分<input id="technology_use_hours" type="number" step="0.1" value="1.0" /></label>
        <label>饮酒频率<select id="alcohol_consumption"><option>Never</option><option selected>Sometimes</option><option>Frequently</option><option>Always</option></select></label>
        <label>出行方式<select id="transportation_mode"><option>Public_Transportation</option><option>Automobile</option><option>Walking</option><option>Motorbike</option><option>Bike</option></select></label>
      </div>
      <div style="margin-top: 18px;"><button onclick="submitPrediction()">提交预测</button></div>
    </div>
    <div class="card">
      <div class="section-head"><h2>七、预测结果</h2><span class="subtle">建议答辩时重点讲推荐模型结果，再补充对照模型</span></div>
      <pre id="result">等待提交...</pre>
    </div>
  </section>
</div>
<script>
function formatMetric(value) {
  if (typeof value !== 'number') return value ?? '-';
  return value.toFixed(6);
}

function renderSummary(data) {
  const metrics = document.getElementById('summary-metrics');
  const dataset = data.dataset || {};
  const split = dataset.split || {};
  const recommended = data.recommended_model || {};
  const cards = [
    ['样本总数', dataset.sample_count ?? '-'],
    ['类别数', dataset.class_count ?? '-'],
    ['训练 / 验证 / 测试', `${split.train ?? '-'} / ${split.validation ?? '-'} / ${split.test ?? '-'}`],
    ['推荐模型 Macro F1', formatMetric(recommended.macro_f1 ?? '-')],
  ];
  metrics.innerHTML = cards.map(item => `<div class="metric"><div class="label">${item[0]}</div><div class="value">${item[1]}</div></div>`).join('');
  document.getElementById('recommended-badge').textContent = recommended.family ? `推荐：${recommended.family} / ${recommended.name}` : '尚无推荐模型';
  document.getElementById('summary-status').textContent = data.message || `${data.project_name || '项目'} 训练摘要已加载`;
}

function renderComparison(rows) {
  const tbody = document.getElementById('comparison-body');
  if (!rows || rows.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6">暂无训练结果，请先执行训练命令。</td></tr>';
    return;
  }
  tbody.innerHTML = rows.map(row => `
    <tr>
      <td>${row.family}</td>
      <td>${row.name}</td>
      <td>${formatMetric(row.metrics.accuracy)}</td>
      <td>${formatMetric(row.metrics.macro_precision)}</td>
      <td>${formatMetric(row.metrics.macro_recall)}</td>
      <td>${formatMetric(row.metrics.macro_f1)}</td>
    </tr>`).join('');
}

function renderParameters(rows) {
  const tbody = document.getElementById('parameter-body');
  if (!rows || rows.length === 0) {
    tbody.innerHTML = '<tr><td colspan="3">暂无参数结果。</td></tr>';
    return;
  }
  tbody.innerHTML = rows.map(row => `
    <tr>
      <td>${row.family}</td>
      <td>${row.name}</td>
      <td><code>${JSON.stringify(row.parameters)}</code></td>
    </tr>`).join('');
}

function renderArtifacts(artifacts) {
  const container = document.getElementById('artifact-list');
  const entries = Object.entries(artifacts || {});
  if (entries.length === 0) {
    container.innerHTML = '<div class="empty">暂无训练产物。</div>';
    return;
  }
  container.innerHTML = entries.map(([name, files]) => `
    <div class="kv-item">
      <strong>${name}</strong>
      <div class="subtle">文件数：${files.length}</div>
      <div class="subtle">${files.slice(0, 4).join('<br/>') || '暂无文件'}</div>
    </div>`).join('');
}

function renderFigures(artifacts) {
  const figureGrid = document.getElementById('figure-grid');
  const figureFiles = (artifacts && artifacts.figures) ? artifacts.figures.filter(path => /\.(png|svg)$/i.test(path)).slice(0, 8) : [];
  if (figureFiles.length === 0) {
    figureGrid.innerHTML = '<div class="empty">暂无图表，请先执行训练流程。</div>';
    return;
  }
  figureGrid.innerHTML = figureFiles.map(path => `
    <div class="figure-card">
      <div class="subtle" style="margin-bottom:8px;">${path}</div>
      <img src="/artifacts/${path}" alt="${path}" />
      <div style="margin-top:8px;"><a href="/artifacts/${path}" target="_blank">打开原图</a></div>
    </div>`).join('');
}

async function loadDashboard() {
  const response = await fetch('/api/v1/dashboard');
  const payload = await response.json();
  if (!payload.success) {
    document.getElementById('summary-status').textContent = '训练摘要加载失败';
    return;
  }
  const data = payload.data;
  renderSummary(data);
  renderComparison(data.comparison_rows || []);
  renderParameters(data.parameter_tables || []);
  renderArtifacts(data.artifacts || {});
  renderFigures(data.artifacts || {});
}

async function submitPrediction() {
  const payload = {
    gender: document.getElementById('gender').value,
    age: Number(document.getElementById('age').value),
    height_m: Number(document.getElementById('height_m').value),
    weight_kg: Number(document.getElementById('weight_kg').value),
    family_history_with_overweight: Number(document.getElementById('family_history_with_overweight').value),
    high_calorie_food_frequency: Number(document.getElementById('high_calorie_food_frequency').value),
    vegetable_intake_score: Number(document.getElementById('vegetable_intake_score').value),
    main_meals_per_day: Number(document.getElementById('main_meals_per_day').value),
    snacking_frequency: document.getElementById('snacking_frequency').value,
    smokes: Number(document.getElementById('smokes').value),
    water_intake_liters: Number(document.getElementById('water_intake_liters').value),
    calorie_monitoring: Number(document.getElementById('calorie_monitoring').value),
    physical_activity_score: Number(document.getElementById('physical_activity_score').value),
    technology_use_hours: Number(document.getElementById('technology_use_hours').value),
    alcohol_consumption: document.getElementById('alcohol_consumption').value,
    transportation_mode: document.getElementById('transportation_mode').value,
  };
  const response = await fetch('/api/v1/predict', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
  const data = await response.json();
  document.getElementById('result').textContent = JSON.stringify(data, null, 2);
}

loadDashboard();
</script>
</body>
</html>"""
