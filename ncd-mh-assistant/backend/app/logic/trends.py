"""Trend analysis helpers."""
from __future__ import annotations

from datetime import datetime
from typing import Iterable, List, Optional, Sequence, Tuple

from ..schemas import TrendPoint


def ewma(points: Sequence[float], alpha: float = 0.3) -> Optional[float]:
    """Exponentially weighted moving average."""
    if not points:
        return None
    value = points[0]
    for point in points[1:]:
        value = alpha * point + (1 - alpha) * value
    return value


def linear_slope(points: Sequence[Tuple[datetime, float]]) -> Optional[float]:
    """Return slope per day using least squares."""
    n = len(points)
    if n < 2:
        return None
    base = points[0][0]
    xs: List[float] = []
    ys: List[float] = []
    for ts, value in points:
        delta_days = (ts - base).total_seconds() / 86400.0
        xs.append(delta_days)
        ys.append(value)
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    denominator = sum((x - mean_x) ** 2 for x in xs)
    if denominator == 0:
        return 0.0
    return numerator / denominator


TREND_THRESHOLDS = {
    "bp_sys": 1.0,
    "bp_dia": 1.0,
    "glucose": 3.0,
    "weight": 0.05,
    "phq9": 0.2,
    "gad7": 0.2,
}


def interpret_trend(metric: str, slope: Optional[float], count: int) -> Tuple[str, float]:
    if slope is None or count < 2:
        return "ไม่เพียงพอ", min(0.3, count / 5)

    threshold = TREND_THRESHOLDS.get(metric, 0.5)
    if slope > threshold:
        trend = "แย่ลง"
    elif slope < -threshold:
        trend = "ดีขึ้น"
    else:
        trend = "ทรงตัว"

    confidence = min(1.0, 0.3 + 0.1 * count)
    return trend, confidence


def build_trend_points(records: Iterable[Tuple[datetime, Optional[float]]]) -> List[TrendPoint]:
    points: List[TrendPoint] = []
    for ts, value in records:
        if value is None:
            continue
        points.append(TrendPoint(date=ts, value=float(value)))
    return points
