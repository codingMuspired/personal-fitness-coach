from __future__ import annotations

from datetime import date, timedelta
import pandas as pd
import streamlit as st

from services.app_helpers import PROFILE_ID
from services.run_prescription import format_pace, pace_range_text, treadmill_mph
from services.weekly_plan_editor import fetch_week_scope, replace_run_segments, replace_recovery_exercises, update_session, update_week_metadata
from services.weekly_planner import monday_of

st.set_page_config(page_title="Week Editor", page_icon="🗓️", layout="wide")
st.title("Week Editor")
st.caption("Review the entire week, move sessions to different dates, and edit detailed run prescriptions before training.")


def has_value(value):
    return value is not None and pd.notna(value)

def safe_int(value):
    return int(float(value)) if has_value(value) else None


week_start = monday_of(st.date_input("Week containing", value=date.today()))
plan = fetch_week_scope(PROFILE_ID, week_start.isoformat())
if not plan:
    st.info("Generate the week in Weekly Planner first.")
    st.stop()

with st.expander("Week settings", expanded=False):
    c1, c2, c3, c4 = st.columns(4)
    plan_name = c1.text_input("Plan name", value=plan.get("plan_name") or "")
    phase_options = ["Foundation", "Half Marathon Base", "Spartan Base", "Recovery"]
    current_phase = plan.get("phase_name") or "Foundation"
    phase = c2.selectbox("Phase", phase_options, index=phase_options.index(current_phase) if current_phase in phase_options else 0)
    target_miles = c3.number_input("Weekly run miles", 0.0, 100.0, float(plan.get("target_run_miles") or 0), 0.5)
    is_deload = c4.checkbox("Deload week", value=bool(plan.get("is_deload")))
    if st.button("Save week settings"):
        update_week_metadata(plan["weekly_plan_id"], plan_name=plan_name, phase_name=phase,
                             target_run_miles=target_miles, is_deload=is_deload)
        st.success("Week settings saved.")
        st.rerun()

st.subheader("Full-week scope")
scope_rows = []
for session in plan.get("sessions", []):
    segments = sorted(session.get("prescribed_run_segments") or [], key=lambda x: x["segment_order"])
    run_detail = "; ".join(
        f"{int(x.get('repetitions') or 1)}× {x['label']} {pace_range_text(x.get('pace_min_seconds_per_mile'), x.get('pace_max_seconds_per_mile'))}"
        for x in segments
    )
    recovery_items = sorted(session.get("prescribed_recovery_exercises") or [], key=lambda x: x["exercise_order"])
    recovery_detail = "; ".join(
        f"{x['exercise_name']} ({x.get('target_sets') or 1}×{x.get('target_repetitions') or (str(x.get('target_duration_seconds')) + ' sec' if x.get('target_duration_seconds') else 'by feel')})"
        for x in recovery_items
    )
    scope_rows.append({
        "Date": session["session_date"],
        "Day": date.fromisoformat(session["session_date"]).strftime("%A"),
        "Workout": session["title"],
        "Type": session["workout_type"],
        "Minutes": session["duration_minutes"],
        "Miles": session.get("target_distance_miles"),
        "Intensity": session["intensity"],
        "Status": session["status"],
        "Run details": run_detail,
        "Recovery details": recovery_detail,
    })
st.dataframe(pd.DataFrame(scope_rows), use_container_width=True, hide_index=True)

st.subheader("Edit sessions")
week_min = week_start - timedelta(days=3)
week_max = week_start + timedelta(days=10)

for session in plan.get("sessions", []):
    session_id = session["weekly_plan_session_id"]
    label = f"{session['session_date']} · {session['title']}"
    with st.expander(label, expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        new_date = c1.date_input("Session date", value=date.fromisoformat(session["session_date"]),
                                 min_value=week_min, max_value=week_max, key=f"date_{session_id}")
        workout_type = c2.text_input("Workout type", value=session["workout_type"], key=f"type_{session_id}")
        duration = c3.number_input("Minutes", min_value=0, max_value=300,
                                   value=int(session["duration_minutes"]), key=f"dur_{session_id}")
        intensity = c4.selectbox("Intensity", ["Very easy", "Reduced", "Normal", "Hard"],
                                 index=["Very easy", "Reduced", "Normal", "Hard"].index(session["intensity"]) if session["intensity"] in ["Very easy", "Reduced", "Normal", "Hard"] else 2,
                                 key=f"int_{session_id}")
        title = st.text_input("Title", value=session["title"], key=f"title_{session_id}")
        distance = st.number_input("Target miles", min_value=0.0, max_value=50.0,
                                   value=float(session.get("target_distance_miles") or 0), step=0.1, key=f"miles_{session_id}")
        instructions = st.text_area("Instructions", value=session["instructions"], key=f"instructions_{session_id}")
        home = st.text_area("Home alternative", value=session.get("home_alternative") or "", key=f"home_{session_id}")
        if st.button("Save session details", key=f"save_session_{session_id}"):
            update_session(session_id, {
                "session_date": new_date.isoformat(), "workout_type": workout_type, "title": title,
                "duration_minutes": duration, "target_distance_miles": distance or None,
                "intensity": intensity, "instructions": instructions, "home_alternative": home,
            })
            st.success("Session saved.")
            st.rerun()

        segments = sorted(session.get("prescribed_run_segments") or [], key=lambda x: x["segment_order"])
        if segments or "Run" in session["workout_type"]:
            st.markdown("#### Run prescription")
            initial_rows = []
            for x in segments:
                initial_rows.append({
                    "segment_type": x["segment_type"], "label": x["label"],
                    "repetitions": x.get("repetitions") or 1,
                    "target_distance_miles": x.get("target_distance_miles"),
                    "target_duration_seconds": x.get("target_duration_seconds"),
                    "recovery_seconds": x.get("recovery_seconds"),
                    "pace_min_seconds_per_mile": x.get("pace_min_seconds_per_mile"),
                    "pace_max_seconds_per_mile": x.get("pace_max_seconds_per_mile"),
                    "target_rpe": x.get("target_rpe"), "notes": x.get("notes"),
                })
            if not initial_rows:
                initial_rows = [{"segment_type":"Continuous", "label":"Easy running", "repetitions":1,
                                 "target_distance_miles":distance or 3.0, "target_duration_seconds":None,
                                 "recovery_seconds":None, "pace_min_seconds_per_mile":720,
                                 "pace_max_seconds_per_mile":780, "target_rpe":3.5, "notes":""}]
            edited = st.data_editor(
                pd.DataFrame(initial_rows), num_rows="dynamic", use_container_width=True,
                key=f"segments_{session_id}",
                column_config={
                    "segment_type": st.column_config.SelectboxColumn("Segment", options=["Warm-up","Continuous","Work","Recovery","Finish","Strides","Cool-down"]),
                    "label": "Description", "repetitions": st.column_config.NumberColumn("Reps", min_value=1, step=1),
                    "target_distance_miles": st.column_config.NumberColumn("Miles", min_value=0.0, step=0.1),
                    "target_duration_seconds": st.column_config.NumberColumn("Work sec", min_value=0, step=15),
                    "recovery_seconds": st.column_config.NumberColumn("Recovery sec", min_value=0, step=15),
                    "pace_min_seconds_per_mile": st.column_config.NumberColumn("Fast pace sec/mi", min_value=240, max_value=1200, step=5),
                    "pace_max_seconds_per_mile": st.column_config.NumberColumn("Slow pace sec/mi", min_value=240, max_value=1200, step=5),
                    "target_rpe": st.column_config.NumberColumn("RPE", min_value=1.0, max_value=10.0, step=0.5),
                },
            )
            preview = []
            for row in edited.to_dict("records"):
                fast = row.get("pace_min_seconds_per_mile")
                slow = row.get("pace_max_seconds_per_mile")
                representative = ((fast or slow) + (slow or fast)) / 2 if (fast or slow) else None
                preview.append({
                    "Segment": row.get("label"), "Reps": row.get("repetitions"),
                    "Pace": pace_range_text(fast, slow),
                    "Treadmill": f"{treadmill_mph(representative):.1f} mph" if representative else "By effort",
                    "Recovery": f"{safe_int(row.get('recovery_seconds'))} sec" if has_value(row.get("recovery_seconds")) else "—",
                })
            st.dataframe(preview, use_container_width=True, hide_index=True)
            if st.button("Save run prescription", key=f"save_segments_{session_id}"):
                replace_run_segments(session_id, edited.to_dict("records"))
                st.success("Run prescription saved.")
                st.rerun()

        recovery_items = sorted(session.get("prescribed_recovery_exercises") or [], key=lambda x: x["exercise_order"])
        if recovery_items or session["workout_type"] in {"Recovery", "Rest"}:
            st.markdown("#### Recovery and mobility prescription")
            recovery_rows = [{
                "exercise_name": x["exercise_name"],
                "category": x.get("category") or "Mobility",
                "target_sets": x.get("target_sets") or 1,
                "target_repetitions": x.get("target_repetitions"),
                "target_duration_seconds": x.get("target_duration_seconds"),
                "side_instruction": x.get("side_instruction"),
                "target_rpe": x.get("target_rpe"),
                "is_optional": bool(x.get("is_optional")),
                "notes": x.get("notes"),
            } for x in recovery_items]
            if not recovery_rows:
                recovery_rows = [{
                    "exercise_name": "Easy walk", "category": "Cardio", "target_sets": 1,
                    "target_repetitions": None, "target_duration_seconds": 900,
                    "side_instruction": None, "target_rpe": 2.0,
                    "is_optional": False, "notes": "Conversational effort.",
                }]
            edited_recovery = st.data_editor(
                pd.DataFrame(recovery_rows), num_rows="dynamic", use_container_width=True,
                key=f"recovery_{session_id}",
                column_config={
                    "exercise_name": "Exercise or stretch",
                    "category": st.column_config.SelectboxColumn("Category", options=["Cardio", "Mobility", "Stretch", "Activation", "Breathing", "Yoga"]),
                    "target_sets": st.column_config.NumberColumn("Sets", min_value=1, step=1),
                    "target_repetitions": st.column_config.NumberColumn("Reps", min_value=0, step=1),
                    "target_duration_seconds": st.column_config.NumberColumn("Seconds", min_value=0, step=5),
                    "side_instruction": "Side",
                    "target_rpe": st.column_config.NumberColumn("RPE", min_value=1.0, max_value=10.0, step=0.5),
                    "is_optional": "Optional",
                    "notes": "Instructions",
                },
            )
            if st.button("Save recovery prescription", key=f"save_recovery_{session_id}"):
                replace_recovery_exercises(session_id, edited_recovery.to_dict("records"))
                st.success("Recovery prescription saved.")
                st.rerun()

st.caption("Dates can be moved slightly outside the Monday–Sunday range to handle real scheduling conflicts. Keep hard sessions separated whenever possible.")
