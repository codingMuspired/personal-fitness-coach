from services.running_calculator import HALF_MARATHON_MILES, format_pace, goal_pace, predict_time, training_paces_from_5k
from services.strength_calculator import estimate_one_rep_max, recommend_next_session


def test_sub_two_half_pace():
    pace = goal_pace(2 * 3600, HALF_MARATHON_MILES)
    assert format_pace(pace) == "9:09/mi"


def test_training_ranges_exist():
    ranges = training_paces_from_5k(34 * 60 + 48)
    assert "Easy" in ranges
    assert ranges["Easy"].low_seconds < ranges["Easy"].high_seconds


def test_prediction_is_longer_for_longer_distance():
    assert predict_time(3.106856, 2088, HALF_MARATHON_MILES) > 2088


def test_e1rm():
    assert estimate_one_rep_max(100, 10) == 133.3


def test_strength_progression():
    result = recommend_next_session(current_weight=100, completed_sets=3, planned_sets=3,
        target_reps=8, minimum_reps_completed=8, average_rpe=7,
        exercise_category="upper push", pain_reported=False)
    assert result.action == "Increase load"
    assert result.next_weight > 100
