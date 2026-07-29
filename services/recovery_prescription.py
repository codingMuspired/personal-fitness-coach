from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class RecoveryExercise:
    order: int
    name: str
    category: str
    sets: int = 1
    repetitions: int | None = None
    duration_seconds: int | None = None
    side: str | None = None
    target_rpe: float = 2.0
    notes: str | None = None
    optional: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_recovery_prescription(*, session_type: str, duration_minutes: int,
                                is_deload: bool = False,
                                recovery_level: str = "Green") -> tuple[RecoveryExercise, ...]:
    """Create an ordered active-recovery or gentle-mobility routine."""
    lower = session_type.lower()
    is_rest = "rest" in lower
    is_red = recovery_level == "Red"

    if is_red:
        return (
            RecoveryExercise(1, "Easy walk", "Cardio", duration_seconds=600, target_rpe=1.5,
                             notes="Only if walking is pain-free; otherwise rest."),
            RecoveryExercise(2, "Diaphragmatic breathing", "Breathing", duration_seconds=300,
                             target_rpe=1.0, notes="Slow nasal breathing with a long exhale."),
            RecoveryExercise(3, "Pain-free mobility choice", "Mobility", duration_seconds=300,
                             target_rpe=1.0, notes="Use only movements that reduce stiffness and do not reproduce pain."),
        )

    if is_rest:
        return (
            RecoveryExercise(1, "Easy walk", "Cardio", duration_seconds=600 if is_deload else 900,
                             target_rpe=2.0, optional=True,
                             notes="Comfortable pace. Skip when complete rest is more appropriate."),
            RecoveryExercise(2, "90/90 hip switches", "Mobility", sets=2, repetitions=6,
                             side="each side", notes="Move slowly without forcing range."),
            RecoveryExercise(3, "Knee-to-wall ankle rocks", "Mobility", sets=2, repetitions=10,
                             side="each side", notes="Keep the heel down."),
            RecoveryExercise(4, "Open-book rotations", "Mobility", sets=2, repetitions=6,
                             side="each side", notes="Follow the hand with your eyes."),
            RecoveryExercise(5, "Wall slides", "Mobility", sets=2, repetitions=8,
                             notes="Keep ribs controlled and move only through a pain-free range."),
        )

    walk_seconds = 900 if duration_minutes <= 30 else 1200
    routine = [
        RecoveryExercise(1, "Easy walk or light cycle", "Cardio", duration_seconds=walk_seconds,
                         target_rpe=2.0, notes="Conversational effort."),
        RecoveryExercise(2, "90/90 hip switches", "Mobility", sets=2, repetitions=6,
                         side="each side", notes="Use hands for support as needed."),
        RecoveryExercise(3, "Half-kneeling hip-flexor stretch", "Stretch", sets=2,
                         duration_seconds=40, side="each side",
                         notes="Squeeze the rear glute and avoid arching the low back."),
        RecoveryExercise(4, "Knee-to-wall ankle rocks", "Mobility", sets=2, repetitions=10,
                         side="each side", notes="Keep the heel planted."),
        RecoveryExercise(5, "Straight-knee calf stretch", "Stretch", sets=1,
                         duration_seconds=30, side="each side"),
        RecoveryExercise(6, "Bent-knee calf stretch", "Stretch", sets=1,
                         duration_seconds=30, side="each side"),
        RecoveryExercise(7, "Open-book rotations", "Mobility", sets=2, repetitions=6,
                         side="each side"),
        RecoveryExercise(8, "Wall slides", "Mobility", sets=2, repetitions=8,
                         notes="Stop before shoulder discomfort."),
        RecoveryExercise(9, "Band pull-aparts", "Activation", sets=2, repetitions=12,
                         notes="Use a light band and avoid shrugging."),
        RecoveryExercise(10, "Supported deep squat hold", "Mobility", sets=2,
                         duration_seconds=30, notes="Hold a rack, post, or door frame for support."),
        RecoveryExercise(11, "Optional easy yoga flow", "Yoga", duration_seconds=600,
                         target_rpe=2.0, optional=True,
                         notes="Use this only when it helps recovery rather than adding fatigue."),
    ]
    if is_deload or recovery_level == "Yellow":
        routine = [x for x in routine if not (x.optional and x.category == "Yoga")]
    return tuple(routine)


def recovery_summary(items: tuple[RecoveryExercise, ...]) -> str:
    parts: list[str] = []
    for item in items:
        if item.duration_seconds:
            dose = f"{item.sets}×{item.duration_seconds} sec" if item.sets > 1 else f"{item.duration_seconds} sec"
        elif item.repetitions:
            dose = f"{item.sets}×{item.repetitions}"
        else:
            dose = "By feel"
        side = f" {item.side}" if item.side else ""
        optional = " optional" if item.optional else ""
        parts.append(f"{item.name}: {dose}{side}{optional}")
    return "; ".join(parts)
