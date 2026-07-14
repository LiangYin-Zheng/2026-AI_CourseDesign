# 肥胖风险预测系统设计

## 项目简介

本项目用于完成肥胖风险预测课程设计，通过 Python 逐步实现数据处理、分类模型和结果展示。当前处于基础工程初始化阶段。

## 当前阶段

当前工程仅包含：

- YAML 配置读取和基础校验；
- 项目路径解析；
- 原始数据路径保护；
- 基础运行检查；
- 配置与路径单元测试。

## 项目结构

```text
config/
└── default.yaml
src/
└── obesity_risk/
    ├── __init__.py
    ├── __main__.py
    ├── config.py
    └── paths.py
tests/
├── test_config.py
└── test_paths.py
README.md
pyproject.toml
```

## 环境要求

- Python 3.10
- PyYAML
- pytest

## 运行方法

```bash
PYTHONPATH=src python -m obesity_risk
```

## 运行测试

```bash
python -m pytest -v
```

## 当前未实现内容

- 数据清洗；
- 数据分析与可视化；
- 模型训练与评估；
- 手写算法；
- 正式交互界面。

## 数据保护

原始数据文件位于 `data/obesity_level.csv`。程序只检查该文件是否存在，不读取或覆盖其内容；后续处理结果必须保存到其他目录。
