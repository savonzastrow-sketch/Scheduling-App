# app.py - Simple scheduling app (hard-coded date, CSV storage)
import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import tempfile
import os

# -----------------------
# CONFIG  - tweak here
# -----------------------
EVENT_DATE_STR = "Friday, November 14, 2025"   # change this to your event date display
EVENT_INTERNAL_DATE = "2025-11-14"             # change this to the YYYY-MM-DD for stored date
DATA_DIR = Path("data")
DATA_FILE = DATA_DIR / "availability.csv"
TIMEZONE = ZoneInfo("America/New_York")
# -----------------------

st.set_page_config(page_title="Mahjong - Sign-up", layout="centered")

# 💅 Custom global font styles
st.markdown("""
    <style>
    h1 {
        font-size: 32px !important;
        text-align: center;
    }
    h2 {
        font-size: 32px !important;       /* Same as h1 */
        text-align: center;               /* Optional: center it too */
        margin-top: 1.5em;                /* Add some breathing room */
    }
    p, div, label, .stMarkdown {
        font-size: 18px !important;
        line-height: 1.6;
    }
    </style>
    """, unsafe_allow_html=True)

# 🀄 Title and intro text
st.markdown("<h1>🀄 Mahjong - Sign-up</h1>", unsafe_allow_html=True)


st.markdown(f"**Event date:** {EVENT_DATE_STR}")
st.write("Thanks for visiting our scheduling app. Please just tell us your name, select yes or no if you can make it and press submit. If your plans change, you can log back in and change your selection.")

# Ensure data dir exists
DATA_DIR.mkdir(exist_ok=True)

# Initialize session state flags to avoid double writes
if "submitted" not in st.session_state:
    st.session_state.submitted = False

# Helper: read csv (returns DataFrame)
def read_data():
    if DATA_FILE.exists():
        try:
            df = pd.read_csv(DATA_FILE, parse_dates=["timestamp"])
            return df
        except Exception:
            # If file exists but corrupted, return empty
            return pd.DataFrame(columns=["date", "name", "available", "timestamp"])
    else:
        return pd.DataFrame(columns=["date", "name", "available", "timestamp"])

# Helper: safe atomic write
def atomic_write(df: pd.DataFrame, path: Path):
    # write to temp file then replace
    fd, tmp_path = tempfile.mkstemp(dir=str(path.parent))
    os.close(fd)
    try:
        df.to_csv(tmp_path, index=False)
        os.replace(tmp_path, path)  # atomic on most OSes
    except Exception as e:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise e

# When user submits, append / dedup and save
def submit_response(name: str, available: bool):
    # normalize name
    name = (name or "").strip()
    if not name:
        st.error("Please enter your name.")
        return

    df = read_data()

    # create new row
    ts = datetime.now(TIMEZONE)
    new_row = {
        "date": EVENT_INTERNAL_DATE,
        "name": name,
        "available": bool(available),
        "timestamp": ts.isoformat()
    }

    # append
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    # Deduplicate: keep the latest entry per (date, name) by timestamp
    if not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp").drop_duplicates(subset=["date", "name"], keep="last")

    # Save atomically
    try:
        atomic_write(df, DATA_FILE)
        st.session_state.submitted = True
        st.success("Thanks — your response has been recorded.")
    except Exception as e:
        st.error(f"Failed to save response: {e}")

# -----------------------
# UI: form
# -----------------------
with st.form("availability_form", clear_on_submit=False):
    name = st.text_input("Your name")
    avail = st.radio("Are you available to play on the event date?", ("Yes", "No"))
    submitted = st.form_submit_button("Submit")

    if submitted:
        # Prevent double-submit in same session
        if st.session_state.submitted:
            st.warning("You've already submitted in this session. Reload the page to submit again.")
        else:
            submit_response(name, avail == "Yes")

st.write("---")
st.header("Sign-ups")

# Load and show
df_all = read_data()
# Filter for current hard-coded date
df = df_all[df_all["date"] == EVENT_INTERNAL_DATE].copy()
if df.empty:
    st.info("No one has signed up yet. Be the first!")
else:
    # Convert available to boolean if stored as string
    if df["available"].dtype == object:
        df["available"] = df["available"].map({"True": True, "False": False}).fillna(df["available"])

    available_df = df[df["available"] == True].sort_values("timestamp")
    unavailable_df = df[df["available"] == False].sort_values("timestamp")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("✅ Available")
        if not available_df.empty:
            for _, row in available_df.iterrows():
                t = pd.to_datetime(row["timestamp"]).astimezone(TIMEZONE).strftime("%Y-%m-%d %I:%M %p")
                st.write(f"- **{row['name']}** (signed: {t})")
        else:
            st.write("_No one available yet_")

    with col2:
        st.subheader("❌ Not available")
        if not unavailable_df.empty:
            for _, row in unavailable_df.iterrows():
                t = pd.to_datetime(row["timestamp"]).astimezone(TIMEZONE).strftime("%Y-%m-%d %I:%M %p")
                st.write(f"- **{row['name']}** (signed: {t})")
        else:
            st.write("_No one unavailable yet_")

st.write("---")

