from __future__ import annotations

from datetime import date
import streamlit as st

from services.app_helpers import PROFILE_ID
from services.weekly_plan_data import fetch_weekly_plan, update_session_status
from services.weekly_planner import monday_of

st.set_page_config(page_title="Today's Plan", page_icon='✅', layout='wide')
st.title("Today's Plan")

today = date.today()
plan = fetch_weekly_plan(PROFILE_ID, monday_of(today).isoformat())
if not plan:
    st.info('No weekly plan exists. Open Weekly Planner to generate one.')
    st.stop()

sessions = [s for s in plan.get('sessions', []) if s['session_date'] == today.isoformat() and s['status'] not in {'Moved','Cancelled'}]
if not sessions:
    st.success('No planned training today. Rest or complete gentle mobility.')
    st.stop()

for session in sessions:
    st.subheader(session['title'])
    c1,c2,c3 = st.columns(3)
    c1.metric('Duration', f"{session['duration_minutes']} min")
    c2.metric('Intensity', session['intensity'])
    c3.metric('Status', session['status'])
    st.write(session['instructions'])
    if session.get('target_distance_miles'):
        st.write(f"Target distance: **{float(session['target_distance_miles']):.1f} miles**")
    exercises = sorted(session.get('prescribed_exercises') or [], key=lambda x: x['exercise_order'])
    if exercises:
        st.dataframe([{
            'Exercise': x['exercise_name'], 'Sets': x.get('target_sets'),
            'Reps': x.get('target_repetitions'), 'Weight': x.get('target_weight_lb'),
            'Seconds': x.get('target_duration_seconds'), 'RPE': x.get('target_rpe'),
            'Home': x.get('substitution_name')
        } for x in exercises], use_container_width=True, hide_index=True)
    b1,b2 = st.columns(2)
    if b1.button('Mark completed', key=f"done_{session['weekly_plan_session_id']}"):
        update_session_status(session['weekly_plan_session_id'], 'Completed')
        st.success('Session marked completed. Log the actual run or exercise sets separately.')
        st.rerun()
    if b2.button('Skip session', key=f"skip_{session['weekly_plan_session_id']}"):
        update_session_status(session['weekly_plan_session_id'], 'Skipped')
        st.warning('Session skipped. Open Weekly Planner before moving it to another day.')
        st.rerun()
