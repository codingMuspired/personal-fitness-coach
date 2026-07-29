from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import date
from typing import Any

@dataclass(frozen=True)
class RecoveryState:
    level: str
    score: int
    reasons: tuple[str, ...]

@dataclass(frozen=True)
class SessionRecommendation:
    workout_type: str
    title: str
    instructions: str
    duration_minutes: int
    intensity: str
    home_alternative: str
    rationale: tuple[str, ...]
    def to_dict(self) -> dict[str, Any]:
        result = asdict(self); result['rationale'] = list(self.rationale); return result

WEEKLY_TEMPLATE = {
    0: ('Recovery', 'Active recovery + mobility', 35, 'Easy walk plus hips, ankles, and shoulders mobility.'),
    1: ('Strength A', 'Strength A', 65, 'Squat, hinge, push, row, split squat, trunk, and calves.'),
    2: ('Quality Run', 'Quality run', 55, 'Controlled threshold or interval work based on your current block.'),
    3: ('Rest', 'Rest or gentle mobility', 20, 'Keep this easy and use it as a work-stress buffer.'),
    4: ('Strength B', 'Strength B + Spartan', 70, 'Pulling, hangs, carries, step-ups, crawling, and rope-skill work.'),
    5: ('Easy Run', 'Easy run + strides', 45, 'Conversational aerobic work. Remove this first during a busy week.'),
    6: ('Long Run', 'Long easy run', 100, 'Stay conversational and practice hydration or fuel when appropriate.'),
}

def evaluate_recovery(*, sleep_hours: float, soreness: int, stress: int, pain_reported: bool, resting_hr_delta: int = 0) -> RecoveryState:
    reasons=[]; score=100
    if pain_reported: return RecoveryState('Red',0,('Sharp pain or altered movement was reported.',))
    if sleep_hours < 5: score-=35; reasons.append('Less than 5 hours of sleep.')
    elif sleep_hours < 6: score-=22; reasons.append('Less than 6 hours of sleep.')
    elif sleep_hours < 7: score-=8; reasons.append('Sleep was below the preferred 7-hour level.')
    if soreness >= 8: score-=30; reasons.append('Soreness is very high.')
    elif soreness >= 6: score-=16; reasons.append('Soreness is elevated.')
    if stress >= 9: score-=25; reasons.append('Stress is very high.')
    elif stress >= 7: score-=12; reasons.append('Stress is elevated.')
    if resting_hr_delta >= 10: score-=20; reasons.append('Resting heart rate is substantially above normal.')
    elif resting_hr_delta >= 6: score-=10; reasons.append('Resting heart rate is above normal.')
    score=max(0,min(100,score)); level='Green' if score>=75 else 'Yellow' if score>=45 else 'Red'
    if not reasons: reasons.append('Recovery inputs are within normal ranges.')
    return RecoveryState(level,score,tuple(reasons))

def recommend_session(*, target_date: date, recovery: RecoveryState, current_week_miles: float, previous_week_miles: float, last_hard_session_days_ago: int | None, weight_change_per_week: float | None = None) -> SessionRecommendation:
    kind,title,duration,instructions=WEEKLY_TEMPLATE[target_date.weekday()]
    rationale=[f"Base schedule for {target_date.strftime('%A')}."]; intensity='Normal'; home='Use the matching resistance-band or bodyweight variation.'
    if recovery.level=='Red':
        return SessionRecommendation('Recovery','Recovery only','Rest, walk gently, or use pain-free mobility only.',20,'Very easy','Gentle walking and pain-free mobility.',tuple(rationale+list(recovery.reasons)))
    mileage_ratio=(current_week_miles/previous_week_miles) if previous_week_miles>0 else 1.0
    hard_kind=kind in {'Quality Run','Strength A','Strength B','Long Run'}
    if recovery.level=='Yellow':
        intensity='Reduced'; duration=max(20,round(duration*.7)); rationale.extend(recovery.reasons)
        if kind=='Quality Run': kind,title='Easy Run','Easy run or brisk walk'; instructions='Replace quality work with conversational running or run/walk intervals.'
        elif kind in {'Strength A','Strength B'}: instructions += ' Remove one working set from each main movement and keep 3–4 reps in reserve.'
        elif kind=='Long Run': instructions='Keep the run conversational and shorten it by about 20–30%.'
    if hard_kind and last_hard_session_days_ago is not None and last_hard_session_days_ago < 2:
        intensity='Reduced'; rationale.append('A hard session was completed less than 48 hours ago.')
        if kind=='Quality Run': kind,title='Easy Run','Easy aerobic run'; instructions='Run conversationally instead of completing intervals or tempo work.'
        elif kind in {'Strength A','Strength B'}: instructions += ' Use lighter loads and stop well before failure.'
    if kind in {'Easy Run','Quality Run','Long Run'} and mileage_ratio>1.15:
        duration=max(25,round(duration*.8)); intensity='Reduced'; rationale.append('Current mileage is already more than 15% above the previous week.')
    if weight_change_per_week is not None and weight_change_per_week < -1.5:
        intensity='Reduced' if intensity=='Normal' else intensity; rationale.append('Weight is dropping faster than the initial target; monitor fueling and recovery.')
    return SessionRecommendation(kind,title,instructions,duration,intensity,home,tuple(rationale))
