"""
Sidebar SCADA Control Station Component.
Provides operator controls for acquisition mode, UDP port configuration,
chart rolling time windows, alarm threshold tuning, and CSV data logging.
"""

from typing import Dict, Any, Tuple
import streamlit as st
import config


def render_sidebar_controls(
    logger_instance,
    is_monitoring: bool,
    current_mode: str,
    current_port: int,
    current_window: int
) -> Tuple[Dict[str, Any], Dict[str, float]]:
    """
    Render all SCADA supervisory controls in the sidebar.

    Returns:
        (control_state_dict, threshold_dict)
    """
    st.sidebar.markdown(
        f"""
        <div style="padding: 10px 0 14px 0; border-bottom: 1px solid #1e293b; margin-bottom: 14px;">
            <div style="font-family: {config.FONT_MONO}; font-size: 0.75rem; color: #38bdf8; letter-spacing: 1px;">SUPERVISORY CONSOLE</div>
            <div style="font-size: 1.1rem; font-weight: 700; color: #f8fafc;">STATION CONTROLS</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 1. ACQUISITION MODE SELECTION
    st.sidebar.markdown("### 🎛️ Operating Mode")
    mode_options = ["DEMO MODE (Simulated)", "LIVE MODE (ESP32 UDP)"]
    selected_mode_label = st.sidebar.radio(
        "Select Telemetry Source:",
        options=mode_options,
        index=0 if current_mode == "DEMO" else 1,
        help="DEMO generates dynamic physical simulation. LIVE listens on UDP for ESP32 packets."
    )
    new_mode = "DEMO" if "DEMO" in selected_mode_label else "LIVE"

    # Start / Stop Monitoring Buttons
    col_btn1, col_btn2 = st.sidebar.columns(2)
    with col_btn1:
        if st.button("▶ START", use_container_width=True, type="primary" if not is_monitoring else "secondary"):
            st.session_state.is_monitoring = True
            st.rerun()

    with col_btn2:
        if st.button("⏸ PAUSE", use_container_width=True, type="primary" if is_monitoring else "secondary"):
            st.session_state.is_monitoring = False
            st.rerun()

    status_color = "#10b981" if is_monitoring else "#ef4444"
    status_text = "MONITORING ACTIVE" if is_monitoring else "MONITORING PAUSED"
    st.sidebar.markdown(
        f"""
        <div style="text-align: center; margin: 4px 0 12px 0;">
            <span style="font-family: {config.FONT_MONO}; font-size: 0.75rem; font-weight: 700; color: {status_color};">
                ● {status_text}
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 2. UDP NETWORK CONFIGURATION (Active for LIVE mode)
    with st.sidebar.expander("📡 Network / UDP Gateway", expanded=(new_mode == "LIVE")):
        udp_port = st.number_input(
            "UDP Listening Port:",
            min_value=1024,
            max_value=65535,
            value=current_port,
            step=1,
            help="Default is 5005. Must match the target port configured in the ESP32 firmware."
        )
        st.markdown(
            f"""
            <div style="font-size: 0.72rem; color: #94a3b8; background: #0f172a; padding: 8px; border-radius: 4px; border: 1px solid #1e293b;">
                <strong>Local IP Bind:</strong> <code>0.0.0.0</code> (All interfaces)<br>
                <strong>Port:</strong> <code>{udp_port}</code><br>
                <strong>Expected Format:</strong><br>
                <code>outlet,flow,power,cell</code><br>
                <em>e.g. 48.08,5.00,13.20,48.10</em>
            </div>
            """,
            unsafe_allow_html=True
        )

    # 3. DISPLAY & ROLLING WINDOW
    st.sidebar.markdown("### 📈 Display Settings")
    window_choice = st.sidebar.selectbox(
        "Rolling Time Window:",
        options=list(config.TIME_WINDOW_OPTIONS.keys()),
        index=list(config.TIME_WINDOW_OPTIONS.values()).index(current_window) if current_window in config.TIME_WINDOW_OPTIONS.values() else 1,
        help="Duration of historical data displayed on the trend charts."
    )
    window_sec = config.TIME_WINDOW_OPTIONS[window_choice]

    refresh_rate = st.sidebar.slider(
        "UI Refresh Rate (s):",
        min_value=0.5,
        max_value=3.0,
        value=1.0,
        step=0.5,
        help="Streamlit fragment update interval."
    )

    clear_history = st.sidebar.button("🧹 Clear Trend Buffer", use_container_width=True)

    # 4. ALARM THRESHOLD TUNING
    with st.sidebar.expander("⚙️ Alarm Limits Configuration", expanded=False):
        st.markdown("<span style='font-size: 0.75rem; color: #94a3b8;'>Adjust process trip & warning limits:</span>", unsafe_allow_html=True)
        outlet_warn = st.number_input(
            "Outlet Temp Warning (°C):",
            min_value=30.0,
            max_value=75.0,
            value=float(config.DEFAULT_OUTLET_HIGH_WARN),
            step=1.0
        )
        outlet_alarm = st.number_input(
            "Outlet Temp Alarm (°C):",
            min_value=40.0,
            max_value=90.0,
            value=float(config.DEFAULT_OUTLET_HIGH_ALARM),
            step=1.0
        )
        flow_warn = st.number_input(
            "Low Flow Warning (L/min):",
            min_value=0.5,
            max_value=5.0,
            value=float(config.DEFAULT_FLOW_LOW_WARN),
            step=0.2
        )
        burner_warn = st.number_input(
            "Burner High Warning (kW):",
            min_value=10.0,
            max_value=30.0,
            value=float(config.DEFAULT_BURNER_HIGH_WARN),
            step=1.0
        )
        cell_warn = st.number_input(
            "Heat Cell High Warning (°C):",
            min_value=40.0,
            max_value=95.0,
            value=float(config.DEFAULT_HEAT_CELL_HIGH_WARN),
            step=1.0
        )

    # 5. DATA LOGGING & EXPORT
    st.sidebar.markdown("### 💾 CSV Data Logging")
    enable_logging = st.sidebar.checkbox(
        "Enable CSV File Logging",
        value=logger_instance.is_logging_enabled if logger_instance else True
    )
    if logger_instance:
        logger_instance.is_logging_enabled = enable_logging

    rec_count = logger_instance.get_record_count() if logger_instance else 0
    st.sidebar.markdown(
        f"""
        <div style="font-family: {config.FONT_MONO}; font-size: 0.75rem; color: #94a3b8; margin: 4px 0 8px 0;">
            SESSION RECORDS: <strong style="color: #38bdf8;">{rec_count}</strong>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Download CSV Button
    if logger_instance:
        csv_bytes = logger_instance.get_csv_bytes()
        st.sidebar.download_button(
            label="📥 Download CSV Log",
            data=csv_bytes,
            file_name=f"water_heater_scada_log.csv",
            mime="text/csv",
            use_container_width=True
        )

    controls_state = {
        "mode": new_mode,
        "is_monitoring": st.session_state.is_monitoring,
        "udp_port": int(udp_port),
        "window_seconds": window_sec,
        "refresh_rate": refresh_rate,
        "clear_history": clear_history,
    }

    thresholds = {
        "outlet_high_warn": outlet_warn,
        "outlet_high_alarm": outlet_alarm,
        "flow_low_warn": flow_warn,
        "burner_high_warn": burner_warn,
        "heat_cell_high_warn": cell_warn
    }

    return controls_state, thresholds
