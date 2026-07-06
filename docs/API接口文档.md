# API 接口文档

## 1. 接口概览
本项目提供一个健康检查接口和一个肥胖风险预测接口，均由本地服务 `src/interfaces/web/server.py` 提供。

## 2. 健康检查接口
### 接口名称
服务健康检查

### 请求路径
`/health`

### 请求方式
`GET`

### 请求参数
无

### 返回参数
| 参数 | 类型 | 说明 |
| --- | --- | --- |
| success | boolean | 接口是否执行成功 |
| message | string | 服务状态说明 |

### 返回示例
```json
{
  "success": true,
  "message": "service is running"
}
```

## 3. 肥胖风险预测接口
### 接口名称
肥胖等级预测

### 请求路径
`/api/v1/predict`

### 请求方式
`POST`

### 请求参数
| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| gender | string | 是 | 性别，`Female` 或 `Male` |
| age | number | 是 | 年龄 |
| height_m | number | 是 | 身高（米） |
| weight_kg | number | 是 | 体重（千克） |
| family_history_with_overweight | integer | 是 | 家族肥胖史，0=否，1=是 |
| high_calorie_food_frequency | integer | 是 | 高热量饮食偏好，0=否，1=是 |
| vegetable_intake_score | number | 是 | 蔬菜摄入评分 |
| main_meals_per_day | number | 是 | 每日主餐次数 |
| snacking_frequency | string | 是 | 加餐频率，`Never/Sometimes/Frequently/Always` |
| smokes | integer | 是 | 是否吸烟，0=否，1=是 |
| water_intake_liters | number | 是 | 每日饮水量 |
| calorie_monitoring | integer | 是 | 是否热量监测，0=否，1=是 |
| physical_activity_score | number | 是 | 身体活动评分 |
| technology_use_hours | number | 是 | 电子设备使用评分 |
| alcohol_consumption | string | 是 | 饮酒频率，`Never/Sometimes/Frequently/Always` |
| transportation_mode | string | 是 | 出行方式，`Public_Transportation/Automobile/Walking/Motorbike/Bike` |

### 返回参数
| 参数 | 类型 | 说明 |
| --- | --- | --- |
| success | boolean | 请求是否成功 |
| logistic_regression | object | 逻辑回归预测结果 |
| neural_network | object | 神经网络预测结果 |
| recommended_result | string | 推荐输出结果（默认取神经网络） |

### 返回示例
```json
{
  "success": true,
  "logistic_regression": {
    "prediction": "Overweight_Level_II",
    "probabilities": {
      "Insufficient_Weight": 0.017662,
      "Normal_Weight": 0.071175,
      "Obesity_Type_I": 0.263551,
      "Obesity_Type_II": 0.050871,
      "Obesity_Type_III": 0.000763,
      "Overweight_Level_I": 0.254614,
      "Overweight_Level_II": 0.341365
    }
  },
  "neural_network": {
    "prediction": "Overweight_Level_II",
    "probabilities": {
      "Insufficient_Weight": 0.040851,
      "Normal_Weight": 0.086343,
      "Obesity_Type_I": 0.245368,
      "Obesity_Type_II": 0.022271,
      "Obesity_Type_III": 0.000646,
      "Overweight_Level_I": 0.252378,
      "Overweight_Level_II": 0.352142
    }
  },
  "recommended_result": "Overweight_Level_II"
}
```

## 4. 错误码说明
| HTTP 状态码 | 说明 | 场景 |
| --- | --- | --- |
| 200 | 请求成功 | 健康检查或预测成功 |
| 400 | 请求参数错误或预测失败 | JSON 不合法、缺少字段、字段类型异常 |
| 404 | 资源不存在 | 访问了未定义路径 |
