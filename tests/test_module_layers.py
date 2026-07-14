# 验证顶层分层包可以直接协同导入。

from application.workflows import run_all
from core.config import load_config
from data.preparation import PreparedData
from evaluation import evaluate_predictions
from evaluation.metrics import evaluate_predictions as evaluate_predictions_impl
from model import ManualLogisticRegression
from model.manual_logistic import ManualLogisticRegression as ManualLogisticRegressionImpl


# 验证核心、数据、模型和应用层可以同时导入。
def test_layered_packages_import_together() -> None:
    assert callable(load_config)
    assert PreparedData.__name__ == "PreparedData"
    assert callable(run_all)


# 验证模型包入口和具体实现指向同一模型类型。
def test_model_package_exports_single_implementation() -> None:
    assert ManualLogisticRegression is ManualLogisticRegressionImpl


# 验证评估包入口和指标实现指向同一函数。
def test_evaluation_package_exports_single_implementation() -> None:
    assert evaluate_predictions is evaluate_predictions_impl
