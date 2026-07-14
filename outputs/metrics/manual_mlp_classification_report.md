# NumPy 手写神经网络 分类评估

- Accuracy: 0.863520
- Macro precision: 0.847538
- Macro recall: 0.848953
- Macro F1: 0.847877
- Weighted F1: 0.862285
- 训练耗时: 2.052625 秒
- 测试推理耗时: 0.000441 秒

| 类别 | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| `0rmal_Weight` | 0.859729 | 0.822511 | 0.840708 | 462 |
| `Insufficient_Weight` | 0.873762 | 0.933862 | 0.902813 | 378 |
| `Obesity_Type_I` | 0.840278 | 0.830664 | 0.835443 | 437 |
| `Obesity_Type_II` | 0.925636 | 0.971253 | 0.947896 | 487 |
| `Obesity_Type_III` | 0.993410 | 0.993410 | 0.993410 | 607 |
| `Overweight_Level_I` | 0.718023 | 0.678571 | 0.697740 | 364 |
| `Overweight_Level_II` | 0.721925 | 0.712401 | 0.717131 | 379 |

参数：

```json
{
  "hidden_size": 48,
  "learning_rate": 0.01,
  "l2": 0.0005,
  "max_epochs": 220,
  "batch_size": 256,
  "patience": 25,
  "tolerance": 1e-05
}
```
