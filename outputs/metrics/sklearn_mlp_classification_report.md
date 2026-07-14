# sklearn 神经网络 分类评估

- Accuracy: 0.874438
- Macro precision: 0.860722
- Macro recall: 0.860306
- Macro F1: 0.859775
- Weighted F1: 0.873493
- 训练耗时: 0.506731 秒
- 测试推理耗时: 0.008059 秒

| 类别 | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| `0rmal_Weight` | 0.854031 | 0.848485 | 0.851249 | 462 |
| `Insufficient_Weight` | 0.907216 | 0.931217 | 0.919060 | 378 |
| `Obesity_Type_I` | 0.850917 | 0.848970 | 0.849943 | 437 |
| `Obesity_Type_II` | 0.950100 | 0.977413 | 0.963563 | 487 |
| `Obesity_Type_III` | 0.995041 | 0.991763 | 0.993399 | 607 |
| `Overweight_Level_I` | 0.755556 | 0.653846 | 0.701031 | 364 |
| `Overweight_Level_II` | 0.712195 | 0.770449 | 0.740177 | 379 |

参数：

```json
{
  "hidden_layer_sizes": [
    64,
    32
  ],
  "activation": "tanh",
  "alpha": 0.0001,
  "learning_rate_init": 0.001
}
```
