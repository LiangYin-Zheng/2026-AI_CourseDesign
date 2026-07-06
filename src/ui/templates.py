from __future__ import annotations


# 构建演示界面 HTML 页面

def build_index_page() -> str:
    return """<!DOCTYPE html>
<html lang=\"zh-CN\">
<head>
    <meta charset=\"UTF-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
    <title>肥胖风险预测系统</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif; margin: 0; background: #f3f4f6; color: #111827; }
        .container { max-width: 1080px; margin: 0 auto; padding: 32px 20px 48px; }
        .card { background: #ffffff; border-radius: 16px; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08); padding: 24px; margin-bottom: 24px; }
        h1, h2 { margin-top: 0; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; }
        label { display: flex; flex-direction: column; gap: 6px; font-size: 14px; color: #374151; }
        input, select { border: 1px solid #d1d5db; border-radius: 10px; padding: 10px 12px; font-size: 14px; }
        button { background: #2563eb; color: #fff; border: none; border-radius: 10px; padding: 12px 20px; font-size: 15px; cursor: pointer; }
        button:hover { background: #1d4ed8; }
        pre { background: #0f172a; color: #e5e7eb; padding: 16px; border-radius: 12px; overflow: auto; }
        .tip { font-size: 13px; color: #6b7280; }
    </style>
</head>
<body>
<div class=\"container\">
    <div class=\"card\">
        <h1>肥胖风险预测系统</h1>
        <p>本系统基于课程项目数据集构建，支持输入个人生活与身体指标后，实时输出肥胖等级预测结果与类别概率。</p>
        <p class=\"tip\">推荐先执行训练流程生成模型文件，再启动当前服务。</p>
    </div>
    <div class=\"card\">
        <h2>风险预测表单</h2>
        <div class=\"grid\">
            <label>性别<select id=\"gender\"><option>Female</option><option>Male</option></select></label>
            <label>年龄<input id=\"age\" type=\"number\" step=\"0.1\" value=\"24\" /></label>
            <label>身高（米）<input id=\"height_m\" type=\"number\" step=\"0.01\" value=\"1.70\" /></label>
            <label>体重（千克）<input id=\"weight_kg\" type=\"number\" step=\"0.1\" value=\"72\" /></label>
            <label>家族肥胖史<select id=\"family_history_with_overweight\"><option value=\"1\">Yes</option><option value=\"0\">No</option></select></label>
            <label>高热量饮食偏好<select id=\"high_calorie_food_frequency\"><option value=\"1\">Yes</option><option value=\"0\">No</option></select></label>
            <label>蔬菜摄入评分<input id=\"vegetable_intake_score\" type=\"number\" step=\"0.1\" value=\"2.5\" /></label>
            <label>每日正餐次数<input id=\"main_meals_per_day\" type=\"number\" step=\"0.1\" value=\"3\" /></label>
            <label>加餐频率<select id=\"snacking_frequency\"><option>Never</option><option selected>Sometimes</option><option>Frequently</option><option>Always</option></select></label>
            <label>是否吸烟<select id=\"smokes\"><option value=\"0\">No</option><option value=\"1\">Yes</option></select></label>
            <label>饮水量（升）<input id=\"water_intake_liters\" type=\"number\" step=\"0.1\" value=\"2.0\" /></label>
            <label>是否进行热量监测<select id=\"calorie_monitoring\"><option value=\"0\">No</option><option value=\"1\">Yes</option></select></label>
            <label>运动评分<input id=\"physical_activity_score\" type=\"number\" step=\"0.1\" value=\"1.5\" /></label>
            <label>电子设备使用评分<input id=\"technology_use_hours\" type=\"number\" step=\"0.1\" value=\"1.0\" /></label>
            <label>饮酒频率<select id=\"alcohol_consumption\"><option>Never</option><option selected>Sometimes</option><option>Frequently</option><option>Always</option></select></label>
            <label>出行方式<select id=\"transportation_mode\"><option>Public_Transportation</option><option>Automobile</option><option>Walking</option><option>Motorbike</option><option>Bike</option></select></label>
        </div>
        <div style=\"margin-top: 20px;\"><button onclick=\"submitPrediction()\">提交预测</button></div>
    </div>
    <div class=\"card\">
        <h2>预测结果</h2>
        <pre id=\"result\">等待提交...</pre>
    </div>
</div>
<script>
async function submitPrediction() {
    const payload = {
        gender: document.getElementById('gender').value,
        age: Number(document.getElementById('age').value),
        height_m: Number(document.getElementById('height_m').value),
        weight_kg: Number(document.getElementById('weight_kg').value),
        family_history_with_overweight: Number(document.getElementById('family_history_with_overweight').value),
        high_calorie_food_frequency: Number(document.getElementById('high_calorie_food_frequency').value),
        vegetable_intake_score: Number(document.getElementById('vegetable_intake_score').value),
        main_meals_per_day: Number(document.getElementById('main_meals_per_day').value),
        snacking_frequency: document.getElementById('snacking_frequency').value,
        smokes: Number(document.getElementById('smokes').value),
        water_intake_liters: Number(document.getElementById('water_intake_liters').value),
        calorie_monitoring: Number(document.getElementById('calorie_monitoring').value),
        physical_activity_score: Number(document.getElementById('physical_activity_score').value),
        technology_use_hours: Number(document.getElementById('technology_use_hours').value),
        alcohol_consumption: document.getElementById('alcohol_consumption').value,
        transportation_mode: document.getElementById('transportation_mode').value
    };
    const response = await fetch('/api/v1/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });
    const data = await response.json();
    document.getElementById('result').textContent = JSON.stringify(data, null, 2);
}
</script>
</body>
</html>"""
