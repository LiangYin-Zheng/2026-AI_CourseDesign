from pathlib import Path

import pandas as pd

from obesity_risk.eda import run_eda
from obesity_risk.schema import DatasetSchema


# 验证小型数据可以生成完整 EDA 报告和六张非空图片
def test_run_eda_generates_reports_and_figures(tmp_path: Path) -> None:
    rows = []
    for index in range(24):
        rows.append(
            {
                "Age": 18 + index,
                "Height": 1.55 + index * 0.01,
                "Weight": 50 + index * 2,
                "Gender": "Female" if index % 2 else "Male",
                "target": "A" if index < 12 else "B",
            }
        )
    frame = pd.DataFrame(rows)
    schema = DatasetSchema(
        required_columns=("Age", "Height", "Weight", "Gender", "target"),
        target_column="target",
        numeric_columns=("Age", "Height", "Weight"),
        categorical_columns=("Gender",),
        excluded_columns=(),
        allow_extra_columns=False,
        allow_missing_columns=False,
        allow_all_null_columns=False,
    )
    paths = run_eda(
        frame,
        schema,
        tmp_path / "figures",
        tmp_path,
        {"dpi": 80, "scatter_sample_size": 20},
        42,
    )
    assert paths["summary"].is_file()
    assert paths["report"].is_file()
    figures = list((tmp_path / "figures").glob("*.png"))
    assert len(figures) == 6
    assert all(path.stat().st_size > 0 for path in figures)
