from __future__ import annotations

import json
from typing import Any, Dict


def build_index_page(dashboard: Dict[str, Any]) -> str:
    dashboard_json = json.dumps(dashboard, ensure_ascii=False)
    sample_fields_json = json.dumps(dashboard.get('sample_fields', []), ensure_ascii=False)
    training_modes_json = json.dumps(dashboard.get('available_training_modes', []), ensure_ascii=False)
    template = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>肥胖风险预测系统 · 本地 Web 控制台</title>
  <style>
    :root {{
      --bg: #f3f6fb;
      --panel: #ffffff;
      --line: #dbe4f0;
      --text: #102033;
      --muted: #55657a;
      --primary: #2563eb;
      --primary-soft: #dbeafe;
      --success: #059669;
      --warning: #b45309;
      --shadow: 0 12px 30px rgba(16, 32, 51, 0.08);
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: var(--bg); color: var(--text); }}
    a {{ color: inherit; text-decoration: none; }}
    .topbar {{
      position: sticky; top: 0; z-index: 20;
      backdrop-filter: blur(10px);
      background: rgba(243, 246, 251, 0.92);
      border-bottom: 1px solid var(--line);
    }}
    .topbar-inner {{
      max-width: 1400px; margin: 0 auto; padding: 16px 20px;
      display: flex; gap: 16px; align-items: center; justify-content: space-between; flex-wrap: wrap;
    }}
    .brand h1 {{ margin: 0; font-size: 22px; }}
    .brand .subtle {{ color: var(--muted); font-size: 13px; margin-top: 4px; }}
    .nav {{ display: flex; gap: 10px; flex-wrap: wrap; }}
    .nav a {{
      display: inline-flex; align-items: center; gap: 8px;
      padding: 10px 14px; border-radius: 999px; background: #fff; border: 1px solid var(--line);
      box-shadow: var(--shadow); font-size: 14px;
    }}
    .nav a:hover {{ border-color: #b6c7e4; }}
    .shell {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
    .section {{ margin-bottom: 18px; }}
    .section-head {{
      display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap;
      margin-bottom: 12px;
    }}
    .section-title {{ margin: 0; font-size: 18px; }}
    .section-note {{ color: var(--muted); font-size: 13px; }}
    .panel {{
      background: var(--panel); border: 1px solid var(--line); border-radius: 12px;
      box-shadow: var(--shadow); padding: 16px;
    }}
    .metric-grid {{ display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); }}
    .metric {{
      padding: 14px; border-radius: 10px; border: 1px solid var(--line); background: #f8fbff;
      min-height: 92px;
    }}
    .metric .label {{ color: var(--muted); font-size: 13px; }}
    .metric .value {{ margin-top: 8px; font-size: 22px; font-weight: 700; word-break: break-word; }}
    .status-row {{ display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); margin-top: 12px; }}
    .pill {{
      display: inline-flex; align-items: center; gap: 8px; padding: 8px 12px; border-radius: 999px;
      background: var(--primary-soft); color: var(--primary); font-size: 13px; font-weight: 700;
    }}
    .muted {{ color: var(--muted); }}
    .grid-two {{ display: grid; gap: 14px; grid-template-columns: 1.1fr 0.9fr; }}
    .grid-three {{ display: grid; gap: 14px; grid-template-columns: 1fr 1fr 1fr; }}
    .table-wrap {{ overflow-x: auto; }}
    table {{ width: 100%; border-collapse: collapse; min-width: 720px; }}
    th, td {{ border-bottom: 1px solid var(--line); padding: 11px 10px; text-align: left; vertical-align: top; }}
    th {{ font-size: 13px; color: #38506d; background: #f8fafc; }}
    td {{ font-size: 14px; }}
    .chip-row {{ display: flex; gap: 8px; flex-wrap: wrap; }}
    .chip {{
      display: inline-flex; align-items: center; gap: 6px;
      padding: 8px 10px; border-radius: 999px; border: 1px solid var(--line); background: #fff;
      font-size: 13px;
    }}
    .toolbar {{ display: flex; gap: 8px; flex-wrap: wrap; }}
    button {{
      border: 1px solid transparent; border-radius: 10px; padding: 10px 14px; cursor: pointer;
      font: inherit; font-weight: 600;
    }}
    .primary {{ background: var(--primary); color: #fff; }}
    .secondary {{ background: #fff; border-color: var(--line); color: var(--text); }}
    .danger {{ background: #fff7ed; border-color: #fed7aa; color: var(--warning); }}
    .field-grid {{ display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); }}
    label {{ display: flex; flex-direction: column; gap: 6px; font-size: 14px; color: #314458; }}
    input, select {{ font: inherit; border: 1px solid var(--line); border-radius: 10px; padding: 10px 12px; background: #fff; }}
    .stack {{ display: grid; gap: 12px; }}
    .artifact-grid {{ display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); }}
    .artifact-card, .chart-card {{
      border: 1px solid var(--line); border-radius: 12px; padding: 14px; background: #fff;
    }}
    .artifact-card .name, .chart-card .name {{ font-weight: 700; margin-bottom: 6px; }}
    .artifact-card .meta, .chart-card .meta {{ color: var(--muted); font-size: 13px; margin-bottom: 8px; }}
    .chart-card img {{ width: 100%; border-radius: 8px; border: 1px solid var(--line); background: #fff; }}
    .result-box {{
      border: 1px solid var(--line); border-radius: 12px; padding: 14px; background: #0f172a; color: #e2e8f0;
      min-height: 280px; white-space: pre-wrap; overflow: auto;
    }}
    .branch-grid {{ display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); }}
    .branch-card {{
      border: 1px solid var(--line); border-radius: 12px; padding: 14px; background: #fff;
    }}
    .branch-title {{ font-weight: 700; margin-bottom: 8px; }}
    .prob-list {{ margin: 8px 0 0; padding-left: 18px; color: var(--muted); }}
    .empty {{
      padding: 16px; border-radius: 12px; border: 1px dashed #cbd5e1; color: var(--muted); background: #fff;
    }}
    .hidden {{ display: none; }}
    @media (max-width: 1080px) {{
      .grid-two, .grid-three {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <header class="topbar">
    <div class="topbar-inner">
      <div class="brand">
        <h1>肥胖风险预测系统 · 本地 Web 控制台</h1>
        <div class="subtle">训练选择、过程摘要、参数配置、产物状态、图表预览、单样本预测统一在同一页面。</div>
      </div>
      <nav class="nav">
        <a href="#overview">总览</a>
        <a href="#training">训练</a>
        <a href="#comparison">对比</a>
        <a href="#parameters">参数</a>
        <a href="#artifacts">产物</a>
        <a href="#prediction">预测</a>
      </nav>
    </div>
  </header>

  <main class="shell">
    <section id="overview" class="section">
      <div class="section-head">
        <div>
          <h2 class="section-title">项目总览</h2>
          <div class="section-note" id="overview-note">正在加载训练摘要...</div>
        </div>
        <div class="toolbar">
          <button class="secondary" onclick="refreshDashboard()">刷新摘要</button>
          <button class="secondary" onclick="downloadDashboard()">导出摘要</button>
        </div>
      </div>
      <div class="panel stack">
        <div id="overview-pills" class="chip-row"></div>
        <div id="overview-metrics" class="metric-grid"></div>
        <div class="status-row">
          <div class="panel" style="box-shadow:none;">
            <div class="muted" style="font-size:13px;">训练路线</div>
            <div id="training-route" style="font-size:18px;font-weight:700;margin-top:6px;">-</div>
          </div>
          <div class="panel" style="box-shadow:none;">
            <div class="muted" style="font-size:13px;">推荐模型</div>
            <div id="recommended-model" style="font-size:18px;font-weight:700;margin-top:6px;">-</div>
          </div>
          <div class="panel" style="box-shadow:none;">
            <div class="muted" style="font-size:13px;">最近训练时间</div>
            <div id="latest-time" style="font-size:18px;font-weight:700;margin-top:6px;">-</div>
          </div>
        </div>
      </div>
    </section>

    <section id="training" class="section">
      <div class="section-head">
        <div>
          <h2 class="section-title">训练选择</h2>
          <div class="section-note">显式选择训练路线后再启动本地训练进程。</div>
        </div>
        <div class="toolbar">
          <button class="primary" onclick="startTraining()">训练</button>
          <button class="secondary" onclick="refreshDashboard()">加载/刷新</button>
        </div>
      </div>
      <div class="panel grid-two">
        <div class="stack">
          <div id="training-modes" class="chip-row"></div>
          <div class="stack">
            <div class="muted" style="font-size:13px;">训练说明</div>
            <div id="training-note" class="empty"></div>
          </div>
        </div>
        <div class="stack">
          <div class="muted" style="font-size:13px;">训练过程与状态</div>
          <div id="training-status" class="result-box" style="min-height: 220px;"></div>
        </div>
      </div>
    </section>

    <section id="comparison" class="section">
      <div class="section-head">
        <div>
          <h2 class="section-title">模型对比</h2>
          <div class="section-note">统一展示 sklearn 与手搓模型的测试集指标。</div>
        </div>
      </div>
      <div class="panel table-wrap">
        <table>
          <thead>
            <tr>
              <th>家族</th>
              <th>模型名称</th>
              <th>Accuracy</th>
              <th>Macro Precision</th>
              <th>Macro Recall</th>
              <th>Macro F1</th>
            </tr>
          </thead>
          <tbody id="comparison-body"></tbody>
        </table>
      </div>
    </section>

    <section id="parameters" class="section">
      <div class="section-head">
        <div>
          <h2 class="section-title">参数配置</h2>
          <div class="section-note">当前训练路线、默认模型、单样本字段和优化后参数汇总。</div>
        </div>
      </div>
      <div class="grid-two">
        <div class="panel table-wrap">
          <table>
            <thead>
              <tr>
                <th>家族</th>
                <th>模型</th>
                <th>参数</th>
              </tr>
            </thead>
            <tbody id="parameter-body"></tbody>
          </table>
        </div>
        <div class="panel stack">
          <div>
            <div class="muted" style="font-size:13px;">单样本字段</div>
            <div id="sample-fields" class="chip-row" style="margin-top:8px;"></div>
          </div>
          <div>
            <div class="muted" style="font-size:13px;">训练路线</div>
            <div id="route-summary" style="margin-top:8px;font-weight:700;">-</div>
          </div>
          <div>
            <div class="muted" style="font-size:13px;">默认模型</div>
            <div id="default-model" style="margin-top:8px;font-weight:700;">-</div>
          </div>
        </div>
      </div>
    </section>

    <section id="artifacts" class="section">
      <div class="section-head">
        <div>
          <h2 class="section-title">产物与图表</h2>
          <div class="section-note">模型、报告、日志和图表都在这里集中展示。</div>
        </div>
      </div>
      <div class="grid-two">
        <div class="panel">
          <div id="artifact-grid" class="artifact-grid"></div>
        </div>
        <div class="panel stack">
          <div class="muted" style="font-size:13px;">图表预览</div>
          <div id="chart-grid" class="artifact-grid"></div>
        </div>
      </div>
    </section>

    <section id="prediction" class="section">
      <div class="section-head">
        <div>
          <h2 class="section-title">单样本预测</h2>
          <div class="section-note">同时输出 sklearn、手搓模型和推荐结果的概率分布。</div>
        </div>
        <div class="toolbar">
          <button class="primary" onclick="submitPrediction()">预测</button>
        </div>
      </div>
      <div class="grid-two">
        <div class="panel stack">
          <div id="prediction-form" class="field-grid"></div>
        </div>
        <div class="panel stack">
          <div id="prediction-head" class="chip-row"></div>
          <div id="prediction-result" class="result-box">等待提交预测...</div>
          <div id="prediction-branches" class="branch-grid"></div>
        </div>
      </div>
    </section>
  </main>

  <script>
    const INITIAL_DASHBOARD = __DASHBOARD_JSON__;
    const SAMPLE_FIELDS = __SAMPLE_FIELDS_JSON__;
    const TRAINING_MODES = __TRAINING_MODES_JSON__;
    let dashboardState = INITIAL_DASHBOARD;
    const fieldInputs = {{}};

    function escapeHtml(value) {{
      return String(value ?? '').replace(/[&<>\"']/g, (char) => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[char]));
    }}

    function formatMetric(value) {{
      if (value === null || value === undefined || value === '') return '-';
      const number = Number(value);
      return Number.isFinite(number) ? number.toFixed(6) : String(value);
    }}

    function renderOverview(data) {{
      const overview = data.overview || {{}};
      const artifactStatus = data.artifact_status || {{}};
      document.getElementById('overview-note').textContent = data.message || '训练摘要已加载。';
      document.getElementById('training-route').textContent = overview.training_mode_label || '-';
      document.getElementById('recommended-model').textContent = overview.recommended_model ? `${{overview.recommended_model.family}} / ${{overview.recommended_model.name}}` : '-';
      document.getElementById('latest-time').textContent = data.generated_at || '-';
      document.getElementById('route-summary').textContent = overview.training_mode_label || '-';
      document.getElementById('default-model').textContent = overview.recommended_model ? overview.recommended_model.name : '-';

      const pills = [
        `项目：${{overview.project_name || data.project_name || '-'}}`,
        `样本量：${{overview.sample_count ?? '-' }}`,
        `类别数：${{overview.class_count ?? '-' }}`,
        `最优 Macro F1：${{formatMetric(overview.best_macro_f1)}}`,
        `日志：${{artifactStatus.log_path || '-' }}`,
      ];
      document.getElementById('overview-pills').innerHTML = pills.map((item) => `<span class="pill">${{escapeHtml(item)}}</span>`).join('');

      const metrics = [
        ['项目名称', overview.project_name || data.project_name || '-'],
        ['数据集样本量', overview.sample_count ?? '-'],
        ['类别数', overview.class_count ?? '-'],
        ['当前训练状态', overview.training_status || data.status || '-'],
        ['最优 Macro F1', formatMetric(overview.best_macro_f1)],
        ['推荐模型', overview.recommended_model ? `${{overview.recommended_model.family}} / ${{overview.recommended_model.name}}` : '-'],
      ];
      document.getElementById('overview-metrics').innerHTML = metrics.map(([label, value]) => `
        <div class="metric">
          <div class="label">${{escapeHtml(label)}}</div>
          <div class="value">${{escapeHtml(value)}}</div>
        </div>
      `).join('');

      document.getElementById('training-note').innerHTML = `
        <div><strong>训练路线：</strong>${{escapeHtml(overview.training_mode_label || '-')}}</div>
        <div style="margin-top:8px;"><strong>当前状态：</strong>${{escapeHtml(overview.training_status || data.status || '-')}}</div>
        <div style="margin-top:8px;"><strong>说明：</strong>选择训练路线后点击“训练”，服务端会在本地启动对应的 `main.py` 命令。</div>
      `;

      const statusLines = [
        `摘要状态：${{data.status || '-'}}`,
        `生成时间：${{data.generated_at || '-'}}`,
        `训练路线：${{overview.training_mode_label || '-'}}`,
        `推荐模型：${{overview.recommended_model ? `${{overview.recommended_model.family}} / ${{overview.recommended_model.name}}` : '-' }}`,
        '',
        '参数摘要：',
      ];
      (data.parameter_rows || []).slice(0, 8).forEach((row) => {{
        statusLines.push(`- ${{row.family}}/${{row.name}}: ${{JSON.stringify(row.parameters)}}`);
      }});
      if ((data.parameter_rows || []).length === 0) {{
        statusLines.push('- 暂无参数摘要，请先执行训练。');
      }}
      document.getElementById('training-status').textContent = statusLines.join('\n');
    }}

    function renderTrainingModes(data) {{
      const container = document.getElementById('training-modes');
      const current = data.training_mode || 'train';
      container.innerHTML = TRAINING_MODES.map((item) => `
        <label class="chip" style="cursor:pointer;">
          <input type="radio" name="training_mode" value="${{escapeHtml(item.value)}}" ${{item.value === current ? 'checked' : ''}} />
          <span>${{escapeHtml(item.label)}}</span>
        </label>
      `).join('');
      container.querySelectorAll('input[name="training_mode"]').forEach((input) => {{
        input.addEventListener('change', () => {{
          dashboardState.training_mode = input.value;
          document.getElementById('route-summary').textContent = TRAINING_MODES.find((item) => item.value === input.value)?.label || input.value;
        }});
      }});
    }}

    function renderComparison(rows) {{
      const tbody = document.getElementById('comparison-body');
      if (!rows || rows.length === 0) {{
        tbody.innerHTML = '<tr><td colspan="6">暂无训练结果，请先执行训练。</td></tr>';
        return;
      }}
      tbody.innerHTML = rows.map((row) => `
        <tr>
          <td>${{escapeHtml(row.family)}}</td>
          <td>${{escapeHtml(row.name)}}</td>
          <td>${{formatMetric(row.metrics?.accuracy)}}</td>
          <td>${{formatMetric(row.metrics?.macro_precision)}}</td>
          <td>${{formatMetric(row.metrics?.macro_recall)}}</td>
          <td>${{formatMetric(row.metrics?.macro_f1)}}</td>
        </tr>
      `).join('');
    }}

    function renderParameters(rows) {{
      const tbody = document.getElementById('parameter-body');
      if (!rows || rows.length === 0) {{
        tbody.innerHTML = '<tr><td colspan="3">暂无参数摘要。</td></tr>';
        return;
      }}
      tbody.innerHTML = rows.map((row) => `
        <tr>
          <td>${{escapeHtml(row.family)}}</td>
          <td>${{escapeHtml(row.name)}}</td>
          <td><code>${{escapeHtml(JSON.stringify(row.parameters))}}</code></td>
        </tr>
      `).join('');
    }}

    function renderFields(fields) {{
      const container = document.getElementById('sample-fields');
      container.innerHTML = (fields || []).map((field) => `<span class="chip">${{escapeHtml(field.label)}}` + (field.options ? ` · ${{escapeHtml(field.options.join('/'))}}` : '') + `</span>`).join('');
      const form = document.getElementById('prediction-form');
      form.innerHTML = '';
      (fields || []).forEach((field) => {{
        const wrap = document.createElement('label');
        wrap.innerHTML = `<span>${{escapeHtml(field.label)}}</span>`;
        let input;
        if (Array.isArray(field.options) && field.options.length > 0) {{
          input = document.createElement('select');
          field.options.forEach((option) => {{
            const optionNode = document.createElement('option');
            optionNode.value = option;
            optionNode.textContent = option;
            input.appendChild(optionNode);
          }});
          input.value = String(field.default);
        }} else {{
          input = document.createElement('input');
          input.type = 'number';
          input.step = field.name === 'age' || field.name.includes('height') || field.name.includes('weight') ? '0.1' : '0.01';
          input.value = field.default;
        }}
        input.id = `field-${{field.name}}`;
        fieldInputs[field.name] = input;
        wrap.appendChild(input);
        form.appendChild(wrap);
      }});
    }}

    function renderArtifacts(groups) {{
      const container = document.getElementById('artifact-grid');
      if (!groups || groups.length === 0) {{
        container.innerHTML = '<div class="empty">暂无产物。</div>';
        return;
      }}
      container.innerHTML = groups.map((group) => `
        <div class="artifact-card">
          <div class="name">${{escapeHtml(group.label || group.name)}}</div>
          <div class="meta">文件数：${{group.file_count ?? 0}} · ${{group.exists ? '存在' : '缺失'}}</div>
          <div class="meta">${{escapeHtml((group.files || []).slice(0, 3).join('，') || '暂无文件')}}</div>
        </div>
      `).join('');
    }}

    function renderCharts(groups) {{
      const container = document.getElementById('chart-grid');
      const chartFiles = [];
      (groups || []).forEach((group) => {{
        (group.files || []).forEach((filePath) => {{
          if (/\\.(png|jpg|jpeg)$/i.test(filePath)) {{
            chartFiles.push(filePath);
          }}
        }});
      }});
      if (chartFiles.length === 0) {{
        container.innerHTML = '<div class="empty">暂无可预览图表。</div>';
        return;
      }}
      container.innerHTML = chartFiles.slice(0, 8).map((filePath) => `
        <div class="chart-card">
          <div class="name">${{escapeHtml(filePath)}}</div>
          <img src="/artifacts/${{encodeURIComponent(filePath)}}" alt="${{escapeHtml(filePath)}}" />
        </div>
      `).join('');
    }}

    function renderPrediction(result) {{
      const head = document.getElementById('prediction-head');
      const box = document.getElementById('prediction-result');
      const branches = document.getElementById('prediction-branches');
      if (!result || !result.success) {{
        head.innerHTML = '<span class="pill">预测失败</span>';
        box.textContent = result?.message || '预测失败';
        branches.innerHTML = '';
        return;
      }}
      if (result.message && !result.sklearn && !result.manual) {{
        head.innerHTML = '';
        box.textContent = result.message;
        branches.innerHTML = '';
        return;
      }}

      const chips = [];
      if (result.recommended_model) chips.push(`推荐模型：${{escapeHtml(result.recommended_model)}}`);
      if (result.recommended_result) chips.push(`推荐结果：${{escapeHtml(result.recommended_result)}}`);
      head.innerHTML = chips.map((item) => `<span class="pill">${{item}}</span>`).join('');

      box.textContent = JSON.stringify(result, null, 2);

      const renderBranch = (title, branch) => {{
        if (!branch) return '';
        return `
          <div class="branch-card">
            <div class="branch-title">${{escapeHtml(title)}}</div>
            ${(branch.models || []).map((model) => `
              <div class="stack" style="margin-top:10px;border-top:1px solid var(--line);padding-top:10px;">
                <div><strong>${{escapeHtml(model.name)}}</strong></div>
                <div>预测：${{escapeHtml(model.prediction || '-')}}</div>
                <div class="muted">参数：${{escapeHtml(JSON.stringify(model.best_parameters || {{}}))}}</div>
                <div class="muted">概率分布：</div>
                <ul class="prob-list">
                  ${(model.probabilities || []).map((item) => `<li>${{escapeHtml(item.label)}}：${{formatMetric(item.probability)}}</li>`).join('')}
                </ul>
              </div>
            `).join('')}
            <div style="margin-top:10px;" class="muted">推荐结果：${{escapeHtml(branch.recommended_result || '-')}}</div>
          </div>
        `;
      }};

      branches.innerHTML = [
        renderBranch('sklearn 结果', result.sklearn),
        renderBranch('手搓模型结果', result.manual),
      ].filter(Boolean).join('');
    }}

    function getTrainingMode() {{
      const selected = document.querySelector('input[name="training_mode"]:checked');
      return selected ? selected.value : dashboardState.training_mode || 'train';
    }}

    function collectPayload() {{
      const payload = {{}};
      SAMPLE_FIELDS.forEach((field) => {{
        const input = fieldInputs[field.name];
        if (!input) return;
        if (Array.isArray(field.options) && field.options.length > 0) {{
          payload[field.name] = input.value;
        }} else {{
          payload[field.name] = Number(input.value);
        }}
      }});
      return payload;
    }}

    async function refreshDashboard() {{
      const response = await fetch('/api/v1/dashboard');
      const payload = await response.json();
      if (!payload.success) {{
        dashboardState = INITIAL_DASHBOARD;
        renderDashboard(dashboardState);
        return;
      }}
      dashboardState = payload.data;
      renderDashboard(dashboardState);
    }}

    function renderDashboard(data) {{
      renderOverview(data);
      renderTrainingModes(data);
      renderComparison(data.comparison_rows || []);
      renderParameters(data.parameter_rows || []);
      renderFields(data.sample_fields || SAMPLE_FIELDS);
      renderArtifacts(data.artifact_groups || []);
      renderCharts(data.chart_groups || []);
      document.getElementById('training-status').textContent = [
        `摘要状态：${{data.status || '-' }}`,
        `最近训练：${{data.generated_at || '-' }}`,
        `训练路线：${{data.overview?.training_mode_label || '-' }}`,
      ].join('\n');
      renderPrediction({{success: true, message: '等待提交预测...'}});
    }}

    async function startTraining() {{
      const trainingMode = getTrainingMode();
      const response = await fetch('/api/v1/train', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ training_mode: trainingMode }})
      }});
      const payload = await response.json();
      document.getElementById('training-status').textContent = payload.message || '训练请求已提交。';
    }}

    async function submitPrediction() {{
      const payload = collectPayload();
      const response = await fetch('/api/v1/predict', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify(payload)
      }});
      const data = await response.json();
      renderPrediction(data);
    }}

    function downloadDashboard() {{
      const blob = new Blob([JSON.stringify(dashboardState, null, 2)], {{ type: 'application/json;charset=utf-8' }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'training_dashboard.json';
      a.click();
      URL.revokeObjectURL(url);
    }}

    renderDashboard(dashboardState);
  </script>
</body>
</html>"""
    template = template.replace('{{', '{').replace('}}', '}')
    return (
        template
        .replace('__DASHBOARD_JSON__', dashboard_json)
        .replace('__SAMPLE_FIELDS_JSON__', sample_fields_json)
        .replace('__TRAINING_MODES_JSON__', training_modes_json)
    )
