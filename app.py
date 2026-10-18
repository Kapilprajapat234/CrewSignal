import hmac
import os
import time

import streamlit as st

from core import METRICS
from core.simulator import load_scenario, generate_readings
from core.baseline import compute_baseline
from core.anomaly import detect
from db.database import init_db, save_readings
from core.sync import sync_pending

from ui import profile as ui_profile
from ui import charts as ui_charts
from ui import flags as ui_flags
from ui import symptoms as ui_symptoms
from ui import workflow as ui_workflow

st.set_page_config(page_title="CrewSignal", layout="wide")

# FIX: DB hamesha ready ho — warna symptom save pe crash
init_db()

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;700&display=swap');

    .stApp h1, .stApp h2, .stApp h3, .stApp h4,
    .stApp p, .stApp label, .stApp span,
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {
        font-family: 'Playfair Display', Georgia, 'Times New Roman', serif !important;
        font-style: normal !important;
    }

    [data-testid="stDeployButton"],
    button[kind="headerDeployButton"],
    [class*="stDeployButton"] {
        display: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

MAX_ATTEMPTS = 3
LOCKOUT_SECONDS = 30
SESSION_TIMEOUT = 600


def get_pins():
    return {
        "crew": os.getenv("CREW_PIN", "1234"),
        "medical": os.getenv("MEDIC_PIN", "9999"),
    }


def check_pin(entered):
    matched_role = None
    for role, pin in get_pins().items():
        if hmac.compare_digest(entered.encode(), pin.encode()):
            matched_role = role
    return matched_role


def login():
    if st.session_state.get("role"):
        idle = time.time() - st.session_state.get("last_active", 0)
        if idle <= SESSION_TIMEOUT:
            st.session_state["last_active"] = time.time()
            return st.session_state["role"]
        st.session_state.clear()
        st.warning("Session locked after inactivity. Enter your PIN again.")

    st.title("CrewSignal — Secure Access")
    st.caption("Authorised personnel only. Synthetic-data prototype.")

    remaining = int(st.session_state.get("locked_until", 0) - time.time())
    if remaining > 0:
        st.error(f"Too many failed attempts. Try again in {remaining} seconds.")
        st.stop()

    with st.form("login_form"):
        pin = st.text_input("Access PIN", type="password")
        submitted = st.form_submit_button("Unlock", type="primary")

    if submitted:
        role = check_pin(pin)
        if role:
            st.session_state["role"] = role
            st.session_state["last_active"] = time.time()
            st.session_state["failed_attempts"] = 0
            st.rerun()
        else:
            attempts = st.session_state.get("failed_attempts", 0) + 1
            if attempts >= MAX_ATTEMPTS:
                st.session_state["locked_until"] = time.time() + LOCKOUT_SECONDS
                st.session_state["failed_attempts"] = 0
                st.error(f"Too many failed attempts. Locked for {LOCKOUT_SECONDS} seconds.")
            else:
                st.session_state["failed_attempts"] = attempts
                st.error(f"Wrong PIN. {MAX_ATTEMPTS - attempts} attempt(s) left.")

    st.stop()


def call_ui(module, function_name, *args, **kwargs):
    func = getattr(module, function_name, None)
    if func is None:
        st.info(f"`{module.__name__}.{function_name}()` is not implemented yet.")
    else:
        func(*args, **kwargs)


def load_mission(scenario_name):
    scenario = load_scenario(scenario_name)
    readings = generate_readings(scenario)
    save_readings(readings)

    st.session_state["scenario"] = scenario
    st.session_state["all_readings"] = readings
    st.session_state["astronauts"] = sorted(readings["astronaut_id"].unique())


def _filter_by_day(df, day):
    """Replay-day slider ko readings par apply karo."""
    for col in ("mission_day", "day"):
        if col in df.columns:
            return df[df[col] <= day]
    return df


def analyze_astronaut(astronaut_id):
    readings = st.session_state["all_readings"]
    day = st.session_state.get("replay_day", 14)

    full = readings[readings["astronaut_id"] == astronaut_id]
    recent = _filter_by_day(full, day)  # baselines POORE data se, trends/flags selected day tak

    baselines = {
        metric: compute_baseline(full[full["metric"] == metric], metric)
        for metric in METRICS
    }
    flags = detect(recent, baselines, astronaut_id) if not recent.empty else {}

    st.session_state["astronaut"] = astronaut_id
    st.session_state["readings"] = recent
    st.session_state["baselines"] = baselines
    st.session_state["flags"] = flags
    st.session_state["_analyzed_day"] = day


def build_profile(astronaut_id, scenario, baselines):
    sc = scenario if isinstance(scenario, dict) else {}
    return {
        "name": astronaut_id,
        "age": sc.get("age", "—"),
        "mission_day": st.session_state.get("replay_day", 1),
        "baselines": baselines,
        "timeline": sc.get("events", []),
    }


# Offline toggle ka state callback se handle — banner/sync kabhi
# out-of-sync nahi honge
def _on_offline_change():
    if st.session_state.get("offline_mode"):
        st.session_state["was_offline"] = True
        return
    if st.session_state.get("was_offline"):
        try:
            st.session_state["sync_result"] = sync_pending()
        except Exception as exc:
            st.session_state["sync_result"] = {"error": str(exc)}
        st.session_state["was_offline"] = False


role = login()

st.title("CrewSignal — Astronaut Health Monitoring")
st.caption("Decision-support prototype. Not a medical diagnosis system.")

st.sidebar.header("Mission Control")
st.sidebar.caption(f"Signed in as: **{role}**")
if st.sidebar.button("Lock session"):
    st.session_state.clear()
    st.rerun()

# Scenarios folder na ho to crash nahi
try:
    scenario_files = sorted(f[:-5] for f in os.listdir("scenarios") if f.endswith(".json"))
except FileNotFoundError:
    scenario_files = []

scenario_choice = st.sidebar.selectbox("Scenario", scenario_files)

# Offline toggle: key + on_change (session_state assign MAT karna — widget khud store karta hai)
offline = st.sidebar.toggle(
    "Offline mode",
    key="offline_mode",
    on_change=_on_offline_change,
)

if offline:
    st.sidebar.warning(
        "OFFLINE — monitoring continues. Sync happens when connectivity returns."
    )
else:
    result = st.session_state.pop("sync_result", None)
    if result:
        if "error" in result:
            st.sidebar.error(f"Sync failed: {result['error']}")
        else:
            if result.get("synced", 0) > 0:
                st.sidebar.success(f"Synced {result['synced']} pending readings.")
            if result.get("conflicts", 0) > 0:
                st.sidebar.warning(result.get("message", "Sync conflicts found."))

load_clicked = st.sidebar.button("Load scenario", type="primary")

# Replay slider: key do, value session_state mein khud store hoti hai
# (isliye yahan st.session_state["replay_day"] = ... assign karna HAI galat)
st.sidebar.slider("Mission replay (day)", 1, 14, 14, key="replay_day")

if load_clicked and scenario_choice:
    with st.spinner("Running pipeline..."):
        load_mission(scenario_choice)
        analyze_astronaut(st.session_state["astronauts"][0])
    st.sidebar.success(f"Loaded '{scenario_choice}'.")

if "astronauts" in st.session_state:
    astronauts = st.session_state["astronauts"]
    current = st.session_state.get("astronaut", astronauts[0])
    chosen = st.sidebar.selectbox(
        "Astronaut",
        astronauts,
        index=astronauts.index(current) if current in astronauts else 0,
    )
    # Replay day badalne pe analysis dobara chale
    needs_analysis = (
        chosen != st.session_state.get("astronaut")
        or st.session_state.get("_analyzed_day") != st.session_state.get("replay_day", 14)
        or "readings" not in st.session_state
    )
    if needs_analysis:
        analyze_astronaut(chosen)

tab_profile, tab_trends, tab_flags, tab_symptoms = st.tabs(
    ["Profile", "Trends", "Flags & Evidence", "Symptoms & Workflow"]
)

if "scenario" not in st.session_state:
    st.info("Select a scenario in the sidebar and click **Load scenario** to begin.")
else:
    with tab_profile:
        call_ui(
            ui_profile,
            "show_profile",
            build_profile(
                st.session_state["astronaut"],
                st.session_state["scenario"],
                st.session_state["baselines"],
            ),
        )
    with tab_trends:
        call_ui(
            ui_charts,
            "trend_chart",
            st.session_state["readings"],
            st.session_state["baselines"],
        )
    with tab_flags:
        call_ui(ui_flags, "show", st.session_state["flags"])
    with tab_symptoms:
        call_ui(ui_symptoms, "show", st.session_state["astronaut"])
        st.divider()
        call_ui(ui_workflow, "show", st.session_state["flags"])