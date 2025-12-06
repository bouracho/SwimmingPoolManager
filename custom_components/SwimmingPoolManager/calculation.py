"""Cubic polynomial algorithm and schedule helpers."""
import logging
from datetime import datetime, timedelta

LOGGER = logging.getLogger(__name__)

# base coefficients (provided by user earlier)
_BASE_A = 0.00335
_BASE_B = -0.14953
_BASE_C = 2.43489
_BASE_D = -10.72859

MIN_HOURS = 0.0
MAX_HOURS = 24.0


def compute_filtration_duration_cubic(temp_celsius: float, coef_pct: float) -> float:
    try:
        t = float(temp_celsius)
        scale = float(coef_pct) / 100.0
        a = _BASE_A * scale
        b = _BASE_B * scale
        c = _BASE_C * scale
        d = _BASE_D * scale

        hours = (a * (t ** 3)) + (b * (t ** 2)) + (c * t) + d
        hours_clamped = max(MIN_HOURS, min(MAX_HOURS, float(hours)))
        LOGGER.debug("Cubic calc: T=%.2f coef=%s -> raw=%.3f clamped=%.3f", t, coef_pct, hours, hours_clamped)
        return hours_clamped
    except Exception:
        LOGGER.exception("Error computing cubic filtration duration")
        return MIN_HOURS


def compute_schedule_windows(pivot_time_str: str, pause_minutes: int, total_hours: float):
    pivot_today = datetime.combine(datetime.now().date(), datetime.strptime(pivot_time_str, "%H:%M").time())
    half_td = timedelta(hours=total_hours / 2.0)
    pause_td = timedelta(minutes=int(pause_minutes))

    start1 = pivot_today - half_td - (pause_td / 2)
    end1 = pivot_today - (pause_td / 2)
    start2 = pivot_today + (pause_td / 2)
    end2 = start2 + half_td

    return [(start1, end1), (start2, end2)]


def check_frost_protection(outdoor_temp: float, no_frost_temp: float) -> bool:
    if outdoor_temp is None:
        return False
    try:
        return float(outdoor_temp) < float(no_frost_temp)
    except Exception:
        return False
