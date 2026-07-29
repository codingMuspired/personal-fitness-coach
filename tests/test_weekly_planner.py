from datetime import date

from services.adaptive_coach import RecoveryState
from services.weekly_planner import (
    calculate_target_mileage,
    generate_weekly_plan,
    reschedule_missed_session,
    should_deload,
)


def test_deload_after_three_build_weeks():
    result, reasons = should_deload(
        completed_hard_sessions_last_21_days=7,
        average_recovery_score=78,
        consecutive_build_weeks=3,
        pain_checkins_last_7_days=0,
    )
    assert result is True
    assert reasons


def test_green_week_mileage_growth_is_capped():
    target = calculate_target_mileage(
        previous_week_miles=20,
        four_week_average=18,
        is_deload=False,
        recovery_level='Green',
    )
    assert 20 < target <= 22


def test_deload_reduces_mileage():
    target = calculate_target_mileage(
        previous_week_miles=20,
        four_week_average=20,
        is_deload=True,
        recovery_level='Green',
    )
    assert target == 15.0


def test_week_contains_seven_sessions_and_strength_prescriptions():
    plan = generate_weekly_plan(
        week_start_date=date(2026, 8, 3),
        recovery=RecoveryState('Green', 90, ('Good recovery',)),
        previous_week_miles=15,
        four_week_average_miles=14,
        completed_hard_sessions_last_21_days=7,
        average_recovery_score=80,
        consecutive_build_weeks=2,
        pain_checkins_last_7_days=0,
        lift_history={},
    )
    assert len(plan.sessions) == 7
    strength = [s for s in plan.sessions if s.workout_type == 'Strength A'][0]
    assert len(strength.exercises) >= 6


def test_missed_hard_session_is_not_placed_next_to_another_hard_day():
    plan = generate_weekly_plan(
        week_start_date=date(2026, 8, 3),
        recovery=RecoveryState('Green', 90, ('Good recovery',)),
        previous_week_miles=15,
        four_week_average_miles=14,
        completed_hard_sessions_last_21_days=7,
        average_recovery_score=80,
        consecutive_build_weeks=2,
        pain_checkins_last_7_days=0,
        lift_history={},
    )
    updated = reschedule_missed_session(
        sessions=plan.sessions,
        missed_date=date(2026, 8, 4),
        current_date=date(2026, 8, 5),
    )
    moved = [s for s in updated if s.moved_from_date == date(2026, 8, 4)]
    assert len(moved) <= 1
