"""
admin_ui.py — Admin dashboard UI for the Pharmacy Management System.

Round-2 improvements:
  - Low-stock alert banner shown at the top of the Drugs section
  - Search / filter on drug inventory view
  - Price field in Add Drug form and View inventory table
  - Image filename field in Add Drug (links image to drug record)
  - Order view uses the new normalised OrderItems schema
  - Admin can delete orders from the Orders section
"""

import streamlit as st
import pandas as pd
import logging

from database import (
    LOW_STOCK_THRESHOLD,
    drug_add_data, drug_view_all_data, drug_update, drug_delete,
    drug_get_low_stock, drug_update_price,
    customer_view_all_data, customer_update, customer_delete,
    order_view_all_data, order_delete,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def show_admin_dashboard() -> None:
    st.title("🏥 Pharmacy Database Dashboard")

    # ---- Global low-stock alert ------------------------------------------------
    low = drug_get_low_stock()
    if low:
        names = ", ".join(r[0] for r in low)
        st.warning(
            f"⚠️ **Low stock alert** — {len(low)} drug(s) at or below "
            f"{LOW_STOCK_THRESHOLD} units: **{names}**"
        )
    # ---------------------------------------------------------------------------

    section = st.sidebar.selectbox(
        "Section", ["Drugs", "Customers", "Orders", "About"]
    )

    if section == "Drugs":
        _show_drugs_section()
    elif section == "Customers":
        _show_customers_section()
    elif section == "Orders":
        _show_orders_section()
    elif section == "About":
        _show_about()


# ---------------------------------------------------------------------------
# Drugs section
# ---------------------------------------------------------------------------

def _show_drugs_section() -> None:
    action = st.sidebar.selectbox("Action", ["View", "Add", "Update", "Delete"])

    if action == "View":
        st.subheader("📋 Drug Inventory")
        drugs = drug_view_all_data()
        if not drugs:
            st.info("No drugs in the inventory yet.")
            return

        df = pd.DataFrame(
            drugs,
            columns=["Name", "Expiry Date", "Use", "Quantity", "ID", "Price (₹)", "Image"]
        )

        # ---- Search / filter ---------------------------------------------------
        search = st.text_input("🔍 Search by name or ID", "")
        if search:
            mask = (
                df["Name"].str.contains(search, case=False, na=False)
                | df["ID"].str.contains(search, case=False, na=False)
            )
            df = df[mask]
            if df.empty:
                st.info(f"No drugs match '{search}'.")
                return
        # -----------------------------------------------------------------------

        with st.expander("All Drugs", expanded=True):
            st.dataframe(df.drop(columns=["Image"]), use_container_width=True)

        with st.expander("Stock Levels"):
            stock_df = df[["Name", "Quantity", "Price (₹)"]].copy()
            # Highlight low-stock rows in red
            def _highlight_low(row):
                try:
                    color = "background-color: #ffcccc" if int(row["Quantity"]) <= LOW_STOCK_THRESHOLD else ""
                except (ValueError, TypeError):
                    color = ""
                return [color] * len(row)

            st.dataframe(
                stock_df.style.apply(_highlight_low, axis=1),
                use_container_width=True
            )

    elif action == "Add":
        st.subheader("➕ Add Drug")

        col1, col2 = st.columns(2)
        with col1:
            drug_name   = st.text_input("Drug Name")
            drug_expiry = st.date_input("Expiry Date")
            drug_use    = st.text_area("When to Use")
        with col2:
            drug_qty   = st.number_input("Quantity", min_value=0, step=1)
            drug_price = st.number_input("Price (₹)", min_value=0.0, step=0.5, format="%.2f")
            drug_id    = st.text_input("Drug ID  (e.g. #D1)")
            drug_image = st.text_input(
                "Image filename (optional)",
                placeholder="e.g. dolo650.jpg"
            )

        if st.button("Add Drug", type="primary"):
            if not drug_name.strip():
                st.warning("Drug Name is required.")
            elif not drug_id.strip():
                st.warning("Drug ID is required.")
            else:
                image_val = drug_image.strip() if drug_image.strip() else None
                success = drug_add_data(
                    drug_name.strip(), str(drug_expiry),
                    drug_use.strip(), int(drug_qty),
                    drug_id.strip(), float(drug_price), image_val
                )
                if success:
                    st.success("✅ Drug added successfully!")
                else:
                    st.error("❌ Failed — Drug ID may already exist.")

    elif action == "Update":
        st.subheader("✏️ Update Drug")
        drug_id    = st.text_input("Drug ID")
        drug_use   = st.text_area("Updated Usage Description")
        drug_price = st.number_input(
            "Updated Price (₹)  — leave 0 to skip",
            min_value=0.0, step=0.5, format="%.2f"
        )

        if st.button("Update", type="primary"):
            if not drug_id.strip():
                st.warning("Drug ID is required.")
            else:
                ok_use = drug_update(drug_id.strip(), drug_use.strip())
                ok_price = (
                    drug_update_price(drug_id.strip(), float(drug_price))
                    if drug_price > 0
                    else True
                )
                if ok_use and ok_price:
                    st.success("✅ Drug updated successfully!")
                else:
                    st.error("❌ Update failed — Drug ID not found.")

    elif action == "Delete":
        st.subheader("🗑️ Delete Drug")
        drug_id = st.text_input("Drug ID")
        st.warning("⚠️ This action cannot be undone.")
        if st.button("Delete", type="primary"):
            if not drug_id.strip():
                st.warning("Drug ID is required.")
            else:
                success = drug_delete(drug_id.strip())
                if success:
                    st.success("✅ Drug deleted.")
                else:
                    st.error("❌ Delete failed — Drug ID not found.")


# ---------------------------------------------------------------------------
# Customers section
# ---------------------------------------------------------------------------

def _show_customers_section() -> None:
    action = st.sidebar.selectbox("Action", ["View", "Update", "Delete"])

    if action == "View":
        st.subheader("👥 Customer List")
        customers = customer_view_all_data()
        if not customers:
            st.info("No customers registered yet.")
            return
        df = pd.DataFrame(customers, columns=["Name", "Email", "State", "Phone"])
        with st.expander("All Customers", expanded=True):
            st.dataframe(df, use_container_width=True)

    elif action == "Update":
        st.subheader("✏️ Update Customer")
        email  = st.text_input("Customer Email")
        number = st.text_input("New Phone Number")
        if st.button("Update", type="primary"):
            if not email.strip() or not number.strip():
                st.warning("Email and phone number are both required.")
            else:
                success = customer_update(email.strip(), number.strip())
                if success:
                    st.success("✅ Customer updated.")
                else:
                    st.error("❌ Update failed — Email not found.")

    elif action == "Delete":
        st.subheader("🗑️ Delete Customer")
        email = st.text_input("Customer Email")
        st.warning("⚠️ This will permanently delete the customer account.")
        if st.button("Delete", type="primary"):
            if not email.strip():
                st.warning("Email is required.")
            else:
                success = customer_delete(email.strip())
                if success:
                    st.success("✅ Customer deleted.")
                else:
                    st.error("❌ Delete failed — Email not found.")


# ---------------------------------------------------------------------------
# Orders section
# ---------------------------------------------------------------------------

def _show_orders_section() -> None:
    st.subheader("📦 All Orders")
    orders = order_view_all_data()

    if not orders:
        st.info("No orders placed yet.")
        return

    df = pd.DataFrame(
        orders,
        columns=["Order ID", "Customer", "Timestamp", "Drug", "Qty", "Unit Price (₹)"]
    )
    df["Line Total (₹)"] = df["Qty"] * df["Unit Price (₹)"]

    with st.expander("All Orders", expanded=True):
        st.dataframe(df, use_container_width=True)

    # ---- Order summary by customer -----------------------------------------
    with st.expander("Order Totals by Customer"):
        summary = (
            df.groupby("Customer")["Line Total (₹)"]
            .sum()
            .reset_index()
            .rename(columns={"Line Total (₹)": "Total Spent (₹)"})
        )
        st.dataframe(summary, use_container_width=True)

    # ---- Delete an order ---------------------------------------------------
    st.divider()
    st.subheader("🗑️ Delete Order")
    order_id_to_delete = st.text_input("Order ID to delete")
    if st.button("Delete Order", type="primary"):
        if not order_id_to_delete.strip():
            st.warning("Order ID is required.")
        else:
            success = order_delete(order_id_to_delete.strip())
            if success:
                st.success("✅ Order deleted.")
            else:
                st.error("❌ Delete failed — Order ID not found.")


# ---------------------------------------------------------------------------
# About section
# ---------------------------------------------------------------------------

def _show_about() -> None:
    st.subheader("ℹ️ About")
    st.info("Pharmacy Management System — Made by Himanshu Sharma")
    st.markdown(
        """
        **Stack:**  Python · Streamlit · SQLite · Pandas  
        **Security:** PBKDF2-HMAC-SHA256 password hashing, env-var admin credentials  
        **Schema:** Normalised OrderItems join table, atomic transactions, FK enforcement
        """
    )
