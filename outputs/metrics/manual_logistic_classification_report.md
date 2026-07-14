# NumPy 手写逻辑回归 分类评估

- Accuracy: 0.688825
- Macro precision: 0.652455
- Macro recall: 0.654932
- Macro F1: 0.644650
- Weighted F1: 0.672718
- 训练耗时: 0.414877 秒
- 测试推理耗时: 0.000230 秒

| 类别 | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| `0rmal_Weight` | 0.544732 | 0.593074 | 0.567876 | 462 |
| `Insufficient_Weight` | 0.666667 | 0.761905 | 0.711111 | 378 |
| `Obesity_Type_I` | 0.605206 | 0.638444 | 0.621381 | 437 |
| `Obesity_Type_II` | 0.757525 | 0.930185 | 0.835023 | 487 |
| `Obesity_Type_III` | 0.920611 | 0.993410 | 0.955626 | 607 |
| `Overweight_Level_I` | 0.489879 | 0.332418 | 0.396072 | 364 |
| `Overweight_Level_II` | 0.582569 | 0.335092 | 0.425461 | 379 |

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
