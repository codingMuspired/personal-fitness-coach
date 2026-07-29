from services.run_prescription import build_run_prescription, treadmill_mph


def test_quality_run_contains_work_repetitions():
    segments = build_run_prescription("Quality Run", 4.0, five_k_seconds=2088, week_number=1)
    work = next(x for x in segments if x.segment_type == "Work")
    assert work.repetitions == 6
    assert work.duration_seconds == 180
    assert work.recovery_seconds == 120
    assert work.pace_min_seconds_per_mile < work.pace_max_seconds_per_mile


def test_even_week_uses_long_threshold_repeats():
    segments = build_run_prescription("Quality Run", 4.0, week_number=2)
    work = next(x for x in segments if x.segment_type == "Work")
    assert work.repetitions == 3
    assert work.duration_seconds == 480


def test_easy_run_adds_strides():
    segments = build_run_prescription("Easy Run", 4.0, is_deload=False)
    assert any(x.segment_type == "Strides" for x in segments)


def test_deload_easy_run_removes_strides():
    segments = build_run_prescription("Easy Run", 4.0, is_deload=True)
    assert not any(x.segment_type == "Strides" for x in segments)


def test_treadmill_conversion():
    assert treadmill_mph(600) == 6.0
