from pathlib import Path


# 返回包含源码、配置和数据目录的项目根目录
def get_project_root() -> Path:
    """返回当前安装源码对应的项目根目录。"""
    return Path(__file__).resolve().parents[2]


# 阻止配置路径越出项目目录
def _ensure_inside_project(project_root: Path, path: Path, field_name: str) -> None:
    if path != project_root and project_root not in path.parents:
        raise ValueError(f"{field_name}不能位于项目目录之外")


# 解析并校验所有读写路径
def get_project_paths(project_root: Path, config: dict) -> dict[str, Path]:
    """解析项目路径，并阻止任何输出覆盖原始 CSV。"""
    project_root = project_root.resolve()
    relative_paths = {
        "raw_data": config["data"]["raw_path"],
        "processed_dir": config["paths"]["processed_dir"],
        "output_dir": config["paths"]["output_dir"],
        "audit_report_dir": config["audit"]["report_dir"],
        "figures_dir": config["outputs"]["figures_dir"],
        "metrics_dir": config["outputs"]["metrics_dir"],
        "models_dir": config["outputs"]["models_dir"],
        "reports_dir": config["outputs"]["reports_dir"],
    }
    paths = {name: (project_root / value).resolve() for name, value in relative_paths.items()}
    labels = {
        "raw_data": "原始数据路径", "processed_dir": "处理数据目录",
        "output_dir": "输出目录", "audit_report_dir": "审查报告目录",
        "figures_dir": "图表目录", "metrics_dir": "指标目录",
        "models_dir": "模型目录", "reports_dir": "报告目录",
    }
    for name, path in paths.items():
        _ensure_inside_project(project_root, path, labels[name])
    raw_data = paths["raw_data"]
    write_paths = [path for name, path in paths.items() if name != "raw_data"]
    if any(path == raw_data for path in write_paths):
        raise ValueError("输出路径不能覆盖原始数据文件")
    if paths["processed_dir"] == paths["output_dir"]:
        raise ValueError("处理数据目录和输出目录不能相同")
    if any(path == project_root for path in write_paths):
        raise ValueError("处理数据目录和输出目录不能直接使用项目根目录")
    for name in ("audit_report_dir", "figures_dir", "metrics_dir", "models_dir", "reports_dir"):
        if paths[name] != paths["output_dir"] and paths["output_dir"] not in paths[name].parents:
            raise ValueError(f"{labels[name]}必须位于输出目录内")
    if not raw_data.is_file():
        raise FileNotFoundError("原始数据文件不存在或不是普通文件")
    return paths
