# 肥胖风险预测系统设计

本项目肥胖风险预测系统设计，是基于仓库内 `data/obesity_level.csv` 完成可复现的肥胖等级多分类流程。当前已完成数据处理、EDA、sklearn 模型、NumPy 手写模型、统一评估、核心预测接口和 Streamlit 交互界面；正式 Word 报告、实习日志和周汇报 PPT 尚未完成。预测仅用于课程演示，不构成医学诊断或健康建议。

## 环境与依赖

- macOS / Apple Silicon；
- 使用项目指定的 Python 3.10 Conda 环境：`/Users/liang/dev/envs/workspace`；
- Python 3.10.20；
- NumPy、pandas、scikit-learn、Matplotlib、PyYAML、joblib、Streamlit、pytest。

## 启动交互界面

```bash
/Users/liang/dev/envs/workspace/bin/streamlit run src/app.py
```

界面包含系统概览、肥胖风险预测、模型性能分析、数据探索分析、模型训练中心和项目说明六个页面。预测页只加载当前活动模型；训练完成后会先保留为实验结果，只有用户明确点击“应用到预测页面”才会替换活动模型。

现有数据说明尚未正式确认部分缩写字段的完整含义、单位与 0/1 映射，因此界面使用“中文候选名 + 原字段名 + 真实观察范围/取值”的中性展示，避免将推测写成既定事实。

第二轮界面优化使用统一蓝灰设计令牌、圆角卡片、整行侧边导航、Plotly 模型对比图和响应式布局。Streamlit 主题与演示工具栏配置位于 `.streamlit/config.toml`，设计参考和许可证决策记录在 `docs/requirements/14_ui_visual_reference.md`。修改前后视觉截图保存于 `outputs/ui_screenshots/before/` 和 `outputs/ui_screenshots/after/`；该目录属于本地视觉验收产物，不进入版本控制。

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

## 当前实现状态

- 原始数据审查结果：20758 行、18 列、7 个目标类别，缺失单元格和完全重复行均为 0。
- 四类模型均已训练并保存：sklearn 逻辑回归、sklearn MLP、NumPy 手写逻辑回归、NumPy 手写神经网络。
- 统一测试命令为 `conda run -p /Users/liang/dev/envs/workspace env PYTHONPATH=src pytest -q`；最近一次结果为 85 passed、0 failed、0 skipped、11 warnings。
- 核心预测入口为 `model.predictor.load_predictor()`、`Predictor.predict_single()` 和 `Predictor.predict_batch()`；模型加载、输入校验和 UI 单条预测已接通，但尚无独立预测 CLI。
- 仍待完成：字段含义/单位确认、日志、周报 PPT 和正式课程报告。

## 非 UI 命令

```bash
conda run -p /Users/liang/dev/envs/workspace env PYTHONPATH=src python src/main.py audit-data
conda run -p /Users/liang/dev/envs/workspace env PYTHONPATH=src python src/main.py prepare-data
conda run -p /Users/liang/dev/envs/workspace env PYTHONPATH=src python src/main.py run-eda
conda run -p /Users/liang/dev/envs/workspace env PYTHONPATH=src python src/main.py train-sklearn
conda run -p /Users/liang/dev/envs/workspace env PYTHONPATH=src python src/main.py train-manual
conda run -p /Users/liang/dev/envs/workspace env PYTHONPATH=src python src/main.py evaluate
conda run -p /Users/liang/dev/envs/workspace env PYTHONPATH=src python src/main.py run-all
```

训练命令会更新处理数据、模型和评估输出；预测页面应只加载已有模型，不应在每次请求中调用训练命令。

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
