from __future__ import annotations

from datetime import date
import pandas as pd
import streamlit as st

from services.app_helpers import PROFILE_ID
from services.run_prescription import pace_range_text, treadmill_mph
from services.weekly_plan_editor import fetch_week_scope
from services.weekly_plan_data import update_session_status
from services.weekly_planner import monday_of

st.set_page_config(page_title="Today's Plan", page_icon="✅", layout="wide")
st.title("Today's Plan")

week_start = monday_of(date.today())
plan = fetch_week_scope(PROFILE_ID, week_start.isoformat())
if not plan:
    st.info("No weekly plan exists for this week. Generate one in Weekly Planner.")
    st.stop()

sessions = [s for s in plan.get("sessions", []) if s["session_date"] == date.today().isoformat() and s["status"] not in {"Cancelled", "Moved"}]
if not sessions:
    st.info("No active session is scheduled for today. Use Week Editor to move or add detail to the week.")
    st.stop()

for session in sessions:
    st.header(session["title"])
    c1, c2, c3 = st.columns(3)
    c1.metric("Duration", f"{session['duration_minutes']} min")
    c2.metric("Intensity", session["intensity"])
    c3.metric("Distance", f"{float(session['target_distance_miles']):.1f} mi" if session.get("target_distance_miles") else "—")
    st.write(session["instructions"])
    if session.get("home_alternative"):
        st.caption(f"Home pivot: {session['home_alternative']}")

    run_segments = sorted(session.get("prescribed_run_segments") or [], key=lambda x: x["segment_order"])
    if run_segments:
        st.subheader("Run details")
        rows = []
        for x in run_segments:
            fast, slow = x.get("pace_min_seconds_per_mile"), x.get("pace_max_seconds_per_mile")
            representative = ((fast or slow) + (slow or fast)) / 2 if (fast or slow) else None
            work = f"{float(x['target_distance_miles']):.2f} mi" if x.get("target_distance_miles") else (f"{int(x['target_duration_seconds'])} sec" if x.get("target_duration_seconds") else "By feel")
            rows.append({
                "Segment": x["segment_type"], "Description": x["label"], "Reps": x.get("repetitions") or 1,
                "Work": work, "Pace": pace_range_text(fast, slow),
                "Treadmill": f"{treadmill_mph(representative):.1f} mph" if representative else "By effort",
                "Recovery": f"{int(x['recovery_seconds'])} sec" if x.get("recovery_seconds") else "—",
                "RPE": x.get("target_rpe"), "Notes": x.get("notes"),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    recovery_items = sorted(session.get("prescribed_recovery_exercises") or [], key=lambda x: x["exercise_order"])
    if recovery_items:
        st.subheader("Recovery and mobility details")
        st.dataframe(pd.DataFrame([{
            "Exercise": x["exercise_name"],
            "Category": x.get("category"),
            "Sets": x.get("target_sets"),
            "Reps": x.get("target_repetitions"),
            "Seconds": x.get("target_duration_seconds"),
            "Side": x.get("side_instruction") or "—",
            "RPE": x.get("target_rpe"),
            "Optional": "Yes" if x.get("is_optional") else "No",
            "Instructions": x.get("notes"),
        } for x in recovery_items]), use_container_width=True, hide_index=True)

    exercises = sorted(session.get("prescribed_exercises") or [], key=lambda x: x["exercise_order"])
    if exercises:
        st.subheader("Strength details")
        st.dataframe(pd.DataFrame([{
            "Exercise": x["exercise_name"], "Sets": x.get("target_sets"), "Reps": x.get("target_repetitions"),
            "Weight": x.get("target_weight_lb"), "Seconds": x.get("target_duration_seconds"),
            "RPE": x.get("target_rpe"), "RIR": x.get("reps_in_reserve"), "Home substitute": x.get("substitution_name"),
        } for x in exercises]), use_container_width=True, hide_index=True)

    b1, b2 = st.columns(2)
    if b1.button("Mark completed", key=f"complete_{session['weekly_plan_session_id']}"):
        update_session_status(session["weekly_plan_session_id"], "Completed")
        st.success("Session completed.")
        st.rerun()
    if b2.button("Skip session", key=f"skip_{session['weekly_plan_session_id']}"):
        update_session_status(session["weekly_plan_session_id"], "Skipped")
        st.warning("Session skipped. Use Week Editor to move another session if needed.")
        st.rerun()
