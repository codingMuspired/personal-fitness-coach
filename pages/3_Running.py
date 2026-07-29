from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from services.app_helpers import PROFILE_ID, configure_page, pace_per_mile
from services.database import fetch_rows, insert_row
from services.progress_calculator import current_week_mileage, mileage_guidance, previous_week_mileage
from services.running_calculator import (
    HALF_MARATHON_MILES, KM_5_MILES, MARATHON_MILES, adjusted_pace_range,
    format_duration, format_pace, goal_pace, predict_time, treadmill_mph,
    training_paces_from_5k,
)

configure_page("Running", "🏃")
st.title("Running")

log_tab, paces_tab, goals_tab = st.tabs(["Log run", "Training paces", "Race calculator"])

with log_tab:
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
                "profile_id": PROFILE_ID, "run_date": run_date.isoformat(), "run_type": run_type,
                "distance_miles": distance, "duration_seconds": total_seconds,
                "average_heart_rate": avg_hr or None, "elevation_feet": elevation or None,
                "average_rpe": rpe, "surface_type": surface, "notes": notes or None,
            })
            st.success(f"Run saved. Average pace: {pace_per_mile(total_seconds, distance)}")

    runs = fetch_rows("running_sessions", filters={"profile_id": PROFILE_ID}, order_by="run_date", descending=True, limit=250)
    current = current_week_mileage(runs)
    previous = previous_week_mileage(runs)
    a, b = st.columns(2)
    a.metric("Miles this week", f"{current:.1f}")
    b.metric("Previous week", f"{previous:.1f}")
    st.caption(mileage_guidance(current, previous))
    if runs:
        df = pd.DataFrame([{
            "Date": r["run_date"], "Type": r["run_type"], "Miles": float(r["distance_miles"]),
            "Pace": pace_per_mile(int(r["duration_seconds"]), float(r["distance_miles"])),
            "RPE": r.get("average_rpe"), "Surface": r.get("surface_type")
        } for r in runs])
        st.dataframe(df, use_container_width=True, hide_index=True)

with paces_tab:
    benchmarks = fetch_rows("running_benchmarks", filters={"profile_id": PROFILE_ID}, order_by="benchmark_date", descending=True, limit=20)
    latest_5k = next((b for b in benchmarks if str(b.get("distance_name", "")).upper() == "5K"), None)
    default_seconds = int(latest_5k["duration_seconds"]) if latest_5k else 2088
    c1, c2, c3 = st.columns(3)
    mins = c1.number_input("Recent 5K minutes", 10, 90, default_seconds // 60)
    secs = c2.number_input("Recent 5K seconds", 0, 59, default_seconds % 60)
    temperature = c3.number_input("Expected temperature °F", 30.0, 120.0, 65.0, 1.0)
    sleep = st.slider("Expected sleep", 0.0, 12.0, 7.0, 0.5)
    soreness = st.slider("Soreness", 1, 10, 3, key="pace_soreness")
    stress = st.slider("Stress", 1, 10, 5, key="pace_stress")
    pace_rows = []
    for name, base in training_paces_from_5k(int(mins * 60 + secs)).items():
        adjusted = adjusted_pace_range(base, sleep_hours=sleep, soreness=soreness, stress=stress, temperature_f=temperature)
        midpoint = (adjusted.low_seconds + adjusted.high_seconds) / 2
        pace_rows.append({"Run type": name, "Recommended range": adjusted.display, "Treadmill midpoint": f"{treadmill_mph(midpoint):.1f} mph"})
    st.dataframe(pd.DataFrame(pace_rows), use_container_width=True, hide_index=True)
    st.info("Use RPE and the talk test first. Heat, poor sleep, soreness, trails, and elevation can make the correct pace slower.")

with goals_tab:
    distance_name = st.selectbox("Goal distance", ["5K", "10K", "Half marathon", "Marathon"])
    distances = {"5K": KM_5_MILES, "10K": 6.21371, "Half marathon": HALF_MARATHON_MILES, "Marathon": MARATHON_MILES}
    c1, c2, c3 = st.columns(3)
    goal_h = c1.number_input("Goal hours", 0, 12, 2 if distance_name == "Half marathon" else 0)
    goal_m = c2.number_input("Goal minutes", 0, 59, 0)
    goal_s = c3.number_input("Goal seconds", 0, 59, 0)
    total = int(goal_h * 3600 + goal_m * 60 + goal_s)
    if total > 0:
        pace = goal_pace(total, distances[distance_name])
        st.metric("Required average pace", format_pace(pace))
        st.caption(f"Treadmill equivalent: approximately {treadmill_mph(pace):.1f} mph")
    source_seconds = st.number_input("Prediction source 5K time in seconds", 600, 7200, default_seconds)
    predictions = [
        {"Distance": "10K", "Predicted time": format_duration(predict_time(KM_5_MILES, source_seconds, 6.21371))},
        {"Distance": "Half marathon", "Predicted time": format_duration(predict_time(KM_5_MILES, source_seconds, HALF_MARATHON_MILES))},
        {"Distance": "Marathon", "Predicted time": format_duration(predict_time(KM_5_MILES, source_seconds, MARATHON_MILES))},
    ]
    st.dataframe(pd.DataFrame(predictions), use_container_width=True, hide_index=True)
    st.caption("Race predictions are estimates, not promises. Longer-race results depend heavily on mileage, fueling, terrain, weather, and durability.")
