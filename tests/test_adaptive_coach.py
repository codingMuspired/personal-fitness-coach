from datetime import date
from services.adaptive_coach import evaluate_recovery,recommend_session

def test_green_recovery():
    s=evaluate_recovery(sleep_hours=7.5,soreness=3,stress=5,pain_reported=False); assert s.level=='Green' and s.score>=75

def test_pain_forces_red():
    assert evaluate_recovery(sleep_hours=8,soreness=2,stress=2,pain_reported=True).level=='Red'

def test_yellow_quality_becomes_easy():
    s=evaluate_recovery(sleep_hours=5.5,soreness=7,stress=8,pain_reported=False); r=recommend_session(target_date=date(2026,7,29),recovery=s,current_week_miles=5,previous_week_miles=10,last_hard_session_days_ago=3); assert r.workout_type=='Easy Run' and r.intensity=='Reduced'

def test_mileage_reduces_run_duration():
    s=evaluate_recovery(sleep_hours=8,soreness=2,stress=3,pain_reported=False); r=recommend_session(target_date=date(2026,8,2),recovery=s,current_week_miles=20,previous_week_miles=15,last_hard_session_days_ago=3); assert r.duration_minutes<100
