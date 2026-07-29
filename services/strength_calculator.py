from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StrengthRecommendation:
    next_weight: float
    next_sets: int
    target_reps: int
    action: str
    reason: str
    estimated_one_rep_max: float | None


def round_to_increment(value: float, increment: float) -> float:
    if increment <= 0:
        raise ValueError("Increment must be greater than zero.")
    return round(value / increment) * increment


def estimate_one_rep_max(weight: float, repetitions: int) -> float | None:
    """Epley estimate. Suppress estimates for unloaded or very high-repetition sets."""
    if weight <= 0 or repetitions <= 0 or repetitions > 15:
        return None
    return round(weight * (1 + repetitions / 30), 1)


def recommend_next_session(*, current_weight: float, completed_sets: int, planned_sets: int,
                           target_reps: int, minimum_reps_completed: int, average_rpe: float,
                           exercise_category: str, pain_reported: bool = False) -> StrengthRecommendation:
    category = (exercise_category or "").lower()
    upper = any(word in category for word in ("upper", "push", "pull", "grip"))
    increment = 5.0 if upper else 10.0
    plate_increment = 2.5 if upper else 5.0
    e1rm = estimate_one_rep_max(current_weight, max(1, minimum_reps_completed))

    if pain_reported:
        return StrengthRecommendation(
            current_weight, max(2, planned_sets - 1), target_reps,
            "Do not auto-progress", "Pain was reported. Use a pain-free substitute or seek qualified guidance.", e1rm,
        )

    all_sets = completed_sets >= planned_sets
    all_reps = minimum_reps_completed >= target_reps

    if all_sets and all_reps and average_rpe <= 7.5:
        return StrengthRecommendation(
            round_to_increment(current_weight + increment, plate_increment), planned_sets, target_reps,
            "Increase load", "All target work was completed with at least a few repetitions in reserve.", e1rm,
        )
    if all_sets and all_reps and average_rpe <= 8.5:
        return StrengthRecommendation(
            current_weight, planned_sets, target_reps,
            "Repeat load", "The load was productive and sufficiently challenging.", e1rm,
        )
    if all_sets and minimum_reps_completed >= max(1, target_reps - 1) and average_rpe <= 9:
        return StrengthRecommendation(
            current_weight, planned_sets, target_reps,
            "Repeat and complete", "Keep the load until every set reaches the repetition target cleanly.", e1rm,
        )
    return StrengthRecommendation(
        round_to_increment(max(0, current_weight * 0.95), plate_increment), max(2, planned_sets - 1), target_reps,
        "Reduce fatigue", "The prior work was incomplete or too difficult. Reduce load or one set next time.", e1rm,
    )


def recommend_timed_progression(*, best_seconds: int, average_rpe: float, pain_reported: bool = False) -> tuple[int, str]:
    if pain_reported:
        return best_seconds, "Hold duration and use only a pain-free variation."
    if average_rpe <= 7.5:
        return best_seconds + 5, "Add 5 seconds next session."
    if average_rpe <= 8.5:
        return best_seconds, "Repeat the same duration."
    return max(5, best_seconds - 5), "Reduce by 5 seconds and rebuild cleanly."
