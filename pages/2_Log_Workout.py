from __future__ import annotations

from datetime import date, datetime, timezone

import pandas as pd
import streamlit as st

from services.app_helpers import PROFILE_ID, configure_page
from services.database import fetch_rows, insert_row, insert_rows

configure_page("Log Strength Workout", "🏋️")
st.title("Log Strength Workout")

exercises = fetch_rows("exercises", filters={"is_active": True}, order_by="exercise_name")
if not exercises:
    st.error("No exercises exist. Run sql/02_seed_exercises.sql in Supabase.")
    st.stop()

exercise_lookup = {e["exercise_name"]: e for e in exercises}

with st.form("strength_session"):
    session_date = st.date_input("Workout date", date.today())
    workout_type = st.selectbox("Workout type", ["Strength A", "Strength B / Spartan", "Home Strength", "Other"])
    location = st.selectbox("Location", ["Gym", "Home", "Outdoor"])
    sleep_hours = st.number_input("Sleep hours", 0.0, 12.0, 7.0, 0.5)
    soreness = st.slider("Soreness before workout", 1, 10, 3)
    pain = st.checkbox("Pain reported")
    duration = st.number_input("Duration in minutes", 0, 240, 60, 5)
    overall_rpe = st.slider("Overall workout RPE", 1, 10, 7)
    notes = st.text_area("Session notes")

    st.markdown("### Sets")
    rows = st.data_editor(
        pd.DataFrame([
            {"Exercise": "", "Set": 1, "Weight lb": 0.0, "Reps": 0, "Seconds": 0, "RPE": 7.0, "Completed": True}
            for _ in range(8)
        ]),
        column_config={
            "Exercise": st.column_config.SelectboxColumn("Exercise", options=[""] + list(exercise_lookup)),
            "Set": st.column_config.NumberColumn(min_value=1, max_value=20, step=1),
            "Weight lb": st.column_config.NumberColumn(min_value=0.0, step=2.5),
            "Reps": st.column_config.NumberColumn(min_value=0, max_value=100, step=1),
            "Seconds": st.column_config.NumberColumn(min_value=0, max_value=3600, step=5),
            "RPE": st.column_config.NumberColumn(min_value=1.0, max_value=10.0, step=0.5),
        },
        hide_index=True,
        use_container_width=True,
        num_rows="dynamic",
    )
    submitted = st.form_submit_button("Save strength workout", type="primary")

if submitted:
    valid = rows[rows["Exercise"].fillna("").str.strip() != ""]
    if valid.empty:
        st.error("Add at least one exercise row.")
    else:
        session = insert_row("workout_sessions", {
            "profile_id": PROFILE_ID,
            "scheduled_date": session_date.isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "workout_type": workout_type,
            "location_type": location,
            "duration_minutes": duration,
            "overall_rpe": overall_rpe,
            "soreness_before": soreness,
            "sleep_hours": sleep_hours,
            "pain_reported": pain,
            "notes": notes or None,
        })
        set_rows = []
        for _, row in valid.iterrows():
            set_rows.append({
                "workout_session_id": session["workout_session_id"],
                "exercise_id": exercise_lookup[row["Exercise"]]["exercise_id"],
                "set_number": int(row["Set"]),
                "weight_lb": float(row["Weight lb"] or 0),
                "repetitions": int(row["Reps"] or 0),
                "duration_seconds": int(row["Seconds"] or 0),
                "rpe": float(row["RPE"] or 0),
                "completed": bool(row["Completed"]),
            })
        insert_rows("exercise_sets", set_rows)
        st.success("Strength workout saved.")
