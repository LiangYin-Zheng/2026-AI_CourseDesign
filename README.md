# 肥胖风险预测系统设计

一个面向《人工智能综合实践 / 课程设计》的完整机器学习项目示例。项目围绕肥胖风险预测展开，覆盖了**数据清洗、探索性分析、`sklearn` 建模、手搓模型实现、训练结果可视化、日志管理、桌面 GUI 演示与命令行推理**等完整流程。

> [!IMPORTANT]
> 本仓库中的命令都以**仓库根目录**为执行基准。

## 这个项目解决什么问题

很多课程设计项目只停留在“能训练出一个模型”，但很难把过程讲清楚、把结果展示清楚，也很难让别人拿到仓库后直接运行。本项目的目标不是只给出一个分类结果，而是把下面几件事一起做好：

- 让数据处理、建模、评估、可视化有一条完整主线。
- 同时保留 **工程化建模路线** 和 **算法原理实现路线** 两种视角。
- 给出适合答辩展示的图表、报告、日志和界面。
- 让命令、目录结构和运行方式都尽量可复现、可迁移、可共享。

## 项目特性

- **双训练路线**：同时支持 `sklearn` 模型族与手搓多分类模型族。
- **双入口模式**：本地桌面管理台与命令行推理并行保留，桌面端入口位于 `src/ui/desktop.py`。
- **统一训练进度**：训练阶段重点展示“全流程百分比进度”，减少终端噪音。
- **参数摘要输出**：训练完成后统一输出各模型优化后的关键参数。
- **项目级日志体系**：位于 `src/log/` 的统一日志模块，基于标准库 `logging` 封装终端和文件双输出、`DEBUG/INFO/NOTICE/WARNING/ERROR/CRITICAL` 分级、日志轮转与保留策略。
- **结构化源码组织**：主实现已按模块归档。

## 现在的源码结构

```text
src/
├── core/                   # 配置与共享契约
├── data_processing/          # 数据读取、清洗、切分
├── features/                 # 特征工程与预处理
├── models/                   # sklearn 模型、手搓模型、训练器
├── serving/                  # 共享推理与模型加载逻辑
├── log/                      # 项目级日志模块
├── utils/                    # 文件、进度等基础工具
├── reporting.py              # EDA 摘要与模型报告
├── visualization.py          # 图表绘制
└── ui/
    └── desktop.py            # Fluent 桌面管理台
```

### 目录划分背后的思路

- `data_processing/` 只负责“把数据变干净、可切分”。
- `features/` 只负责“把数据变成模型能吃的特征”。
- `models/` 只负责“训练、保存、加载模型”。
- 核心契约层与桌面界面分开，避免界面逻辑和字段定义散在多个目录。
- `serving/` 抽出两种界面都需要的推理共享逻辑，避免重复实现。

## 整体运行关系

```mermaid
flowchart LR
    A[原始数据 data/obesity_level.csv] --> B[data_processing]
    B --> C[reporting / EDA]
    B --> D[features / preprocessor]
    D --> E1[models / sklearn]
    D --> E2[models / manual]
    E1 --> F[output/ 模型、图表、报告、日志]
    E2 --> F
    F --> G1[ui/desktop.py 本地桌面 GUI]
    F --> G2[CLI 单样本预测]
```

## 快速开始

### 1. 准备环境

在仓库根目录执行：

```bash
python -m pip install -r requirements.txt
```

如果你已经在自己的虚拟环境中安装过依赖，可以直接跳过这一步。

### 2. 运行完整训练流程

```bash
python main.py train
```

这条命令会依次完成：

1. 读取并清洗数据
2. 生成 EDA 摘要与图表
3. 训练 `sklearn` 模型族
4. 训练手搓模型族
5. 汇总模型对比、参数摘要、报告与日志

### 3. 只运行某一条训练路线

仅训练 `sklearn`：

```bash
python main.py train-sklearn
```

仅训练手搓模型：

```bash
python main.py train-manual
```

如果只想查看命令列表，可以运行：

```bash
python main.py --help
```

## 桌面界面

### 桌面主界面

```bash
python main.py gui-local
```

这是当前主线入口，采用 PySide6 + qfluentwidgets 的 Fluent 风格桌面管理台。

命令行单样本预测：

```bash
python main.py predict --json '{"gender":"Male","age":24,"height_m":1.75,"weight_kg":85,"family_history_with_overweight":1,"high_calorie_food_frequency":1,"vegetable_intake_score":2.0,"main_meals_per_day":3.0,"snacking_frequency":"Sometimes","smokes":0,"water_intake_liters":2.0,"calorie_monitoring":0,"physical_activity_score":1.0,"technology_use_hours":1.0,"alcohol_consumption":"Sometimes","transportation_mode":"Automobile"}'
```

## 训练时会看到什么

训练日志优先展示：

- **全流程百分比进度**
- **当前阶段名称**
- **阶段性关键信息**，例如数据量、当前最佳 `Macro F1`
- **训练结束后的优化参数汇总**

## 日志系统说明

日志文件默认写入：

```text
output/logs/project.log
```

日志体系分为两层：

1. **运行时终端日志**：重点展示整体进度、关键状态和异常告警。
2. **文件日志**：写入 `output/logs/project.log`，记录更完整的项目运行信息，便于回溯和排错。

当前实现位于 `src/log/project.py`，基于标准库 `logging` 统一封装了项目级 logger、结构化组件字段、日志轮转和保留策略。

## 训练产物会输出到哪里

```text
output/
├── analysis/        # 清洗后数据、EDA 摘要
├── evaluation/      # 模型评估结果、训练仪表盘 JSON
├── figures/         # EDA 图、训练曲线、对比图
├── logs/            # 项目日志
├── models/          # 训练后模型与预处理器
├── predictions/     # 测试集预测结果
└── reports/         # Markdown 训练/评估报告
```

其中比较关键的产物包括：

- `output/evaluation/training_dashboard.json`
- `output/reports/final_summary.md`
- `output/reports/family_comparison_report.md`
- `output/logs/project.log`

## 测试命令

在仓库根目录执行：

```bash
python -m unittest tests/test_project_pipeline.py tests/test_sklearn_pipeline.py tests/test_progress.py -v
```

## 文档索引

- 方案设计：`docs/方案设计.md`
- 数据说明：`docs/数据说明.md`
- 测试说明：`docs/测试说明.md`
- 部署说明：`docs/部署说明.md`

## 当前已知边界

- 桌面界面与命令行推理都是本地演示模式，不包含生产级部署配置。
- README 提供的是通用根目录命令，具体 Python 环境由使用者自行选择。
- 单样本预测会同时尝试加载 `sklearn` 与手搓模型；如果训练只生成了其中一条链路，返回结果也会相应减少。

## Commit 提交规范
格式：`<type>(<scope>): <description>`

说明：
- `type` 表示提交类型
- `scope` 表示影响范围
- `description` 表示提交内容摘要，使用简洁、明确的中文或英文短语

`type` 说明：

| type | 适用场景 |
| --- | --- |
| `feat` | 新增功能、新入口、新流程 |
| `fix` | 修复 bug、异常处理、错误行为 |
| `docs` | README、说明文档、注释类文档修改 |
| `style` | 纯格式调整，不改变逻辑 |
| `refactor` | 重构内部实现，不新增功能也不修复问题 |
| `test` | 新增或调整测试 |
| `chore` | 零散维护、脚本、小工具、杂项整理 |
| `perf` | 性能优化 |
| `build` | 构建、打包、依赖、配置相关修改 |
| `ci` | CI/CD、自动化流程相关修改 |

`description` 写法：

- 用动词开头更自然，比如 `补充`、`修复`、`拆分`、`统一`、`优化`
- 尽量写成“动作 + 对象”，例如 `补充训练命令说明`
- 不要只写 `修改`、`更新`、`优化` 这种看不出内容的词
- 保持简短，通常一眼能看完即可

提交要求：

- 一次提交只做一类事情，避免把无关修改混在一起
- 如果这次改动能明显分成两类，优先拆成两个提交
- `scope` 尽量具体，避免写成过于宽泛的 `project`、`misc`
- 如果不确定 `type`，优先问自己：这次改动对用户是新增、修复，还是仅仅整理
- 如果不确定 `description`，优先描述结果，而不是描述过程
