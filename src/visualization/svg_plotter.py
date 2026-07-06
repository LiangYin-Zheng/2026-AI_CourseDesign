from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np


# 写入 SVG 文本到目标文件

def write_svg(path: str | Path, content: str) -> None:
    Path(path).write_text(content, encoding="utf-8")


# 生成条形图 SVG

def save_bar_chart(labels: Sequence[str], values: Sequence[float], title: str, output_path: str | Path) -> None:
    width, height = 960, 560
    left_margin, right_margin, top_margin, bottom_margin = 120, 40, 90, 150
    chart_width = width - left_margin - right_margin
    chart_height = height - top_margin - bottom_margin
    max_value = max(values) if values else 1
    bar_count = max(len(values), 1)
    bar_width = chart_width / bar_count * 0.72
    gap = chart_width / bar_count * 0.28

    bars = []
    for index, (label, value) in enumerate(zip(labels, values)):
        x_position = left_margin + index * (bar_width + gap) + gap / 2
        bar_height = 0 if max_value == 0 else (value / max_value) * chart_height
        y_position = top_margin + (chart_height - bar_height)
        bars.append(
            f'<rect x="{x_position:.2f}" y="{y_position:.2f}" width="{bar_width:.2f}" '
            f'height="{bar_height:.2f}" fill="#4F81BD" rx="6" />'
        )
        bars.append(
            f'<text x="{x_position + bar_width / 2:.2f}" y="{y_position - 8:.2f}" text-anchor="middle" '
            f'font-size="13" fill="#1F2937">{value:.2f}</text>'
        )
        bars.append(
            f'<text x="{x_position + bar_width / 2:.2f}" y="{height - 50}" text-anchor="end" '
            f'transform="rotate(-35 {x_position + bar_width / 2:.2f} {height - 50})" '
            f'font-size="12" fill="#374151">{escape(str(label))}</text>'
        )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
    <rect width="100%" height="100%" fill="#FFFFFF" />
    <text x="{width / 2}" y="45" text-anchor="middle" font-size="24" fill="#111827">{escape(title)}</text>
    <line x1="{left_margin}" y1="{top_margin}" x2="{left_margin}" y2="{top_margin + chart_height}" stroke="#6B7280" stroke-width="2" />
    <line x1="{left_margin}" y1="{top_margin + chart_height}" x2="{width - right_margin}" y2="{top_margin + chart_height}" stroke="#6B7280" stroke-width="2" />
    {''.join(bars)}
    </svg>'''
    write_svg(output_path, svg)


# 生成直方图 SVG

def save_histogram(values: Iterable[float], bins: int, title: str, output_path: str | Path) -> None:
    array = np.asarray(list(values), dtype=float)
    counts, edges = np.histogram(array, bins=bins)
    labels = [f"{edges[index]:.1f}-{edges[index + 1]:.1f}" for index in range(len(edges) - 1)]
    save_bar_chart(labels, counts.astype(float).tolist(), title, output_path)


# 生成热力图 SVG

def save_heatmap(matrix: np.ndarray, row_labels: Sequence[str], col_labels: Sequence[str], title: str, output_path: str | Path) -> None:
    width, height = 980, 760
    cell_size = 70
    left_margin, top_margin = 180, 140
    max_abs_value = float(np.max(np.abs(matrix))) if matrix.size else 1.0
    max_abs_value = max(max_abs_value, 1e-8)
    cells = []

    for row_index in range(matrix.shape[0]):
        for col_index in range(matrix.shape[1]):
            value = float(matrix[row_index, col_index])
            intensity = int(255 - abs(value) / max_abs_value * 155)
            color = f"rgb(255,{intensity},{intensity})" if value >= 0 else f"rgb({intensity},{intensity},255)"
            x_position = left_margin + col_index * cell_size
            y_position = top_margin + row_index * cell_size
            cells.append(
                f'<rect x="{x_position}" y="{y_position}" width="{cell_size}" height="{cell_size}" fill="{color}" stroke="#D1D5DB" />'
            )
            cells.append(
                f'<text x="{x_position + cell_size / 2}" y="{y_position + cell_size / 2 + 5}" text-anchor="middle" font-size="12" fill="#111827">{value:.2f}</text>'
            )

    row_text = []
    for row_index, label in enumerate(row_labels):
        y_position = top_margin + row_index * cell_size + cell_size / 2 + 5
        row_text.append(f'<text x="{left_margin - 10}" y="{y_position}" text-anchor="end" font-size="12">{escape(str(label))}</text>')

    col_text = []
    for col_index, label in enumerate(col_labels):
        x_position = left_margin + col_index * cell_size + cell_size / 2
        col_text.append(
            f'<text x="{x_position}" y="{top_margin - 15}" text-anchor="end" transform="rotate(-35 {x_position} {top_margin - 15})" font-size="12">{escape(str(label))}</text>'
        )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
    <rect width="100%" height="100%" fill="#FFFFFF" />
    <text x="{width / 2}" y="45" text-anchor="middle" font-size="24" fill="#111827">{escape(title)}</text>
    {''.join(cells)}
    {''.join(row_text)}
    {''.join(col_text)}
    </svg>'''
    write_svg(output_path, svg)
