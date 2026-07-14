import json
from pathlib import Path

import joblib

from ui.constants import CLASS_LABELS, MODEL_INFO
from ui.services import (
    activate_model,
    load_dashboard_data,
    load_example_sample,
    predict_sample,
    project_relative_path,
)


# 验证全部真实目标类别和四种模型都有中文展示信息
def test_ui_constants_cover_dataset_classes_and_models() -> None:
    expected_classes = {
        "0rmal_Weight",
        "Insufficient_Weight",
        "Overweight_Level_I",
        "Overweight_Level_II",
        "Obesity_Type_I",
        "Obesity_Type_II",
        "Obesity_Type_III",
    }

    assert set(CLASS_LABELS) == expected_classes
    assert set(MODEL_INFO) == {
        "sklearn_logistic",
        "sklearn_mlp",
        "manual_logistic",
        "manual_mlp",
    }


# 验证首页数据来自现有 CSV 和指标产物
def test_dashboard_data_uses_real_artifacts() -> None:
    dashboard = load_dashboard_data()

    assert dashboard["sample_count"] == 20758
    assert dashboard["feature_count"] == 16
    assert dashboard["class_count"] == 7
    assert dashboard["active_model"] in MODEL_INFO
    assert len(dashboard["comparison"]) == 4


# 验证示例输入可由真实活动模型完成七分类预测
def test_predict_example_with_real_bundle() -> None:
    sample = load_example_sample()
    result = predict_sample(sample)

    assert result["predicted_class"] in CLASS_LABELS
    assert len(result["probabilities"]) == 7
    assert abs(sum(result["probabilities"].values()) - 1.0) < 1e-6
    assert result["elapsed_ms"] >= 0


# 验证界面不暴露本机绝对路径
def test_project_relative_path_hides_absolute_prefix() -> None:
    relative = project_relative_path(
        Path("/Users/liang/workspace/nepu/2026-AI_CourseDesign/outputs/models/model.joblib"),
        Path("/Users/liang/workspace/nepu/2026-AI_CourseDesign"),
    )

    assert relative == "outputs/models/model.joblib"
    assert not relative.startswith("/")


# 验证应用模型时才会替换活动模型和元数据
def test_activate_model_copies_selected_bundle(tmp_path: Path) -> None:
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    source = models_dir / "manual_mlp.joblib"
    joblib.dump({"model_name": "manual_mlp"}, source)
    metrics_dir = tmp_path / "metrics"
    metrics_dir.mkdir()
    metric = {
        "model_name": "manual_mlp",
        "validation_metrics": {"macro_f1": 0.8},
    }
    (metrics_dir / "manual_mlp_metrics.json").write_text(
        json.dumps(metric), encoding="utf-8"
    )

    metadata = activate_model(
        "manual_mlp",
        {"models_dir": models_dir, "metrics_dir": metrics_dir},
    )

    assert joblib.load(models_dir / "best_model.joblib")["model_name"] == "manual_mlp"
    assert metadata["model_name"] == "manual_mlp"
    assert metadata["test_set_used_for_selection"] is False
    saved = json.loads((models_dir / "best_model.json").read_text(encoding="utf-8"))
    assert saved == metadata
