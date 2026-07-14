import json
from pathlib import Path


# 将结构化审查结果整理为人工可读的 Markdown
def _markdown_report(result: dict) -> str:
    dataset = result["dataset_summary"]
    target = result["target_summary"]
    lines = [
        "# 数据审查报告",
        "",
        "## 数据集概况",
        "",
        f"- 行数：{dataset['row_count']}",
        f"- 列数：{dataset['column_count']}",
        f"- 字段：{', '.join(f'`{name}`' for name in dataset['columns'])}",
        f"- 缺失单元格：{result['missing_summary']['total_missing']}",
        f"- 完全重复行：{result['duplicate_summary']['duplicate_row_count']}",
        f"- Schema 是否通过：{'是' if result['schema_summary']['is_valid'] else '否'}",
        f"- 原始文件 SHA-256：`{result.get('file_snapshot', {}).get('sha256', '未提供')}`",
        "",
        "## 数值存储字段摘要",
        "",
        "| 字段 | count | mean | std | min | 25% | 50% | 75% | max | IQR 疑似极端值 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, summary in result["numeric_summary"].items():
        values = []
        for key in ("count", "mean", "std", "min", "25%", "50%", "75%", "max"):
            value = summary[key]
            values.append("-" if value is None else f"{value:.6g}")
        lines.append(
            f"| `{name}` | {' | '.join(values)} | {summary['iqr_extreme_count']} |"
        )
    lines.extend(
        [
            "",
            "## 类别字段摘要",
            "",
            "| 字段 | 唯一值数 | 类别分布（数量） | 空字符串 | 前后空格 | 未预期值 |",
            "|---|---:|---|---:|---:|---|",
        ]
    )
    for name, summary in result["categorical_summary"].items():
        distribution = ", ".join(
            f"{item['value']}: {item['count']}" for item in summary["distribution"]
        )
        unexpected = ", ".join(map(str, summary["unexpected_values"])) or "无"
        lines.append(
            f"| `{name}` | {summary['unique_count']} | {distribution} | "
            f"{summary['empty_string_count']} | "
            f"{summary['leading_or_trailing_whitespace_count']} | {unexpected} |"
        )
    lines.extend(
        [
        "",
        "## 目标类别分布",
        "",
        "| 类别 | 数量 | 比例 |",
        "|---|---:|---:|",
        ]
    )
    for item in target.get("class_distribution", []):
        lines.append(f"| `{item['value']}` | {item['count']} | {item['ratio']:.2%} |")
    lines.extend(
        [
            "",
            "## 质量问题",
            "",
        ]
    )
    if result["quality_issues"]:
        for issue in result["quality_issues"]:
            details = issue.get("flags", issue.get("details", {}))
            suffix = f"：`{json.dumps(details, ensure_ascii=False)}`" if details else ""
            if issue["code"] == "target_imbalance":
                suffix = f"：最大类/最小类数量比为 {issue['ratio']:.3f}"
            lines.append(f"- `{issue['code']}`（{issue['severity']}）{suffix}")
    else:
        lines.append("- 未发现自动规则可识别的问题。")
    lines.extend(
        [
            "",
            "> 本报告仅执行只读结构与质量审查，不包含清洗、编码、划分、建模或医学判断。",
            "",
        ]
    )
    return "\n".join(lines)


# 使用临时文件替换目标文件，避免报告写入中断留下半份文件
def _write_text_atomically(path: Path, content: str) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)


# 在安全输出目录生成 JSON 和 Markdown 审查报告
def write_audit_reports(result: dict, report_dir: Path, raw_data: Path) -> dict[str, Path]:
    report_dir = report_dir.resolve()
    raw_data = raw_data.resolve()
    json_path = report_dir / "data_audit.json"
    markdown_path = report_dir / "data_audit.md"
    if raw_data in (json_path, markdown_path) or raw_data == report_dir:
        raise ValueError("审查报告不能覆盖原始数据文件")
    if report_dir.exists() and not report_dir.is_dir():
        raise ValueError("审查报告路径已存在但不是目录")
    report_dir.mkdir(parents=True, exist_ok=True)
    json_content = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    _write_text_atomically(json_path, json_content)
    _write_text_atomically(markdown_path, _markdown_report(result))
    return {"json": json_path, "markdown": markdown_path}
