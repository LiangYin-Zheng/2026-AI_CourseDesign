"""桌面端与 Web 端共享的数据契约。"""

from .dashboard_schema import (
    ARTIFACT_GROUP_NAMES,
    DEFAULT_TRAINING_MODE,
    TRAINING_MODE_OPTIONS,
    normalize_dashboard_summary,
)
from .formatters import format_probability_map, normalize_prediction_result
from .sample_schema import FIELD_DEFINITIONS, build_sample_payload, coerce_sample_value

