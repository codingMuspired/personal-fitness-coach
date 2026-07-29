from services.recovery_prescription import build_recovery_prescription, recovery_summary


def test_active_recovery_contains_hips_ankles_shoulders():
    items = build_recovery_prescription(session_type="Recovery", duration_minutes=35)
    names = {x.name for x in items}
    assert "90/90 hip switches" in names
    assert "Knee-to-wall ankle rocks" in names
    assert "Wall slides" in names


def test_rest_day_is_shorter_and_optional_walk():
    items = build_recovery_prescription(session_type="Rest", duration_minutes=20)
    walk = items[0]
    assert walk.optional is True
    assert walk.duration_seconds in {600, 900}


def test_red_recovery_is_restricted():
    items = build_recovery_prescription(
        session_type="Recovery", duration_minutes=30, recovery_level="Red"
    )
    assert len(items) == 3
    assert all(x.target_rpe <= 1.5 for x in items)


def test_yellow_removes_optional_yoga():
    items = build_recovery_prescription(
        session_type="Recovery", duration_minutes=35, recovery_level="Yellow"
    )
    assert not any(x.category == "Yoga" for x in items)


def test_summary_has_dose():
    items = build_recovery_prescription(session_type="Recovery", duration_minutes=35)
    summary = recovery_summary(items)
    assert "90/90 hip switches" in summary
    assert "2×6" in summary
