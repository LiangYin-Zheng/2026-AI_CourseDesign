# NumPy 手写神经网络 分类评估

- Accuracy: 0.883109
- Macro precision: 0.870202
- Macro recall: 0.870277
- Macro F1: 0.870047
- Weighted F1: 0.882372
- 训练耗时: 2.793955 秒
- 测试推理耗时: 0.000567 秒

| 类别 | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| `0rmal_Weight` | 0.864035 | 0.852814 | 0.858388 | 462 |
| `Insufficient_Weight` | 0.909794 | 0.933862 | 0.921671 | 378 |
| `Obesity_Type_I` | 0.849438 | 0.864989 | 0.857143 | 437 |
| `Obesity_Type_II` | 0.957490 | 0.971253 | 0.964322 | 487 |
| `Obesity_Type_III` | 0.990164 | 0.995058 | 0.992605 | 607 |
| `Overweight_Level_I` | 0.763314 | 0.708791 | 0.735043 | 364 |
| `Overweight_Level_II` | 0.757180 | 0.765172 | 0.761155 | 379 |

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
