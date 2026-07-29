from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from services.app_helpers import PROFILE_ID, configure_page, get_profile, pace_per_mile, week_start
from services.database import fetch_rows

configure_page("Fitness Coach", "🏃")
profile = get_profile()

st.title("Bryan's Fitness Coach")
st.caption("Release 1: personal logging and history")

measurements = fetch_rows(
    "body_measurements",
    filters={"profile_id": PROFILE_ID},
    order_by="measured_on",
    descending=False,
)
runs = fetch_rows(
    "running_sessions",
    filters={"profile_id": PROFILE_ID},
    order_by="run_date",
    descending=True,
    limit=20,
)
workouts = fetch_rows(
    "workout_sessions",
    filters={"profile_id": PROFILE_ID},
    order_by="scheduled_date",
    descending=True,
    limit=20,
)

latest_weight = float(measurements[-1]["weight_lb"]) if measurements else float(profile["starting_weight"])
goal_weight = float(profile["goal_weight"])
starting_weight = float(profile["starting_weight"])
week = week_start(date.today())
weekly_runs = [r for r in runs if r.get("run_date") and r["run_date"] >= week.isoformat()]
weekly_workouts = [w for w in workouts if w.get("scheduled_date") and w["scheduled_date"] >= week.isoformat()]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Current weight", f"{latest_weight:.1f} lb", f"{latest_weight - starting_weight:+.1f} lb")
c2.metric("Goal remaining", f"{max(0, latest_weight - goal_weight):.1f} lb")
c3.metric("Miles this week", f"{sum(float(r['distance_miles']) for r in weekly_runs):.1f}")
c4.metric("Sessions this week", len(weekly_workouts))

st.subheader("Quick links")
q1, q2, q3, q4 = st.columns(4)
q1.page_link("pages/1_Today.py", label="Today's plan", icon="📅")
q2.page_link("pages/2_Log_Workout.py", label="Log strength", icon="🏋️")
q3.page_link("pages/3_Running.py", label="Log a run", icon="🏃")
q4.page_link("pages/5_Nutrition_Weight.py", label="Weight & nutrition", icon="🥗")

st.subheader("Recent runs")
if runs:
    run_df = pd.DataFrame([
        {
            "Date": r["run_date"],
            "Type": r["run_type"],
            "Miles": float(r["distance_miles"]),
            "Time": f"{int(r['duration_seconds']) // 60}:{int(r['duration_seconds']) % 60:02d}",
            "Pace": pace_per_mile(int(r["duration_seconds"]), float(r["distance_miles"])),
            "RPE": r.get("average_rpe"),
        }
        for r in runs[:5]
    ])
    st.dataframe(run_df, use_container_width=True, hide_index=True)
else:
    st.info("No runs logged yet.")

if measurements:
    st.subheader("Weight trend")
    weight_df = pd.DataFrame(measurements)
    weight_df["measured_on"] = pd.to_datetime(weight_df["measured_on"])
    weight_df["weight_lb"] = weight_df["weight_lb"].astype(float)
    st.line_chart(weight_df, x="measured_on", y="weight_lb")
