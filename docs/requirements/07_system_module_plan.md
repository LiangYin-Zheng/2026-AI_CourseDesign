# 系统模块规划

## 当前非 UI 核心实际结构

```text
config/
└── default.yaml
src/
└── obesity_risk/
    ├── __init__.py
    ├── __main__.py
    ├── audit_report.py
    ├── config.py
    ├── data_audit.py
    ├── data_loader.py
    ├── eda.py
    ├── evaluation.py
    ├── io_utils.py
    ├── manual_models.py
    ├── paths.py
    ├── predictor.py
    ├── preparation.py
    ├── training.py
    ├── workflows.py
    └── schema.py
tests/
├── test_config.py
├── test_paths.py
└── test_*.py
```

`data/obesity_level.csv` 始终只读；划分/预处理元数据位于 `data/processed/`，EDA、四模型、指标和实验总结位于 `outputs/`。真实完整流程运行前后原始文件快照一致。

## 后续阶段规划结构

核心包保持扁平结构，避免为当前规模建立过深目录。阶段五只新增实际 UI 所需模块，并直接消费 `predictor.py` 与现有输出，不复制训练逻辑。

## 模块清单

| 模块 | 阶段/状态 | 职责 | 建议文件 | 测试重点 |
|---|---|---|---|---|
| 配置 | 阶段二已实现 | 读取并校验当前 YAML 配置 | `config.py` | 缺项、类型、比例和关键值 |
| 路径 | 阶段二已实现 | 固定根目录解析、路径防逃逸和原始数据保护 | `paths.py` | 越界、覆盖、目录冲突、文件缺失 |
| CLI 入口 | 阶段四已实现 | 调用七个非 UI 工作流命令 | `__main__.py` | 命令 smoke 与错误退出码 |
| 数据读取/质量 | 阶段三第一步已实现 | 只读加载 CSV、Schema 与质量检查、结构化报告 | `data_loader.py`、`schema.py`、`data_audit.py`、`audit_report.py` | 缺文件、格式错误、输入不变、统计和序列化 |
| 数据划分/预处理 | 阶段三已实现 | 固定分层三分和训练集拟合预处理 | `preparation.py` | 互斥、复现、无泄漏 |
| EDA/模型/评估/产物 | 阶段三至四已实现 | 分析、四模型训练、统一评估和产物保存 | `eda.py`、`training.py`、`manual_models.py`、`evaluation.py`、`workflows.py` | 指标、接口、可复现和公平比较 |
| 预测服务 | 阶段四已实现 | 重载最佳模型并提供单条/批量结构化预测 | `predictor.py` | schema、概率、错误提示、免责声明 |
| 应用服务/交互页面 | 阶段五规划 | 五页面展示、训练、预测和比较 | `app/` | 输入校验、状态、结果和免责声明 |

## 调用关系

```mermaid
flowchart LR
    ENTRY["简单入口"] --> CFG["配置/路径"]
    UI["交互页面"] --> SVC["应用服务"]
    SVC --> CFG
    FUTURE["后续业务入口"] --> DATA["数据读取/质量/划分/预处理"]
    SVC --> DATA
    DATA --> EDA["EDA"]
    DATA --> SK["sklearn 模型"]
    DATA --> MAN["手写模型"]
    SK --> EVAL["统一评估"]
    MAN --> EVAL
    EDA --> ART["产物管理"]
    EVAL --> ART
    ART --> SVC
```

## 配置规划

当前 `config/default.yaml` 已包含数据、划分、预处理、训练、优化、EDA 和输出配置；尚未增加 UI 参数。

固定初值候选：`random_seed: 42`、训练/验证/测试 `0.70/0.15/0.15`、目标精确值 `0be1dad`、排除列 `[id]`。数值和类别字段清单必须与数据 schema 校验，不能默默忽略拼写错误。

## 输出规划

- `outputs/figures/<run_id>/`：PNG/SVG 图表与图表说明索引。
- `outputs/metrics/<run_id>/`：JSON 指标、CSV 对比、分类报告、运行元数据。
- `outputs/models/<run_id>/`：模型、预处理器、标签映射、输入 schema、清单和校验信息。
- 进入阶段三实验运行后，根据实际记录需求决定日志的保存方式和目录。
- 自动产物默认不与源代码提交混合；报告选用的稳定图表按交付策略另行纳入。

## 测试规划

- 当前测试为 `tests/test_config.py` 和 `tests/test_paths.py`。
- 阶段三及以后可按实际规模增加数据、模型、集成和界面测试；不提前建立空目录。
- 测试命令统一为 `python -m pytest`。
