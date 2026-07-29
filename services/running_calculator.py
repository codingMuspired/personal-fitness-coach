from __future__ import annotations

from dataclasses import dataclass
from math import pow

MILE_METERS = 1609.344
KM_5_MILES = 3.106856
HALF_MARATHON_MILES = 13.1094
MARATHON_MILES = 26.2188


@dataclass(frozen=True)
class PaceRange:
    low_seconds: int
    high_seconds: int

    @property
    def display(self) -> str:
        return f"{format_pace(self.low_seconds)}–{format_pace(self.high_seconds)}"


def format_pace(seconds_per_mile: float) -> str:
    total = max(1, round(seconds_per_mile))
    minutes, seconds = divmod(total, 60)
    return f"{minutes}:{seconds:02d}/mi"


def treadmill_mph(seconds_per_mile: float) -> float:
    if seconds_per_mile <= 0:
        raise ValueError("Pace must be greater than zero.")
    return round(3600 / seconds_per_mile, 1)


def predict_time(source_distance_miles: float, source_seconds: int, target_distance_miles: float) -> int:
    """Riegel race prediction using exponent 1.06."""
    if source_distance_miles <= 0 or source_seconds <= 0 or target_distance_miles <= 0:
        raise ValueError("Distances and time must be greater than zero.")
    return round(source_seconds * pow(target_distance_miles / source_distance_miles, 1.06))


def training_paces_from_5k(five_k_seconds: int) -> dict[str, PaceRange]:
    """Conservative starting ranges from a recent 5K result.

    Ranges deliberately overlap because RPE, terrain, heat, sleep, and accumulated
    fatigue matter more than hitting one exact pace.
    """
    if five_k_seconds <= 0:
        raise ValueError("5K time must be greater than zero.")
    race_pace = five_k_seconds / KM_5_MILES
    return {
        "Recovery": PaceRange(round(race_pace + 80), round(race_pace + 145)),
        "Easy": PaceRange(round(race_pace + 50), round(race_pace + 110)),
        "Long": PaceRange(round(race_pace + 60), round(race_pace + 125)),
        "Steady": PaceRange(round(race_pace + 15), round(race_pace + 45)),
        "Tempo": PaceRange(round(race_pace - 35), round(race_pace - 5)),
        "Intervals": PaceRange(round(race_pace - 85), round(race_pace - 45)),
    }


def adjusted_pace_range(base: PaceRange, *, sleep_hours: float, soreness: int, stress: int,
                        temperature_f: float | None = None) -> PaceRange:
    """Slow a recommendation for poor recovery or warm conditions.

    This never makes a session faster than the base range.
    """
    adjustment = 0
    if sleep_hours < 6:
        adjustment += 20
    if soreness >= 7:
        adjustment += 20
    if stress >= 8:
        adjustment += 15
    if temperature_f is not None and temperature_f >= 75:
        adjustment += min(45, round((temperature_f - 70) * 1.5))
    return PaceRange(base.low_seconds + adjustment, base.high_seconds + adjustment)


def goal_pace(total_seconds: int, distance_miles: float) -> int:
    if total_seconds <= 0 or distance_miles <= 0:
        raise ValueError("Time and distance must be greater than zero.")
    return round(total_seconds / distance_miles)


def format_duration(total_seconds: int) -> str:
    hours, remainder = divmod(max(0, round(total_seconds)), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}:{minutes:02d}:{seconds:02d}"
