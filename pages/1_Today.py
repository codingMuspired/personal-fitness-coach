from datetime import date

import streamlit as st

from services.app_helpers import PROFILE_ID, configure_page
from services.database import fetch_rows

configure_page("Today's Plan", "📅")
st.title("Today's Plan")

weekday = date.today().strftime("%A")
defaults = {
    "Sunday": ("Long easy run", "Stay conversational. Record distance, time, RPE, and fueling notes."),
    "Monday": ("Active recovery + mobility", "Easy walk plus the 20-minute hips, ankles, and shoulders routine."),
    "Tuesday": ("Strength A", "Squat, hinge, push, row, split squat, Pallof press, and calves."),
    "Wednesday": ("Quality run", "Use the current week from your 12-week running progression."),
    "Thursday": ("Rest or gentle mobility", "Keep this easy unless recovery is excellent."),
    "Friday": ("Strength B + Spartan", "Pulling, hangs, carries, step-ups, crawling, and rope skill."),
    "Saturday": ("Easy run + strides", "Easy aerobic work. Remove this first during a busy week."),
}
name, instructions = defaults[weekday]

st.subheader(f"{weekday}: {name}")
st.write(instructions)

recent = fetch_rows(
    "workout_sessions",
    filters={"profile_id": PROFILE_ID},
    order_by="scheduled_date",
    descending=True,
    limit=5,
)

with st.expander("Recovery check", expanded=True):
    sleep = st.number_input("Sleep last night", 0.0, 12.0, 7.0, 0.5)
    soreness = st.slider("Soreness", 1, 10, 3)
    stress = st.slider("Stress", 1, 10, 5)
    pain = st.checkbox("Sharp pain or altered movement")

    if pain:
        st.error("Red day: do not progress training. Rest or use pain-free gentle movement.")
    elif sleep < 6 or soreness >= 7 or stress >= 8:
        st.warning("Yellow day: reduce one strength set or replace hard running with easy running/walking.")
    else:
        st.success("Green day: the planned session is reasonable if you otherwise feel normal.")

st.subheader("Recent sessions")
if recent:
    st.dataframe(recent, use_container_width=True, hide_index=True)
else:
    st.info("No completed sessions yet.")
