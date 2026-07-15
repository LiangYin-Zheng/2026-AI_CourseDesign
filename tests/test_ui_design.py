from pathlib import Path


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
