from streamlit.testing.v1 import AppTest

from application.workflows import load_workflow_context


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


# 验证性能页只为存在真实逐轮历史的模型显示训练曲线标签页。
def test_performance_tabs_follow_saved_training_history() -> None:
    app = AppTest.from_file("src/app.py", default_timeout=45).run()

    app.radio(key="navigation").set_value("模型性能分析").run()
    assert "训练曲线" not in [tab.label for tab in app.tabs]

    app.selectbox[0].set_value("sklearn_mlp").run()
    assert "训练曲线" in [tab.label for tab in app.tabs]
    assert not app.exception


# 验证页面预测仍返回七类概率且训练页刷新不会自动改写模型。
def test_prediction_runs_and_training_page_does_not_train_on_render() -> None:
    _, paths = load_workflow_context()
    model_path = paths["models_dir"] / "sklearn_logistic.joblib"
    modified_before = model_path.stat().st_mtime_ns
    app = AppTest.from_file("src/app.py", default_timeout=45).run()

    app.radio(key="navigation").set_value("肥胖风险预测").run()
    prediction_button = next(
        button for button in app.button if button.label == "开始预测"
    )
    prediction_button.click().run()
    assert "prediction_result" in app.session_state
    assert len(app.session_state["prediction_result"]["probabilities"]) == 7
    assert "prediction_result_is_new" not in app.session_state
    app.run()
    assert "prediction_result" in app.session_state
    assert "prediction_result_is_new" not in app.session_state

    app.radio(key="navigation").set_value("模型训练中心").run()
    app.run()
    assert model_path.stat().st_mtime_ns == modified_before
