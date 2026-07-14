import argparse
from pathlib import Path

from application.workflows import (
    build_model_comparison,
    load_workflow_context,
    prepare_workflow_data,
    run_all,
    run_audit_workflow,
    write_experiment_summary,
)
from data.eda import run_eda
from model.training import train_manual_models, train_sklearn_models

COMMANDS = (
    "audit-data",
    "prepare-data",
    "run-eda",
    "train-sklearn",
    "train-manual",
    "evaluate",
    "run-all",
)


# 创建保持简洁的非 UI 命令行解析器
def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python src/main.py")
    parser.add_argument("command", nargs="?", choices=COMMANDS)
    parser.add_argument("--config", type=Path, help="YAML 配置路径")
    parser.add_argument("--model", choices=("logistic", "mlp"), help="仅训练一个算法")
    return parser


# 执行一个已解析的项目命令
def _execute_command(
    command: str | None, config: dict, paths: dict, model: str | None
) -> str:
    if command is None:
        return "项目配置检查通过，原始数据文件已找到"
    if command == "audit-data":
        run_audit_workflow(config, paths)
        return "数据只读审查完成，原始数据保持不变"
    if command == "prepare-data":
        prepare_workflow_data(config, paths)
        return "数据清洗、分层划分和无泄漏预处理完成"
    if command == "run-eda":
        cleaned, schema, _ = prepare_workflow_data(config, paths)
        run_eda(
            cleaned,
            schema,
            paths["figures_dir"],
            paths["figures_dir"].parent,
            config["eda"],
            int(config["split"]["random_seed"]),
        )
        return "探索性数据分析与图表生成完成"
    if command in ("train-sklearn", "train-manual"):
        _, _, prepared = prepare_workflow_data(config, paths)
        if command == "train-sklearn":
            train_sklearn_models(
                prepared, config, paths["models_dir"], paths["metrics_dir"], model
            )
            return "sklearn 模型训练与评估完成"
        train_manual_models(
            prepared, config, paths["models_dir"], paths["metrics_dir"], model
        )
        return "NumPy 手写模型训练与评估完成"
    if command == "evaluate":
        _, summary = build_model_comparison(paths)
        write_experiment_summary(paths, summary)
        return f"四模型统一比较完成，部署模型：{summary['selected_model']}"
    if command == "run-all":
        result = run_all(config, paths)
        selected_model = result["selected_model"]
        return f"全部非 UI 流程完成，部署模型：{selected_model}"
    raise ValueError(f"不支持的命令：{command}")


# 解析命令、集中处理用户可见错误并返回退出码
def main(argv: list[str] | None = None) -> int:
    # 运行肥胖风险预测项目的命令行入口。
    args = _build_parser().parse_args(argv)
    try:
        config, paths = load_workflow_context(args.config)
        message = _execute_command(args.command, config, paths, args.model)
    except (
        FileNotFoundError,
        OSError,
        ValueError,
        RuntimeError,
        FloatingPointError,
    ) as error:
        print(f"项目运行失败：{error}")
        return 1
    print(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
