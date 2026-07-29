from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from services.app_helpers import PROFILE_ID, configure_page, pace_per_mile
from services.database import fetch_rows, insert_row

configure_page("Running", "🏃")
st.title("Running")

with st.form("run_form"):
    run_date = st.date_input("Run date", date.today())
    run_type = st.selectbox("Run type", ["Recovery", "Easy", "Long", "Steady", "Tempo", "Intervals", "Race/Test"])
    distance = st.number_input("Distance (miles)", 0.1, 100.0, 3.0, 0.1)
    c1, c2, c3 = st.columns(3)
    hours = c1.number_input("Hours", 0, 20, 0)
    minutes = c2.number_input("Minutes", 0, 59, 30)
    seconds = c3.number_input("Seconds", 0, 59, 0)
    rpe = st.slider("Average RPE", 1, 10, 4)
    surface = st.selectbox("Surface", ["Road", "Trail", "Treadmill", "Track", "Mixed"])
    avg_hr = st.number_input("Average heart rate, optional", 0, 240, 0)
    elevation = st.number_input("Elevation gain in feet, optional", 0, 50000, 0)
    notes = st.text_area("Notes")
    submitted = st.form_submit_button("Save run", type="primary")

if submitted:
    total_seconds = int(hours * 3600 + minutes * 60 + seconds)
    if total_seconds <= 0:
        st.error("Run duration must be greater than zero.")
    else:
        insert_row("running_sessions", {
            "profile_id": PROFILE_ID,
            "run_date": run_date.isoformat(),
            "run_type": run_type,
            "distance_miles": distance,
            "duration_seconds": total_seconds,
            "average_heart_rate": avg_hr or None,
            "elevation_feet": elevation or None,
            "average_rpe": rpe,
            "surface_type": surface,
            "notes": notes or None,
        })
        st.success(f"Run saved. Average pace: {pace_per_mile(total_seconds, distance)}")

st.subheader("Running history")
runs = fetch_rows("running_sessions", filters={"profile_id": PROFILE_ID}, order_by="run_date", descending=True)
if runs:
    df = pd.DataFrame([{
        "Date": r["run_date"], "Type": r["run_type"], "Miles": float(r["distance_miles"]),
        "Pace": pace_per_mile(int(r["duration_seconds"]), float(r["distance_miles"])),
        "RPE": r.get("average_rpe"), "Surface": r.get("surface_type")
    } for r in runs])
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("No runs logged yet.")
