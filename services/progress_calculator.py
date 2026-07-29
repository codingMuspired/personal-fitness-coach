from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from statistics import mean


@dataclass(frozen=True)
class WeightTrend:
    weekly_change: float | None
    projected_12_week_change: float | None
    recommendation: str


def calculate_weight_trend(measurements: list[dict]) -> WeightTrend:
    points = sorted(
        [(date.fromisoformat(str(r["measured_on"])), float(r["weight_lb"])) for r in measurements],
        key=lambda item: item[0],
    )
    if len(points) < 2 or (points[-1][0] - points[0][0]).days < 7:
        return WeightTrend(None, None, "Log at least two measurements spanning seven days.")
    days = (points[-1][0] - points[0][0]).days
    weekly = (points[-1][1] - points[0][1]) / days * 7
    projected = weekly * 12
    loss = -weekly
    if loss < 0.5:
        message = "Below target trend. Hold intake until you have three consistent weeks, then consider a small adjustment."
    elif loss <= 1.5:
        message = "Trend is within a sustainable starting range. Keep calories and training consistent."
    else:
        message = "Loss is fast. Review hunger, recovery, and performance before reducing intake further."
    return WeightTrend(round(weekly, 2), round(projected, 1), message)


def current_week_mileage(runs: list[dict], today: date | None = None) -> float:
    today = today or date.today()
    start = today - timedelta(days=today.weekday())
    return round(sum(float(r["distance_miles"]) for r in runs if date.fromisoformat(str(r["run_date"])) >= start), 2)


def previous_week_mileage(runs: list[dict], today: date | None = None) -> float:
    today = today or date.today()
    current_start = today - timedelta(days=today.weekday())
    previous_start = current_start - timedelta(days=7)
    return round(sum(float(r["distance_miles"]) for r in runs
                     if previous_start <= date.fromisoformat(str(r["run_date"])) < current_start), 2)


def mileage_guidance(current: float, previous: float) -> str:
    if previous <= 0:
        return "No prior complete week is available. Build from a comfortable baseline."
    change = (current - previous) / previous
    if change > 0.15:
        return "Mileage is already more than 15% above last week. Do not add optional distance."
    if change < -0.25:
        return "This is a lower-volume week. That can be appropriate for recovery or schedule constraints."
    return "Mileage is reasonably close to the previous week. Let recovery guide any remaining optional running."


def average_nutrition(logs: list[dict], field: str) -> float | None:
    values = [float(r[field]) for r in logs if r.get(field) is not None]
    return round(mean(values), 1) if values else None
