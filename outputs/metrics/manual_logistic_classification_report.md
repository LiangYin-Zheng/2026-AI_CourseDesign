# NumPy 手写逻辑回归 分类评估

- Accuracy: 0.793834
- Macro precision: 0.772399
- Macro recall: 0.768066
- Macro F1: 0.764593
- Weighted F1: 0.785133
- 训练耗时: 0.551212 秒
- 测试推理耗时: 0.000456 秒

| 类别 | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| `0rmal_Weight` | 0.674074 | 0.787879 | 0.726547 | 462 |
| `Insufficient_Weight` | 0.814356 | 0.870370 | 0.841432 | 378 |
| `Obesity_Type_I` | 0.742489 | 0.791762 | 0.766334 | 437 |
| `Obesity_Type_II` | 0.877589 | 0.956879 | 0.915521 | 487 |
| `Obesity_Type_III` | 0.948276 | 0.996705 | 0.971888 | 607 |
| `Overweight_Level_I` | 0.646825 | 0.447802 | 0.529221 | 364 |
| `Overweight_Level_II` | 0.703180 | 0.525066 | 0.601208 | 379 |

参数：

```json
{
  "learning_rate": 0.08,
  "l2": 0.0005,
  "max_epochs": 300,
  "patience": 25,
  "tolerance": 1e-05
}
```
