# 第二轮 UI 视觉参考与依赖决策

## 参考范围

| 项目或资料 | 本项目借鉴内容 | 代码或依赖使用情况 | 许可证 |
|---|---|---|---|
| [shadcn-ui/ui](https://github.com/shadcn-ui/ui) | 语义化颜色令牌、Card 层级、按钮变体、Badge、Tabs、空状态和清晰焦点 | 未复制代码，未引入 React 依赖 | MIT |
| [satnaing/shadcn-admin](https://github.com/satnaing/shadcn-admin) | 侧边导航选中态、页面标题密度、指标卡与响应式仪表盘间距 | 未复制代码，未引入依赖 | MIT |
| [ObservedObserver/streamlit-shadcn-ui](https://github.com/ObservedObserver/streamlit-shadcn-ui) | 研究 Shadcn 组件在 Streamlit 中的卡片、Badge、Tabs 和 Toggle 表达 | 未采用组件；原生 Streamlit 与集中 CSS 已满足需求 | MIT；其临时组件库部分为 Apache-2.0 |
| [Sven-Bo/streamlit-shadcn-dashboard](https://github.com/Sven-Bo/streamlit-shadcn-dashboard) | 参考 Streamlit 仪表盘中指标卡与图表组合 | 未复制代码，未引入依赖 | 仓库未在本项目中复用代码 |
| [victoryhb/streamlit-option-menu](https://github.com/victoryhb/streamlit-option-menu) | 参考整行可点击、图标加文字的垂直导航 | 未引入依赖；使用原生 `st.radio`、Material 图标和稳定 `data-testid` 样式实现 | MIT |
| [Streamlit 官方主题与导航文档](https://docs.streamlit.io/develop/api-reference/configuration/config.toml) | `config.toml` 主题、minimal 工具栏、隐藏错误详情、原生 pills/segmented control/status | 使用项目现有 Streamlit 1.59 能力 | Apache-2.0 |
| [okld/streamlit-elements](https://github.com/okld/streamlit-elements) | 仅研究 Material UI 卡片和仪表盘布局思路 | 未引入；不需要 iframe、拖拽或可调整布局 | MIT |

## 决策结论

- 不引入 React、Node.js、独立前端工程或拖拽布局。
- 不引入 `streamlit-option-menu`、`streamlit-shadcn-ui` 或 `streamlit-elements`。
- 新增 Plotly 作为唯一图表依赖，用于完整模型名称、末端数值标签和当前模型高亮；Plotly.py 使用 MIT 许可证。
- 所有应用 CSS 继续集中在 `src/ui/styles.py`，主题集中在 `.streamlit/config.toml`。
- 参考项目只用于设计语言研究，没有直接复制其源代码。
