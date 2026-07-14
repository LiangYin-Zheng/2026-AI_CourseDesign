# sklearn 逻辑回归 分类评估

- Accuracy: 0.858060
- Macro precision: 0.841735
- Macro recall: 0.843174
- Macro F1: 0.841870
- Weighted F1: 0.856663
- 训练耗时: 0.237666 秒
- 测试推理耗时: 0.005988 秒

| 类别 | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| `0rmal_Weight` | 0.863741 | 0.809524 | 0.835754 | 462 |
| `Insufficient_Weight` | 0.875000 | 0.944444 | 0.908397 | 378 |
| `Obesity_Type_I` | 0.805369 | 0.823799 | 0.814480 | 437 |
| `Obesity_Type_II` | 0.923679 | 0.969199 | 0.945892 | 487 |
| `Obesity_Type_III` | 0.996694 | 0.993410 | 0.995050 | 607 |
| `Overweight_Level_I` | 0.734328 | 0.675824 | 0.703863 | 364 |
| `Overweight_Level_II` | 0.693333 | 0.686016 | 0.689655 | 379 |

参数：

```json
{
  "C": 1.0,
  "class_weight": null,
  "solver": "lbfgs"
}
```
