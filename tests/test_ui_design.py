import json
from pathlib import Path

from data.loader import load_csv_readonly
from ui.pages import _eda_figure


# 验证项目主题精简工具栏并统一基础视觉颜色。
def test_streamlit_theme_is_configured_for_course_demo() -> None:
    config = Path(".streamlit/config.toml").read_text(encoding="utf-8")

    assert 'toolbarMode = "minimal"' in config
    assert 'showErrorDetails = "none"' in config
    assert 'primaryColor = "#2563EB"' in config
    assert 'backgroundColor = "#F6F8FB"' in config
    assert 'showSidebarNavigation = false' in config


# 验证集中样式包含完整设计令牌和响应式规则。
def test_ui_styles_define_shared_design_tokens() -> None:
    styles = Path("src/ui/styles.py").read_text(encoding="utf-8")
    required_tokens = (
        "--color-primary:",
        "--color-background:",
        "--color-text-secondary:",
        "--color-border:",
        "--radius-sm:",
        "--radius-xl:",
        "--shadow-sm:",
        "--shadow-hover:",
        "--space-1:",
        "--space-8:",
    )

    assert all(token in styles for token in required_tokens)
    assert "PingFang SC" in styles
    assert "@media (max-width: 1100px)" in styles
    assert "@media (max-width: 760px)" in styles
    assert "nth-child" not in styles


# 验证模型对比已使用 Plotly，训练摘要不再默认输出原始 JSON。
def test_pages_use_plotly_and_human_readable_training_summary() -> None:
    pages = Path("src/ui/pages.py").read_text(encoding="utf-8")

    assert "plotly.graph_objects" in pages
    assert "parameter_summary_frame" in pages
    assert 'st.json(parameters)' not in pages


# 验证侧边导航和主按钮保持克制、清晰的选中与强调状态。
def test_navigation_and_primary_button_styles_are_unified() -> None:
    styles = Path("src/ui/styles.py").read_text(encoding="utf-8")

    assert "label[data-testid=\"stRadioOption\"] span:focus-visible" in styles
    assert "outline: none;" in styles
    assert 'button[kind="primary"] p' in styles
    assert 'button[kind="primaryFormSubmit"] p' in styles
    assert "color: #FFFFFF;" in styles


# 验证 EDA 主展示由只读真实数据生成现代交互图表。
def test_eda_uses_readonly_data_and_plotly_figures() -> None:
    pages = Path("src/ui/pages.py").read_text(encoding="utf-8")

    assert "def _eda_figure(" in pages
    assert "load_csv_readonly(paths[\"raw_data\"])" in pages
    assert 'st.plotly_chart(figure, width="stretch"' in pages


# 验证全部 EDA 展示主题都能由真实只读数据生成图表。
def test_all_eda_display_figures_render_from_real_data() -> None:
    frame = load_csv_readonly(Path("data/obesity_level.csv"))
    summary = json.loads(Path("outputs/eda/eda_summary.json").read_text(encoding="utf-8"))
    chart_names = (
        "年龄分布",
        "身高分布",
        "体重分布",
        "目标类别分布",
        "类别特征频数",
        "关键特征分组关系",
        "年龄身高体重关系",
        "相关性热力图",
    )

    for chart_name in chart_names:
        figure = _eda_figure(chart_name, frame, summary)
        assert figure.data
        assert figure.layout.height >= 450
