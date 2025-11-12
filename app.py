import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime, date
from zoneinfo import ZoneInfo

# =====================================================
# CONFIG
# =====================================================
TIMEZONE = ZoneInfo("America/New_York")
DATA_DIR = Path("data")
DATA_FILE = DATA_DIR / "availability.csv"
EVENT_FILE = DATA_DIR / "event_date.txt"
EVENT_LOCATION_FILE = DATA_DIR / "event_location.txt"
DATA_DIR.mkdir(exist_ok=True)

# =====================================================
# LOAD / INIT EVENT INFO
# =====================================================
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

# =====================================================
# PAGE SETUP
# =====================================================
st.set_page_config(page_title="🀄 Mahjong Sign-up", layout="centered")

st.markdown("""
    <style>
    h1 { font-size: 32px !important; text-align: center; }
    h2 { font-size: 28px !important; text-align: center; }
    p, div, label, .stMarkdown { font-size: 18px !important; line-height: 1.6; }

     <script>
        // Wait for toggles to render
        const observer = new MutationObserver(() => {
            document.querySelectorAll('[data-testid="stThumb"]').forEach(el => {
                if (el.getAttribute('aria-checked') === 'true') {
                    el.style.backgroundColor = '#22c55e';   // ✅ green when ON
                } else {
                    el.style.backgroundColor = '#d3d3d3';   // ⚪ gray when OFF
                }
            });
        });
        observer.observe(document.body, { attributes: true, childList: true, subtree: true });
        </script>
""", unsafe_allow_html=True)

# =====================================================
# TAB NAVIGATION
# =====================================================
tabs = ["📋 Sign-up", "🔒 Admin"]
selected_tab = st.session_state.get("selected_tab", tabs[0])
selected_tab = st.radio("Navigation", tabs, horizontal=True, label_visibility="collapsed")

# Track tab changes
previous_tab = st.session_state.get("previous_tab", None)
if previous_tab != selected_tab:
    st.session_state["previous_tab"] = selected_tab
    if selected_tab == "📋 Sign-up":
        st.rerun()
st.session_state["selected_tab"] = selected_tab

# =====================================================
# HELPER FUNCTIONS
# =====================================================
def load_data():
    """Load CSV or initialize empty dataframe"""
    if DATA_FILE.exists() and DATA_FILE.stat().st_size > 0:
        try:
            return pd.read_csv(DATA_FILE)
        except pd.errors.EmptyDataError:
            return pd.DataFrame(columns=["timestamp", "name", "available"])
    return pd.DataFrame(columns=["timestamp", "name", "available"])

def save_data(df):
    """Write DataFrame to CSV"""
    df.to_csv(DATA_FILE, index=False)

# =====================================================
# TAB 1 — SIGN-UP PAGE
# =====================================================
if selected_tab == "📋 Sign-up":
    st.markdown("<h1>🀄 Mahjong - Sign-up</h1>", unsafe_allow_html=True)
    st.markdown(f"<p>Event date: <b>{EVENT_DATE_STR}</b></p>", unsafe_allow_html=True)
    st.markdown(f"<p>Event location: <b>{EVENT_LOCATION}</b></p>", unsafe_allow_html=True)
    st.write("Add your name below and toggle your availability.")

    df = load_data()

    # --- Add new player form ---
    with st.form("add_player_form", clear_on_submit=True):
        new_name = st.text_input("Enter your name to join the list:")
        submit_new = st.form_submit_button("Add Name")

    if submit_new:
        if not new_name.strip():
            st.warning("Please enter your name.")
        else:
            new_name = new_name.strip()
            if new_name in df["name"].values:
                st.info(f"{new_name} is already on the list.")
            else:
                new_row = {
                    "timestamp": datetime.now().astimezone(TIMEZONE),
                    "name": new_name,
                    "available": False  # default toggle off
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                save_data(df)
                st.success(f"{new_name} has been added to the list.")
                st.rerun()

    # --- Editable list of players ---
    if not df.empty:
        st.divider()
        st.markdown("### 😄 Player Availability")

        for i, row in df.iterrows():
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.markdown(f"**{row['name']}**")
            with col2:
                toggle = st.toggle(
                    "Can play?",
                    value=bool(row["available"]),
                    key=f"toggle_{i}"
                )
                if toggle != bool(row["available"]):
                    # Update and save immediately
                    df.loc[i, "available"] = toggle
                    df.loc[i, "timestamp"] = datetime.now().astimezone(TIMEZONE)
                    save_data(df)
            with col3:
                # Friendly emojis instead of check/X
                if toggle:
                    st.markdown("<span style='color:green; font-weight:bold;'>😄 Available</span>", unsafe_allow_html=True)
                else:
                    st.markdown("<span style='color:gray; font-weight:bold;'>🙁 Not available</span>", unsafe_allow_html=True)

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
