"""
customer_ui.py — Customer-facing dashboard: medicine card grid, order placement.

Round-3 improvements:
  - Medicine search / filter bar
  - Expired drug cards visually marked and blocked from ordering
  - Expiring-soon (≤30 days) warning badge
  - Order confirmation step before placing (shows item summary + total)
  - uuid4 order IDs
  - Atomic order_place() with full rollback
"""

import os
import uuid
import logging
from datetime import date
from typing import Optional

import streamlit as st
import pandas as pd
from PIL import Image

from database import drug_view_all_data, order_view_data, order_place
from styles import (
    medicine_card_header, order_total_banner,
    alert_success, alert_danger, alert_warning,
    page_header, section_header,
)

logger      = logging.getLogger(__name__)
IMAGES_DIR  = "images"
COLS        = 3


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_image(filename: Optional[str]):
    if not filename:
        return None
    path = os.path.join(IMAGES_DIR, filename)
    try:
        return Image.open(path)
    except Exception:
        return None


def _days_to_expiry(expdate_str: str) -> int:
    try:
        return (date.fromisoformat(str(expdate_str)) - date.today()).days
    except (ValueError, TypeError):
        return 9999


def _is_expired(expdate_str: str) -> bool:
    return _days_to_expiry(expdate_str) < 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def show_customer_dashboard(username: str, email: str) -> None:
    page_header(f"👋 Hello, {username}!", "Browse medicines and place your order below.")
    _order_history(email)
    st.divider()
    _medicine_catalog(username, email)


# ---------------------------------------------------------------------------
# Order history
# ---------------------------------------------------------------------------

def _order_history(email: str) -> None:
    section_header("📦", "Your Order History")
    with st.expander("View past orders", expanded=False):
        rows = order_view_data(email)
        if not rows:
            st.markdown(
                "<p style='color:#64748B;font-size:0.875rem;padding:0.5rem 0;'>"
                "You haven't placed any orders yet.</p>",
                unsafe_allow_html=True,
            )
            return

        df = pd.DataFrame(rows, columns=["Order ID", "Date & Time", "Drug", "Qty", "Unit Price (₹)"])
        df["Line Total (₹)"] = (df["Qty"] * df["Unit Price (₹)"]).round(2)
        st.dataframe(df, use_container_width=True, hide_index=True)

        totals = (
            df.groupby("Order ID")["Line Total (₹)"]
            .sum().reset_index()
            .rename(columns={"Line Total (₹)": "Order Total (₹)"})
            .sort_values("Order Total (₹)", ascending=False)
        )
        st.markdown("**Order totals:**")
        st.dataframe(totals, use_container_width=True, hide_index=True)

        st.download_button(
            "⬇️ Download History",
            data=df.to_csv(index=False).encode(),
            file_name="my_orders.csv",
            mime="text/csv",
        )


# ---------------------------------------------------------------------------
# Medicine catalog
# ---------------------------------------------------------------------------

def _medicine_catalog(username: str, email: str) -> None:
    section_header("🛒", "Available Medicines")

    drugs = drug_view_all_data()
    if not drugs:
        alert_warning("No medicines available", "The inventory is currently empty. Please check back later.")
        return

    # ── Search bar ───────────────────────────────────────────────────────────
    search = st.text_input("🔍  Search medicines", placeholder="e.g. Aspirin, Ibuprofen…")
    if search:
        drugs = [d for d in drugs
                 if search.lower() in d[0].lower() or search.lower() in (d[2] or "").lower()]
        if not drugs:
            st.info(f"No medicines match **'{search}'**. Try a different keyword.")
            return

    quantities: dict = {}

    # ── Card grid ────────────────────────────────────────────────────────────
    for row_start in range(0, len(drugs), COLS):
        row_drugs = drugs[row_start: row_start + COLS]
        cols      = st.columns(COLS, gap="medium")

        for col, drug in zip(cols, row_drugs):
            d_name, d_expiry, d_use, d_qty, d_id, d_price, d_image = drug
            expired     = _is_expired(d_expiry)
            days_left   = _days_to_expiry(d_expiry)
            out_of_stock = int(d_qty or 0) == 0

            with col:
                # ── Expiry overlay for expired drugs ─────────────────────
                if expired:
                    st.markdown(f"""
                    <div style="background:#FEE2E2;border:2px solid #EF4444;border-radius:16px;
                                padding:1.25rem;margin-bottom:0.25rem;opacity:0.75;
                                position:relative;">
                        <div style="position:absolute;top:0.6rem;right:0.75rem;
                                    background:#EF4444;color:white;font-size:0.68rem;
                                    font-weight:700;padding:0.2rem 0.5rem;border-radius:20px;">
                            EXPIRED
                        </div>
                        <div style="font-size:1rem;font-weight:700;color:#991B1B;
                                    margin-bottom:0.3rem;">💊 {d_name}</div>
                        <div style="font-size:0.78rem;color:#B91C1C;">
                            Expired: {d_expiry}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    quantities[d_id] = 0
                    continue   # skip slider — expired drugs cannot be ordered

                # ── Normal card header ───────────────────────────────────
                medicine_card_header(
                    name   = d_name,
                    use    = d_use,
                    price  = float(d_price),
                    expiry = str(d_expiry),
                    qty    = int(d_qty or 0),
                )

                # ── Expiring soon badge ──────────────────────────────────
                if 0 <= days_left <= 30:
                    st.markdown(
                        f"<div style='background:#FEF3C7;border:1px solid #FDE68A;"
                        f"border-radius:8px;padding:0.3rem 0.7rem;font-size:0.75rem;"
                        f"font-weight:600;color:#92400E;margin-bottom:0.3rem;'>"
                        f"⏰ Expiring in {days_left} day{'s' if days_left != 1 else ''}</div>",
                        unsafe_allow_html=True,
                    )

                # ── Drug image ───────────────────────────────────────────
                img = _load_image(d_image)
                if img:
                    st.image(img, use_container_width=True)

                # ── Quantity slider (disabled if out of stock) ────────────
                max_qty = min(int(d_qty or 0), 20)
                if out_of_stock:
                    st.markdown(
                        "<div style='text-align:center;font-size:0.8rem;"
                        "color:#EF4444;font-weight:600;padding:0.5rem 0;'>"
                        "❌ Out of stock</div>",
                        unsafe_allow_html=True,
                    )
                    quantities[d_id] = 0
                else:
                    quantities[d_id] = st.slider(
                        label     = f"Qty — {d_name}",
                        min_value = 0,
                        max_value = max_qty,
                        value     = 0,
                        key       = f"qty_{d_id}",
                        label_visibility = "collapsed",
                    )
                    if quantities[d_id] > 0:
                        subtotal = quantities[d_id] * float(d_price)
                        st.markdown(
                            f"<div style='text-align:center;font-size:0.78rem;"
                            f"color:#2563EB;font-weight:600;margin-top:0.2rem;'>"
                            f"{quantities[d_id]} × ₹{float(d_price):.2f} = ₹{subtotal:.2f}</div>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            "<div style='text-align:center;font-size:0.75rem;"
                            "color:#94A3B8;margin-top:0.2rem;'>Slide to select qty</div>",
                            unsafe_allow_html=True,
                        )

        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    # ── Order total banner ───────────────────────────────────────────────────
    selected_drugs = [d for d in drugs if quantities.get(d[4], 0) > 0]
    if selected_drugs:
        total = sum(float(d[5]) * quantities[d[4]] for d in selected_drugs)
        order_total_banner(len(selected_drugs), total)

    # ── Place Order with confirmation step ───────────────────────────────────
    if "confirm_order" not in st.session_state:
        st.session_state.confirm_order = False

    _, btn_col, _ = st.columns([1, 2, 1])
    with btn_col:
        if not st.session_state.confirm_order:
            review = st.button(
                "🛒  Review Order" if selected_drugs else "Select medicines above",
                use_container_width=True,
                disabled=not bool(selected_drugs),
            )
            if review and selected_drugs:
                st.session_state.confirm_order = True
                st.rerun()
        else:
            # ── Confirmation panel ───────────────────────────────────────
            grand_total = sum(float(d[5]) * quantities[d[4]] for d in selected_drugs)
            st.markdown("""
            <div style="background:white;border:2px solid #2563EB;border-radius:16px;
                        padding:1.5rem;margin-top:0.5rem;">
                <h4 style="margin:0 0 1rem;color:#1E293B;">📋 Order Summary</h4>
            """, unsafe_allow_html=True)

            for drug in selected_drugs:
                qty  = quantities[drug[4]]
                line = qty * float(drug[5])
                st.markdown(
                    f"<div style='display:flex;justify-content:space-between;"
                    f"font-size:0.875rem;color:#374151;padding:0.3rem 0;'>"
                    f"<span>💊 {drug[0]} × {qty}</span>"
                    f"<span style='font-weight:600;'>₹ {line:.2f}</span></div>",
                    unsafe_allow_html=True,
                )

            st.markdown(
                f"<div style='border-top:2px solid #F1F5F9;margin-top:0.75rem;"
                f"padding-top:0.75rem;display:flex;justify-content:space-between;"
                f"font-size:1rem;font-weight:800;color:#1E293B;'>"
                f"<span>Total</span><span>₹ {grand_total:,.2f}</span></div>"
                f"</div>",
                unsafe_allow_html=True,
            )

            c_confirm, c_cancel = st.columns(2)
            with c_confirm:
                if st.button("✅  Confirm Order", use_container_width=True, type="primary"):
                    order_id = f"{username}#{uuid.uuid4().hex[:8].upper()}"
                    items = [
                        {"drug_id": d[4], "drug_name": d[0],
                         "quantity": quantities[d[4]], "unit_price": float(d[5])}
                        for d in selected_drugs
                    ]
                    success = order_place(email, order_id, items)
                    st.session_state.confirm_order = False
                    if success:
                        alert_success(
                            "Order Placed Successfully! 🎉",
                            f"**Order ID:** `{order_id}`  ·  **Total: ₹ {grand_total:,.2f}**  ·  "
                            f"{len(items)} item(s) dispatched.",
                        )
                        st.balloons()
                    else:
                        alert_danger(
                            "Order Failed",
                            "One or more items may be out of stock. Adjust quantities and try again.",
                        )
            with c_cancel:
                if st.button("✖  Cancel", use_container_width=True):
                    st.session_state.confirm_order = False
                    st.rerun()
