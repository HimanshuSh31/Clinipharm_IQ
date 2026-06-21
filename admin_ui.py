"""
admin_ui.py — Admin dashboard: metric cards, inventory, customers, orders.

Round-3 improvements:
  - Drug image upload via st.file_uploader (saves to images/ dir)
  - "Add Stock" field in Update Drug form (uses drug_update_details)
  - Expiry date warnings in inventory view
  - Search/filter on customer and order tables
  - CSV export for drugs, customers, orders
"""

import logging
import os
from datetime import date

import streamlit as st
import pandas as pd

from database import (
    LOW_STOCK_THRESHOLD, get_connection,
    drug_add_data, drug_view_all_data, drug_update_details,
    drug_delete, drug_get_low_stock,
    customer_view_all_data, customer_update, customer_delete,
    order_view_all_data, order_delete,
)
from styles import (
    metric_cards_row, alert_warning, alert_danger, alert_success,
    page_header, section_header, sidebar_section_label,
)

logger    = logging.getLogger(__name__)
IMAGE_DIR = "images"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_metrics() -> dict:
    conn = get_connection()
    c    = conn.cursor()
    c.execute("SELECT COUNT(*) FROM Drugs");                              total_drugs     = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM Drugs WHERE D_Qty <= ?", (LOW_STOCK_THRESHOLD,)); low_stock_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM Customers");                          total_customers = c.fetchone()[0]
    c.execute("SELECT COUNT(DISTINCT O_id) FROM Orders");                 total_orders    = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(quantity * unit_price), 0) FROM OrderItems"); total_revenue = c.fetchone()[0]
    return dict(total_drugs=total_drugs, low_stock_count=low_stock_count,
                total_customers=total_customers, total_orders=total_orders,
                total_revenue=total_revenue)


def _save_uploaded_image(uploaded_file) -> str:
    """Save an uploaded file to images/ and return the filename."""
    os.makedirs(IMAGE_DIR, exist_ok=True)
    filename = uploaded_file.name
    filepath = os.path.join(IMAGE_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return filename


def _is_expired(expdate_str: str) -> bool:
    try:
        exp = date.fromisoformat(str(expdate_str))
        return exp < date.today()
    except (ValueError, TypeError):
        return False


def _days_to_expiry(expdate_str: str) -> int:
    try:
        exp = date.fromisoformat(str(expdate_str))
        return (exp - date.today()).days
    except (ValueError, TypeError):
        return 9999


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def show_admin_dashboard() -> None:
    page_header("🏥 Pharmacy Dashboard", "Manage inventory, customers, and orders")

    m = _get_metrics()
    metric_cards_row([
        {"icon": "💊", "value": m["total_drugs"],          "label": "Total Drugs",    "color": "#2563EB", "bg": "#EFF6FF"},
        {"icon": "⚠️", "value": m["low_stock_count"],      "label": "Low Stock",      "color": "#EF4444", "bg": "#FEF2F2"},
        {"icon": "👥", "value": m["total_customers"],      "label": "Customers",      "color": "#7C3AED", "bg": "#F5F3FF"},
        {"icon": "📦", "value": m["total_orders"],         "label": "Total Orders",   "color": "#0891B2", "bg": "#ECFEFF"},
        {"icon": "₹",  "value": f"{m['total_revenue']:,.0f}", "label": "Revenue (₹)", "color": "#059669", "bg": "#ECFDF5"},
    ])

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

    low = drug_get_low_stock()
    if low:
        names = ", ".join(f"**{r[0]}** ({r[2]} left)" for r in low)
        alert_danger(f"Low Stock Alert — {len(low)} drug(s) need restocking", names)

    sidebar_section_label("Navigation")
    section = st.sidebar.selectbox("Section", ["Drugs", "Customers", "Orders", "About"],
                                   label_visibility="collapsed")
    sidebar_section_label("Actions")
    action  = st.sidebar.selectbox("Action", ["View", "Add", "Update", "Delete"],
                                   label_visibility="collapsed")

    if section == "Drugs":
        _drugs_section(action)
    elif section == "Customers":
        _customers_section(action)
    elif section == "Orders":
        _orders_section()
    elif section == "About":
        _about_section()


# ---------------------------------------------------------------------------
# Drugs
# ---------------------------------------------------------------------------

def _drugs_section(action: str) -> None:
    section_header("💊", "Drug Inventory")

    if action == "View":
        drugs = drug_view_all_data()
        if not drugs:
            alert_warning("No drugs yet", "Add your first drug using the sidebar → Add.")
            return

        df = pd.DataFrame(drugs,
                          columns=["Name", "Expiry Date", "Use", "Qty", "ID", "Price (₹)", "Image"])

        # ── Search ──────────────────────────────────────────────────────────
        search = st.text_input("🔍  Search by name or ID", placeholder="e.g. Aspirin or #ASP")
        if search:
            mask = (df["Name"].str.contains(search, case=False, na=False) |
                    df["ID"].str.contains(search, case=False, na=False))
            df = df[mask]
            if df.empty:
                st.info(f"No drugs match **'{search}'**.")
                return

        col_table, col_stock = st.columns([2, 1])

        with col_table:
            st.markdown("##### 📋 All Drugs")

            def _highlight(row):
                exp_days = _days_to_expiry(row["Expiry Date"])
                if _is_expired(row["Expiry Date"]):
                    return ["background-color:#FEE2E2; color:#991B1B"] * len(row)
                if int(row["Qty"]) <= LOW_STOCK_THRESHOLD:
                    return ["background-color:#FEF9C3; color:#854D0E"] * len(row)
                if exp_days <= 30:
                    return ["background-color:#FEF3C7; color:#92400E"] * len(row)
                return [""] * len(row)

            display_df = df.drop(columns=["Image"])
            st.dataframe(display_df.style.apply(_highlight, axis=1),
                         use_container_width=True, hide_index=True)

            # ── Legend ──────────────────────────────────────────────────────
            st.markdown("""
            <div style="display:flex; gap:1rem; font-size:0.73rem; color:#64748B; margin-top:0.4rem;">
                <span>🔴 Expired</span>
                <span>🟡 Low stock (≤10)</span>
                <span>🟠 Expiring in 30 days</span>
            </div>
            """, unsafe_allow_html=True)

        with col_stock:
            st.markdown("##### 📊 Stock Summary")
            total    = int(df["Qty"].sum())
            low_cnt  = int((df["Qty"].astype(int) <= LOW_STOCK_THRESHOLD).sum())
            exp_cnt  = int(df["Expiry Date"].apply(_is_expired).sum())
            avg_price = df["Price (₹)"].astype(float).mean()
            st.metric("Total Units",    total)
            st.metric("Low Stock",      low_cnt, delta=f"-{low_cnt}" if low_cnt else None, delta_color="inverse")
            st.metric("Expired Drugs",  exp_cnt, delta=f"-{exp_cnt}" if exp_cnt else None, delta_color="inverse")
            st.metric("Avg. Price ₹",  f"{avg_price:.2f}")

        # ── CSV Export ──────────────────────────────────────────────────────
        st.download_button(
            "⬇️ Export to CSV",
            data=display_df.to_csv(index=False).encode(),
            file_name="drugs_export.csv",
            mime="text/csv",
        )

    elif action == "Add":
        with st.form("form_add_drug"):
            st.markdown("##### ➕ Add New Drug")
            c1, c2 = st.columns(2)
            with c1:
                d_name   = st.text_input("Drug Name",   placeholder="e.g. Paracetamol")
                d_expiry = st.date_input("Expiry Date")
                d_use    = st.text_area("When to Use",  placeholder="Describe indication…", height=100)
            with c2:
                d_qty    = st.number_input("Quantity",      min_value=0, step=1)
                d_price  = st.number_input("Price (₹)",     min_value=0.0, step=0.5, format="%.2f")
                d_id     = st.text_input("Drug ID",         placeholder="e.g. #D001")
            d_image_file = st.file_uploader("Drug Image (optional)",
                                            type=["jpg","jpeg","png","webp"],
                                            help="Upload an image for this drug")
            submitted = st.form_submit_button("Add Drug →", use_container_width=True)

        if submitted:
            if not d_name.strip() or not d_id.strip():
                st.warning("Drug Name and Drug ID are required.")
            else:
                filename = None
                if d_image_file:
                    filename = _save_uploaded_image(d_image_file)
                ok = drug_add_data(
                    d_name.strip(), str(d_expiry), d_use.strip(),
                    int(d_qty), d_id.strip(), float(d_price), filename
                )
                if ok:
                    alert_success("Drug Added", f"**{d_name}** (ID: {d_id}) added to inventory.")
                else:
                    alert_danger("Failed", "Drug ID already exists. Choose a unique ID.")

    elif action == "Update":
        with st.form("form_update_drug"):
            st.markdown("##### ✏️ Update Drug")
            d_id      = st.text_input("Drug ID",                     placeholder="#D001")
            d_use     = st.text_area("Updated Usage",                 height=80)
            c1, c2    = st.columns(2)
            with c1:
                d_price   = st.number_input("Updated Price (₹) — 0 to skip",
                                            min_value=0.0, step=0.5, format="%.2f")
            with c2:
                d_add_qty = st.number_input("Add Stock Units — 0 to skip",
                                            min_value=0, step=1,
                                            help="This adds to existing stock, not replaces it.")
            submitted = st.form_submit_button("Save Changes →", use_container_width=True)

        if submitted:
            if not d_id.strip():
                st.warning("Drug ID is required.")
            else:
                ok = drug_update_details(
                    d_id.strip(),
                    d_use.strip(),
                    float(d_price),
                    int(d_add_qty)
                )
                if ok:
                    msg = f"Drug **{d_id}** updated."
                    if d_add_qty > 0:
                        msg += f" Added **{d_add_qty}** units to stock."
                    alert_success("Updated", msg)
                else:
                    alert_danger("Not Found", f"No drug with ID **{d_id}** exists.")

    elif action == "Delete":
        with st.form("form_delete_drug"):
            st.markdown("##### 🗑️ Delete Drug")
            st.markdown("<p style='color:#64748B;font-size:0.85rem;'>⚠️ This action is irreversible.</p>",
                        unsafe_allow_html=True)
            d_id      = st.text_input("Drug ID to delete", placeholder="#D001")
            submitted = st.form_submit_button("Delete Drug", use_container_width=True)

        if submitted:
            if not d_id.strip():
                st.warning("Drug ID is required.")
            else:
                ok, msg = drug_delete(d_id.strip())
                if ok:
                    alert_success("Deleted", f"Drug **{d_id}** has been removed.")
                else:
                    alert_danger("Delete Failed", msg)


# ---------------------------------------------------------------------------
# Customers
# ---------------------------------------------------------------------------

def _customers_section(action: str) -> None:
    section_header("👥", "Customer Management")

    if action == "View":
        customers = customer_view_all_data()
        if not customers:
            alert_warning("No customers yet", "Customers appear here once they register.")
            return

        df = pd.DataFrame(customers, columns=["Name", "Email", "State", "Phone"])

        # ── Search ──────────────────────────────────────────────────────────
        search = st.text_input("🔍  Search by name or email", placeholder="e.g. John or john@example.com")
        if search:
            mask = (df["Name"].str.contains(search, case=False, na=False) |
                    df["Email"].str.contains(search, case=False, na=False))
            df = df[mask]
            if df.empty:
                st.info(f"No customers match **'{search}'**.")
                return

        st.markdown(f"**{len(df)} customer(s)**")
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.download_button(
            "⬇️ Export to CSV",
            data=df.to_csv(index=False).encode(),
            file_name="customers_export.csv",
            mime="text/csv",
        )

    elif action == "Update":
        with st.form("form_update_customer"):
            st.markdown("##### ✏️ Update Customer Phone")
            email  = st.text_input("Customer Email")
            number = st.text_input("New Phone Number")
            sub    = st.form_submit_button("Save →", use_container_width=True)
        if sub:
            if not email.strip() or not number.strip():
                st.warning("Both fields are required.")
            elif customer_update(email.strip(), number.strip()):
                alert_success("Updated", f"Phone updated for **{email}**.")
            else:
                alert_danger("Not Found", f"No customer with email **{email}**.")

    elif action == "Delete":
        with st.form("form_delete_customer"):
            st.markdown("##### 🗑️ Delete Customer")
            st.markdown("<p style='color:#64748B;font-size:0.85rem;'>⚠️ Permanently removes the account.</p>",
                        unsafe_allow_html=True)
            email = st.text_input("Customer Email")
            sub   = st.form_submit_button("Delete Customer", use_container_width=True)
        if sub:
            if not email.strip():
                st.warning("Email is required.")
            else:
                ok, msg = customer_delete(email.strip())
                if ok:
                    alert_success("Deleted", f"Customer **{email}** removed.")
                else:
                    alert_danger("Failed", msg)


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------

def _orders_section() -> None:
    section_header("📦", "All Orders")

    rows = order_view_all_data()
    if not rows:
        alert_warning("No orders yet", "Orders appear here once customers place them.")
        return

    df = pd.DataFrame(rows,
                      columns=["Order ID", "Customer", "Timestamp", "Drug", "Qty", "Unit Price (₹)"])
    df["Line Total (₹)"] = (df["Qty"] * df["Unit Price (₹)"]).round(2)

    metric_cards_row([
        {"icon": "📋", "value": df["Order ID"].nunique(), "label": "Total Orders",  "color": "#2563EB", "bg": "#EFF6FF"},
        {"icon": "👤", "value": df["Customer"].nunique(), "label": "Customers",     "color": "#7C3AED", "bg": "#F5F3FF"},
        {"icon": "₹",  "value": f"{df['Line Total (₹)'].sum():,.0f}", "label": "Total Revenue", "color": "#059669", "bg": "#ECFDF5"},
    ])

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # ── Search ──────────────────────────────────────────────────────────────
    search = st.text_input("🔍  Search by customer name or order ID",
                           placeholder="e.g. Alice or alice#A1B2C3D4")
    if search:
        mask = (df["Customer"].str.contains(search, case=False, na=False) |
                df["Order ID"].str.contains(search, case=False, na=False))
        df = df[mask]
        if df.empty:
            st.info(f"No orders match **'{search}'**.")

    st.dataframe(df, use_container_width=True, hide_index=True)

    st.download_button(
        "⬇️ Export to CSV",
        data=df.to_csv(index=False).encode(),
        file_name="orders_export.csv",
        mime="text/csv",
    )

    with st.expander("📊 Revenue by Customer"):
        summary = (
            df.groupby("Customer")["Line Total (₹)"]
            .sum().reset_index()
            .rename(columns={"Line Total (₹)": "Total Spent (₹)"})
            .sort_values("Total Spent (₹)", ascending=False)
        )
        st.dataframe(summary, use_container_width=True, hide_index=True)

    st.divider()
    section_header("🗑️", "Delete Order")
    with st.form("form_delete_order"):
        order_id = st.text_input("Order ID", placeholder="e.g. alice#A1B2C3D4")
        sub      = st.form_submit_button("Delete Order", use_container_width=True)
    if sub:
        if not order_id.strip():
            st.warning("Order ID is required.")
        elif order_delete(order_id.strip()):
            alert_success("Deleted", f"Order **{order_id}** and its items removed.")
        else:
            alert_danger("Not Found", f"No order with ID **{order_id}**.")


# ---------------------------------------------------------------------------
# About
# ---------------------------------------------------------------------------

def _about_section() -> None:
    section_header("ℹ️", "About")
    st.markdown("""
    <div style="background:white;border-radius:16px;padding:2rem;
                border:1px solid #F1F5F9;
                box-shadow:0 1px 3px rgba(0,0,0,0.05),0 4px 16px rgba(0,0,0,0.06);">
        <h3 style="margin:0 0 0.5rem;color:#1E293B;">Pharmacy Management System</h3>
        <p style="color:#64748B;font-size:0.9rem;margin:0 0 1.5rem;">
            Made by <strong>Himanshu Sharma</strong>
        </p>
        <table style="width:100%;border-collapse:collapse;font-size:0.875rem;">
            <tr style="border-bottom:1px solid #F1F5F9;">
                <td style="padding:0.6rem 0.5rem;color:#64748B;font-weight:600;width:35%;">Stack</td>
                <td style="padding:0.6rem 0.5rem;color:#1E293B;">Python · Streamlit · SQLite · Pandas</td>
            </tr>
            <tr style="border-bottom:1px solid #F1F5F9;">
                <td style="padding:0.6rem 0.5rem;color:#64748B;font-weight:600;">Security</td>
                <td style="padding:0.6rem 0.5rem;color:#1E293B;">PBKDF2-HMAC-SHA256 · env-var admin credentials · login rate limiting</td>
            </tr>
            <tr style="border-bottom:1px solid #F1F5F9;">
                <td style="padding:0.6rem 0.5rem;color:#64748B;font-weight:600;">Schema</td>
                <td style="padding:0.6rem 0.5rem;color:#1E293B;">Normalised OrderItems · Atomic transactions · FK enforcement</td>
            </tr>
            <tr>
                <td style="padding:0.6rem 0.5rem;color:#64748B;font-weight:600;">Testing</td>
                <td style="padding:0.6rem 0.5rem;color:#1E293B;">62 pytest tests · In-memory SQLite · GitHub Actions CI</td>
            </tr>
        </table>
    </div>
    """, unsafe_allow_html=True)
