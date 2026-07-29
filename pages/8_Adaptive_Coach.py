from __future__ import annotations
from datetime import date, datetime
import streamlit as st
from services.adaptive_coach import evaluate_recovery, recommend_session
from services.app_helpers import PROFILE_ID, configure_page
from services.coach_data import approve_recommendation, save_recommendation, save_recovery
from services.database import fetch_rows
from services.progress_calculator import calculate_weight_trend, current_week_mileage, previous_week_mileage

configure_page('Adaptive Coach','🧭'); st.title('Adaptive Coach')
st.caption('Review the evidence, edit the recommendation, and approve it. Nothing is applied automatically.')
target_date=st.date_input('Session date',date.today())
with st.form('recovery_form'):
    c1,c2,c3=st.columns(3); sleep=c1.number_input('Sleep hours',0.0,12.0,7.0,.5); soreness=c2.slider('Soreness',1,10,3); stress=c3.slider('Stress',1,10,5)
    c4,c5=st.columns(2); hr_delta=c4.number_input('Resting HR above normal',0,40,0); pain=c5.checkbox('Sharp pain or altered movement')
    notes=st.text_area('Recovery notes'); generate=st.form_submit_button('Generate recommendation',type='primary')
if generate:
    recovery=evaluate_recovery(sleep_hours=sleep,soreness=soreness,stress=stress,pain_reported=pain,resting_hr_delta=hr_delta)
    runs=fetch_rows('running_sessions',filters={'profile_id':PROFILE_ID},order_by='run_date',descending=True,limit=250)
    current_miles=current_week_mileage(runs,today=target_date); previous_miles=previous_week_mileage(runs,today=target_date)
    sessions=fetch_rows('workout_sessions',filters={'profile_id':PROFILE_ID},order_by='completed_at',descending=True,limit=30)
    last_hard_days=None
    for row in sessions:
        if row.get('workout_type') in {'Strength A','Strength B','Quality Run','Long Run','Race/Test'} and row.get('completed_at'):
            completed=datetime.fromisoformat(str(row['completed_at']).replace('Z','+00:00')).date(); last_hard_days=max(0,(target_date-completed).days); break
    measurements=fetch_rows('body_measurements',filters={'profile_id':PROFILE_ID},order_by='measured_on',descending=False,limit=100)
    trend=calculate_weight_trend(measurements); weekly_change=trend.weekly_change
    rec=recommend_session(target_date=target_date,recovery=recovery,current_week_miles=current_miles,previous_week_miles=previous_miles,last_hard_session_days_ago=last_hard_days,weight_change_per_week=weekly_change)
    checkin=save_recovery(PROFILE_ID,target_date,sleep_hours=sleep,soreness=soreness,stress=stress,pain_reported=pain,resting_hr_delta=hr_delta,recovery_level=recovery.level,recovery_score=recovery.score,notes=notes or None)
    evidence={'recovery_level':recovery.level,'recovery_score':recovery.score,'current_week_miles':current_miles,'previous_week_miles':previous_miles,'last_hard_session_days_ago':last_hard_days,'weight_change_per_week':weekly_change,'recovery_checkin_id':checkin['recovery_checkin_id']}
    saved=save_recommendation(PROFILE_ID,target_date,rec.to_dict(),evidence); st.session_state['draft_recommendation']=saved
rec=st.session_state.get('draft_recommendation')
if rec:
    ev=rec.get('evidence',{}); a,b,c=st.columns(3); a.metric('Recovery',ev.get('recovery_level','Unknown')); b.metric('Score',ev.get('recovery_score','--')); c.metric('Intensity',rec['intensity'])
    st.subheader('Proposed session'); title=st.text_input('Title',rec['title']); instructions=st.text_area('Instructions',rec['instructions'],height=130)
    duration=st.number_input('Duration in minutes',10,240,int(rec['duration_minutes']),5); options=['Very easy','Reduced','Normal']; intensity=st.selectbox('Intensity',options,index=options.index(rec['intensity']))
    st.write('**Home alternative:**',rec.get('home_alternative'))
    with st.expander('Why this was recommended',expanded=True):
        for reason in rec.get('rationale',[]): st.write(f'• {reason}')
    if st.button('Approve session',type='primary'):
        approve_recommendation(int(rec['recommendation_id']),title=title,instructions=instructions,duration_minutes=int(duration),intensity=intensity); st.success("Session approved. It now appears on Today's Plan."); st.session_state.pop('draft_recommendation',None)
