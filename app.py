import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime, date
from zoneinfo import ZoneInfo

# -----------------------
# CONFIG
# -----------------------
TIMEZONE = ZoneInfo("America/New_York")
DATA_DIR = Path("data")
DATA_FILE = DATA_DIR / "availability.csv"
EVENT_FILE = DATA_DIR / "event_date.txt"
DATA_DIR.mkdir(exist_ok=True)

# -----------------------
# Load or initialize event date
# -----------------------
if EVENT_FILE.exists():
    EVENT_DATE_STR = EVENT_FILE.read_text().strip()
else:
    EVENT_DATE_STR = "Friday, November 14, 2025"
    EVENT_FILE.write_text(EVENT_DATE_STR)

# -----------------------
# PAGE SETUP
# -----------------------
st.set_page_config(page_title="🀄 Mahjong Sign-up", layout="centered")

# -----------------------
# STYLES
# -----------------------
st.markdown("""
    <style>
    h1 { font-size: 32px !important; text-align: center; }
    h2 { font-size: 28px !important; text-align: center; }
    p, div, label, .stMarkdown { font-size: 18px !important; line-height: 1.6; }
    </style>
""", unsafe_allow_html=True)

# -----------------------
# MAIN APP TABS
# -----------------------
tab1, tab2 = st.tabs(["📋 Sign-up", "🔒 Admin"])

# =====================================================
# TAB 1 — SIGN-UP PAGE
# =====================================================
with tab1:
    st.markdown(f"<h1>🀄 Mahjong - Sign-up</h1>", unsafe_allow_html=True)
    st.markdown(f"<p>Event date: <b>{EVENT_DATE_STR}</b></p>", unsafe_allow_html=True)
    st.write("Please enter your name and let us know if you can play.")

    # Load data
    if DATA_FILE.exists() and DATA_FILE.stat().st_size > 0:
        try:
            df = pd.read_csv(DATA_FILE)
        except pd.errors.EmptyDataError:
            df = pd.DataFrame(columns=["timestamp", "name", "available"])
    else:
        df = pd.DataFrame(columns=["timestamp", "name", "available"])

    # Form
    name = st.text_input("Your name")
    available = st.radio("Can you play?", ["Yes", "No"])
    if st.button("Submit"):
        if name.strip():
            new_entry = pd.DataFrame([{
                "timestamp": datetime.now(TIMEZONE).isoformat(),
                "name": name.strip(),
                "available": available == "Yes"
            }])
            df = pd.concat([df, new_entry], ignore_index=True)
            df.to_csv(DATA_FILE, index=False)
            st.success("Your response has been recorded!")
        else:
            st.warning("Please enter your name.")

    # Display results
    st.header("Sign-ups")
    available_df = df[df["available"] == True]
    unavailable_df = df[df["available"] == False]

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("✅ Available")
        for n in available_df["name"]:
            st.write(f"- **{n}**")

    with col2:
        st.subheader("❌ Not available")
        for n in unavailable_df["name"]:
            st.write(f"- **{n}**")

# =====================================================
# TAB 2 — ADMIN PAGE
# =====================================================
with tab2:
    st.markdown("<h1>🔒 Admin Page</h1>", unsafe_allow_html=True)
    st.write("Enter admin name to access controls:")

    admin_name = st.text_input("Admin name")
    if admin_name.strip().lower() == "becky":
        st.success("Welcome, Becky! 👋")

        # Change event date
        st.subheader("🗓 Change Event Date")
        new_date = st.date_input("Select new date", value=date.today())
        if st.button("Save New Date"):
            pretty_date = new_date.strftime("%A, %B %d, %Y")
            EVENT_FILE.write_text(pretty_date)
            st.success(f"Event date updated to {pretty_date}")

        # Reset signups
        st.subheader("🧹 Reset Sign-ups")
        if st.button("Clear all sign-ups"):
            DATA_FILE.write_text("")  # wipe file
            st.success("All sign-ups cleared!")

    elif admin_name:
        st.error("Access denied.")
