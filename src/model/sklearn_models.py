# sklearn 分类器构建和配置规范化。

from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier


def normalize_candidate(model_name: str, candidate: dict) -> dict:
    # 规范化 YAML 中 sklearn 需要元组的参数。
    normalized = dict(candidate)
    if model_name == "sklearn_mlp" and isinstance(
        normalized.get("hidden_layer_sizes"), list
    ):
        normalized["hidden_layer_sizes"] = tuple(normalized["hidden_layer_sizes"])
    return normalized


def build_sklearn_classifier(model_name: str, parameters: dict, config: dict) -> object:
    # 根据模型名和候选参数创建 sklearn 分类器。
    seed = int(config["split"]["random_seed"])
    if model_name == "sklearn_logistic":
        return LogisticRegression(
            **parameters,
            max_iter=int(config["training"][model_name]["max_iter"]),
            random_state=seed,
        )
    if model_name == "sklearn_mlp":
        model_config = config["training"][model_name]
        return MLPClassifier(
            **parameters,
            max_iter=int(model_config["max_iter"]),
            early_stopping=bool(model_config["early_stopping"]),
            validation_fraction=float(model_config["validation_fraction"]),
            random_state=seed,
        )
    raise ValueError(f"不支持的 sklearn 模型：{model_name}")
