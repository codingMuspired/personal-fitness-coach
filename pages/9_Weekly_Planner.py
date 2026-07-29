from __future__ import annotations

from datetime import date, timedelta
import streamlit as st

from services.adaptive_coach import evaluate_recovery
from services.app_helpers import PROFILE_ID
from services.weekly_plan_data import approve_weekly_plan, fetch_weekly_plan, save_weekly_plan
from services.weekly_planner import generate_weekly_plan, monday_of

st.set_page_config(page_title='Weekly Planner', page_icon='📅', layout='wide')
st.title('Weekly Planner')
st.caption('Generate, review, and approve an entire training week. Recommendations remain editable and require approval.')

week_start = monday_of(st.date_input('Week containing', value=date.today()))
phase = st.selectbox('Training phase', ['Foundation','Half Marathon Base','Spartan Base','Recovery'])

with st.expander('Planning inputs', expanded=True):
    c1,c2,c3 = st.columns(3)
    with c1:
        sleep = st.number_input('Recent average sleep', 3.0, 10.0, 6.5, 0.25)
        soreness = st.slider('Current soreness', 1, 10, 4)
        stress = st.slider('Current stress', 1, 10, 6)
    with c2:
        previous_miles = st.number_input('Previous week miles', 0.0, 100.0, 15.0, 0.5)
        four_week_average = st.number_input('Four-week average miles', 0.0, 100.0, 14.0, 0.5)
        hard_sessions = st.number_input('Hard sessions in last 21 days', 0, 30, 7)
    with c3:
        avg_recovery = st.number_input('Average recovery score', 0.0, 100.0, 75.0, 1.0)
        build_weeks = st.number_input('Consecutive build weeks', 0, 12, 2)
        pain_days = st.number_input('Pain check-ins in last 7 days', 0, 7, 0)
        requested_deload = st.checkbox('Request a deload week')

pain_now = st.checkbox('Sharp pain or altered movement now')

if st.button('Generate weekly plan', type='primary'):
    recovery = evaluate_recovery(sleep_hours=sleep, soreness=soreness, stress=stress, pain_reported=pain_now)
    # Release 4 starter accepts an empty history. Connect the helper to your Release 2 strength history next.
    lift_history = {}
    plan = generate_weekly_plan(
        week_start_date=week_start,
        recovery=recovery,
        previous_week_miles=previous_miles,
        four_week_average_miles=four_week_average,
        completed_hard_sessions_last_21_days=hard_sessions,
        average_recovery_score=avg_recovery,
        consecutive_build_weeks=build_weeks,
        pain_checkins_last_7_days=pain_days,
        lift_history=lift_history,
        requested_deload=requested_deload,
        phase_name=phase,
    )
    saved = save_weekly_plan(PROFILE_ID, plan)
    st.session_state['release4_plan_id'] = saved['weekly_plan_id']
    st.success('Draft week generated and saved.')
    st.rerun()

plan = fetch_weekly_plan(PROFILE_ID, week_start.isoformat())
if not plan:
    st.info('No plan exists for this week yet.')
    st.stop()

c1,c2,c3,c4 = st.columns(4)
c1.metric('Status', plan['status'])
c2.metric('Run target', f"{float(plan.get('target_run_miles') or 0):.1f} mi")
c3.metric('Deload', 'Yes' if plan.get('is_deload') else 'No')
c4.metric('Phase', plan.get('phase_name','Foundation'))

if plan['status'] == 'Draft' and st.button('Approve entire week'):
    approve_weekly_plan(plan['weekly_plan_id'])
    st.success('Week approved.')
    st.rerun()

with st.expander('Why this week was generated'):
    for reason in plan.get('rationale') or []:
        st.write(f'• {reason}')
    st.json(plan.get('evidence') or {})

for session in plan.get('sessions', []):
    label = f"{session['session_date']} · {session['title']} · {session['status']}"
    with st.expander(label, expanded=session['session_date'] == date.today().isoformat()):
        m1,m2,m3 = st.columns(3)
        m1.metric('Duration', f"{session['duration_minutes']} min")
        m2.metric('Intensity', session['intensity'])
        distance = session.get('target_distance_miles')
        m3.metric('Distance', f"{float(distance):.1f} mi" if distance else '—')
        st.write(session['instructions'])
        if session.get('home_alternative'):
            st.caption(f"Home pivot: {session['home_alternative']}")
        exercises = sorted(session.get('prescribed_exercises') or [], key=lambda x: x['exercise_order'])
        if exercises:
            rows=[]
            for x in exercises:
                rows.append({
                    'Exercise': x['exercise_name'],
                    'Sets': x.get('target_sets'),
                    'Reps': x.get('target_repetitions'),
                    'Weight': x.get('target_weight_lb'),
                    'Seconds': x.get('target_duration_seconds'),
                    'RPE': x.get('target_rpe'),
                    'Home substitute': x.get('substitution_name'),
                })
            st.dataframe(rows, use_container_width=True, hide_index=True)

st.caption('Release 4 starter uses manual workload inputs on this page. The next refinement can pull every input directly from your stored history.')
