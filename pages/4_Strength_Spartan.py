import pandas as pd
import streamlit as st

from services.app_helpers import PROFILE_ID, configure_page
from services.database import get_supabase_client

configure_page("Strength & Spartan History", "💪")
st.title("Strength & Spartan History")

response = (
    get_supabase_client().table("exercise_sets")
    .select("weight_lb,repetitions,duration_seconds,rpe,completed,workout_sessions!inner(profile_id,scheduled_date,workout_type),exercises!inner(exercise_name,category)")
    .eq("workout_sessions.profile_id", PROFILE_ID)
    .order("exercise_set_id", desc=True)
    .limit(250)
    .execute()
)
rows = response.data or []

if not rows:
    st.info("Log a strength workout first.")
else:
    flat = []
    for row in rows:
        flat.append({
            "Date": row["workout_sessions"]["scheduled_date"],
            "Workout": row["workout_sessions"]["workout_type"],
            "Exercise": row["exercises"]["exercise_name"],
            "Category": row["exercises"]["category"],
            "Weight lb": float(row.get("weight_lb") or 0),
            "Reps": row.get("repetitions") or 0,
            "Seconds": row.get("duration_seconds") or 0,
            "RPE": row.get("rpe"),
        })
    df = pd.DataFrame(flat)
    exercise = st.selectbox("Filter exercise", ["All"] + sorted(df["Exercise"].unique().tolist()))
    shown = df if exercise == "All" else df[df["Exercise"] == exercise]
    st.dataframe(shown, use_container_width=True, hide_index=True)

    st.subheader("Current Spartan focus")
    st.write("Track assisted pull-ups, dead hangs, farmer carries, towel-grip pulldowns, step-ups, bear crawls, and burpees. Release 2 will calculate the next recommended load or duration.")
