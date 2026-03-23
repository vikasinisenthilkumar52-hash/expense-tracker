import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

# ── Page Config ──
st.set_page_config(page_title="Smart Expense Tracker", page_icon="💸")

# ── User Config ──
# ── User Config ──
config = {
    'credentials': {
        'usernames': {
            'admin': {
                'email': 'admin@example.com',
                'name': 'Admin User',
                'password': '$2b$12$OvADU3PNT0roMBBxfJBJx.8oQ3pBRBDxGiAhBmFnxMZJHuSBm6QVW'
            },
            'john': {
                'email': 'john@example.com',
                'name': 'John',
                'password': '$2b$12$sHHsXxBMpHmzYCmgDJFxQO1.5fZcMqFjuZvJcGgGwJO8DxGkZCZOi'
            }
        }
    },
    'cookie': {
        'expiry_days': 30,
        'key': 'expense_tracker_key',
        'name': 'expense_tracker_cookie'
    }
}# ── Authenticator ──
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

name, authentication_status, username = authenticator.login("Login", "main")

# ── Not Logged In ──
if authentication_status is False:
    st.error("❌ Incorrect username or password!")
    st.stop()

elif authentication_status is None:
    st.warning("👆 Please enter your username and password")
    st.stop()

# ── Logged In ──
elif authentication_status:
    # Each user gets their own CSV file
    FILE = f"expenses_{username}.csv"

    def load_data():
        if os.path.exists(FILE):
            return pd.read_csv(FILE)
        else:
            return pd.DataFrame(columns=["date", "amount", "category", "note"])

    def save_data(df):
        df.to_csv(FILE, index=False)

    df = load_data()

    # ── Header ──
    st.title("💸 Smart Expense Tracker")
    st.sidebar.success(f"👋 Welcome, {name}!")
    authenticator.logout("Logout", "sidebar")

    # ── Sidebar Menu ──
    menu = st.sidebar.radio("Navigation", ["➕ Add Expense", "📊 Summary", "📅 Filter by Date", "🗑️ Delete Expense"])

    # ── Add Expense ──
    if menu == "➕ Add Expense":
        st.header("Add New Expense")
        amount = st.number_input("Amount (Rs)", min_value=0.0, format="%.2f")
        category = st.selectbox("Category", ["food", "transport", "bills", "shopping", "other"])
        note = st.text_input("Note (optional)")
        if st.button("Add Expense"):
            if amount <= 0:
                st.error("Please enter a valid amount!")
            else:
                date = datetime.now().strftime("%Y-%m-%d")
                new_row = {"date": date, "amount": amount, "category": category, "note": note}
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                save_data(df)
                st.success(f"✅ Expense of Rs.{amount:.2f} added under '{category}'!")

    # ── Summary ──
    elif menu == "📊 Summary":
        st.header("Expense Summary")
        if df.empty:
            st.warning("No expenses recorded yet!")
        else:
            st.metric("💰 Total Spent", f"Rs. {df['amount'].sum():,.2f}")
            st.subheader("By Category")
            cat_summary = df.groupby("category")["amount"].sum().reset_index()
            st.dataframe(cat_summary, use_container_width=True)
            st.subheader("📊 Spending Breakdown")
            fig, ax = plt.subplots()
            ax.pie(cat_summary["amount"], labels=cat_summary["category"],
                   autopct="%1.1f%%", startangle=90)
            ax.axis("equal")
            st.pyplot(fig)

    # ── Filter by Date ──
    elif menu == "📅 Filter by Date":
        st.header("Filter Expenses")
        filter_type = st.radio("Show", ["Today", "This Week", "Custom Range"])
        df["date"] = pd.to_datetime(df["date"]).dt.date
        today = datetime.now().date()
        if filter_type == "Today":
            filtered = df[df["date"] == today]
        elif filter_type == "This Week":
            filtered = df[df["date"] >= today - timedelta(days=7)]
        else:
            start = st.date_input("Start Date", today - timedelta(days=7))
            end = st.date_input("End Date", today)
            filtered = df[(df["date"] >= start) & (df["date"] <= end)]
        if filtered.empty:
            st.warning("No expenses found for this period.")
        else:
            st.dataframe(filtered, use_container_width=True)
            st.metric("Total", f"Rs. {filtered['amount'].sum():,.2f}")

    # ── Delete Expense ──
    elif menu == "🗑️ Delete Expense":
        st.header("Delete an Expense")
        if df.empty:
            st.warning("No expenses to delete!")
        else:
            st.dataframe(df, use_container_width=True)
            index = st.number_input("Enter row number to delete (starts from 0)",
                                    min_value=0, max_value=len(df)-1, step=1)
            if st.button("Delete"):
                df = df.drop(index=index).reset_index(drop=True)
                save_data(df)
                st.success("🗑️ Expense deleted successfully!")
                st.rerun()