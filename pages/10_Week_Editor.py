from __future__ import annotations

from datetime import date, timedelta
import pandas as pd
import streamlit as st

from services.app_helpers import PROFILE_ID
from services.run_prescription import format_pace, pace_range_text, treadmill_mph
from services.weekly_plan_editor import fetch_week_scope, replace_run_segments, update_session, update_week_metadata
from services.weekly_planner import monday_of

st.set_page_config(page_title="Week Editor", page_icon="🗓️", layout="wide")
st.title("Week Editor")
st.caption("Review the entire week, move sessions to different dates, and edit detailed run prescriptions before training.")

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
                    "Recovery": f"{int(row['recovery_seconds'])} sec" if pd.notna(row.get("recovery_seconds")) else "—",
                })
            st.dataframe(preview, use_container_width=True, hide_index=True)
            if st.button("Save run prescription", key=f"save_segments_{session_id}"):
                replace_run_segments(session_id, edited.to_dict("records"))
                st.success("Run prescription saved.")
                st.rerun()

st.caption("Dates can be moved slightly outside the Monday–Sunday range to handle real scheduling conflicts. Keep hard sessions separated whenever possible.")
