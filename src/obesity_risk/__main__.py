from obesity_risk.config import load_config
from obesity_risk.paths import get_project_paths, get_project_root


# 检查默认配置和项目基础路径，不读取原始数据内容
def main() -> int:
    try:
        project_root = get_project_root()
        config = load_config(project_root / "config" / "default.yaml")
        get_project_paths(project_root, config)
    except (FileNotFoundError, ValueError) as error:
        print(f"项目检查失败：{error}")
        return 1

    print("项目配置检查通过")
    print("原始数据文件已找到")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
