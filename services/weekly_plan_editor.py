from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from services.database import get_supabase_client

ALLOWED_SESSION_STATUSES = {"Planned", "Approved", "Completed", "Skipped", "Moved", "Cancelled"}


def update_week_metadata(weekly_plan_id: int, *, plan_name: str, phase_name: str,
                         target_run_miles: float, is_deload: bool) -> None:
    client = get_supabase_client()
    client.table("weekly_plans").update({
        "plan_name": plan_name.strip(),
        "phase_name": phase_name,
        "target_run_miles": target_run_miles,
        "is_deload": is_deload,
    }).eq("weekly_plan_id", weekly_plan_id).execute()


def update_session(session_id: int, values: dict[str, Any]) -> None:
    allowed = {
        "session_date", "sequence_number", "workout_type", "title",
        "duration_minutes", "target_distance_miles", "intensity",
        "instructions", "home_alternative", "status",
    }
    payload = {key: value for key, value in values.items() if key in allowed}
    if payload.get("status") not in ALLOWED_SESSION_STATUSES:
        payload.pop("status", None)
    payload["updated_at"] = datetime.now(timezone.utc).isoformat()
    get_supabase_client().table("weekly_plan_sessions").update(payload).eq(
        "weekly_plan_session_id", session_id
    ).execute()


def replace_run_segments(session_id: int, rows: list[dict[str, Any]]) -> None:
    client = get_supabase_client()
    client.table("prescribed_run_segments").delete().eq(
        "weekly_plan_session_id", session_id
    ).execute()
    clean_rows = []
    for position, row in enumerate(rows, start=1):
        label = str(row.get("label") or "").strip()
        if not label:
            continue
        clean_rows.append({
            "weekly_plan_session_id": session_id,
            "segment_order": position,
            "segment_type": str(row.get("segment_type") or "Work"),
            "label": label,
            "repetitions": max(1, int(row.get("repetitions") or 1)),
            "target_distance_miles": row.get("target_distance_miles") or None,
            "target_duration_seconds": row.get("target_duration_seconds") or None,
            "recovery_seconds": row.get("recovery_seconds") or None,
            "pace_min_seconds_per_mile": row.get("pace_min_seconds_per_mile") or None,
            "pace_max_seconds_per_mile": row.get("pace_max_seconds_per_mile") or None,
            "target_rpe": row.get("target_rpe") or None,
            "notes": row.get("notes") or None,
        })
    if clean_rows:
        client.table("prescribed_run_segments").insert(clean_rows).execute()


def fetch_week_scope(profile_id: int, week_start_date: str) -> dict[str, Any] | None:
    client = get_supabase_client()
    plans = client.table("weekly_plans").select("*").eq(
        "profile_id", profile_id
    ).eq("week_start_date", week_start_date).limit(1).execute().data
    if not plans:
        return None
    plan = plans[0]
    sessions = client.table("weekly_plan_sessions").select(
        "*, prescribed_exercises(*), prescribed_run_segments(*), prescribed_recovery_exercises(*)"
    ).eq("weekly_plan_id", plan["weekly_plan_id"]).order("session_date").order("sequence_number").execute().data
    plan["sessions"] = sessions
    return plan


def _clean_number(value: Any, *, integer: bool = False) -> Any:
    try:
        import pandas as pd
        if value is None or not pd.notna(value):
            return None
    except ImportError:
        if value is None:
            return None
    return int(float(value)) if integer else float(value)


def replace_recovery_exercises(session_id: int, rows: list[dict[str, Any]]) -> None:
    client = get_supabase_client()
    client.table("prescribed_recovery_exercises").delete().eq(
        "weekly_plan_session_id", session_id
    ).execute()
    clean_rows = []
    for position, row in enumerate(rows, start=1):
        name = str(row.get("exercise_name") or "").strip()
        if not name:
            continue
        clean_rows.append({
            "weekly_plan_session_id": session_id,
            "exercise_order": position,
            "exercise_name": name,
            "category": str(row.get("category") or "Mobility"),
            "target_sets": max(1, _clean_number(row.get("target_sets"), integer=True) or 1),
            "target_repetitions": _clean_number(row.get("target_repetitions"), integer=True),
            "target_duration_seconds": _clean_number(row.get("target_duration_seconds"), integer=True),
            "side_instruction": str(row.get("side_instruction") or "").strip() or None,
            "target_rpe": _clean_number(row.get("target_rpe")),
            "notes": str(row.get("notes") or "").strip() or None,
            "is_optional": bool(row.get("is_optional", False)),
        })
    if clean_rows:
        client.table("prescribed_recovery_exercises").insert(clean_rows).execute()
