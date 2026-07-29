from __future__ import annotations

from typing import Any

import streamlit as st
from supabase import Client, create_client


@st.cache_resource
def get_supabase_client() -> Client:
    url = st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_KEY in Streamlit secrets.")
    return create_client(url, key)


def fetch_rows(table: str, *, columns: str = "*", filters: dict[str, Any] | None = None,
               order_by: str | None = None, descending: bool = False,
               limit: int | None = None) -> list[dict[str, Any]]:
    query = get_supabase_client().table(table).select(columns)
    for field, value in (filters or {}).items():
        query = query.eq(field, value)
    if order_by:
        query = query.order(order_by, desc=descending)
    if limit:
        query = query.limit(limit)
    return query.execute().data or []


def insert_row(table: str, values: dict[str, Any]) -> dict[str, Any]:
    rows = get_supabase_client().table(table).insert(values).execute().data or []
    if not rows:
        raise RuntimeError(f"Insert into {table} returned no row.")
    return rows[0]


def insert_rows(table: str, values: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not values:
        return []
    return get_supabase_client().table(table).insert(values).execute().data or []


def upsert_row(table: str, values: dict[str, Any], *, on_conflict: str) -> dict[str, Any]:
    rows = (
        get_supabase_client().table(table)
        .upsert(values, on_conflict=on_conflict)
        .execute().data or []
    )
    if not rows:
        raise RuntimeError(f"Upsert into {table} returned no row.")
    return rows[0]


def update_rows(table: str, values: dict[str, Any], *, filters: dict[str, Any]) -> list[dict[str, Any]]:
    query = get_supabase_client().table(table).update(values)
    for field, value in filters.items():
        query = query.eq(field, value)
    return query.execute().data or []
