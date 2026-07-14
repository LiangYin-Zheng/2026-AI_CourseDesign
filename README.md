# 肥胖风险预测系统设计

本项目肥胖风险预测系统设计，是基于仓库内 `data/obesity_level.csv` 完成可复现的肥胖等级多分类流程。当前已完成除交互式 UI、正式 Word 报告、实习日志和周汇报 PPT 外的全部核心开发；预测仅用于课程演示，不构成医学诊断或健康建议。

## 已完成功能

- 20,758×18 原始 CSV 的只读加载、Schema 与数据质量审查；
- 最小清洗、70/15/15 固定种子目标分层划分、训练集拟合的无泄漏预处理；
- Age、Height、Weight 等字段的单变量、双变量、多变量分析和相关性热力图；
- sklearn `LogisticRegression`、`MLPClassifier` 验证集参数选择；
- NumPy 手写 Softmax 逻辑回归和单隐藏层 ReLU 神经网络；
- 四模型统一分类指标、混淆矩阵、分类报告、耗时、测试集排名和实验总结；
- 按验证集 macro F1 选择部署模型，测试集只用于最终评估；
- 模型保存/重载以及带必填、数值范围、类别选项校验的单条、批量预测接口；
- `audit-data` 至 `run-all` 的命令行流程和快速自动化测试。

## 环境与依赖

- macOS / Apple Silicon；
- 使用项目指定的 Python 3.10 Conda 环境（本机路径通过 `OBESITY_ENV` 传入）；
- Python 3.10；
- NumPy、pandas、scikit-learn、Matplotlib、PyYAML、joblib、pytest。

所有命令均使用指定环境，项目不自动安装依赖：

```bash
export OBESITY_ENV=/path/to/python310-env
conda run -p "$OBESITY_ENV" python --version
conda run -p "$OBESITY_ENV" pip list
```

## 数据与配置

- 原始数据：`data/obesity_level.csv`，流程只读，禁止覆盖；
- 主配置：`config/default.yaml`；
- 随机种子、划分比例、预处理、模型候选和全部输出路径均来自配置；
- `id` 排除于模型输入；未构造 BMI，避免把可能直接关联目标定义的派生量引入为泄漏特征。

## 命令行运行

先在仓库根目录设置无界面绘图后端：

```bash
export PYTHONPATH=src
export MPLBACKEND=Agg
```

各命令如下：

```bash
conda run -p "$OBESITY_ENV" python -m obesity_risk audit-data
conda run -p "$OBESITY_ENV" python -m obesity_risk prepare-data
conda run -p "$OBESITY_ENV" python -m obesity_risk run-eda
conda run -p "$OBESITY_ENV" python -m obesity_risk train-sklearn
conda run -p "$OBESITY_ENV" python -m obesity_risk train-manual
conda run -p "$OBESITY_ENV" python -m obesity_risk evaluate
```

仅训练一个算法：

```bash
conda run -p "$OBESITY_ENV" python -m obesity_risk train-sklearn --model logistic
conda run -p "$OBESITY_ENV" python -m obesity_risk train-manual --model mlp
```

一键运行全部非 UI 流程：

```bash
conda run -p "$OBESITY_ENV" env PYTHONPATH=src MPLBACKEND=Agg python -m obesity_risk run-all
```

所有命令均支持 `--config <YAML 路径>`。

## 测试

```bash
conda run -p "$OBESITY_ENV" python -m compileall src tests
conda run -p "$OBESITY_ENV" pytest -q
```

测试覆盖配置/路径安全、Schema/审查、缺失与未知类别、分层与索引互斥、无 NaN 预处理、手写模型收敛与持久化、sklearn smoke、评估、EDA、预测接口和 CLI。

## 输出目录

```text
data/processed/                 固定划分索引、摘要、特征元数据、预处理器
outputs/data_audit/             JSON/Markdown 数据审查
outputs/eda/                    EDA 摘要、报告和六张 PNG
outputs/models/                 四模型、手写 NPZ、最佳模型 bundle
outputs/metrics/                单模型指标/报告/矩阵/损失与四模型比较
outputs/reports/                非 UI 核心实验总结
```

完整真实结果见 `outputs/metrics/model_comparison.csv` 和 `outputs/reports/experiment_summary.md`。当前部署模型为 `sklearn_mlp`，由验证集 macro F1（0.874530）选出；其测试集 Accuracy 为 0.868979，macro F1 为 0.854291。当前测试集 macro F1 排名第一同为 `sklearn_mlp`，但测试排名不参与部署选择。

## 后续 UI 预测接口

```python
from pathlib import Path

from obesity_risk.predictor import load_predictor

predictor = load_predictor(Path("outputs/models/best_model.joblib"))
single_result = predictor.predict_single(sample_dict)
batch_results = predictor.predict_batch(sample_dataframe)
```

结果包含预测类别、全部类别概率、最高概率、模型名称和非医学诊断声明。UI 尚未开发，后续页面应复用该接口和现有 EDA/指标产物，不在界面层重复训练逻辑。

预测器会统一拒绝缺失或空白必填字段、超出 Schema/训练范围的数值和训练集未出现的类别。`outputs/models/*.joblib` 与 `*.npz` 是可重建二进制文件，若本地不存在 `best_model.joblib`，请先运行 `run-all`。
