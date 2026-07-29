from datetime import date
import streamlit as st
from services.app_helpers import PROFILE_ID, configure_page
from services.database import fetch_rows, update_rows
configure_page("Today's Plan",'📅'); st.title("Today's Plan")
today=date.today().isoformat(); approved=fetch_rows('workout_recommendations',filters={'profile_id':PROFILE_ID,'target_date':today,'status':'Approved'},order_by='approved_at',descending=True,limit=1)
if approved:
    rec=approved[0]; st.subheader(rec['title']); a,b=st.columns(2); a.metric('Duration',f"{rec['duration_minutes']} min"); b.metric('Intensity',rec['intensity']); st.write(rec['instructions']); st.info(f"Home option: {rec.get('home_alternative') or 'Use the closest band or bodyweight variation.'}")
    with st.expander('Recommendation rationale'):
        for reason in rec.get('rationale') or []: st.write(f'• {reason}')
    c1,c2=st.columns(2)
    if c1.button('Mark completed',type='primary'): update_rows('workout_recommendations',{'status':'Completed'},filters={'recommendation_id':rec['recommendation_id']}); st.success('Recommendation marked completed. Log the actual workout details on the normal logging page.'); st.rerun()
    if c2.button('Skip session'): update_rows('workout_recommendations',{'status':'Skipped'},filters={'recommendation_id':rec['recommendation_id']}); st.warning('Session marked skipped. Do not cram it into tomorrow automatically.'); st.rerun()
else: st.info('No approved adaptive session exists for today. Open Adaptive Coach, enter recovery information, and approve a recommendation.')
st.subheader('Recent recommendations'); recent=fetch_rows('workout_recommendations',filters={'profile_id':PROFILE_ID},order_by='target_date',descending=True,limit=10)
if recent: st.dataframe([{k:r.get(k) for k in ('target_date','title','duration_minutes','intensity','status')} for r in recent],use_container_width=True,hide_index=True)
