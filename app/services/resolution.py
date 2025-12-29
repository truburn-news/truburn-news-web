from datetime import datetime, timedelta


def calc_resolution_window(center: datetime, hours: int) -> tuple[datetime, datetime]:
    half = timedelta(hours=hours / 2)
    return center - half, center + half


def compute_resolution_level(start: datetime, end: datetime) -> int:
    span_hours = (end - start).total_seconds() / 3600
    if span_hours <= 1:
        return 5
    if span_hours <= 3:
        return 4
    if span_hours <= 12:
        return 3
    if span_hours <= 24:
        return 2
    return 1


def resolution_multiplier(level: int) -> float:
    """
    Convert resolution level to UI multiplier (x1.0〜x2.5).
    """
    base = 1.0
    step = 0.375  # 1.0 + 4 * 0.375 = 2.5
    level = max(1, min(5, level))
    return round(base + (level - 1) * step, 1)
