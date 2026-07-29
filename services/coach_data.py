from __future__ import annotations
from datetime import date, datetime, timezone
from typing import Any
from services.database import insert_row, update_rows

def save_recovery(profile_id:int,target_date:date,**values)->dict[str,Any]:
    return insert_row('recovery_checkins', {'profile_id':profile_id,'checkin_date':target_date.isoformat(),**values})

def save_recommendation(profile_id:int,target_date:date,recommendation:dict[str,Any],evidence:dict[str,Any])->dict[str,Any]:
    return insert_row('workout_recommendations', {'profile_id':profile_id,'target_date':target_date.isoformat(),**recommendation,'evidence':evidence,'status':'Draft'})

def approve_recommendation(recommendation_id:int,*,title:str,instructions:str,duration_minutes:int,intensity:str):
    return update_rows('workout_recommendations', {'title':title,'instructions':instructions,'duration_minutes':duration_minutes,'intensity':intensity,'status':'Approved','approved_at':datetime.now(timezone.utc).isoformat()}, filters={'recommendation_id':recommendation_id})
