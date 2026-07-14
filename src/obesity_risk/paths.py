from pathlib import Path


# 根据固定的 src 包布局确定项目根目录
def get_project_root() -> Path:
    return Path(__file__).resolve().parents[2]


# 确保配置路径不能离开项目目录
def _ensure_inside_project(project_root: Path, path: Path, field_name: str) -> None:
    if path != project_root and project_root not in path.parents:
        raise ValueError(f"{field_name}不能位于项目目录之外")


# 解析并检查原始数据、处理目录和输出目录
def get_project_paths(project_root: Path, config: dict) -> dict:
    project_root = project_root.resolve()
    raw_data = (project_root / config["data"]["raw_path"]).resolve()
    processed_dir = (project_root / config["paths"]["processed_dir"]).resolve()
    output_dir = (project_root / config["paths"]["output_dir"]).resolve()

    _ensure_inside_project(project_root, raw_data, "原始数据路径")
    _ensure_inside_project(project_root, processed_dir, "处理数据目录")
    _ensure_inside_project(project_root, output_dir, "输出目录")

    if processed_dir == raw_data or output_dir == raw_data:
        raise ValueError("输出路径不能覆盖原始数据文件")
    if processed_dir == output_dir:
        raise ValueError("处理数据目录和输出目录不能相同")
    if processed_dir == project_root or output_dir == project_root:
        raise ValueError("处理数据目录和输出目录不能直接使用项目根目录")
    if not raw_data.is_file():
        raise FileNotFoundError("原始数据文件不存在或不是普通文件")

    return {
        "root": project_root,
        "raw_data": raw_data,
        "processed_dir": processed_dir,
        "output_dir": output_dir,
    }
