import pandas as pd
import streamlit as st

from services.app_helpers import PROFILE_ID, configure_page, pace_per_mile
from services.database import fetch_rows

configure_page("History", "📊")
st.title("History")

runs = fetch_rows("running_sessions", filters={"profile_id": PROFILE_ID}, order_by="run_date", descending=True)
workouts = fetch_rows("workout_sessions", filters={"profile_id": PROFILE_ID}, order_by="scheduled_date", descending=True)
weights = fetch_rows("body_measurements", filters={"profile_id": PROFILE_ID}, order_by="measured_on", descending=True)
nutrition = fetch_rows("daily_nutrition", filters={"profile_id": PROFILE_ID}, order_by="log_date", descending=True)

for label, rows in [("Runs", runs), ("Strength sessions", workouts), ("Weight", weights), ("Nutrition", nutrition)]:
    with st.expander(label, expanded=(label == "Runs")):
        if not rows:
            st.info(f"No {label.lower()} records yet.")
        elif label == "Runs":
            df = pd.DataFrame(rows)
            df["pace"] = df.apply(lambda r: pace_per_mile(int(r["duration_seconds"]), float(r["distance_miles"])), axis=1)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
