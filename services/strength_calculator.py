from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StrengthRecommendation:
    next_weight: float
    next_sets: int
    next_repetitions: int
    action: str
    reason: str


def round_to_increment(value: float, increment: float) -> float:
    if increment <= 0:
        raise ValueError("Increment must be greater than zero.")

    return round(value / increment) * increment


def estimate_one_rep_max(weight: float, repetitions: int) -> float:
    """
    Estimate one-repetition maximum using the Epley formula.
    Avoid using very high-repetition sets for this estimate.
    """

    if weight <= 0:
        raise ValueError("Weight must be greater than zero.")

    if repetitions <= 0:
        raise ValueError("Repetitions must be greater than zero.")

    return weight * (1 + repetitions / 30)


def recommend_next_session(
    current_weight: float,
    sets: int,
    repetitions: int,
    all_sets_completed: bool,
    average_rpe: float,
    exercise_type: str,
    pain_reported: bool = False,
) -> StrengthRecommendation:
    if pain_reported:
        return StrengthRecommendation(
            next_weight=current_weight,
            next_sets=sets,
            next_repetitions=repetitions,
            action="Stop automatic progression",
            reason="Pain was reported. Review or substitute the movement.",
        )

    increment = 5.0 if exercise_type.lower() == "upper" else 10.0

    if all_sets_completed and average_rpe <= 7:
        next_weight = round_to_increment(
            current_weight + increment,
            2.5 if exercise_type.lower() == "upper" else 5.0,
        )

        return StrengthRecommendation(
            next_weight=next_weight,
            next_sets=sets,
            next_repetitions=repetitions,
            action="Increase weight",
            reason="All sets were completed with manageable effort.",
        )

    if all_sets_completed and average_rpe <= 8:
        return StrengthRecommendation(
            next_weight=current_weight,
            next_sets=sets,
            next_repetitions=repetitions,
            action="Repeat weight",
            reason="The session was successful but sufficiently challenging.",
        )

    return StrengthRecommendation(
        next_weight=round_to_increment(current_weight * 0.95, 2.5),
        next_sets=max(2, sets - 1),
        next_repetitions=repetitions,
        action="Reduce load",
        reason="The previous session was incomplete or too difficult.",
    )