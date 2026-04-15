import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import hashlib
import json

# ── User Database File ──
USERS_FILE = "users.json"

# ── Load & Save Users ──
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    else:
        # Default admin account
        return {
            "admin": {
                "password": hash_password("admin123"),
                "name": "Admin User",
                "email": "admin@example.com"
            }
        }

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

# ── Helper: Hash Password ──
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ── Session State Init ──
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "page" not in st.session_state:
    st.session_state["page"] = "login"

# ── Login Page ──
def login_page():
    st.title("💸 Smart Expense Tracker")
    st.subheader("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Login", use_container_width=True):
            users = load_users()
            if username in users and users[username]["password"] == hash_password(password):
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.rerun()
            else:
                st.error("❌ Incorrect username or password!")

    with col2:
        if st.button("Register", use_container_width=True):
            st.session_state["page"] = "register"
            st.rerun()

# ── Register Page ──
def register_page():
    st.title("💸 Smart Expense Tracker")
    st.subheader("📝 Create New Account")

    name = st.text_input("Full Name")
    email = st.text_input("Email")
    username = st.text_input("Choose Username")
    password = st.text_input("Choose Password", type="password")
    confirm = st.text_input("Confirm Password", type="password")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Create Account", use_container_width=True):
            users = load_users()
            if not name or not email or not username or not password:
                st.error("❌ Please fill in all fields!")
            elif username in users:
                st.error("❌ Username already exists! Choose another.")
            elif password != confirm:
                st.error("❌ Passwords do not match!")
            elif len(password) < 6:
                st.error("❌ Password must be at least 6 characters!")
            else:
                users[username] = {
                    "password": hash_password(password),
                    "name": name,
                    "email": email
                }
                save_users(users)
                st.success("✅ Account created successfully! Please login.")
                st.session_state["page"] = "login"
                st.rerun()

    with col2:
        if st.button("Back to Login", use_container_width=True):
            st.session_state["page"] = "login"
            st.rerun()

# ── Show Login or Register ──
if not st.session_state["logged_in"]:
    if st.session_state["page"] == "login":
        login_page()
    else:
        register_page()
    st.stop()

# ── Main App (after login) ──
username = st.session_state["username"]
users = load_users()
name = users[username]["name"]
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

if st.sidebar.button("Logout"):
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""
    st.session_state["page"] = "login"
    st.rerun()

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
