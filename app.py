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
EVENT_LOCATION_FILE = DATA_DIR / "event_location.txt"
DATA_DIR.mkdir(exist_ok=True)

# -----------------------
# Load or initialize event date & location
# -----------------------
if EVENT_FILE.exists():
    EVENT_DATE_STR = EVENT_FILE.read_text().strip()
else:
    EVENT_DATE_STR = "Friday, November 14, 2025"
    EVENT_FILE.write_text(EVENT_DATE_STR)

if EVENT_LOCATION_FILE.exists():
    EVENT_LOCATION = EVENT_LOCATION_FILE.read_text().strip()
else:
    EVENT_LOCATION = "TBD"
    EVENT_LOCATION_FILE.write_text(EVENT_LOCATION)

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
# Track active tab in session state
# -----------------------
tabs = ["📋 Sign-up", "🔒 Admin"]
selected_tab = st.session_state.get("selected_tab", tabs[0])
selected_tab = st.radio("Navigation", tabs, horizontal=True, label_visibility="collapsed")

# Detect tab switch and refresh sign-up data when returning
previous_tab = st.session_state.get("previous_tab", None)
if previous_tab != selected_tab:
    st.session_state["previous_tab"] = selected_tab
    if selected_tab == "📋 Sign-up":
        st.rerun()

st.session_state["selected_tab"] = selected_tab

# =====================================================
# TAB 1 — SIGN-UP PAGE
# =====================================================
if selected_tab == "📋 Sign-up":
    st.markdown(f"<h1>🀄 Mahjong - Sign-up</h1>", unsafe_allow_html=True)
    st.markdown(f"<p>Event date: <b>{EVENT_DATE_STR}</b></p>", unsafe_allow_html=True)
    st.markdown(f"<p>Event location: <b>{EVENT_LOCATION}</b></p>", unsafe_allow_html=True)
    st.write("Please enter your name and let us know if you can play.")

    # --- Load data safely (no cache) ---
    if DATA_FILE.exists() and DATA_FILE.stat().st_size > 0:
        try:
            df = pd.read_csv(DATA_FILE)
        except pd.errors.EmptyDataError:
            df = pd.DataFrame(columns=["timestamp", "name", "available"])
    else:
        df = pd.DataFrame(columns=["timestamp", "name", "available"])

    # --- Display current sign-ups ---
    st.markdown("### 😄 Available")
    for n in df[df["available"] == True]["name"].tolist():
        st.markdown(f"- {n}")

    st.markdown("### 🙁 Not Available")
    for n in df[df["available"] == False]["name"].tolist():
        st.markdown(f"- {n}")

    st.divider()

    # --- Sign-up form ---
    st.markdown("### Sign Up Below")

    name = st.text_input("Your name")
    available = st.radio("Can you play?", ["Yes", "No"], horizontal=True)
    submit = st.button("Submit")

    if submit:
        if not name.strip():
            st.warning("Please enter your name before submitting.")
        else:
            name = name.strip()
            if name in df["name"].values:
                st.warning(f"The name **{name}** already has a response.")
                change = st.radio(
                    "Would you like to change your response?",
                    ["No", "Yes"],
                    horizontal=True,
                    key="change_prompt"
                )

                if change == "Yes":
                    # Remove the old record first
                    df = df[df["name"] != name].copy()
                    df.reset_index(drop=True, inplace=True)

                    # Add the updated entry
                    new_row = {
                        "timestamp": datetime.now(),
                        "name": name,
                        "available": available == "Yes"
                    }
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    df.to_csv(DATA_FILE, index=False)
                    st.success(f"{name}'s response has been updated to '{available}'.")
                    st.rerun()

                elif change == "No":
                    st.info("No changes made.")
            else:
                # New entry
                new_row = {
                    "timestamp": datetime.now(),
                    "name": name,
                    "available": available == "Yes"
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                df.to_csv(DATA_FILE, index=False)
                st.success(f"Thanks, {name}! Your response has been recorded.")
                st.rerun()

# =====================================================
# TAB 2 — ADMIN PAGE
# =====================================================
elif selected_tab == "🔒 Admin":
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

        # Change event location
        st.subheader("📍 Change Event Location")
        new_location = st.text_input("Enter new event location", value=EVENT_LOCATION)
        if st.button("Save New Location"):
            EVENT_LOCATION_FILE.write_text(new_location.strip())
            st.success(f"Event location updated to {new_location}")
        
        # Reset signups
        st.subheader("🧹 Reset Sign-ups")
        if st.button("Clear all sign-ups"):
            DATA_FILE.write_text("")  # wipe file
            st.success("All sign-ups cleared!")

    elif admin_name:
        st.error("Access denied.")
