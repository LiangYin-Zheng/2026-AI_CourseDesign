# sklearn 逻辑回归 分类评估

- Accuracy: 0.886641
- Macro precision: 0.874296
- Macro recall: 0.874804
- Macro F1: 0.874444
- Weighted F1: 0.886168
- 训练耗时: 0.249985 秒
- 测试推理耗时: 0.011015 秒

| 类别 | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| `0rmal_Weight` | 0.867257 | 0.848485 | 0.857768 | 462 |
| `Insufficient_Weight` | 0.904884 | 0.931217 | 0.917862 | 378 |
| `Obesity_Type_I` | 0.867277 | 0.867277 | 0.867277 | 437 |
| `Obesity_Type_II` | 0.951710 | 0.971253 | 0.961382 | 487 |
| `Obesity_Type_III` | 0.993410 | 0.993410 | 0.993410 | 607 |
| `Overweight_Level_I` | 0.767908 | 0.736264 | 0.751753 | 364 |
| `Overweight_Level_II` | 0.767624 | 0.775726 | 0.771654 | 379 |

参数：

```json
{
  "C": 1.0,
  "class_weight": "balanced",
  "solver": "lbfgs"
}
```
