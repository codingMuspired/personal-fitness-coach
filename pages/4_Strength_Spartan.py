from __future__ import annotations

from collections import defaultdict

import pandas as pd
import streamlit as st

from services.app_helpers import PROFILE_ID, configure_page
from services.database import get_supabase_client
from services.strength_calculator import recommend_next_session, recommend_timed_progression

configure_page("Strength & Spartan", "💪")
st.title("Strength & Spartan")

response = (
    get_supabase_client().table("exercise_sets")
    .select("exercise_set_id,weight_lb,repetitions,duration_seconds,rpe,completed,workout_sessions!inner(profile_id,scheduled_date,workout_type,pain_reported),exercises!inner(exercise_id,exercise_name,category)")
    .eq("workout_sessions.profile_id", PROFILE_ID)
    .order("exercise_set_id", desc=True)
    .limit(500)
    .execute()
)
rows = response.data or []

history_tab, recommendation_tab, spartan_tab = st.tabs(["History", "Next lift", "Spartan progression"])

flat = [{
    "Set ID": r["exercise_set_id"], "Date": r["workout_sessions"]["scheduled_date"],
    "Workout": r["workout_sessions"]["workout_type"], "Exercise": r["exercises"]["exercise_name"],
    "Category": r["exercises"]["category"], "Weight lb": float(r.get("weight_lb") or 0),
    "Reps": int(r.get("repetitions") or 0), "Seconds": int(r.get("duration_seconds") or 0),
    "RPE": float(r.get("rpe") or 0), "Completed": bool(r.get("completed")),
    "Pain": bool(r["workout_sessions"].get("pain_reported")),
} for r in rows]
df = pd.DataFrame(flat)

with history_tab:
    if df.empty:
        st.info("Log a strength workout first.")
    else:
        exercise = st.selectbox("Filter exercise", ["All"] + sorted(df["Exercise"].unique().tolist()))
        shown = df if exercise == "All" else df[df["Exercise"] == exercise]
        st.dataframe(shown, use_container_width=True, hide_index=True)

with recommendation_tab:
    if df.empty:
        st.info("At least one logged strength session is needed.")
    else:
        weighted = sorted(df.loc[(df["Weight lb"] > 0) & (df["Reps"] > 0), "Exercise"].unique().tolist())
        if not weighted:
            st.info("No weighted repetition sets are available yet.")
        else:
            selected = st.selectbox("Exercise", weighted, key="recommend_exercise")
            exercise_rows = df[df["Exercise"] == selected].copy()
            latest_date = exercise_rows["Date"].max()
            latest = exercise_rows[exercise_rows["Date"] == latest_date]
            current_weight = float(latest["Weight lb"].max())
            working = latest[latest["Weight lb"] == current_weight]
            completed_sets = int(working["Completed"].sum())
            planned_sets = len(working)
            minimum_reps = int(working.loc[working["Completed"], "Reps"].min()) if completed_sets else 0
            average_rpe = float(working["RPE"].mean())
            default_target = max(1, int(round(working["Reps"].median())))
            target_reps = st.number_input("Target repetitions next session", 1, 30, default_target)
            recommendation = recommend_next_session(
                current_weight=current_weight, completed_sets=completed_sets, planned_sets=planned_sets,
                target_reps=target_reps, minimum_reps_completed=minimum_reps, average_rpe=average_rpe,
                exercise_category=str(working.iloc[0]["Category"]), pain_reported=bool(working["Pain"].any()),
            )
            a, b, c = st.columns(3)
            a.metric("Recommended load", f"{recommendation.next_weight:g} lb")
            b.metric("Sets × reps", f"{recommendation.next_sets} × {recommendation.target_reps}")
            c.metric("Estimated 1RM", f"{recommendation.estimated_one_rep_max:g} lb" if recommendation.estimated_one_rep_max else "Not estimated")
            st.subheader(recommendation.action)
            st.write(recommendation.reason)
            st.caption(f"Based on the latest {selected} session dated {latest_date}: {planned_sets} sets at up to {current_weight:g} lb, minimum {minimum_reps} reps, average RPE {average_rpe:.1f}.")

with spartan_tab:
    if df.empty:
        st.info("Log hangs, carries, assisted pulls, and other obstacle work to receive progressions.")
    else:
        timed_names = sorted(df.loc[df["Seconds"] > 0, "Exercise"].unique().tolist())
        if timed_names:
            selected_timed = st.selectbox("Timed grip or carry exercise", timed_names)
            timed = df[df["Exercise"] == selected_timed]
            latest_date = timed["Date"].max()
            latest = timed[timed["Date"] == latest_date]
            best = int(latest["Seconds"].max())
            avg_rpe = float(latest["RPE"].mean())
            next_seconds, message = recommend_timed_progression(best_seconds=best, average_rpe=avg_rpe, pain_reported=bool(latest["Pain"].any()))
            st.metric("Next duration target", f"{next_seconds} sec")
            st.write(message)
        else:
            st.info("No timed sets exist yet. Log dead hangs or carries using the Seconds field.")
        st.markdown("**Suggested skill order:** dead hang → active hang/scapular pull → assisted pull-up → controlled negative → strict pull-up → towel grip → rope foot-lock practice.")
