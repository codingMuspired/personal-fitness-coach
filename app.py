from __future__ import annotations

from datetime import date

import streamlit as st

from services.database import fetch_records, insert_record


st.set_page_config(
    page_title="Bryan's Fitness Coach",
    page_icon="🏃",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.title("Bryan's Fitness Coach")
st.caption("Running, strength, Spartan, mobility, nutrition, and progress tracking")

profiles = fetch_records("profiles")

if not profiles:
    st.error("No profile was found in the database.")
    st.stop()

profile = profiles[0]

column1, column2, column3 = st.columns(3)

with column1:
    st.metric("Starting weight", f"{profile['starting_weight']} lb")

with column2:
    st.metric("Goal weight", f"{profile['goal_weight']} lb")

with column3:
    pounds_remaining = float(profile["starting_weight"]) - float(profile["goal_weight"])
    st.metric("Initial goal", f"{pounds_remaining:.0f} lb")

st.subheader("Log today's weight")

with st.form("weight_form"):
    measured_on = st.date_input("Date", value=date.today())
    weight_lb = st.number_input(
        "Weight in pounds",
        min_value=100.0,
        max_value=400.0,
        value=225.0,
        step=0.2,
    )
    notes = st.text_area("Notes")

    submitted = st.form_submit_button("Save weight")

if submitted:
    try:
        insert_record(
            "body_measurements",
            {
                "profile_id": profile["profile_id"],
                "measured_on": measured_on.isoformat(),
                "weight_lb": weight_lb,
                "notes": notes or None,
            },
        )
        st.success("Weight saved.")
        st.rerun()
    except Exception as exc:
        st.error(f"Unable to save weight: {exc}")

st.subheader("Weight history")

measurements = fetch_records(
    "body_measurements",
    order_by="measured_on",
    descending=False,
)

if measurements:
    st.dataframe(
        measurements,
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No measurements have been recorded yet.")