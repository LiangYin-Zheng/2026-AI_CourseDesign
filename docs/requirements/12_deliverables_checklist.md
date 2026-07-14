# 最终交付物清单

复选框仅在存在可验证产物后勾选。当前阶段三、阶段四的非 UI 核心实现已有真实产物和测试证据；阶段五及课程过程材料仍按实际状态保留未完成。

## 阶段一：需求与规划

- [x] 仓库、分支、远程和工作区核验记录
- [x] 指定 Conda Python 3.10 环境核验
- [x] 根目录 `AGENTS.md` 长期上下文
- [x] `00_source_review.md`
- [x] `01_project_requirements.md`
- [x] `02_course_requirement_mapping.md`
- [x] `03_project_scope.md`
- [x] `04_data_understanding.md`
- [x] `05_data_dictionary.md`
- [x] `06_technical_route.md`
- [x] `07_system_module_plan.md`
- [x] `08_acceptance_criteria.md`
- [x] `09_development_plan.md`
- [x] `10_issue_plan.md`
- [x] `11_risk_and_assumptions.md`
- [x] `12_deliverables_checklist.md`
- [ ] 字段官方定义、单位和编码确认记录

## 阶段二：工程基础

- [x] `config/default.yaml`
- [x] `src/main.py` CLI 入口与健康检查
- [x] `src/core/config.py` 配置读取与基础校验
- [x] `src/core/paths.py` 路径管理及原始数据保护
- [x] `tests/test_config.py`
- [x] `tests/test_paths.py`
- [x] `pyproject.toml` Python 3.10 依赖与 pytest 配置
- [x] README 环境要求、运行、测试和数据保护说明

## 阶段三：sklearn 完整版本

- [x] 数据只读加载与 schema 检查
- [x] 数据质量审查及 JSON/Markdown 报告
- [x] 数据清洗规则及清洗前后摘要
- [x] 固定分层训练/验证/测试索引
- [x] 无泄漏 `ColumnTransformer`/`Pipeline`
- [x] Age/Height/Weight 单变量分析与解释
- [x] 双变量分析与解释
- [x] 多变量分析与解释
- [x] 相关性热力图与解释
- [x] sklearn 逻辑回归基线、优化和最终模型
- [x] sklearn MLP 基线、优化和最终模型
- [x] 完整分类指标、混淆矩阵和分类报告
- [x] 训练/推理耗时和实验配置
- [x] 模型、预处理器、标签和输入 schema 产物
- [x] 阶段三自动化测试与验收记录

## 阶段四：手写算法与统一比较

- [x] 稳定 Softmax 和交叉熵实现
- [x] 手写多分类逻辑回归、正则化和损失曲线
- [x] 逻辑回归梯度/接口/收敛测试
- [x] 手写前馈神经网络及激活函数
- [x] 反向传播、Batch/Epoch 和参数更新
- [x] 神经网络梯度/接口/收敛测试
- [x] 四模型同划分、同标签、同指标对比
- [x] Accuracy/P/R/F1（每类、macro、weighted）
- [x] 四模型混淆矩阵和分类报告
- [x] 训练时间、推理时间、复杂度、优缺点、场景分析

## 阶段五：交互系统

- [ ] UI 框架兼容性证据和技术决策
- [ ] 系统首页
- [ ] 数据分析页面及文字解释
- [ ] 模型训练页面（参数、进度、状态、耗时、结果）
- [ ] 预测模型选择/发布能力
- [ ] 风险预测页输入 schema、必填/范围/类别校验
- [ ] 类别、全类概率、最高概率、模型和解释展示
- [ ] 非医学诊断声明
- [ ] 模型比较页面
- [ ] 五页面功能/集成/异常路径测试

## 课程过程与最终材料

- [ ] 每个实际工作日的实习日志
- [ ] 日志覆盖方案、完成、结果、分析、问题、收获六类内容
- [ ] 第 19 周周报 PPT 与 ≤5 分钟计时记录
- [ ] 第 20 周周报 PPT 与 ≤5 分钟计时记录
- [ ] 第 21 周周报 PPT 与 ≤5 分钟计时记录
- [ ] 使用指定模板的独立课程设计报告
- [ ] 报告正文 ≥10 页且 ≥5,000 字
- [ ] 报告至少 4 个一级标题且每部分满足篇幅要求
- [ ] 报告至少 5 篇按序引用的参考文献
- [ ] 图表均有编号、名称和文字解释
- [ ] 仅含本人程序/图表/界面截图，无网络截图
- [ ] 环境、可持续发展、成本、工程管理与经济决策分析
- [ ] 技术总结、局限与致谢
- [ ] 按模板边距、字体、行距完成最终版式检查

## 最终复现与版本控制

- [x] 原始 CSV 最终哈希与基线一致
- [x] 全套 pytest 在项目 Python 3.10 环境通过（85 passed、11 warnings）
- [x] 非 UI 输出可按 README 的 `run-all` 覆盖复现
- [x] 依赖版本与运行环境记录
- [ ] 所有阶段验收证据归档
- [ ] Git 提交细粒度、中文 Conventional Commits、双 `-m`
- [ ] 无账号、密码、Token、私钥、Cookie 或个人隐私
- [ ] 未自动 push；远程操作仅在用户明确授权后执行
