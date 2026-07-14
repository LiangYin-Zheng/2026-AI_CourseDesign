import json
from pathlib import Path

from obesity_risk.workflows import MODEL_NAMES, build_model_comparison


def make_paths(tmp_path: Path) -> dict[str, Path]:
    metrics_dir = tmp_path / "metrics"
    models_dir = tmp_path / "models"
    metrics_dir.mkdir()
    models_dir.mkdir()
    return {"metrics_dir": metrics_dir, "models_dir": models_dir}


def write_model_result(
    paths: dict[str, Path],
    model_name: str,
    validation_macro_f1: float,
    validation_accuracy: float,
    test_macro_f1: float,
    test_accuracy: float,
    training_time: float,
) -> None:
    result = {
        "model_name": model_name,
        "display_name": model_name,
        "validation_metrics": {
            "macro_f1": validation_macro_f1,
            "accuracy": validation_accuracy,
        },
        "test_metrics": {
            "macro_f1": test_macro_f1,
            "accuracy": test_accuracy,
            "macro_precision": test_macro_f1,
            "macro_recall": test_macro_f1,
            "weighted_f1": test_macro_f1,
        },
        "training_time_seconds": training_time,
        "inference_time_seconds": 0.01,
    }
    metric_path = paths["metrics_dir"] / f"{model_name}_metrics.json"
    metric_path.write_text(json.dumps(result), encoding="utf-8")
    (paths["models_dir"] / f"{model_name}.joblib").write_text(
        model_name, encoding="utf-8"
    )


def write_default_results(paths: dict[str, Path]) -> None:
    values = {
        "sklearn_logistic": (0.80, 0.81, 0.99, 0.99, 0.4),
        "sklearn_mlp": (0.92, 0.91, 0.80, 0.82, 0.8),
        "manual_logistic": (0.75, 0.77, 0.70, 0.72, 0.3),
        "manual_mlp": (0.85, 0.86, 0.90, 0.91, 0.6),
    }
    for model_name in MODEL_NAMES:
        write_model_result(paths, model_name, *values[model_name])


def test_deployment_selection_uses_validation_while_test_table_keeps_test_ranking(
    tmp_path: Path,
) -> None:
    paths = make_paths(tmp_path)
    write_default_results(paths)

    comparison, summary = build_model_comparison(paths)

    assert summary["selected_model"] == "sklearn_mlp"
    assert summary["deployment_selection_metric"] == "validation_macro_f1"
    assert summary["test_ranking_metric"] == "test_macro_f1"
    assert comparison.iloc[0]["model_name"] == "sklearn_logistic"
    selected_row = comparison.loc[comparison["selected_for_deployment"]].iloc[0]
    assert selected_row["model_name"] == "sklearn_mlp"
    assert (paths["models_dir"] / "best_model.joblib").read_text(encoding="utf-8") == (
        "sklearn_mlp"
    )


def test_changing_only_test_metrics_does_not_change_deployment_selection(
    tmp_path: Path,
) -> None:
    paths = make_paths(tmp_path)
    write_default_results(paths)
    _, first_summary = build_model_comparison(paths)
    write_model_result(paths, "manual_logistic", 0.75, 0.77, 1.0, 1.0, 0.3)

    _, second_summary = build_model_comparison(paths)

    assert first_summary["selected_model"] == second_summary["selected_model"]


def test_changing_validation_macro_f1_changes_deployment_selection(tmp_path: Path) -> None:
    paths = make_paths(tmp_path)
    write_default_results(paths)
    write_model_result(paths, "manual_mlp", 0.95, 0.86, 0.50, 0.55, 0.6)

    _, summary = build_model_comparison(paths)

    assert summary["selected_model"] == "manual_mlp"


def test_deployment_tie_breaking_is_stable_and_recorded(tmp_path: Path) -> None:
    paths = make_paths(tmp_path)
    for model_name in MODEL_NAMES:
        write_model_result(paths, model_name, 0.9, 0.8, 0.7, 0.7, 1.0)

    _, summary = build_model_comparison(paths)
    best_metadata = json.loads(
        (paths["models_dir"] / "best_model.json").read_text(encoding="utf-8")
    )

    assert summary["selected_model"] == MODEL_NAMES[0]
    assert best_metadata["model_name"] == MODEL_NAMES[0]
    assert best_metadata["selection_metric"] == "validation_macro_f1"
    assert best_metadata["tie_breakers"] == [
        "validation_accuracy",
        "training_time_seconds",
        "fixed_model_order",
    ]
