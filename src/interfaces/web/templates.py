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
  <title>肥胖风险预测系统 · 应用式 Web 界面</title>
  <style>
    :root {
      --bg: #eef2f7;
      --panel: #ffffff;
      --panel-strong: #0f172a;
      --line: #d7dfea;
      --text: #0f172a;
      --muted: #5b6574;
      --primary: #0f766e;
      --primary-soft: #ccfbf1;
      --secondary: #f97316;
      --secondary-soft: #ffedd5;
      --success: #16a34a;
      --danger: #dc2626;
      --shadow: 0 18px 40px rgba(15, 23, 42, 0.08);
    }
    * { box-sizing: border-box; }
    html { scroll-behavior: smooth; }
    body {
      margin: 0;
      min-height: 100vh;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      background: var(--bg);
      color: var(--text);
    }
    a { color: inherit; text-decoration: none; }
    button, input, select, textarea { font: inherit; }
    code, pre { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }
    .app-shell {
      min-height: 100vh;
      display: grid;
      grid-template-columns: 300px minmax(0, 1fr);
    }
    .sidebar {
      position: sticky;
      top: 0;
      align-self: start;
      min-height: 100vh;
      padding: 20px;
      background: var(--panel-strong);
      color: #e5eefb;
      border-right: 1px solid #1f2937;
      display: grid;
      gap: 18px;
      grid-template-rows: auto auto auto 1fr auto;
    }
    .brand h1 {
      margin: 0;
      font-size: 24px;
      line-height: 1.2;
    }
    .brand .subtle {
      margin-top: 10px;
      color: #94a3b8;
      font-size: 13px;
      line-height: 1.6;
    }
    .sidebar-card {
      border: 1px solid #223047;
      border-radius: 14px;
      background: #111827;
      padding: 14px;
      box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.02);
    }
    .sidebar-label {
      font-size: 12px;
      color: #94a3b8;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .sidebar-value {
      margin-top: 8px;
      font-size: 18px;
      font-weight: 700;
      line-height: 1.35;
      word-break: break-word;
    }
    .nav-list {
      display: grid;
      gap: 10px;
    }
    .nav-button {
      width: 100%;
      border: 1px solid #243244;
      background: #111827;
      color: #e5eefb;
      border-radius: 14px;
      padding: 12px 14px;
      cursor: pointer;
      text-align: left;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      transition: border-color 0.15s ease, background 0.15s ease, transform 0.15s ease;
    }
    .nav-button:hover { transform: translateY(-1px); border-color: #3b4a63; }
    .nav-button.active {
      background: #12273b;
      border-color: var(--primary);
      box-shadow: 0 0 0 1px rgba(15, 118, 110, 0.2);
    }
    .nav-button strong { display: block; font-size: 14px; }
    .nav-button small { display: block; margin-top: 3px; color: #94a3b8; font-size: 12px; line-height: 1.4; }
    .sidebar-actions {
      display: grid;
      gap: 10px;
    }
    .sidebar-actions button {
      width: 100%;
      border-radius: 12px;
      padding: 11px 14px;
      border: 1px solid #2a3950;
      background: #0b1220;
      color: #e5eefb;
      cursor: pointer;
    }
    .sidebar-actions button:hover { border-color: var(--primary); }
    .workspace {
      min-width: 0;
      display: grid;
      grid-template-rows: auto 1fr;
    }
    .workspace-top {
      position: sticky;
      top: 0;
      z-index: 10;
      padding: 18px 24px;
      border-bottom: 1px solid var(--line);
      background: rgba(238, 242, 247, 0.92);
      backdrop-filter: blur(12px);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      flex-wrap: wrap;
    }
    .breadcrumb {
      display: grid;
      gap: 6px;
    }
    .breadcrumb .kicker {
      font-size: 12px;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .breadcrumb .title {
      font-size: 20px;
      font-weight: 800;
      line-height: 1.25;
    }
    .breadcrumb .desc {
      font-size: 13px;
      color: var(--muted);
      line-height: 1.5;
    }
    .toolbar {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
    }
    .btn {
      border: 1px solid transparent;
      border-radius: 12px;
      padding: 10px 14px;
      cursor: pointer;
      font-weight: 700;
      transition: transform 0.15s ease, border-color 0.15s ease, background 0.15s ease;
    }
    .btn:hover { transform: translateY(-1px); }
    .btn-primary { background: var(--primary); color: #fff; }
    .btn-secondary { background: #fff; color: var(--text); border-color: var(--line); }
    .btn-ghost { background: #f8fafc; color: var(--text); border-color: var(--line); }
    .content {
      padding: 24px;
      display: grid;
      gap: 20px;
    }
    .view {
      display: none;
      gap: 20px;
    }
    .view.active { display: grid; }
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 16px;
      box-shadow: var(--shadow);
      padding: 16px;
      min-width: 0;
    }
    .panel.compact { padding: 14px; }
    .panel-title {
      margin: 0;
      font-size: 18px;
      line-height: 1.3;
    }
    .panel-note {
      margin-top: 6px;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.6;
    }
    .metric-grid {
      display: grid;
      gap: 12px;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    }
    .metric {
      border: 1px solid var(--line);
      border-radius: 14px;
      background: linear-gradient(180deg, #ffffff, #f8fafc);
      padding: 14px;
      min-height: 94px;
    }
    .metric .label {
      color: var(--muted);
      font-size: 13px;
    }
    .metric .value {
      margin-top: 10px;
      font-size: 22px;
      font-weight: 800;
      line-height: 1.2;
      word-break: break-word;
    }
    .chip-row {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }
    .chip {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 8px 11px;
      border-radius: 999px;
      border: 1px solid var(--line);
      background: #fff;
      font-size: 13px;
      line-height: 1.2;
      word-break: break-word;
    }
    .launchpad {
      display: grid;
      gap: 12px;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    }
    .launch-card {
      border: 1px solid var(--line);
      background: #fff;
      border-radius: 14px;
      padding: 14px;
      text-align: left;
      cursor: pointer;
      display: grid;
      gap: 10px;
      min-height: 114px;
      transition: border-color 0.15s ease, transform 0.15s ease, box-shadow 0.15s ease;
    }
    .launch-card:hover {
      border-color: var(--primary);
      box-shadow: 0 14px 26px rgba(15, 118, 110, 0.08);
      transform: translateY(-1px);
    }
    .launch-card .name {
      font-weight: 800;
      font-size: 15px;
    }
    .launch-card .desc {
      color: var(--muted);
      font-size: 13px;
      line-height: 1.55;
    }
    .split {
      display: grid;
      gap: 16px;
      grid-template-columns: minmax(0, 1.08fr) minmax(280px, 0.92fr);
    }
    .stack {
      display: grid;
      gap: 12px;
    }
    .grid-two {
      display: grid;
      gap: 16px;
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .grid-three {
      display: grid;
      gap: 16px;
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }
    .table-wrap { overflow: auto; }
    table {
      width: 100%;
      min-width: 760px;
      border-collapse: collapse;
    }
    th, td {
      border-bottom: 1px solid var(--line);
      padding: 11px 10px;
      text-align: left;
      vertical-align: top;
    }
    th {
      background: #f8fafc;
      color: #334155;
      font-size: 13px;
      font-weight: 700;
    }
    td { font-size: 14px; }
    .table-row {
      cursor: pointer;
      transition: background 0.15s ease;
    }
    .table-row:hover { background: #f8fafc; }
    .table-row.active { background: #ecfeff; }
    .mode-grid {
      display: grid;
      gap: 12px;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    }
    .mode-card {
      position: relative;
      border: 1px solid var(--line);
      border-radius: 14px;
      background: #fff;
      padding: 14px;
      cursor: pointer;
      display: grid;
      gap: 10px;
      min-height: 132px;
    }
    .mode-card input {
      position: absolute;
      opacity: 0;
      pointer-events: none;
    }
    .mode-card.active {
      border-color: var(--primary);
      background: #ecfeff;
    }
    .mode-card .name {
      font-size: 15px;
      font-weight: 800;
    }
    .mode-card .desc {
      color: var(--muted);
      font-size: 13px;
      line-height: 1.55;
    }
    .status-console {
      border: 1px solid var(--line);
      border-radius: 14px;
      background: #0f172a;
      color: #dbe7ff;
      min-height: 280px;
      padding: 14px;
      white-space: pre-wrap;
      overflow: auto;
    }
    .field-grid {
      display: grid;
      gap: 12px;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    }
    label.field {
      display: flex;
      flex-direction: column;
      gap: 6px;
      font-size: 14px;
      color: #334155;
    }
    input, select, textarea {
      border: 1px solid var(--line);
      border-radius: 12px;
      background: #fff;
      padding: 10px 12px;
      min-width: 0;
    }
    .result-box {
      border: 1px solid var(--line);
      border-radius: 14px;
      background: #0b1220;
      color: #dbe7ff;
      min-height: 220px;
      padding: 14px;
      white-space: pre-wrap;
      overflow: auto;
    }
    .branch-grid {
      display: grid;
      gap: 12px;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    }
    .branch-card {
      border: 1px solid var(--line);
      border-radius: 14px;
      background: #fff;
      padding: 14px;
      display: grid;
      gap: 10px;
    }
    .branch-title {
      font-weight: 800;
      font-size: 15px;
    }
    .prob-list {
      margin: 0;
      padding-left: 18px;
      color: var(--muted);
      display: grid;
      gap: 4px;
    }
    .artifact-layout {
      display: grid;
      gap: 16px;
      grid-template-columns: minmax(240px, 300px) minmax(0, 1fr);
    }
    .artifact-nav {
      display: grid;
      gap: 10px;
    }
    .artifact-nav button {
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 12px 14px;
      background: #fff;
      color: var(--text);
      text-align: left;
      cursor: pointer;
      display: grid;
      gap: 6px;
      transition: border-color 0.15s ease, background 0.15s ease;
    }
    .artifact-nav button.active {
      border-color: var(--primary);
      background: #ecfeff;
    }
    .artifact-nav button .meta {
      font-size: 12px;
      color: var(--muted);
    }
    .artifact-panel {
      display: grid;
      gap: 12px;
    }
    .artifact-list {
      display: grid;
      gap: 8px;
      max-height: 360px;
      overflow: auto;
      padding-right: 2px;
    }
    .file-button {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 12px;
      background: #fff;
      padding: 10px 12px;
      text-align: left;
      cursor: pointer;
      display: grid;
      gap: 4px;
    }
    .file-button.active {
      border-color: var(--primary);
      background: #f0fdfa;
    }
    .file-button .meta {
      color: var(--muted);
      font-size: 12px;
      word-break: break-word;
    }
    .preview-stage {
      border: 1px solid var(--line);
      border-radius: 14px;
      background: #0b1220;
      color: #dbe7ff;
      min-height: 360px;
      padding: 14px;
      display: grid;
      gap: 12px;
    }
    .preview-stage img,
    .preview-stage iframe {
      width: 100%;
      min-height: 300px;
      border: 0;
      border-radius: 12px;
      background: #fff;
    }
    .preview-stage img {
      object-fit: contain;
      max-height: 70vh;
    }
    .preview-text {
      background: #0b1220;
      color: #dbe7ff;
      border-radius: 12px;
      padding: 14px;
      white-space: pre-wrap;
      overflow: auto;
      min-height: 300px;
      line-height: 1.6;
    }
    .preview-meta {
      color: #cbd5e1;
      font-size: 13px;
      line-height: 1.6;
      word-break: break-word;
    }
    .preview-actions {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
    }
    .empty {
      border: 1px dashed #cbd5e1;
      border-radius: 14px;
      background: #fff;
      color: var(--muted);
      padding: 18px;
      line-height: 1.6;
    }
    .muted { color: var(--muted); }
    .hidden { display: none !important; }
    @media (max-width: 1180px) {
      .app-shell { grid-template-columns: 1fr; }
      .sidebar {
        position: relative;
        min-height: auto;
        border-right: 0;
        border-bottom: 1px solid #1f2937;
      }
      .workspace-top { position: relative; }
      .split, .grid-two, .grid-three, .artifact-layout { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <h1>肥胖风险预测系统</h1>
        <div class="subtle">本地 Web 应用壳。左侧切换视图，右侧查看训练总览、模型对比、产物原图和单样本预测。</div>
      </div>

      <div class="sidebar-card">
        <div class="sidebar-label">项目</div>
        <div class="sidebar-value" id="sidebar-project">-</div>
      </div>

      <div class="sidebar-card">
        <div class="sidebar-label">当前状态</div>
        <div class="sidebar-value" id="sidebar-status">-</div>
      </div>

      <nav class="nav-list" aria-label="主导航">
        <button class="nav-button" data-nav-view="overview" onclick="showView('overview')">
          <span>
            <strong>总览</strong>
            <small>摘要、状态、快捷入口</small>
          </span>
          <span>01</span>
        </button>
        <button class="nav-button" data-nav-view="training" onclick="showView('training')">
          <span>
            <strong>训练</strong>
            <small>路线选择与启动</small>
          </span>
          <span>02</span>
        </button>
        <button class="nav-button" data-nav-view="compare" onclick="showView('compare')">
          <span>
            <strong>对比</strong>
            <small>指标和参数检查</small>
          </span>
          <span>03</span>
        </button>
        <button class="nav-button" data-nav-view="artifacts" onclick="showView('artifacts')">
          <span>
            <strong>产物</strong>
            <small>图表、日志、模型文件</small>
          </span>
          <span>04</span>
        </button>
        <button class="nav-button" data-nav-view="predict" onclick="showView('predict')">
          <span>
            <strong>预测</strong>
            <small>单样本推理</small>
          </span>
          <span>05</span>
        </button>
      </nav>

      <div class="sidebar-actions">
        <button onclick="refreshDashboard()">刷新摘要</button>
        <button onclick="downloadDashboard()">导出摘要</button>
        <button onclick="showView('artifacts')">查看原图</button>
      </div>
    </aside>

    <div class="workspace">
      <header class="workspace-top">
        <div class="breadcrumb">
          <div class="kicker">Local application console</div>
          <div class="title" id="view-title">总览</div>
          <div class="desc" id="view-desc">正在加载训练摘要。</div>
        </div>
        <div class="toolbar">
          <button class="btn btn-secondary" onclick="refreshDashboard()">刷新</button>
          <button class="btn btn-ghost" onclick="downloadDashboard()">导出 JSON</button>
          <button class="btn btn-primary" onclick="showView('predict')">进入预测</button>
        </div>
      </header>

      <main class="content">
        <section class="view active" data-view="overview" id="view-overview">
          <div class="panel">
            <div class="panel-title">项目总览</div>
            <div class="panel-note" id="overview-note">正在加载训练摘要...</div>
            <div class="chip-row" id="overview-chips" style="margin-top: 14px;"></div>
            <div class="metric-grid" id="overview-metrics" style="margin-top: 14px;"></div>
            <div class="launchpad" style="margin-top: 16px;">
              <button class="launch-card" onclick="showView('training')">
                <span class="name">进入训练</span>
                <span class="desc">选择训练路线并启动本地训练进程。</span>
              </button>
              <button class="launch-card" onclick="showView('compare')">
                <span class="name">查看模型对比</span>
                <span class="desc">快速核对 sklearn 与手搓模型的测试结果。</span>
              </button>
              <button class="launch-card" onclick="showView('artifacts')">
                <span class="name">查看产物原图</span>
                <span class="desc">打开图表、日志、报告与模型文件。</span>
              </button>
              <button class="launch-card" onclick="showView('predict')">
                <span class="name">单样本预测</span>
                <span class="desc">输入一条样本，查看推荐模型输出。</span>
              </button>
            </div>
          </div>
        </section>

        <section class="view" data-view="training" id="view-training">
          <div class="split">
            <div class="panel stack">
              <div>
                <div class="panel-title">训练路线</div>
                <div class="panel-note">显式选择训练路线后再提交请求。当前页面只负责发起本地训练，不改动训练逻辑。</div>
              </div>
              <div class="mode-grid" id="training-modes"></div>
              <div class="toolbar">
                <button class="btn btn-primary" onclick="startTraining()">启动训练</button>
                <button class="btn btn-secondary" onclick="refreshDashboard()">重新加载摘要</button>
              </div>
            </div>
            <div class="panel stack">
              <div>
                <div class="panel-title">训练状态</div>
                <div class="panel-note">包含最近摘要、当前路线和参数摘要。</div>
              </div>
              <div class="status-console" id="training-status">等待加载...</div>
            </div>
          </div>
        </section>

        <section class="view" data-view="compare" id="view-compare">
          <div class="split">
            <div class="panel table-wrap">
              <div class="panel-title">模型对比</div>
              <div class="panel-note">点击任意一行查看该模型的指标和参数。</div>
              <table style="margin-top: 14px;">
                <thead>
                  <tr>
                    <th>家族</th>
                    <th>模型</th>
                    <th>Accuracy</th>
                    <th>Macro Precision</th>
                    <th>Macro Recall</th>
                    <th>Macro F1</th>
                  </tr>
                </thead>
                <tbody id="comparison-body"></tbody>
              </table>
            </div>
            <div class="panel stack">
              <div>
                <div class="panel-title">模型详情</div>
                <div class="panel-note">展示当前选中模型的参数和说明。</div>
              </div>
              <div id="comparison-inspector" class="stack"></div>
            </div>
          </div>
        </section>

        <section class="view" data-view="artifacts" id="view-artifacts">
          <div class="artifact-layout">
            <div class="panel stack">
              <div>
                <div class="panel-title">产物分类</div>
                <div class="panel-note">切换分类后，右侧可以直接查看原图、日志、报告或模型文件。</div>
              </div>
              <div class="artifact-nav" id="artifact-nav"></div>
            </div>
            <div class="panel artifact-panel">
              <div>
                <div class="panel-title" id="artifact-panel-title">产物详情</div>
                <div class="panel-note" id="artifact-panel-note">选择一个分类和一个文件开始查看。</div>
              </div>
              <div class="toolbar">
                <button class="btn btn-secondary" onclick="openSelectedArtifact()">查看原文件</button>
                <button class="btn btn-ghost" onclick="copySelectedArtifactPath()">复制路径</button>
              </div>
              <div class="grid-two">
                <div class="stack">
                  <div class="muted">文件列表</div>
                  <div class="artifact-list" id="artifact-list"></div>
                </div>
                <div class="stack">
                  <div class="muted">原图 / 内容预览</div>
                  <div id="artifact-preview" class="preview-stage">请选择左侧分类中的文件。</div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section class="view" data-view="predict" id="view-predict">
          <div class="split">
            <div class="panel stack">
              <div>
                <div class="panel-title">单样本输入</div>
                <div class="panel-note">字段来自当前 dashboard 的 sample_fields，默认值已经填好。</div>
              </div>
              <div class="toolbar">
                <button class="btn btn-primary" onclick="submitPrediction()">提交预测</button>
                <button class="btn btn-secondary" onclick="resetPredictionForm()">恢复默认样本</button>
              </div>
              <div class="field-grid" id="prediction-form"></div>
            </div>
            <div class="panel stack">
              <div>
                <div class="panel-title">预测结果</div>
                <div class="panel-note">同时保留推荐模型、各分支输出和概率分布。</div>
              </div>
              <div class="chip-row" id="prediction-head"></div>
              <div class="result-box" id="prediction-result">等待提交预测...</div>
              <div class="branch-grid" id="prediction-branches"></div>
            </div>
          </div>
        </section>
      </main>
    </div>
  </div>

  <script>
    const INITIAL_DASHBOARD = __DASHBOARD_JSON__;
    const SAMPLE_FIELDS = __SAMPLE_FIELDS_JSON__;
    const TRAINING_MODES = __TRAINING_MODES_JSON__;

    const VIEW_META = {
      overview: { title: '总览', desc: '查看摘要、状态和快捷入口。' },
      training: { title: '训练', desc: '选择训练路线并在本地启动训练。' },
      compare: { title: '对比', desc: '查看模型指标、参数和训练结果。' },
      artifacts: { title: '产物', desc: '查看原图、日志、报告和模型文件。' },
      predict: { title: '预测', desc: '输入单样本并查看推理结果。' },
    };

    const state = {
      dashboard: INITIAL_DASHBOARD,
      selectedView: 'overview',
      selectedTrainingMode: INITIAL_DASHBOARD.training_mode || 'train',
      selectedComparisonIndex: 0,
      selectedArtifactGroup: null,
      selectedArtifactFile: null,
    };

    const fieldInputs = {};

    function escapeHtml(value) {
      return String(value ?? '').replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
    }

    function formatMetric(value) {
      if (value === null || value === undefined || value === '') return '-';
      const number = Number(value);
      return Number.isFinite(number) ? number.toFixed(6) : String(value);
    }

    function getArtifactSrc(filePath) {
      return `/artifacts/${encodeURIComponent(filePath)}`;
    }

    function inferArtifactKind(filePath) {
      const lower = String(filePath || '').toLowerCase();
      if (/\.(png|jpg|jpeg|gif|webp|bmp|svg)$/.test(lower)) return 'image';
      if (/\.pdf$/.test(lower)) return 'pdf';
      if (/\.(json|md|txt|log|csv|tsv|yaml|yml)$/.test(lower)) return 'text';
      return 'binary';
    }

    function getCurrentViewFromHash() {
      const raw = (window.location.hash || '').replace('#', '').trim();
      return VIEW_META[raw] ? raw : 'overview';
    }

    function updateTopbarForView(viewName) {
      const meta = VIEW_META[viewName] || VIEW_META.overview;
      document.getElementById('view-title').textContent = meta.title;
      document.getElementById('view-desc').textContent = meta.desc;
      document.querySelectorAll('[data-nav-view]').forEach((button) => {
        button.classList.toggle('active', button.dataset.navView === viewName);
      });
      document.querySelectorAll('[data-view]').forEach((view) => {
        view.classList.toggle('active', view.dataset.view === viewName);
      });
      history.replaceState(null, '', `#${viewName}`);
      state.selectedView = viewName;
    }

    function showView(viewName) {
      updateTopbarForView(VIEW_META[viewName] ? viewName : 'overview');
      if (state.selectedView === 'artifacts') {
        renderArtifactSelection();
      }
      if (state.selectedView === 'compare') {
        renderComparisonInspector(state.dashboard.comparison_rows?.[state.selectedComparisonIndex] || null);
      }
    }

    function renderOverview(data) {
      const overview = data.overview || {};
      const artifactStatus = data.artifact_status || {};
      document.getElementById('sidebar-project').textContent = overview.project_name || data.project_name || '-';
      document.getElementById('sidebar-status').textContent = overview.training_status || data.status || '-';
      document.getElementById('overview-note').textContent = data.message || '训练摘要已加载。';

      const chips = [
        `训练路线：${overview.training_mode_label || '-'}`,
        `最近时间：${data.generated_at || '-'}`,
        `日志：${artifactStatus.log_path || '-'}`,
        `推荐模型：${overview.recommended_model ? `${overview.recommended_model.family}/${overview.recommended_model.name}` : '-'}`,
      ];
      document.getElementById('overview-chips').innerHTML = chips.map((item) => `<span class="chip">${escapeHtml(item)}</span>`).join('');

      const metrics = [
        ['项目名称', overview.project_name || data.project_name || '-'],
        ['样本量', overview.sample_count ?? '-'],
        ['类别数', overview.class_count ?? '-'],
        ['训练状态', overview.training_status || data.status || '-'],
        ['最佳 Macro F1', formatMetric(overview.best_macro_f1)],
        ['推荐模型', overview.recommended_model ? `${overview.recommended_model.family}/${overview.recommended_model.name}` : '-'],
      ];
      document.getElementById('overview-metrics').innerHTML = metrics.map(([label, value]) => `
        <div class="metric">
          <div class="label">${escapeHtml(label)}</div>
          <div class="value">${escapeHtml(value)}</div>
        </div>
      `).join('');
    }

    function renderTrainingModes(data) {
      const currentMode = data.training_mode || 'train';
      const container = document.getElementById('training-modes');
      container.innerHTML = TRAINING_MODES.map((item) => `
        <label class="mode-card ${item.value === currentMode ? 'active' : ''}">
          <input type="radio" name="training_mode" value="${escapeHtml(item.value)}" ${item.value === currentMode ? 'checked' : ''} />
          <div class="name">${escapeHtml(item.label)}</div>
          <div class="desc">${escapeHtml(item.description || '')}</div>
        </label>
      `).join('');
      container.querySelectorAll('input[name="training_mode"]').forEach((input) => {
        input.addEventListener('change', () => {
          state.selectedTrainingMode = input.value;
          container.querySelectorAll('.mode-card').forEach((card) => {
            const radio = card.querySelector('input[name="training_mode"]');
            card.classList.toggle('active', radio && radio.checked);
          });
        });
      });
      state.selectedTrainingMode = currentMode;
    }

    function buildParameterLookup(rows) {
      const lookup = new Map();
      (rows || []).forEach((row) => {
        lookup.set(`${row.family}::${row.name}`, row);
      });
      return lookup;
    }

    function renderComparison(rows) {
      const tbody = document.getElementById('comparison-body');
      if (!rows || rows.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6">暂无训练结果，请先执行训练。</td></tr>';
        renderComparisonInspector(null);
        return;
      }
      tbody.innerHTML = rows.map((row, index) => `
        <tr class="table-row ${index === state.selectedComparisonIndex ? 'active' : ''}" data-index="${index}">
          <td>${escapeHtml(row.family)}</td>
          <td>${escapeHtml(row.name)}</td>
          <td>${formatMetric(row.metrics?.accuracy)}</td>
          <td>${formatMetric(row.metrics?.macro_precision)}</td>
          <td>${formatMetric(row.metrics?.macro_recall)}</td>
          <td>${formatMetric(row.metrics?.macro_f1)}</td>
        </tr>
      `).join('');
      tbody.querySelectorAll('tr[data-index]').forEach((row) => {
        row.addEventListener('click', () => {
          state.selectedComparisonIndex = Number(row.dataset.index || 0);
          renderComparison(rows);
          renderComparisonInspector(rows[state.selectedComparisonIndex] || null);
        });
      });
      renderComparisonInspector(rows[state.selectedComparisonIndex] || rows[0] || null);
    }

    function renderComparisonInspector(row) {
      const container = document.getElementById('comparison-inspector');
      const lookup = buildParameterLookup(state.dashboard.parameter_rows || []);
      if (!row) {
        container.innerHTML = '<div class="empty">暂无模型详情，请先运行训练。</div>';
        return;
      }
      const params = lookup.get(`${row.family}::${row.name}`);
      const metrics = row.metrics || {};
      container.innerHTML = `
        <div class="panel compact" style="box-shadow:none;">
          <div class="sidebar-label">当前模型</div>
          <div class="sidebar-value" style="color: var(--text);">${escapeHtml(row.family)} / ${escapeHtml(row.name)}</div>
        </div>
        <div class="metric-grid">
          <div class="metric"><div class="label">Accuracy</div><div class="value">${formatMetric(metrics.accuracy)}</div></div>
          <div class="metric"><div class="label">Macro Precision</div><div class="value">${formatMetric(metrics.macro_precision)}</div></div>
          <div class="metric"><div class="label">Macro Recall</div><div class="value">${formatMetric(metrics.macro_recall)}</div></div>
          <div class="metric"><div class="label">Macro F1</div><div class="value">${formatMetric(metrics.macro_f1)}</div></div>
        </div>
        <div class="panel compact" style="box-shadow:none;">
          <div class="sidebar-label">参数摘要</div>
          <div style="margin-top: 8px; word-break: break-word;">${escapeHtml(JSON.stringify(params ? params.parameters : {}, null, 2))}</div>
        </div>
      `;
    }

    function renderFields(fields) {
      const container = document.getElementById('prediction-form');
      document.getElementById('prediction-head').innerHTML = '';
      container.innerHTML = '';
      (fields || []).forEach((field) => {
        const wrapper = document.createElement('label');
        wrapper.className = 'field';
        wrapper.innerHTML = `<span>${escapeHtml(field.label)}</span>`;
        let input;
        if (Array.isArray(field.options) && field.options.length > 0) {
          input = document.createElement('select');
          field.options.forEach((option) => {
            const node = document.createElement('option');
            node.value = option;
            node.textContent = option;
            input.appendChild(node);
          });
          input.value = String(field.default);
        } else {
          input = document.createElement('input');
          input.type = 'number';
          input.step = (field.name === 'age' || field.name.includes('height') || field.name.includes('weight')) ? '0.1' : '0.01';
          input.value = field.default;
        }
        input.id = `field-${field.name}`;
        fieldInputs[field.name] = input;
        wrapper.appendChild(input);
        container.appendChild(wrapper);
      });
    }

    function getSelectedArtifactGroup() {
      const groups = state.dashboard.artifact_groups || [];
      if (groups.length === 0) return null;
      if (state.selectedArtifactGroup) {
        const found = groups.find((group) => group.name === state.selectedArtifactGroup);
        if (found) return found;
      }
      return groups[0];
    }

    function renderArtifactSelection() {
      const groups = state.dashboard.artifact_groups || [];
      const nav = document.getElementById('artifact-nav');
      const selectedGroup = getSelectedArtifactGroup();

      if (groups.length === 0) {
        nav.innerHTML = '<div class="empty">暂无产物可展示。</div>';
        document.getElementById('artifact-list').innerHTML = '';
        document.getElementById('artifact-preview').textContent = '暂无产物可展示。';
        return;
      }

      nav.innerHTML = groups.map((group) => `
        <button class="${selectedGroup && group.name === selectedGroup.name ? 'active' : ''}" data-group="${escapeHtml(group.name)}">
          <span>${escapeHtml(group.label || group.name)}</span>
          <span class="meta">${group.file_count || 0} 个文件${group.exists ? '' : ' · 缺失'}</span>
        </button>
      `).join('');
      nav.querySelectorAll('button[data-group]').forEach((button) => {
        button.addEventListener('click', () => {
          state.selectedArtifactGroup = button.dataset.group;
          state.selectedArtifactFile = null;
          renderArtifactSelection();
        });
      });

      const files = (selectedGroup.files || []).slice();
      const list = document.getElementById('artifact-list');
      const title = document.getElementById('artifact-panel-title');
      const note = document.getElementById('artifact-panel-note');

      title.textContent = selectedGroup.label || selectedGroup.name;
      note.textContent = `${selectedGroup.file_count || 0} 个文件，点击任意文件即可查看原图或原始内容。`;

      if (files.length === 0) {
        list.innerHTML = '<div class="empty">当前分类没有文件。</div>';
        document.getElementById('artifact-preview').textContent = '当前分类没有文件。';
        return;
      }

      if (!state.selectedArtifactFile || !files.includes(state.selectedArtifactFile)) {
        state.selectedArtifactFile = files[0];
      }

      list.innerHTML = files.map((filePath) => {
        const kind = inferArtifactKind(filePath);
        const badge = kind === 'image' ? '图片' : kind === 'pdf' ? 'PDF' : kind === 'text' ? '文本' : '二进制';
        return `
          <button class="file-button ${state.selectedArtifactFile === filePath ? 'active' : ''}" data-file="${escapeHtml(filePath)}">
            <span>${escapeHtml(filePath)}</span>
            <span class="meta">${badge} · ${escapeHtml(getArtifactSrc(filePath))}</span>
          </button>
        `;
      }).join('');
      list.querySelectorAll('button[data-file]').forEach((button) => {
        button.addEventListener('click', () => {
          state.selectedArtifactFile = button.dataset.file;
          renderArtifactSelection();
        });
      });
      renderArtifactPreview(state.selectedArtifactFile, selectedGroup.name);
    }

    async function renderArtifactPreview(filePath, groupName) {
      const preview = document.getElementById('artifact-preview');
      const src = getArtifactSrc(filePath);
      const kind = inferArtifactKind(filePath);
      document.getElementById('artifact-panel-title').textContent = groupName || '产物详情';
      document.getElementById('artifact-panel-note').textContent = `当前文件：${filePath}`;
      if (kind === 'image') {
        preview.innerHTML = `
          <div class="preview-meta">${escapeHtml(filePath)}</div>
          <img src="${src}" alt="${escapeHtml(filePath)}" />
          <div class="preview-actions">
            <button class="btn btn-secondary" data-src="${escapeHtml(src)}" onclick="openArtifactInNewTab(this.dataset.src)">打开原图</button>
            <button class="btn btn-ghost" data-text="${escapeHtml(filePath)}" onclick="copyText(this.dataset.text)">复制路径</button>
          </div>
        `;
        return;
      }
      if (kind === 'pdf') {
        preview.innerHTML = `
          <div class="preview-meta">${escapeHtml(filePath)}</div>
          <iframe src="${src}" title="${escapeHtml(filePath)}"></iframe>
          <div class="preview-actions">
            <button class="btn btn-secondary" data-src="${escapeHtml(src)}" onclick="openArtifactInNewTab(this.dataset.src)">打开文件</button>
            <button class="btn btn-ghost" data-text="${escapeHtml(filePath)}" onclick="copyText(this.dataset.text)">复制路径</button>
          </div>
        `;
        return;
      }
      if (kind === 'text') {
        preview.innerHTML = `
          <div class="preview-meta">${escapeHtml(filePath)}</div>
          <div class="preview-text" id="artifact-text-loading">正在加载内容...</div>
          <div class="preview-actions">
            <button class="btn btn-secondary" data-src="${escapeHtml(src)}" onclick="openArtifactInNewTab(this.dataset.src)">打开原文件</button>
            <button class="btn btn-ghost" data-text="${escapeHtml(filePath)}" onclick="copyText(this.dataset.text)">复制路径</button>
          </div>
        `;
        try {
          const response = await fetch(src);
          const text = await response.text();
          const holder = document.getElementById('artifact-text-loading');
          if (holder) {
            holder.textContent = text || '文件为空。';
          }
        } catch (error) {
          const holder = document.getElementById('artifact-text-loading');
          if (holder) {
            holder.textContent = `加载失败：${error}`;
          }
        }
        return;
      }
      preview.innerHTML = `
        <div class="preview-meta">${escapeHtml(filePath)}</div>
        <div class="empty">当前文件类型暂不支持内嵌预览，可以直接打开原文件查看。</div>
        <div class="preview-actions">
          <button class="btn btn-secondary" data-src="${escapeHtml(src)}" onclick="openArtifactInNewTab(this.dataset.src)">打开原文件</button>
          <button class="btn btn-ghost" data-text="${escapeHtml(filePath)}" onclick="copyText(this.dataset.text)">复制路径</button>
        </div>
      `;
    }

    function renderPrediction(result) {
      const head = document.getElementById('prediction-head');
      const box = document.getElementById('prediction-result');
      const branches = document.getElementById('prediction-branches');
      if (!result || !result.success) {
        head.innerHTML = '<span class="chip">预测失败</span>';
        box.textContent = result?.message || '预测失败';
        branches.innerHTML = '';
        return;
      }
      if (result.message && !result.sklearn && !result.manual) {
        head.innerHTML = '';
        box.textContent = result.message;
        branches.innerHTML = '';
        return;
      }
      const chips = [];
      if (result.recommended_model) chips.push(`推荐模型：${result.recommended_model}`);
      if (result.recommended_result) chips.push(`推荐结果：${result.recommended_result}`);
      head.innerHTML = chips.map((item) => `<span class="chip">${escapeHtml(item)}</span>`).join('');
      box.textContent = JSON.stringify(result, null, 2);

      const renderBranch = (title, branch) => {
        if (!branch) return '';
        return `
          <div class="branch-card">
            <div class="branch-title">${escapeHtml(title)}</div>
            ${(branch.models || []).map((model) => `
              <div class="stack" style="padding-top: 10px; border-top: 1px solid var(--line);">
                <div><strong>${escapeHtml(model.name)}</strong></div>
                <div>预测：${escapeHtml(model.prediction || '-')}</div>
                <div class="muted">参数：${escapeHtml(JSON.stringify(model.best_parameters || {}, null, 2))}</div>
                <div class="muted">概率分布：</div>
                <ul class="prob-list">
                  ${(model.probabilities || []).map((item) => `<li>${escapeHtml(item.label)}：${formatMetric(item.probability)}</li>`).join('')}
                </ul>
              </div>
            `).join('')}
            <div class="muted">推荐结果：${escapeHtml(branch.recommended_result || '-')}</div>
          </div>
        `;
      };

      branches.innerHTML = [
        renderBranch('sklearn 结果', result.sklearn),
        renderBranch('手搓模型结果', result.manual),
      ].filter(Boolean).join('');
    }

    function getTrainingMode() {
      const selected = document.querySelector('input[name="training_mode"]:checked');
      return selected ? selected.value : state.selectedTrainingMode || 'train';
    }

    function collectPayload() {
      const payload = {};
      SAMPLE_FIELDS.forEach((field) => {
        const input = fieldInputs[field.name];
        if (!input) return;
        if (Array.isArray(field.options) && field.options.length > 0) {
          payload[field.name] = input.value;
        } else {
          payload[field.name] = Number(input.value);
        }
      });
      return payload;
    }

    function resetPredictionForm() {
      SAMPLE_FIELDS.forEach((field) => {
        const input = fieldInputs[field.name];
        if (!input) return;
        input.value = field.default;
      });
    }

    function renderDashboard(data) {
      state.dashboard = data;
      renderOverview(data);
      renderTrainingModes(data);
      renderComparison(data.comparison_rows || []);
      renderFields(data.sample_fields || SAMPLE_FIELDS);
      renderArtifactSelection();
      renderPrediction({ success: true, message: '等待提交预测...' });
      document.getElementById('training-status').textContent = [
        `摘要状态：${data.status || '-'}`,
        `生成时间：${data.generated_at || '-'}`,
        `训练路线：${data.overview?.training_mode_label || '-'}`,
        `推荐模型：${data.overview?.recommended_model ? `${data.overview.recommended_model.family} / ${data.overview.recommended_model.name}` : '-'}`,
        '',
        '参数摘要：',
        ...(data.parameter_rows || []).slice(0, 8).map((row) => `- ${row.family}/${row.name}: ${JSON.stringify(row.parameters)}`),
      ].join('\\n');
    }

    async function refreshDashboard() {
      const response = await fetch('/api/v1/dashboard');
      const payload = await response.json();
      if (!payload.success) {
        state.dashboard = INITIAL_DASHBOARD;
        renderDashboard(state.dashboard);
        return;
      }
      renderDashboard(payload.data);
      showView(state.selectedView || getCurrentViewFromHash());
    }

    async function startTraining() {
      const response = await fetch('/api/v1/train', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ training_mode: getTrainingMode() }),
      });
      const payload = await response.json();
      document.getElementById('training-status').textContent = payload.message || '训练请求已提交。';
    }

    async function submitPrediction() {
      const payload = collectPayload();
      const response = await fetch('/api/v1/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      renderPrediction(data);
    }

    function downloadDashboard() {
      const blob = new Blob([JSON.stringify(state.dashboard, null, 2)], { type: 'application/json;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'training_dashboard.json';
      a.click();
      URL.revokeObjectURL(url);
    }

    function openArtifactInNewTab(src) {
      window.open(src, '_blank', 'noopener,noreferrer');
    }

    async function copyText(text) {
      try {
        await navigator.clipboard.writeText(text);
      } catch (error) {
        console.warn('复制失败', error);
      }
    }

    function openSelectedArtifact() {
      const group = getSelectedArtifactGroup();
      if (!group || !state.selectedArtifactFile) return;
      openArtifactInNewTab(getArtifactSrc(state.selectedArtifactFile));
    }

    function copySelectedArtifactPath() {
      if (!state.selectedArtifactFile) return;
      copyText(state.selectedArtifactFile);
    }

    function bindHashNavigation() {
      window.addEventListener('hashchange', () => {
        showView(getCurrentViewFromHash());
      });
    }

    function bootstrap() {
      renderDashboard(state.dashboard);
      bindHashNavigation();
      showView(getCurrentViewFromHash());
    }

    bootstrap();
  </script>
</body>
</html>"""
    return (
        template
        .replace('__DASHBOARD_JSON__', dashboard_json)
        .replace('__SAMPLE_FIELDS_JSON__', sample_fields_json)
        .replace('__TRAINING_MODES_JSON__', training_modes_json)
    )
