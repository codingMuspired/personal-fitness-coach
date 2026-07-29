from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import date, timedelta
from typing import Any, Iterable

from services.adaptive_coach import RecoveryState
from services.strength_calculator import recommend_next_session
from services.run_prescription import RunSegment, build_run_prescription, segments_summary, pace_range_text, treadmill_mph
from services.recovery_prescription import RecoveryExercise, build_recovery_prescription, recovery_summary


@dataclass(frozen=True)
class ExercisePrescription:
    exercise_name: str
    order: int
    sets: int | None = None
    reps: int | None = None
    weight_lb: float | None = None
    duration_seconds: int | None = None
    distance_meters: float | None = None
    target_rpe: float | None = 7.5
    reps_in_reserve: float | None = 2.5
    substitution_name: str | None = None
    notes: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PlannedSession:
    session_date: date
    sequence_number: int
    workout_type: str
    title: str
    duration_minutes: int
    target_distance_miles: float | None
    intensity: str
    instructions: str
    home_alternative: str
    exercises: tuple[ExercisePrescription, ...] = ()
    run_segments: tuple[RunSegment, ...] = ()
    recovery_exercises: tuple[RecoveryExercise, ...] = ()
    pace_guidance: str | None = None
    treadmill_guidance: str | None = None
    run_structure_summary: str | None = None
    status: str = 'Planned'
    moved_from_date: date | None = None

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result['session_date'] = self.session_date.isoformat()
        result['moved_from_date'] = self.moved_from_date.isoformat() if self.moved_from_date else None
        result['exercises'] = [x.to_dict() for x in self.exercises]
        result['run_segments'] = [x.to_dict() for x in self.run_segments]
        result['recovery_exercises'] = [x.to_dict() for x in self.recovery_exercises]
        return result


@dataclass(frozen=True)
class WeeklyPlan:
    week_start_date: date
    plan_name: str
    phase_name: str
    is_deload: bool
    target_run_miles: float
    rationale: tuple[str, ...]
    evidence: dict[str, Any]
    sessions: tuple[PlannedSession, ...]

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result['week_start_date'] = self.week_start_date.isoformat()
        result['rationale'] = list(self.rationale)
        result['sessions'] = [s.to_dict() for s in self.sessions]
        return result


BASE_TEMPLATE = (
    (0, 'Recovery', 'Active recovery + mobility', 35, None,
     'Easy walking plus the 20-minute hips, ankles, and shoulders routine.'),
    (1, 'Strength A', 'Strength A', 65, None,
     'Lower-body foundation, push, pull, trunk, and calves.'),
    (2, 'Quality Run', 'Quality run', 55, 4.0,
     'Controlled threshold or intervals. Keep the final repetition technically clean.'),
    (3, 'Rest', 'Rest or gentle mobility', 20, None,
     'Use this as the recovery and work-stress buffer.'),
    (4, 'Strength B', 'Strength B + Spartan', 70, None,
     'Pulling, grip, carries, step-ups, crawling, and rope-skill work.'),
    (5, 'Easy Run', 'Easy run + strides', 45, 3.5,
     'Conversational running with four relaxed strides if recovery is green.'),
    (6, 'Long Run', 'Long easy run', 100, 8.0,
     'Conversational long run with hydration and fueling practice.'),
)

STRENGTH_A = (
    ('Goblet Squat', 3, 8, 'Band Squat'),
    ('Romanian Deadlift', 3, 10, 'Band Romanian Deadlift'),
    ('Dumbbell Bench Press', 3, 10, 'Push-Up'),
    ('Cable Row', 3, 10, 'Band Row'),
    ('Reverse Lunge', 2, 8, 'Bodyweight Reverse Lunge'),
    ('Pallof Press', 3, 10, 'Band Pallof Press'),
    ('Standing Calf Raise', 3, 15, 'Single-Leg Calf Raise'),
)

STRENGTH_B = (
    ('Assisted Pull-Up', 3, 8, 'Kneeling Band Pulldown'),
    ('Dead Hang', 4, None, 'Band Straight-Arm Pulldown'),
    ('Farmer Carry', 4, None, 'Loaded Backpack Carry'),
    ('Step-Up', 3, 10, 'Stair Step-Up'),
    ('Overhead Press', 3, 10, 'Band Overhead Press'),
    ('Bear Crawl', 3, None, 'Bear Crawl'),
    ('Towel-Grip Pulldown', 3, 10, 'Band Towel Isometric Pull'),
)


def monday_of(day: date) -> date:
    return day - timedelta(days=day.weekday())


def should_deload(*, completed_hard_sessions_last_21_days: int,
                  average_recovery_score: float | None,
                  consecutive_build_weeks: int,
                  pain_checkins_last_7_days: int,
                  requested: bool = False) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    if requested:
        reasons.append('A deload was manually requested.')
    if consecutive_build_weeks >= 3:
        reasons.append('Three or more consecutive build weeks were completed.')
    if average_recovery_score is not None and average_recovery_score < 65:
        reasons.append('Average recovery score is below 65.')
    if completed_hard_sessions_last_21_days >= 10:
        reasons.append('Recent hard-session density is high.')
    if pain_checkins_last_7_days > 0:
        reasons.append('Pain was reported during the last seven days.')
    return bool(reasons), tuple(reasons)


def calculate_target_mileage(*, previous_week_miles: float,
                             four_week_average: float,
                             is_deload: bool,
                             recovery_level: str) -> float:
    baseline = previous_week_miles if previous_week_miles > 0 else four_week_average
    if baseline <= 0:
        baseline = 12.0
    if is_deload:
        factor = 0.75
    elif recovery_level == 'Red':
        factor = 0.65
    elif recovery_level == 'Yellow':
        factor = 0.90
    else:
        factor = 1.05
    target = baseline * factor
    ceiling = max(baseline + 1.5, baseline * 1.10)
    if not is_deload and recovery_level == 'Green':
        target = min(target, ceiling)
    return round(max(6.0, target), 1)


def _latest_lift(history: dict[str, dict[str, Any]], exercise_name: str,
                 default_weight: float | None, sets: int, reps: int | None) -> tuple[float | None, int]:
    row = history.get(exercise_name)
    if not row or not row.get('weight_lb'):
        return default_weight, sets
    rec = recommend_next_session(
        current_weight=float(row['weight_lb']),
        sets=int(row.get('sets', sets)),
        repetitions=int(row.get('repetitions', reps or 1)),
        all_sets_completed=bool(row.get('all_sets_completed', True)),
        average_rpe=float(row.get('average_rpe', 8.0)),
        exercise_type=str(row.get('exercise_type', 'upper')),
        pain_reported=bool(row.get('pain_reported', False)),
    )
    return rec.next_weight, rec.next_sets


def build_strength_prescriptions(kind: str, lift_history: dict[str, dict[str, Any]],
                                 *, is_deload: bool, recovery_level: str) -> tuple[ExercisePrescription, ...]:
    template = STRENGTH_A if kind == 'Strength A' else STRENGTH_B
    rows: list[ExercisePrescription] = []
    defaults = {
        'Goblet Squat': 25.0, 'Romanian Deadlift': 45.0, 'Dumbbell Bench Press': 15.0,
        'Cable Row': 40.0, 'Reverse Lunge': 10.0, 'Pallof Press': 15.0,
        'Standing Calf Raise': 0.0, 'Assisted Pull-Up': None, 'Dead Hang': None,
        'Farmer Carry': 20.0, 'Step-Up': 10.0, 'Overhead Press': 10.0,
        'Bear Crawl': None, 'Towel-Grip Pulldown': 20.0,
    }
    timed = {'Dead Hang': 20, 'Farmer Carry': 40, 'Bear Crawl': 30}
    for order, (name, sets, reps, substitute) in enumerate(template, start=1):
        weight, prescribed_sets = _latest_lift(lift_history, name, defaults.get(name), sets, reps)
        if is_deload or recovery_level == 'Yellow':
            prescribed_sets = max(2, prescribed_sets - 1)
            if weight:
                weight = round(weight * 0.9 / 2.5) * 2.5
        if recovery_level == 'Red':
            prescribed_sets = 0
        rows.append(ExercisePrescription(
            exercise_name=name,
            order=order,
            sets=prescribed_sets,
            reps=reps,
            weight_lb=weight,
            duration_seconds=timed.get(name),
            target_rpe=6.5 if is_deload else 7.5,
            reps_in_reserve=3.5 if is_deload else 2.5,
            substitution_name=substitute,
            notes='Technique first; manual override allowed.',
        ))
    return tuple(rows)


def generate_weekly_plan(*, week_start_date: date,
                         recovery: RecoveryState,
                         previous_week_miles: float,
                         four_week_average_miles: float,
                         completed_hard_sessions_last_21_days: int,
                         average_recovery_score: float | None,
                         consecutive_build_weeks: int,
                         pain_checkins_last_7_days: int,
                         lift_history: dict[str, dict[str, Any]],
                         requested_deload: bool = False,
                         phase_name: str = 'Foundation') -> WeeklyPlan:
    week_start_date = monday_of(week_start_date)
    is_deload, deload_reasons = should_deload(
        completed_hard_sessions_last_21_days=completed_hard_sessions_last_21_days,
        average_recovery_score=average_recovery_score,
        consecutive_build_weeks=consecutive_build_weeks,
        pain_checkins_last_7_days=pain_checkins_last_7_days,
        requested=requested_deload,
    )
    if recovery.level == 'Red':
        is_deload = True
        deload_reasons = deload_reasons + ('Current recovery state is red.',)
    target_miles = calculate_target_mileage(
        previous_week_miles=previous_week_miles,
        four_week_average=four_week_average_miles,
        is_deload=is_deload,
        recovery_level=recovery.level,
    )
    base_run_total = sum(float(x[4] or 0) for x in BASE_TEMPLATE)
    run_scale = target_miles / base_run_total if base_run_total else 1.0
    rationale = list(deload_reasons)
    if not rationale:
        rationale.append('Recovery and recent workload support a normal build week.')
    rationale.append(f'Run target is based on last week and recent average: {target_miles:.1f} miles.')
    sessions: list[PlannedSession] = []
    for seq, (weekday, kind, title, duration, distance, instructions) in enumerate(BASE_TEMPLATE, start=1):
        session_date = week_start_date + timedelta(days=weekday)
        intensity = 'Reduced' if is_deload or recovery.level == 'Yellow' else 'Normal'
        session_distance = round(distance * run_scale, 1) if distance else None
        session_duration = duration
        if is_deload:
            session_duration = max(20, round(duration * 0.75))
        if recovery.level == 'Yellow':
            session_duration = max(20, round(session_duration * 0.9))
        if recovery.level == 'Red' and kind not in {'Recovery', 'Rest'}:
            kind, title = 'Recovery', 'Recovery only'
            session_distance = None
            session_duration = 20
            instructions = 'Rest, gentle walking, and pain-free mobility only.'
            intensity = 'Very easy'
        exercises: tuple[ExercisePrescription, ...] = ()
        run_segments: tuple[RunSegment, ...] = ()
        recovery_exercises: tuple[RecoveryExercise, ...] = ()
        pace_guidance = None
        treadmill_guidance = None
        run_structure_summary = None
        if kind in {'Strength A', 'Strength B'}:
            exercises = build_strength_prescriptions(kind, lift_history, is_deload=is_deload, recovery_level=recovery.level)
        if kind in {'Recovery', 'Rest'}:
            recovery_exercises = build_recovery_prescription(
                session_type=kind, duration_minutes=session_duration,
                is_deload=is_deload, recovery_level=recovery.level,
            )
            instructions = recovery_summary(recovery_exercises)
        if kind in {'Quality Run', 'Easy Run', 'Long Run'} and session_distance:
            run_segments = build_run_prescription(
                kind, session_distance, five_k_seconds=2088,
                week_number=max(1, ((week_start_date.toordinal() // 7) % 12) + 1),
                is_deload=is_deload,
            )
            run_structure_summary = segments_summary(run_segments)
            paced = [x for x in run_segments if x.pace_min_seconds_per_mile or x.pace_max_seconds_per_mile]
            if paced:
                pace_guidance = '; '.join(f"{x.label}: {pace_range_text(x.pace_min_seconds_per_mile, x.pace_max_seconds_per_mile)}" for x in paced)
                first = paced[0]
                midpoint = ((first.pace_min_seconds_per_mile or first.pace_max_seconds_per_mile) + (first.pace_max_seconds_per_mile or first.pace_min_seconds_per_mile)) / 2
                treadmill_guidance = f"Approximately {treadmill_mph(midpoint):.1f} mph for the first paced segment"
        sessions.append(PlannedSession(
            session_date=session_date,
            sequence_number=seq,
            workout_type=kind,
            title=title,
            duration_minutes=session_duration,
            target_distance_miles=session_distance,
            intensity=intensity,
            instructions=instructions,
            home_alternative='Use the listed resistance-band or bodyweight substitutions.',
            exercises=exercises,
            run_segments=run_segments,
            recovery_exercises=recovery_exercises,
            pace_guidance=pace_guidance,
            treadmill_guidance=treadmill_guidance,
            run_structure_summary=run_structure_summary,
        ))
    evidence = {
        'recovery_level': recovery.level,
        'recovery_score': recovery.score,
        'previous_week_miles': previous_week_miles,
        'four_week_average_miles': four_week_average_miles,
        'completed_hard_sessions_last_21_days': completed_hard_sessions_last_21_days,
        'average_recovery_score': average_recovery_score,
        'consecutive_build_weeks': consecutive_build_weeks,
        'pain_checkins_last_7_days': pain_checkins_last_7_days,
    }
    return WeeklyPlan(
        week_start_date=week_start_date,
        plan_name=f"Week of {week_start_date.strftime('%B %d, %Y')}",
        phase_name=phase_name,
        is_deload=is_deload,
        target_run_miles=target_miles,
        rationale=tuple(rationale),
        evidence=evidence,
        sessions=tuple(sessions),
    )


def reschedule_missed_session(*, sessions: Iterable[PlannedSession], missed_date: date,
                              current_date: date) -> tuple[PlannedSession, ...]:
    rows = list(sessions)
    missed = next((s for s in rows if s.session_date == missed_date and s.status in {'Planned','Approved'}), None)
    if missed is None:
        return tuple(rows)
    hard_types = {'Quality Run', 'Strength A', 'Strength B', 'Long Run'}
    occupied = {s.session_date for s in rows if s.status not in {'Skipped','Cancelled','Moved'}}
    candidates = [current_date + timedelta(days=i) for i in range(0, 7)]
    target = None
    for candidate in candidates:
        if candidate > missed_date + timedelta(days=6):
            break
        if candidate in occupied:
            continue
        previous_hard = any(s.session_date == candidate - timedelta(days=1) and s.workout_type in hard_types and s.status not in {'Skipped','Cancelled','Moved'} for s in rows)
        next_hard = any(s.session_date == candidate + timedelta(days=1) and s.workout_type in hard_types and s.status not in {'Skipped','Cancelled','Moved'} for s in rows)
        if missed.workout_type in hard_types and (previous_hard or next_hard):
            continue
        target = candidate
        break
    updated: list[PlannedSession] = []
    for s in rows:
        if s is missed:
            updated.append(replace(s, status='Moved'))
        else:
            updated.append(s)
    if target is not None:
        updated.append(replace(missed, session_date=target, sequence_number=max(s.sequence_number for s in rows)+1, status='Planned', moved_from_date=missed_date))
    return tuple(sorted(updated, key=lambda s: (s.session_date, s.sequence_number)))
