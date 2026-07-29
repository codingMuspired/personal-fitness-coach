from __future__ import annotations

from datetime import timedelta

import streamlit as st

from services.database import fetch_rows


PROFILE_ID = 1


def configure_page(title: str, icon: str = "🏃") -> None:
    st.set_page_config(page_title=title, page_icon=icon, layout="wide")


def get_profile() -> dict:
    rows = fetch_rows("profiles", filters={"profile_id": PROFILE_ID}, limit=1)
    if not rows:
        st.error("Profile 1 was not found. Run the initial profile INSERT in Supabase.")
        st.stop()
    return rows[0]


def format_duration(seconds: int | None) -> str:
    if not seconds:
        return "0:00"
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes}:{secs:02d}"


def pace_per_mile(seconds: int, miles: float) -> str:
    if seconds <= 0 or miles <= 0:
        return "--"
    pace = seconds / miles
    minutes, secs = divmod(round(pace), 60)
    return f"{minutes}:{secs:02d}/mi"


def week_start(day):
    return day - timedelta(days=day.weekday())
