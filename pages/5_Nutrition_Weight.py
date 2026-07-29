from datetime import date

import pandas as pd
import streamlit as st

from services.app_helpers import PROFILE_ID, configure_page
from services.database import fetch_rows, upsert_row
from services.progress_calculator import average_nutrition, calculate_weight_trend

configure_page("Nutrition & Weight", "🥗")
st.title("Nutrition & Weight")

tab1, tab2, tab3 = st.tabs(["Weight", "Daily nutrition", "Trend review"])

with tab1:
    with st.form("weight_form"):
        measured_on = st.date_input("Measurement date", date.today())
        weight = st.number_input("Weight (lb)", 100.0, 400.0, 225.0, 0.2)
        waist = st.number_input("Waist inches, optional", 0.0, 100.0, 0.0, 0.25)
        notes = st.text_area("Weight notes")
        save = st.form_submit_button("Save weight", type="primary")
    if save:
        upsert_row("body_measurements", {"profile_id": PROFILE_ID, "measured_on": measured_on.isoformat(),
            "weight_lb": weight, "waist_inches": waist or None, "notes": notes or None},
            on_conflict="profile_id,measured_on")
        st.success("Weight saved.")
    measurements = fetch_rows("body_measurements", filters={"profile_id": PROFILE_ID}, order_by="measured_on")
    if measurements:
        df = pd.DataFrame(measurements)
        df["measured_on"] = pd.to_datetime(df["measured_on"])
        df["weight_lb"] = df["weight_lb"].astype(float)
        st.line_chart(df, x="measured_on", y="weight_lb")
        st.dataframe(df[["measured_on", "weight_lb", "waist_inches", "notes"]], use_container_width=True, hide_index=True)

with tab2:
    with st.form("nutrition_form"):
        log_date = st.date_input("Log date", date.today(), key="nutrition_date")
        calories = st.number_input("Calories", 0, 10000, 2475, 25)
        protein = st.number_input("Protein grams", 0, 500, 180, 5)
        carbs = st.number_input("Carbohydrate grams", 0, 1000, 250, 5)
        fat = st.number_input("Fat grams", 0, 500, 75, 5)
        water = st.number_input("Water ounces", 0, 500, 80, 5)
        notes = st.text_area("Nutrition notes")
        save_nutrition = st.form_submit_button("Save nutrition", type="primary")
    if save_nutrition:
        upsert_row("daily_nutrition", {"profile_id": PROFILE_ID, "log_date": log_date.isoformat(),
            "calories": calories, "protein_grams": protein, "carbohydrate_grams": carbs,
            "fat_grams": fat, "water_ounces": water, "notes": notes or None}, on_conflict="profile_id,log_date")
        st.success("Nutrition saved.")
    logs = fetch_rows("daily_nutrition", filters={"profile_id": PROFILE_ID}, order_by="log_date", descending=True, limit=30)
    if logs:
        st.dataframe(pd.DataFrame(logs), use_container_width=True, hide_index=True)

with tab3:
    measurements = fetch_rows("body_measurements", filters={"profile_id": PROFILE_ID}, order_by="measured_on", descending=True, limit=30)
    logs = fetch_rows("daily_nutrition", filters={"profile_id": PROFILE_ID}, order_by="log_date", descending=True, limit=21)
    trend = calculate_weight_trend(measurements)
    c1, c2, c3 = st.columns(3)
    c1.metric("Weekly weight change", f"{trend.weekly_change:+.2f} lb" if trend.weekly_change is not None else "Need more data")
    c2.metric("12-week projection", f"{trend.projected_12_week_change:+.1f} lb" if trend.projected_12_week_change is not None else "Need more data")
    avg_calories = average_nutrition(logs, "calories")
    c3.metric("Logged calorie average", f"{avg_calories:.0f}" if avg_calories is not None else "Need logs")
    st.info(trend.recommendation)
    if logs:
        protein = average_nutrition(logs, "protein_grams")
        st.write(f"Average logged protein: **{protein:.0f} g/day**" if protein is not None else "No protein entries available.")
        st.caption("Only adjust calories after a consistent multi-week trend. One weigh-in can move because of hydration, sodium, carbohydrate intake, and digestion.")
