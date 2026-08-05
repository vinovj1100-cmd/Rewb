#!/usr/bin/env python3
"""
Streamlit frontend for the secure Wildberries Supplier Orders Fetcher.

Designed for Streamlit Community Cloud:
  - Token is read from st.secrets["WB_API_TOKEN"] (preferred) or environment / .env
  - Main module for deployment should be set to app.py
"""

from __future__ import annotations

import io
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Import core logic from the CLI module
from wb_orders_fetcher import (
    MOSCOW_TZ,
    USEFUL_COLUMNS,
    fetch_all_orders,
    transform_to_dataframe,
    setup_logging,
    APIError,
)

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Wildberries Orders Fetcher",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def get_token() -> Optional[str]:
    """Retrieve token from Streamlit secrets, environment, or .env."""
    # 1. Streamlit Cloud secrets (preferred for deployment)
    try:
        token = st.secrets.get("WB_API_TOKEN", None)
        if token:
            return str(token).strip()
    except Exception:
        pass

    # 2. Environment / local .env
    load_dotenv()
    token = os.getenv("WB_API_TOKEN", "").strip()
    if token and token != "your_actual_wildberries_token_here":
        return token

    return None


def create_excel_bytes(df: pd.DataFrame) -> bytes:
    """Convert DataFrame to Excel bytes for download."""
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Orders")
    buffer.seek(0)
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

st.title("📦 Wildberries Supplier Orders")
st.markdown(
    "Securely fetch order data from the official Wildberries Statistics API "
    "(` /api/v1/supplier/orders `)."
)

with st.sidebar:
    st.header("Configuration")
    days_back = st.slider("Days to look back", min_value=1, max_value=90, value=30)
    flag = st.selectbox(
        "Flag",
        options=[0, 1],
        format_func=lambda x: "0 – Incremental (lastChangeDate, paginated)" if x == 0 else "1 – Full day (date only)",
        index=0,
    )
    st.markdown("---")
    st.caption(
        "Token is loaded from **Streamlit Secrets** (`WB_API_TOKEN`) "
        "or from a local `.env` file."
    )
    st.caption("Never commit real tokens to the repository.")

token = get_token()

if not token:
    st.error(
        "No valid `WB_API_TOKEN` found.\n\n"
        "On Streamlit Cloud: open **Settings → Secrets** and add:\n\n"
        "```toml\nWB_API_TOKEN = \"your_token_here\"\n```\n\n"
        "Locally: create a `.env` file from `.env.example`."
    )
    st.stop()

if st.button("Fetch Orders", type="primary"):
    logger = setup_logging("INFO")
    progress = st.progress(0, text="Connecting to Wildberries API…")
    status = st.empty()

    try:
        status.info("Fetching orders (this may take a minute due to rate limits)…")
        progress.progress(20, text="Requesting data…")

        orders = fetch_all_orders(
            token=token,
            days_back=days_back,
            flag=flag,
            logger=logger,
        )

        progress.progress(70, text="Processing data…")

        if not orders:
            progress.progress(100, text="Done")
            st.warning("No orders found for the selected period.")
            st.stop()

        df = transform_to_dataframe(orders)
        progress.progress(100, text="Complete")

        st.success(f"Retrieved **{len(df)}** order rows.")

        # Preview
        st.subheader("Preview")
        st.dataframe(df.head(100), use_container_width=True)

        # Download
        excel_bytes = create_excel_bytes(df)
        timestamp = datetime.now(MOSCOW_TZ).strftime("%Y%m%d_%H%M%S")
        st.download_button(
            label="⬇️ Download Excel",
            data=excel_bytes,
            file_name=f"wb_client_orders_{timestamp}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        # Summary metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Total rows", len(df))
        if "Is_Cancelled" in df.columns:
            cancelled = df["Is_Cancelled"].fillna(False).astype(bool).sum()
            col2.metric("Cancelled", int(cancelled))
        if "Price_Paid_By_Client" in df.columns:
            total = pd.to_numeric(df["Price_Paid_By_Client"], errors="coerce").sum()
            col3.metric("Sum of prices", f"{total:,.0f}")

    except APIError as exc:
        progress.empty()
        st.error(f"API error: {exc}")
    except Exception as exc:
        progress.empty()
        st.exception(exc)

else:
    st.info("Configure parameters in the sidebar and click **Fetch Orders**.")
    st.markdown(
        """
        ### Notes
        - Data is retained by Wildberries for approximately 90 days.
        - The endpoint is rate-limited (≈ 1 request per minute). Large periods with `flag=0` may take longer.
        - Recommended unique order identifier: `srid`.
        """
    )
