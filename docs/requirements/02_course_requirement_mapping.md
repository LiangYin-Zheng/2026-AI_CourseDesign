# 课程要求追踪矩阵

状态取值：`已完成`、`已规划`、`待实现`、`待确认`。本表中的“已规划”不代表功能已完成。

| 编号 | 要求来源 | 原始要求摘要 | 实现方式 | 阶段 | 模块 | 对应测试/证据 | 报告章节 | 当前状态 |
|---|---|---|---|---:|---|---|---|---|
| CR-01 | 授课计划 | sklearn 完成选题主体 | sklearn Pipeline 与两类模型 | 3 | `src/model/sklearn_models.py`、`src/model/training.py` | `tests/test_training.py`、真实模型产物 | 第二部分 | 已完成 |
| CR-02 | 执行说明 | Python 自行实现核心算法 | NumPy 手写 Softmax 回归和前馈网络 | 4 | `src/model/manual_logistic.py`、`src/model/manual_mlp.py` | `tests/test_manual_models.py`、NPZ/指标 | 第三部分 | 已完成 |
| CR-03 | 授课计划/课题 | 数据读取、清洗和预处理 | schema、审查、最小清洗、训练拟合预处理 | 3 | `src/data/loader.py`、`src/data/preparation.py` | 数据/准备测试与处理产物 | 2.1/3.1 | 已完成 |
| CR-04 | 课题 | Age/Height/Weight 单变量分析 | 分布图、摘要、IQR/业务边界解释 | 3 | `src/data/eda.py` | `numeric_distributions.png`、EDA 报告 | 第二部分 | 已完成 |
| CR-05 | 课题 | 数值特征双变量分析 | 特征-目标箱线和分组统计 | 3 | `src/data/eda.py` | `key_features_by_target.png` | 第二部分 | 已完成 |
| CR-06 | 课题 | 数值特征多变量分析 | Age/Height/Weight 联合散点与分组统计 | 3 | `src/data/eda.py` | 联合图和 EDA JSON | 第二部分 | 已完成 |
| CR-07 | 课题 | 相关性热力图和结果分析 | 数值相关矩阵热力图，明确不代表因果 | 3 | `src/data/eda.py` | 热力图和 EDA Markdown | 第二部分 | 已完成 |
| CR-08 | 课题 | 逻辑回归分类 | sklearn 多分类逻辑回归 + 手写 Softmax 回归 | 3/4 | `src/model/training.py`、`src/model/manual_logistic.py` | 统一指标与模型文件 | 第二/三部分 | 已完成 |
| CR-09 | 课题 | 神经网络分类 | `MLPClassifier` + 手写前馈网络 | 3/4 | `src/model/training.py`、`src/model/manual_mlp.py` | 统一指标与模型文件 | 第二/三部分 | 已完成 |
| CR-10 | 课题 | 算法优化 | 训练集拟合、验证集 macro F1 选参、测试集锁定评估 | 3/4 | `src/model/training.py` | 候选参数和验证指标 JSON | 第二/三部分 | 已完成 |
| CR-11 | 授课计划/说明 | 输出分析检测结果 | 指标、混淆矩阵、分类报告、错误分析 | 3/4 | `src/evaluation/metrics.py`、`src/application/workflows.py` | `outputs/metrics/`、实验总结 | 2.x/3.3 | 已完成 |
| CR-12 | 执行说明 | Accuracy/Precision/Recall/F1 | 每类、macro、weighted 均输出 | 3/4 | `src/evaluation/metrics.py` | `tests/test_evaluation.py` | 2.x/3.3 | 已完成 |
| CR-13 | 课题 | 分析特征与肥胖等级关系 | EDA + 模型错误分析；只陈述关联 | 3 | `src/data/eda.py`、`outputs/reports/experiment_summary.md` | 文字说明审查 | 第二部分 | 已完成 |
| CR-14 | 授课计划 | 设计交互界面 | 五页面系统，参数/进度/图表/预测 | 5 | UI 模块尚未创建 | UI 功能测试待实现 | 3.4 | 未完成 |
| CR-15 | 执行说明 | 预测输入校验和概率 | 核心预测接口已完成；schema 驱动 UI 控件待接入 | 5 | `src/model/predictor.py`、预测页待实现 | `tests/test_predictor.py`；UI 测试待实现 | 3.4 | 基本完成（核心接口） |
| CR-16 | 授课计划 | 每周汇报，PPT ≤ 5 分钟 | 第 19/20/21 周汇报，留存版本和讲稿计时 | 全程 | 周报材料尚未创建 | 文件、时长记录待实现 | 附件/过程 | 未完成 |
| CR-17 | 授课计划 | 每日实习日志 | 使用指定模板记录六类真实内容 | 全程 | 日志材料尚未创建 | 日期连续性检查待实现 | 附件 | 未完成 |
| CR-18 | 授课计划/模板 | 独立完成模板报告 | ≥10 页、≥5000 字、≥4 一级标题、≥5 文献 | 5 | 正式报告尚未创建 | 报告清单与版式检查待实现 | 全文 | 未完成 |
| CR-19 | 报告模板 | 方案与模块详细讲解 | 技术路线、模块接口、截图和解释 | 1/5 | 设计文档/报告 | 文档覆盖检查 | 1.x/2.x/3.x | 已规划 |
| CR-20 | 报告模板 | 环境、可持续性、成本与管理 | 专章或小节分析设备、耗时、维护和风险 | 5 | 报告 | 内容审查 | 第一/总结 | 已规划 |
| CR-21 | 执行说明 | 防止数据泄漏 | 三集合分离、分层、训练集拟合 Pipeline | 3 | `src/data/preparation.py`、`src/model/training.py` | 索引互斥与未知类别测试 | 3.1 | 已完成 |
| CR-22 | 执行说明 | 原始数据只读 | 哈希核验；处理输出另存 | 1-5 | 数据目录 | 前后 SHA-256 | 数据说明 | 已完成（阶段一） |
| CR-23 | 执行说明 | 五阶段顺序 | 阶段门禁和验收清单 | 全程 | 项目管理 | `AGENTS.md`/计划 | 设计说明 | 已完成（阶段一） |
| CR-24 | 执行说明 | 指定 Conda Python 3.10 | 所有 Python 命令用指定前缀 | 全程 | 工程环境 | 环境核验输出 | 开发环境 | 已完成（阶段一） |

## 当前核验记录

- 指定环境下完整测试：85 passed、0 failed、0 skipped、11 warnings。
- 非 UI 核心产物位于 `data/processed/` 和 `outputs/`；UI、日志、PPT 和正式报告尚未形成可验收产物。
- 模型部署选择使用验证集 macro F1；测试集仅用于最终评估和展示。

## 追踪维护规则

- 每完成一个可验证需求，更新“当前状态”和对应证据路径，不得只凭代码存在改为完成。
- 需求变化时保留编号，新增行并记录来源；不复用已废弃编号。
- 测试名和报告章节在工程/报告结构确定后替换为实际名称。
