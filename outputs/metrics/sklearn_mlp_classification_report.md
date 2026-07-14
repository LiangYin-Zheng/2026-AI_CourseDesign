# sklearn 神经网络 分类评估

- Accuracy: 0.882787
- Macro precision: 0.873041
- Macro recall: 0.868967
- Macro F1: 0.869258
- Weighted F1: 0.881871
- 训练耗时: 0.600210 秒
- 测试推理耗时: 0.012829 秒

| 类别 | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| `0rmal_Weight` | 0.852083 | 0.885281 | 0.868365 | 462 |
| `Insufficient_Weight` | 0.920635 | 0.920635 | 0.920635 | 378 |
| `Obesity_Type_I` | 0.854545 | 0.860412 | 0.857469 | 437 |
| `Obesity_Type_II` | 0.957490 | 0.971253 | 0.964322 | 487 |
| `Obesity_Type_III` | 0.990132 | 0.991763 | 0.990947 | 607 |
| `Overweight_Level_I` | 0.824138 | 0.656593 | 0.730887 | 364 |
| `Overweight_Level_II` | 0.712264 | 0.796834 | 0.752179 | 379 |

参数：

```json
{
  "hidden_layer_sizes": [
    128,
    64
  ],
  "activation": "relu",
  "alpha": 0.0001,
  "learning_rate_init": 0.001
}
```
