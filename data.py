"""
data.py — Cached data-access layer.

Wraps database read functions with @st.cache_data so repeated Streamlit
reruns don't hammer SQLite.  TTL defaults:
  - drugs       30 s  (changes more often)
  - customers   60 s
  - orders      30 s
  - categories  120 s (rarely change)

After any write operation, call the matching invalidate_*() to clear the
cache immediately so the next render reflects fresh data.
"""

import streamlit as st

from database import (
    drug_view_all_data       as _drug_view_all,
    drug_get_low_stock       as _drug_low_stock,
    drug_get_categories      as _drug_categories,
    customer_view_all_data   as _customer_view_all,
    order_view_all_data      as _order_view_all,
    order_view_data          as _order_view_data,
    audit_log_view_all       as _audit_log_view_all,
    analytics_get_raw_sales_data as _analytics_sales_data,
)


# ---------------------------------------------------------------------------
# Cached reads
# ---------------------------------------------------------------------------

@st.cache_data(ttl=30, show_spinner=False)
def get_all_drugs():
    """Return all drug rows (10 columns). Cached 30 s."""
    return _drug_view_all()


@st.cache_data(ttl=30, show_spinner=False)
def get_low_stock_drugs(threshold: int = 10):
    """Return (name, id, qty) for drugs at or below threshold. Cached 30 s."""
    return _drug_low_stock(threshold)


@st.cache_data(ttl=120, show_spinner=False)
def get_drug_categories():
    """Return sorted list of drug categories. Cached 120 s."""
    return _drug_categories()


@st.cache_data(ttl=60, show_spinner=False)
def get_all_customers():
    """Return all customer rows (excl. password). Cached 60 s."""
    return _customer_view_all()


@st.cache_data(ttl=30, show_spinner=False)
def get_all_orders():
    """Return all order rows (admin view). Cached 30 s."""
    return _order_view_all()


@st.cache_data(ttl=30, show_spinner=False)
def get_customer_orders(email: str):
    """Return order rows for one customer. Cached 30 s."""
    return _order_view_data(email)


@st.cache_data(ttl=10, show_spinner=False)
def get_all_audit_logs():
    """Return all audit log rows (AL_id, AL_Timestamp, AL_User, AL_Action, AL_Details). Cached 10 s."""
    return _audit_log_view_all()


@st.cache_data(ttl=30, show_spinner=False)
def get_analytics_sales_data():
    """Return raw sales items for analytics. Cached 30 s."""
    return _analytics_sales_data()


# ---------------------------------------------------------------------------
# Cache invalidators — call after any write to ensure fresh data on next render
# ---------------------------------------------------------------------------

def invalidate_drugs():
    get_all_drugs.clear()
    get_low_stock_drugs.clear()
    get_drug_categories.clear()


def invalidate_customers():
    get_all_customers.clear()


def invalidate_orders():
    get_all_orders.clear()
    # customer-specific order caches are keyed by email — clear all
    get_customer_orders.clear()
    get_analytics_sales_data.clear()


def invalidate_audit_logs():
    get_all_audit_logs.clear()
