from __future__ import annotations

from typing import Any

import streamlit as st
from supabase import Client, create_client


@st.cache_resource
def get_supabase_client() -> Client:
    """Create and cache the Supabase client."""

    url = st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY")

    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_KEY must be configured "
            "in .streamlit/secrets.toml."
        )

    return create_client(url, key)


def insert_record(table_name: str, values: dict[str, Any]) -> list[dict[str, Any]]:
    """Insert one record and return the created rows."""

    client = get_supabase_client()
    response = client.table(table_name).insert(values).execute()
    return response.data


def fetch_records(
    table_name: str,
    order_by: str | None = None,
    descending: bool = False,
) -> list[dict[str, Any]]:
    """Fetch rows from a table."""

    client = get_supabase_client()
    query = client.table(table_name).select("*")

    if order_by:
        query = query.order(order_by, desc=descending)

    response = query.execute()
    return response.data