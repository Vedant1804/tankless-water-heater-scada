"""
================================================================================
TANKLESS GAS WATER HEATER / HEAT CELL PROCESS SCADA MONITORING SYSTEM
Industrial Process Supervisory Control and Data Acquisition (SCADA / HMI)
================================================================================
Academic digital twin interface for real-time telemetry monitoring,
supporting dynamic simulation (DEMO MODE) and UDP hardware telemetry (LIVE MODE).
"""

from datetime import datetime
import pandas as pd
import streamlit as st

import config
from communication.udp_receiver import UDPDataReceiver
from data.sample_data import WaterHeaterDemoSimulator
from utils.data_logger import ProcessDataLogger
from utils.helpers import inject_custom_css, evaluate_alarms
from components.header import render_header
from components.kpi_cards import render_kpi_cards
from components.live_charts import render_live_charts
from components.process_overview import render_process_overview
from components.alarm_panel import render_alarm_panel
from components.controls import render_sidebar_controls

# Page configuration for high-density industrial dashboard
st.set_page_config(
    page_title="SCADA • Tankless Water Heater Monitor",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply SCADA Dark CSS
inject_custom_css()

# ==============================================================================
# SESSION STATE INITIALIZATION (PERSISTENT ACROSS RUNS)
# ==============================================================================
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.mode = "DEMO"
    st.session_state.is_monitoring = True
    st.session_state.udp_port = config.DEFAULT_UDP_PORT
    st.session_state.window_seconds = config.DEFAULT_TIME_WINDOW

    # Persistent singletons
    st.session_state.udp_receiver = UDPDataReceiver(port=config.DEFAULT_UDP_PORT)
    st.session_state.simulator = WaterHeaterDemoSimulator()
    st.session_state.logger = ProcessDataLogger()
    st.session_state.history_records = []
    st.session_state.last_valid_data = None
    st.session_state.last_update_ts = None

# Ensure UDP receiver runs if Live mode is chosen
udp_receiver: UDPDataReceiver = st.session_state.udp_receiver
simulator: WaterHeaterDemoSimulator = st.session_state.simulator
logger_instance: ProcessDataLogger = st.session_state.logger

# ==============================================================================
# SIDEBAR CONTROLS
# ==============================================================================
controls, thresholds = render_sidebar_controls(
    logger_instance=logger_instance,
    is_monitoring=st.session_state.is_monitoring,
    current_mode=st.session_state.mode,
    current_port=st.session_state.udp_port,
    current_window=st.session_state.window_seconds
)

# Handle mode changes
if controls["mode"] != st.session_state.mode:
    st.session_state.mode = controls["mode"]
    if st.session_state.mode == "LIVE":
        if not udp_receiver.is_running:
            success, msg = udp_receiver.start()
            if not success:
                st.sidebar.error(msg)
    st.rerun()

# Handle UDP port reconfiguration
if controls["udp_port"] != st.session_state.udp_port:
    st.session_state.udp_port = controls["udp_port"]
    if udp_receiver.is_running:
        udp_receiver.restart(st.session_state.udp_port)

st.session_state.window_seconds = controls["window_seconds"]

# Handle clear buffer
if controls["clear_history"]:
    st.session_state.history_records.clear()
    st.session_state.last_valid_data = None
    st.session_state.last_update_ts = None
    st.rerun()

# Ensure receiver is active when in LIVE mode
if st.session_state.mode == "LIVE" and not udp_receiver.is_running:
    udp_receiver.start()

# ==============================================================================
# REAL-TIME MONITORING FRAGMENT (SMOOTH NON-FLICKERING PARTIAL REFRESH)
# ==============================================================================
fragment_interval = controls["refresh_rate"] if st.session_state.is_monitoring else None


@st.fragment(run_every=fragment_interval)
def render_scada_live_view():
    """
    Isolated SCADA monitoring fragment. Updates at configurable refresh interval
    without re-rendering sidebar controls or losing page state.
    """
    mode = st.session_state.mode
    is_monitoring = st.session_state.is_monitoring

    latest_data = None
    comm_stats = {}

    if mode == "DEMO":
        comm_stats = {
            "status": "CONNECTED",
            "is_running": True,
            "port": st.session_state.udp_port,
            "packet_count": len(st.session_state.history_records),
            "sample_rate_hz": round(1.0 / controls["refresh_rate"], 1),
            "sender": "INTERNAL DIGITAL MODEL"
        }

        if is_monitoring:
            latest_data = simulator.step(dt=controls["refresh_rate"])
            st.session_state.last_valid_data = latest_data
            st.session_state.last_update_ts = latest_data["timestamp"]
        else:
            latest_data = st.session_state.last_valid_data

    else:  # LIVE MODE
        raw_live_data, comm_stats = udp_receiver.get_latest()

        if raw_live_data:
            latest_data = raw_live_data
            st.session_state.last_valid_data = latest_data
            st.session_state.last_update_ts = latest_data["timestamp"]
        else:
            # When awaiting packets or disconnected, do not fake live data!
            latest_data = st.session_state.last_valid_data

    # Append to rolling history and file logger if monitoring active & data exists
    if is_monitoring and latest_data is not None:
        new_row = {
            "Timestamp": latest_data["timestamp"],
            "Outlet_Temp": latest_data["outlet_temp"],
            "Flow_Rate": latest_data["flow_rate"],
            "Burner_Power": latest_data["burner_power"],
            "Heat_Cell_Temp": latest_data["heat_cell_temp"],
            "Source": mode
        }
        st.session_state.history_records.append(new_row)
        if len(st.session_state.history_records) > config.MAX_HISTORY_POINTS:
            st.session_state.history_records.pop(0)

    # Convert rolling records to DataFrame for plotting and KPIs
    if st.session_state.history_records:
        history_df = pd.DataFrame(st.session_state.history_records)
    else:
        history_df = pd.DataFrame(columns=[
            "Timestamp", "Outlet_Temp", "Flow_Rate", "Burner_Power", "Heat_Cell_Temp", "Source"
        ])

    # Evaluate industrial alarms
    comm_status_str = comm_stats.get("status", "OFFLINE")
    overall_status, active_alarms = evaluate_alarms(
        data=latest_data,
        comm_status=comm_status_str,
        mode=mode,
        thresholds=thresholds
    )

    # Log record to CSV
    if is_monitoring and latest_data is not None:
        logger_instance.log_record(
            data=latest_data,
            source=mode,
            alarm_state=overall_status
        )

    # 1. TOP SCADA HEADER
    render_header(
        system_status=overall_status,
        mode=mode,
        comm_stats=comm_stats,
        last_timestamp=st.session_state.last_update_ts
    )

    # 2. TOP KPI CARDS
    render_kpi_cards(
        latest_data=latest_data,
        history_df=history_df,
        thresholds=thresholds
    )

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # 3. INDUSTRIAL PROCESS SCHEMATIC OVERVIEW
    render_process_overview(data=latest_data)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # 4. MAIN TREND GRAPH SECTION (3 CHARTS)
    render_live_charts(
        history_df=history_df,
        window_seconds=st.session_state.window_seconds,
        thresholds=thresholds
    )

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # 5. ALARM AND STATUS PANEL
    render_alarm_panel(
        overall_status=overall_status,
        active_alarms=active_alarms,
        mode=mode
    )


# Execute the SCADA live fragment
render_scada_live_view()
