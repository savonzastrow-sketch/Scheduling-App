import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime, date
from zoneinfo import ZoneInfo
import tempfile
import os

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
# Helpers: safe read / write
# -----------------------
CSV_COLUMNS = ["timestamp", "name", "available"]

def load_data():
    """Always read the CSV fresh; return DataFrame with correct columns."""
    if DATA_FILE.exists() and DATA_FILE.stat().st_size > 0:
        try:
            df = pd.read_csv(DATA_FILE)
            # ensure columns exist
            for c in CSV_COLUMNS:
                if c not in df.columns:
                    df[c] = pd.NA
            return df[CSV_COLUMNS].copy()
        except pd.errors.EmptyDataError:
            return pd.DataFrame(columns=CSV_COLUMNS)
        except Exception:
            # fallback to empty
            return pd.DataFrame(columns=CSV_COLUMNS)
    else:
        return pd.DataFrame(columns=CSV_COLUMNS)

def atomic_write_df(df: pd.DataFrame, path: Path):
    """Write DataFrame to CSV atomically and ensure headers are present."""
    # Ensure columns order
    df = df.copy()
    for c in CSV_COLUMNS:
        if c not in df.columns:
            df[c] = pd.NA
    df = df[CSV_COLUMNS]
    # write to temp then replace
    fd, tmp_path = tempfile.mkstemp(dir=str(path.parent))
    os.close(fd)
    try:
        df.to_csv(tmp_path, index=False)
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise

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
# PAGE SETUP & STYLES
# -----------------------
st.set_page_config(page_title="🀄 Mahjong Sign-up", layout="centered")
st.markdown("""
    <style>
    h1 { font-size: 32px !important; text-align: center; }
    h2 { font-size: 28px !important; text-align: center; }
    p, div, label, .stMarkdown { font-size: 18px !important; line-height: 1.6; }
    </style>
""", unsafe_allow_html=True)

# -----------------------
# Tab navigation (radio so we can detect change)
# -----------------------
tabs = ["📋 Sign-up", "🔒 Admin"]
selected_tab = st.session_state.get("selected_tab", tabs[0])
selected_tab = st.radio("Navigation", tabs, horizontal=True, label_visibility="collapsed")

previous_tab = st.session_state.get("previous_tab", None)
if previous_tab != selected_tab:
    st.session_state["previous_tab"] = selected_tab
    if selected_tab == "📋 Sign-up":
        st.rerun()
st.session_state["selected_tab"] = selected_tab

# Safe initialization of session variables
for key, default in {
    "duplicate_name": None,
    "pending_change": False,
    "previous_available": None,
    "signup_name": ""
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# =====================================================
# TAB 1 — SIGN-UP PAGE
# =====================================================
if selected_tab == "📋 Sign-up":
    st.markdown(f"<h1>🀄 Mahjong - Sign-up</h1>", unsafe_allow_html=True)
    st.markdown(f"<p>Event date: <b>{EVENT_DATE_STR}</b></p>", unsafe_allow_html=True)
    st.markdown(f"<p>Event location: <b>{EVENT_LOCATION}</b></p>", unsafe_allow_html=True)
    st.write("Please enter your name and let us know if you can play.")

    # Load fresh data
    df = load_data()

    # Normalize 'available' column to booleans where possible
    if "available" in df.columns:
        df["available"] = df["available"].map({True: True, False: False, "True": True, "False": False}).fillna(False)

    # Show lists first (always)
    st.markdown("### 😄 Available")
    avail_list = df[df["available"] == True]["name"].astype(str).tolist()
    if avail_list:
        for n in avail_list:
            st.markdown(f"- {n}")
    else:
        st.markdown("_No one yet_")

    st.markdown("### 🙁 Not Available")
    notavail_list = df[df["available"] == False]["name"].astype(str).tolist()
    if notavail_list:
        for n in notavail_list:
            st.markdown(f"- {n}")
    else:
        st.markdown("_No one yet_")

    st.divider()

    # --- Sign-up form (use named keys so we can clear programmatically) ---
    st.markdown("### Sign Up Below")
    if "signup_name" not in st.session_state:
        st.session_state["signup_name"] = ""
    name = st.text_input("Your name", key="signup_name")
    available = st.radio("Can you play?", ["Yes", "No"], horizontal=True, key="signup_available")
    submit = st.button("Submit")

    # --- Submission handling ---
    if submit:
        if not name or not name.strip():
            st.warning("Please enter your name before submitting.")
        else:
            name_clean = name.strip()
            # reload data just before write to avoid race
            df = load_data()
            # normalize available column again
            df["available"] = df["available"].map({True: True, False: False, "True": True, "False": False}).fillna(False)

            if name_clean in df["name"].astype(str).values:
                # Duplicate exists; ask to clear and start over
                st.warning(f"The name **{name_clean}** already has a response.")
                # choice widget
                change = st.radio(
                    "Would you like to clear your previous response and start over?",
                    ["No", "Yes"],
                    horizontal=True,
                    key="change_prompt_sign"
                )

                if change == "Yes":
                    # Remove old record(s)
                    df2 = df[df["name"].astype(str) != name_clean].copy()
                    # Ensure columns present and write atomically (even if empty)
                    atomic_write_df(df2, DATA_FILE)

                    # Clear the input field so user can re-enter
                    st.session_state["signup_name"] = ""

                    st.success(f"{name_clean}'s previous entry has been cleared. Please re-enter your response.")
                    # reload the page so lists update and the cleared state is visible
                    st.experimental_rerun()

                else:
                    st.info("No changes made.")
            else:
                # Add new entry
                new_row = {
                    "timestamp": datetime.now(TIMEZONE).isoformat(),
                    "name": name_clean,
                    "available": True if available == "Yes" else False
                }
                df2 = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                atomic_write_df(df2, DATA_FILE)
                st.success(f"Thanks, {name_clean}! Your response has been recorded.")
                # clear the text input for convenience
                st.session_state["signup_name"] = ""
                st.experimental_rerun()

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
            # recreate a CSV with headers only
            atomic_write_df(pd.DataFrame(columns=CSV_COLUMNS), DATA_FILE)
            st.success("All sign-ups cleared!")

    elif admin_name:
        st.error("Access denied.")
