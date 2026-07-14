# sklearn 神经网络 分类评估

- Accuracy: 0.868979
- Macro precision: 0.854792
- Macro recall: 0.854272
- Macro F1: 0.854291
- Weighted F1: 0.868238
- 训练耗时: 0.426112 秒
- 测试推理耗时: 0.007739 秒

| 类别 | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| `0rmal_Weight` | 0.841991 | 0.841991 | 0.841991 | 462 |
| `Insufficient_Weight` | 0.907407 | 0.907407 | 0.907407 | 378 |
| `Obesity_Type_I` | 0.832589 | 0.853547 | 0.842938 | 437 |
| `Obesity_Type_II` | 0.944112 | 0.971253 | 0.957490 | 487 |
| `Obesity_Type_III` | 0.995050 | 0.993410 | 0.994229 | 607 |
| `Overweight_Level_I` | 0.745509 | 0.684066 | 0.713467 | 364 |
| `Overweight_Level_II` | 0.716883 | 0.728232 | 0.722513 | 379 |

参数：

```json
{
  "hidden_layer_sizes": [
    64,
    32
  ],
  "activation": "relu",
  "alpha": 0.001,
  "learning_rate_init": 0.001
}
```
