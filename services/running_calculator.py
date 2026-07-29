from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Pace:
    total_seconds_per_mile: float

    @property
    def display(self) -> str:
        minutes = int(self.total_seconds_per_mile // 60)
        seconds = round(self.total_seconds_per_mile % 60)

        if seconds == 60:
            minutes += 1
            seconds = 0

        return f"{minutes}:{seconds:02d}/mi"

    @property
    def treadmill_mph(self) -> float:
        return 3600 / self.total_seconds_per_mile


def calculate_pace(
    distance_miles: float,
    total_seconds: int,
) -> Pace:
    if distance_miles <= 0:
        raise ValueError("Distance must be greater than zero.")

    if total_seconds <= 0:
        raise ValueError("Time must be greater than zero.")

    return Pace(total_seconds_per_mile=total_seconds / distance_miles)


def goal_pace(
    distance_miles: float,
    hours: int,
    minutes: int,
    seconds: int = 0,
) -> Pace:
    total_seconds = hours * 3600 + minutes * 60 + seconds
    return calculate_pace(distance_miles, total_seconds)


def training_paces_from_5k(five_k_seconds: int) -> dict[str, Pace]:
    five_k_pace = calculate_pace(3.10686, five_k_seconds)
    baseline = five_k_pace.total_seconds_per_mile

    return {
        "Recovery": Pace(baseline + 80),
        "Easy": Pace(baseline + 50),
        "Long": Pace(baseline + 65),
        "Steady": Pace(baseline + 20),
        "Tempo": Pace(baseline - 30),
        "Short intervals": Pace(baseline - 75),
    }