"""Utility functions for analyzing trends of observations."""
from __future__ import annotations

from datetime import date
from collections.abc import Sequence
from typing import List, Tuple


def ewma(values: Sequence[float], alpha: float = 0.3) -> List[float]:
    """Exponential weighted moving average."""
    if not values:
        return []

    smoothed: List[float] = []
    current = values[0]
    smoothed.append(current)
    for value in values[1:]:
        current = alpha * value + (1 - alpha) * current
        smoothed.append(current)
    return smoothed


def linear_slope(points: Sequence[Tuple[date, float]]) -> float:
    """Compute the slope per day using ordinary least squares."""
    if len(points) < 2:
        return 0.0

    x_values = [(p[0] - points[0][0]).days for p in points]
    y_values = [p[1] for p in points]

    x_mean = sum(x_values) / len(x_values)
    y_mean = sum(y_values) / len(y_values)

    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values))
    denominator = sum((x - x_mean) ** 2 for x in x_values)

    if denominator == 0:
        return 0.0

    return numerator / denominator


def interpret_trend(metric: str, slope: float) -> str:
    """Provide a qualitative interpretation based on slope."""
    threshold = 0.1
    if slope <= -threshold:
        return "improving"
    if slope >= threshold:
        return "worsening"
    return "stable"


def confidence_from_points(points: Sequence) -> str:
    count = len(points)
    if count >= 8:
        return "high"
    if count >= 4:
        return "medium"
    return "low"
