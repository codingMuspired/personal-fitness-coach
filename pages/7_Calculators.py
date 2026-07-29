import streamlit as st

from services.app_helpers import configure_page
from services.running_calculator import format_duration, format_pace, goal_pace, predict_time, treadmill_mph
from services.strength_calculator import estimate_one_rep_max

configure_page("Calculators", "🧮")
st.title("Calculators")

run_tab, lift_tab = st.tabs(["Run pace", "Strength"])
with run_tab:
    distance = st.number_input("Distance in miles", 0.1, 100.0, 13.1094, 0.1)
    c1, c2, c3 = st.columns(3)
    h = c1.number_input("Hours", 0, 24, 2)
    m = c2.number_input("Minutes", 0, 59, 0)
    s = c3.number_input("Seconds", 0, 59, 0)
    total = int(h * 3600 + m * 60 + s)
    if total > 0:
        pace = goal_pace(total, distance)
        a, b = st.columns(2)
        a.metric("Average pace", format_pace(pace))
        b.metric("Treadmill speed", f"{treadmill_mph(pace):.1f} mph")
    st.subheader("Race prediction")
    source_distance = st.number_input("Completed distance", 0.1, 50.0, 3.106856, 0.1)
    source_seconds = st.number_input("Completed time in seconds", 1, 100000, 2088)
    target_distance = st.number_input("Prediction distance", 0.1, 100.0, 13.1094, 0.1)
    st.metric("Predicted result", format_duration(predict_time(source_distance, source_seconds, target_distance)))

with lift_tab:
    weight = st.number_input("Weight lifted", 0.0, 2000.0, 100.0, 2.5)
    reps = st.number_input("Repetitions", 1, 30, 8)
    estimate = estimate_one_rep_max(weight, reps)
    st.metric("Estimated one-repetition maximum", f"{estimate:.1f} lb" if estimate else "Use 1–15 loaded reps")
    st.caption("This is an estimate for programming, not a reason to attempt a maximal lift.")
