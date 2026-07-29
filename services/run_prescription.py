from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class RunSegment:
    order: int
    segment_type: str
    label: str
    repetitions: int = 1
    distance_miles: float | None = None
    duration_seconds: int | None = None
    recovery_seconds: int | None = None
    pace_min_seconds_per_mile: int | None = None
    pace_max_seconds_per_mile: int | None = None
    target_rpe: float | None = None
    notes: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def format_pace(seconds_per_mile: int | float | None) -> str:
    if seconds_per_mile is None:
        return "—"
    value = int(round(seconds_per_mile))
    return f"{value // 60}:{value % 60:02d}/mi"


def treadmill_mph(seconds_per_mile: int | float | None) -> float | None:
    if not seconds_per_mile or seconds_per_mile <= 0:
        return None
    return round(3600 / float(seconds_per_mile), 1)


def pace_range_text(min_seconds: int | None, max_seconds: int | None) -> str:
    if min_seconds is None and max_seconds is None:
        return "By effort"
    if min_seconds is None:
        return format_pace(max_seconds)
    if max_seconds is None:
        return format_pace(min_seconds)
    fast = min(min_seconds, max_seconds)
    slow = max(min_seconds, max_seconds)
    return f"{format_pace(fast)}–{format_pace(slow)}"


def _scaled_paces(five_k_seconds: int) -> dict[str, tuple[int, int]]:
    five_k_pace = five_k_seconds / 3.106856
    return {
        "recovery": (round(five_k_pace + 70), round(five_k_pace + 120)),
        "easy": (round(five_k_pace + 45), round(five_k_pace + 100)),
        "long": (round(five_k_pace + 55), round(five_k_pace + 110)),
        "steady": (round(five_k_pace + 15), round(five_k_pace + 45)),
        "threshold": (round(five_k_pace - 25), round(five_k_pace + 5)),
        "interval": (round(five_k_pace - 70), round(five_k_pace - 35)),
        "stride": (round(five_k_pace - 100), round(five_k_pace - 65)),
    }


def build_run_prescription(
    workout_type: str,
    target_distance_miles: float,
    five_k_seconds: int = 2088,
    week_number: int = 1,
    is_deload: bool = False,
) -> tuple[RunSegment, ...]:
    """Create structured running segments from a recent 5K benchmark.

    Paces are ranges and should remain subordinate to effort, heat, terrain,
    recovery, and pain. The function intentionally avoids prescribing goal
    half-marathon pace before current fitness supports it.
    """
    zones = _scaled_paces(five_k_seconds)
    kind = workout_type.lower().strip()
    target = max(1.0, float(target_distance_miles))

    if "quality" in kind or "threshold" in kind or "interval" in kind:
        if is_deload:
            reps, work_seconds, recovery = 4, 120, 120
            zone = zones["threshold"]
            label = "Controlled threshold repetitions"
        elif week_number % 3 == 0:
            reps, work_seconds, recovery = 8, 60, 90
            zone = zones["interval"]
            label = "Short controlled intervals"
        elif week_number % 2 == 0:
            reps, work_seconds, recovery = 3, 480, 180
            zone = zones["threshold"]
            label = "Long threshold repetitions"
        else:
            reps, work_seconds, recovery = 6, 180, 120
            zone = zones["threshold"]
            label = "Threshold repetitions"
        return (
            RunSegment(1, "Warm-up", "Easy warm-up", duration_seconds=600,
                       pace_min_seconds_per_mile=zones["easy"][0], pace_max_seconds_per_mile=zones["easy"][1], target_rpe=3,
                       notes="Finish with 3 relaxed accelerations."),
            RunSegment(2, "Work", label, repetitions=reps, duration_seconds=work_seconds,
                       recovery_seconds=recovery, pace_min_seconds_per_mile=zone[0], pace_max_seconds_per_mile=zone[1], target_rpe=6.5 if is_deload else 7,
                       notes="Keep the final repetition controlled; do not sprint."),
            RunSegment(3, "Cool-down", "Easy cool-down", duration_seconds=600,
                       pace_min_seconds_per_mile=zones["recovery"][0], pace_max_seconds_per_mile=zones["recovery"][1], target_rpe=2.5),
        )

    if "long" in kind:
        easy_distance = round(target * (0.85 if not is_deload else 1.0), 1)
        segments = [
            RunSegment(1, "Continuous", "Long easy running", distance_miles=easy_distance,
                       pace_min_seconds_per_mile=zones["long"][0], pace_max_seconds_per_mile=zones["long"][1], target_rpe=3.5,
                       notes="Conversational effort. Walk briefly if form deteriorates."),
        ]
        remaining = round(target - easy_distance, 1)
        if remaining >= 0.5 and not is_deload:
            segments.append(
                RunSegment(2, "Finish", "Controlled steady finish", distance_miles=remaining,
                           pace_min_seconds_per_mile=zones["steady"][0], pace_max_seconds_per_mile=zones["steady"][1], target_rpe=5,
                           notes="Skip the steady finish when sleep or recovery is poor.")
            )
        return tuple(segments)

    # Easy / recovery run
    segments: list[RunSegment] = [
        RunSegment(1, "Continuous", "Easy conversational run", distance_miles=target,
                   pace_min_seconds_per_mile=zones["easy"][0], pace_max_seconds_per_mile=zones["easy"][1], target_rpe=3.5),
    ]
    if "easy" in kind and not is_deload:
        segments.append(
            RunSegment(2, "Strides", "Relaxed strides", repetitions=4, duration_seconds=20,
                       recovery_seconds=60, pace_min_seconds_per_mile=zones["stride"][0], pace_max_seconds_per_mile=zones["stride"][1], target_rpe=7,
                       notes="Fast and relaxed, not all-out. Walk or jog between repetitions.")
        )
    return tuple(segments)


def segments_summary(segments: tuple[RunSegment, ...] | list[RunSegment]) -> str:
    parts: list[str] = []
    for segment in segments:
        if segment.repetitions > 1:
            work = f"{segment.duration_seconds // 60:g} min" if segment.duration_seconds else f"{segment.distance_miles:g} mi"
            parts.append(f"{segment.repetitions} × {work} {segment.label.lower()}")
        elif segment.distance_miles:
            parts.append(f"{segment.distance_miles:g} mi {segment.label.lower()}")
        elif segment.duration_seconds:
            parts.append(f"{segment.duration_seconds // 60:g} min {segment.label.lower()}")
        else:
            parts.append(segment.label)
    return "; ".join(parts)
