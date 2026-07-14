from streamlit.testing.v1 import AppTest


# 验证六个主页面均可在真实产物下完成首屏渲染。
def test_all_ui_pages_render_without_exception() -> None:
    pages = (
        "系统概览",
        "肥胖风险预测",
        "模型性能分析",
        "数据探索分析",
        "模型训练中心",
        "项目说明",
    )
    app = AppTest.from_file("src/app.py", default_timeout=45).run()

    assert not app.exception
    for page in pages[1:]:
        app.radio(key="navigation").set_value(page).run()
        assert not app.exception, page
