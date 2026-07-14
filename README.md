# 肥胖风险预测系统设计

本项目肥胖风险预测系统设计，是基于仓库内 `data/obesity_level.csv` 完成可复现的肥胖等级多分类流程。当前已完成除交互式 UI、正式 Word 报告、实习日志和周汇报 PPT 外的全部核心开发；预测仅用于课程演示，不构成医学诊断或健康建议。

## 环境与依赖

- macOS / Apple Silicon；
- 使用项目指定的 Python 3.10 Conda 环境（本机路径通过 `OBESITY_ENV` 传入）；
- Python 3.10；
- NumPy、pandas、scikit-learn、Matplotlib、PyYAML、joblib、pytest。

## 输出目录

```text
data/processed/                 固定划分索引、摘要、特征元数据、预处理器
outputs/data_audit/             JSON/Markdown 数据审查
outputs/eda/                    EDA 摘要、报告和六张 PNG
outputs/models/                 四模型、手写 NPZ、最佳模型 bundle
outputs/metrics/                单模型指标/报告/矩阵/损失与四模型比较
outputs/reports/                非 UI 核心实验总结
```

完整真实结果见 `outputs/metrics/model_comparison.csv` 和 `outputs/reports/experiment_summary.md`。当前共享预处理在保留标准化连续值的同时，增加仅由训练集拟合的 20 箱 quantile 数值分箱独热特征。部署模型为 `sklearn_mlp`，由验证集 macro F1（0.889690）选出；其测试集 Accuracy 为 0.882787，macro F1 为 0.869258。测试集 macro F1 排名仅用于最终展示，不参与部署选择。

## Git 提交规范

提交标题格式：

```text
<type>(<scope>): <description>
```

常用 `type`：

* `feat`：新增功能
* `fix`：修复问题
* `docs`：文档修改
* `refactor`：代码重构
* `test`：测试修改
* `chore`：日常维护
* `perf`：性能优化
* `build`：构建、依赖或配置
* `ci`：自动化流程
* `style`：仅格式调整

提交要求：

* 每个 Commit 只做一类事情，无关修改必须拆分。
* `scope` 应具体，避免使用 `project`、`misc`。
* `description` 使用“动作 + 对象”，例如：`补充训练说明`、`修复配置解析异常`。
* 源代码、配置、测试、文档和构建产物原则上分别提交。
* 提交前检查：

```bash
git status
git diff --cached
```

每次 Commit 必须使用两个 `-m`：

```bash
git commit \
    -m "<type>(<scope>): <简洁标题>" \
    -m "<说明修改内容、目的和作用。>"
```

AI 生成提交方案时：

* 按功能细粒度拆分。
* 给出可直接执行的 `git add` 和 `git commit` 命令。
* `git add` 明确列出文件，避免默认使用 `git add .`。
* 未经明确要求，不执行 `commit`、`push` 或创建 PR。
