# GitHub Issue 规划

> 2026-07-14 状态：I-05 至 I-13 的非 UI 核心代码和本地产物已完成；I-14 至 I-20 仍待 UI 与课程材料阶段执行。表中建议路径以实际扁平模块实现为准。

本阶段仅规划，不创建远程 Issue。下表每行均给出任务名称、目标、背景、工作内容、文件/模块、完成条件、测试、优先级、阶段、前置依赖和 Label。

| ID/任务名称 | 目标与背景 | 具体工作内容 | 涉及文件/模块 | 完成条件 | 测试方法 | 优先级 | 阶段 | 前置依赖 | 建议 Label |
|---|---|---|---|---|---|---|---:|---|---|
| I-01 建立最小工程骨架 | 让后续功能有统一入口；阶段一仅有数据/文档 | 创建包、配置、简单运行入口、pytest、依赖说明和 README | `src/`, `tests/`, `config/`, README | `python -m obesity_risk` 正常运行，pytest 全部通过 | 入口 smoke、pytest | high | 2 | 阶段一验收 | `type:feature`, `priority:high`, `stage:2` |
| I-02 实现 YAML 配置与校验 | 消除业务硬编码；需明确错误 | 定义配置分区、读取、类型/比例/字段校验 | `config/default.yaml`, `config.py` | 合法配置对象可用，非法项指出路径 | 合法/缺项/比例和类型单测 | high | 2 | I-01 | `type:feature`, `type:test`, `stage:2` |
| I-03 实现项目路径保护 | 防止路径越界或覆盖原始数据 | 固定根目录解析、路径防逃逸、目录冲突和原始文件存在性检查；不读取 CSV 内容 | `src/obesity_risk/paths.py`, `tests/test_paths.py` | 路径不逃逸；处理/输出目录不覆盖原始 CSV；原始文件缺失时明确报错 | 路径边界与临时空文件测试 | high | 2 | I-02 | `type:feature`, `type:test`, `stage:2` |
| I-04 数据读取与 schema 检查（本地已完成） | 实际 CSV 是唯一事实源 | 只读加载、列/目标/type/空数据验证、哈希 | `data_loader.py`, `schema.py`, tests | 正常读取 20,758×18；错误输入清晰失败 | fixture、真实数据 smoke、前后快照 | high | 3 | 阶段二通过 | `type:data`, `priority:high`, `stage:3` |
| I-05 数据质量与清洗报告（审查已完成，清洗待实现） | 课程要求清洗且不得盲删 | 缺失/重复/范围/类别/异常/泄漏候选；下一步配置化清洗并记录 | `data_audit.py`, `audit_report.py`；清洗模块待建 | 审查报告已生成；清洗前后数量和规则仍待完成 | 审查统计测试已通过；清洗测试待实现 | high | 3 | I-04、字段确认 | `type:data`, `type:test`, `stage:3` |
| I-06 分层三分与预处理 | 防泄漏并统一四模型输入 | 固定索引、互斥三分、ColumnTransformer、训练拟合 | `data/split.py`, `preprocessing.py` | 比例/覆盖/复现/分层通过，测试集不 fit | 索引与 spy 拟合边界测试 | high | 3 | I-05 | `type:data`, `priority:high`, `stage:3` |
| I-07 完成 EDA 与热力图 | 覆盖课题单/双/多变量要求 | 生成分布、箱线、关系图、热力图及文字元数据 | `analysis/`, `outputs/figures/` | Age/Height/Weight 三类分析和解释齐全 | 产物清单、统计/标题审查 | high | 3 | I-05 | `type:data`, `type:report`, `stage:3` |
| I-08 sklearn 逻辑回归 | 建立可解释分类基线 | Pipeline 训练、概率、计时、基线参数 | `models/sklearn/logistic.py` | 固定划分训练成功并保存结果 | API、概率和集成测试 | high | 3 | I-06 | `type:model`, `priority:high`, `stage:3` |
| I-09 sklearn 神经网络 | 完成第二个必需模型 | MLP 训练、收敛记录、概率、计时 | `models/sklearn/mlp.py` | 训练完成、警告受控、结果保存 | API、概率和集成测试 | high | 3 | I-06 | `type:model`, `priority:high`, `stage:3` |
| I-10 统一评估与调优 | 满足指标并避免测试选参 | 指标 schema、矩阵/报告、训练验证调参、必要的实验日志、锁定后测试 | `evaluation/`, `experiments.py` | 两模型基线/优化/最终结果可追溯 | 指标对照、测试集隔离测试 | high | 3 | I-08、I-09 | `type:model`, `type:test`, `stage:3` |
| I-11 手写 Softmax 回归 | 展示核心算法自主实现 | 稳定 Softmax、交叉熵、正则、梯度、fit/predict/proba | `models/manual/` | 有限差分与小数据收敛通过 | 数学、梯度、API 测试 | high | 4 | 阶段三通过 | `type:model`, `priority:high`, `stage:4` |
| I-12 手写前馈神经网络 | 完成第二套核心算法 | 初始化、ReLU、前后向、Batch/Epoch、更新、损失 | `models/manual/neural_network.py` | 梯度检查和训练 smoke 通过 | shape、有限差分、稳定性测试 | high | 4 | I-11 基础数学 | `type:model`, `type:test`, `stage:4` |
| I-13 四模型统一比较 | 形成课程结果分析核心证据 | 同划分评估四模型，汇总指标/时间/复杂度/优缺点 | `evaluation/comparison.py`, metrics | 四行模型和所有必需列齐全、哈希一致 | 结果 schema 与划分哈希检查 | high | 4 | I-10、I-11、I-12 | `type:model`, `type:report`, `stage:4` |
| I-14 选择 UI 框架与应用服务 | 降低界面对核心逻辑耦合 | 在目标 Python 3.10 环境完成最小验证，定义服务/ViewModel | `app/services.py`, ADR | 框架依据和最小 smoke 证据齐全 | 启动、服务 mock 测试 | high | 5 | 阶段四通过 | `type:ui`, `priority:high`, `stage:5` |
| I-15 首页与数据分析页 | 展示项目与 EDA 结果 | 首页卡片/入口；数据规模、质量、图表、解释 | `app/pages/home`, `analysis` | 两页所有规划组件可见 | 页面加载与数据一致性测试 | medium | 5 | I-14、I-07 | `type:ui`, `stage:5` |
| I-16 模型训练页 | 支持四模型参数化训练展示 | 类型/算法/参数、进度、状态、耗时、曲线、指标、应用选择 | `app/pages/training` | 成功/失败路径可见且 UI 不假死 | mock 训练状态、集成测试 | high | 5 | I-14、I-13 | `type:ui`, `priority:high`, `stage:5` |
| I-17 预测页与输入校验 | 完成系统核心演示并控制伦理边界 | schema 控件、校验、概率、解释、模型元数据、免责声明 | `app/pages/prediction` | 合法预测完整，非法输入被阻止，声明显著 | 空值/边界/类别/合法样例测试 | high | 5 | I-14、已发布模型 | `type:ui`, `priority:high`, `stage:5` |
| I-18 模型比较页与系统测试 | 统一展示并完成集成 | 四模型表/图/优缺点，导航和端到端功能测试 | `app/pages/comparison`, `tests/ui` | 页面值与产物一致，五页流程通过 | UI/端到端回归 | high | 5 | I-15–I-17 | `type:ui`, `type:test`, `stage:5` |
| I-19 每日日志与三次周报 | 满足 60 分过程考核的重要证据 | 每日六类内容；第19/20/21周 PPT 和计时 | `deliverables/logs`, `ppt` | 日期真实连续；三份 PPT ≤5 分钟 | 清单/计时/事实抽查 | high | 1-5 | 每日真实工作 | `type:report`, `priority:high` |
| I-20 最终模板报告与验收 | 完成 30 分结果考核和交付 | 填写模板、图表/截图/文献、成本与可持续性、复现验收 | `deliverables/report`, README | 页/字/章节/文献/版式与 A5 全通过 | PDF 渲染、清单、干净复现 | high | 5 | I-13、I-18、I-19 | `type:report`, `priority:high`, `stage:5` |

## Issue 正文模板

```markdown
## 任务目标
（写明可观察结果）

## 背景说明
（关联课程要求编号和现状）

## 具体工作内容
- [ ] （可独立验证的步骤）

## 涉及文件或模块
- `实际路径`

## 完成条件
- [ ] （引用验收 ID 或精确条件）

## 测试方法
`python -m pytest ...`

## 管理信息
- 优先级：high/medium/low
- 所属阶段：stage:N
- 前置依赖：#编号或“无”
- Labels：...
```

完成任务才在提交/PR 使用 `Closes #编号` 或 `Fixes #编号`；部分工作或单纯关联使用 `Refs #编号`。
