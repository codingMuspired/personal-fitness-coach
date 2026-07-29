from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from services.database import get_supabase_client
from services.weekly_planner import WeeklyPlan


def save_weekly_plan(profile_id: int, plan: WeeklyPlan) -> dict[str, Any]:
    client = get_supabase_client()
    payload = {
        'profile_id': profile_id,
        'week_start_date': plan.week_start_date.isoformat(),
        'plan_name': plan.plan_name,
        'phase_name': plan.phase_name,
        'is_deload': plan.is_deload,
        'target_run_miles': plan.target_run_miles,
        'status': 'Draft',
        'rationale': list(plan.rationale),
        'evidence': plan.evidence,
    }
    response = client.table('weekly_plans').upsert(
        payload, on_conflict='profile_id,week_start_date'
    ).execute()
    weekly_plan = response.data[0]
    plan_id = weekly_plan['weekly_plan_id']
    client.table('weekly_plan_sessions').delete().eq('weekly_plan_id', plan_id).execute()
    for session in plan.sessions:
        session_payload = {
            'weekly_plan_id': plan_id,
            'profile_id': profile_id,
            'session_date': session.session_date.isoformat(),
            'sequence_number': session.sequence_number,
            'workout_type': session.workout_type,
            'title': session.title,
            'duration_minutes': session.duration_minutes,
            'target_distance_miles': session.target_distance_miles,
            'intensity': session.intensity,
            'instructions': session.instructions,
            'home_alternative': session.home_alternative,
            'pace_guidance': session.pace_guidance,
            'treadmill_guidance': session.treadmill_guidance,
            'run_structure_summary': session.run_structure_summary,
            'status': session.status,
            'moved_from_date': session.moved_from_date.isoformat() if session.moved_from_date else None,
        }
        session_response = client.table('weekly_plan_sessions').insert(session_payload).execute()
        session_id = session_response.data[0]['weekly_plan_session_id']
        if session.run_segments:
            run_rows = [{
                'weekly_plan_session_id': session_id,
                'segment_order': segment.order,
                'segment_type': segment.segment_type,
                'label': segment.label,
                'repetitions': segment.repetitions,
                'target_distance_miles': segment.distance_miles,
                'target_duration_seconds': segment.duration_seconds,
                'recovery_seconds': segment.recovery_seconds,
                'pace_min_seconds_per_mile': segment.pace_min_seconds_per_mile,
                'pace_max_seconds_per_mile': segment.pace_max_seconds_per_mile,
                'target_rpe': segment.target_rpe,
                'notes': segment.notes,
            } for segment in session.run_segments]
            client.table('prescribed_run_segments').insert(run_rows).execute()
        if session.exercises:
            exercise_rows = [{
                'weekly_plan_session_id': session_id,
                'exercise_name': exercise.exercise_name,
                'exercise_order': exercise.order,
                'target_sets': exercise.sets,
                'target_repetitions': exercise.reps,
                'target_weight_lb': exercise.weight_lb,
                'target_duration_seconds': exercise.duration_seconds,
                'target_distance_meters': exercise.distance_meters,
                'target_rpe': exercise.target_rpe,
                'reps_in_reserve': exercise.reps_in_reserve,
                'substitution_name': exercise.substitution_name,
                'notes': exercise.notes,
            } for exercise in session.exercises]
            client.table('prescribed_exercises').insert(exercise_rows).execute()
    return weekly_plan


def approve_weekly_plan(weekly_plan_id: int) -> None:
    client = get_supabase_client()
    now = datetime.now(timezone.utc).isoformat()
    client.table('weekly_plans').update({'status':'Approved','approved_at':now}).eq('weekly_plan_id', weekly_plan_id).execute()
    client.table('weekly_plan_sessions').update({'status':'Approved','updated_at':now}).eq('weekly_plan_id', weekly_plan_id).eq('status','Planned').execute()


def fetch_weekly_plan(profile_id: int, week_start_date: str) -> dict[str, Any] | None:
    client = get_supabase_client()
    response = client.table('weekly_plans').select('*').eq('profile_id', profile_id).eq('week_start_date', week_start_date).limit(1).execute()
    if not response.data:
        return None
    plan = response.data[0]
    sessions = client.table('weekly_plan_sessions').select('*, prescribed_exercises(*), prescribed_run_segments(*)').eq('weekly_plan_id', plan['weekly_plan_id']).order('session_date').order('sequence_number').execute()
    plan['sessions'] = sessions.data
    return plan


def update_session_status(session_id: int, status: str) -> None:
    client = get_supabase_client()
    client.table('weekly_plan_sessions').update({'status':status,'updated_at':datetime.now(timezone.utc).isoformat()}).eq('weekly_plan_session_id', session_id).execute()
