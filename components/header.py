"""
Industrial SCADA Header Component.
Displays plant metadata, system operational state, active data mode,
live connection status (Waiting for ESP32 / Connected / Connection Lost),
and last packet timestamp.
"""

from datetime import datetime
from typing import Dict, Any, Optional
import streamlit as st
import config
from utils.helpers import clean_html


def render_header(
    system_status: str,
    mode: str,
    comm_stats: Dict[str, Any],
    last_timestamp: Optional[datetime]
):
    """
    Render top-level industrial SCADA status banner.
    """
    now_str = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
    update_str = last_timestamp.strftime("%H:%M:%S") if last_timestamp else "--:--:--"

    # Color & badge selection for system status
    if system_status == "NORMAL":
        status_cls = "status-normal"
        led_cls = "led-green"
        status_label = "● SYSTEM NORMAL"
    elif system_status == "WARNING":
        status_cls = "status-warning"
        led_cls = "led-amber"
        status_label = "▲ SYSTEM WARNING"
    elif system_status == "ALARM":
        status_cls = "status-alarm"
        led_cls = "led-red"
        status_label = "■ PROCESS ALARM"
    else:
        status_cls = "status-offline"
        led_cls = "led-grey"
        status_label = "○ SYSTEM OFFLINE"

    # Communication status badge matching exact requirements
    if mode == "DEMO":
        comm_badge = '<span style="background: rgba(14, 165, 233, 0.15); color: #38bdf8; border: 1px solid rgba(14, 165, 233, 0.4); padding: 4px 10px; border-radius: 4px; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.5px;">SOURCE: DEMO SIMULATION</span>'
        ts_label = f'LAST UPDATE: <strong style="color: #f1f5f9;">{update_str}</strong>'
    else:
        c_status = comm_stats.get("status", "OFFLINE")
        port = comm_stats.get("port", config.DEFAULT_UDP_PORT)
        last_pkt_str = comm_stats.get("last_packet_time_str", "Waiting for ESP32...")
        elapsed_sec = comm_stats.get("elapsed_since_packet")

        if c_status == "CONNECTED":
            hz = comm_stats.get("sample_rate_hz", 0.0)
            comm_badge = f'<span style="background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.4); padding: 4px 10px; border-radius: 4px; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.5px;">● Connected / Receiving Data ({hz} Hz)</span>'
            ts_label = f'LAST PACKET: <strong style="color: #34d399;">{last_pkt_str}</strong>'
        elif c_status == "COMMUNICATION_LOSS":
            comm_badge = '<span style="background: rgba(239, 68, 68, 0.18); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.6); padding: 4px 10px; border-radius: 4px; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.5px;">■ Connection Lost</span>'
            elapsed_info = f" ({elapsed_sec}s ago)" if elapsed_sec else ""
            ts_label = f'LAST PACKET: <strong style="color: #f87171;">{last_pkt_str}{elapsed_info}</strong>'
        elif c_status == "STALE":
            comm_badge = '<span style="background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.4); padding: 4px 10px; border-radius: 4px; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.5px;">▲ Receiving Data (Delayed/Stale)</span>'
            ts_label = f'LAST PACKET: <strong style="color: #fbbf24;">{last_pkt_str}</strong>'
        else:  # WAITING_FOR_ESP32 or OFFLINE
            comm_badge = f'<span style="background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.4); padding: 4px 10px; border-radius: 4px; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.5px;">⏳ Waiting for ESP32 (Port {port})</span>'
            ts_label = f'LAST PACKET: <strong style="color: #94a3b8;">Waiting for ESP32...</strong>'

    header_html = f"""
    <div class="scada-header">
        <div class="scada-title-box">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 2px;">
                <span style="font-family: {config.FONT_MONO}; font-size: 0.72rem; color: #38bdf8; background: rgba(56, 189, 248, 0.1); padding: 2px 6px; border-radius: 3px; border: 1px solid rgba(56, 189, 248, 0.25);">{config.PLANT_TAG}</span>
                <span style="font-family: {config.FONT_MONO}; font-size: 0.72rem; color: #64748b;">TAG: {config.SYSTEM_ID}</span>
                <span style="font-family: {config.FONT_MONO}; font-size: 0.72rem; color: #64748b;">REV {config.VERSION}</span>
            </div>
            <h1>{config.APP_NAME}</h1>
            <p>{config.APP_SUBTITLE}</p>
        </div>
        <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 8px;">
            <div style="display: flex; align-items: center; gap: 10px;">
                {comm_badge}
                <div class="scada-status-pill {status_cls}">
                    <span class="led-dot {led_cls}"></span>
                    {status_label}
                </div>
            </div>
            <div style="font-family: {config.FONT_MONO}; font-size: 0.76rem; color: #94a3b8; display: flex; gap: 14px;">
                <span>{ts_label}</span>
                <span>SYS CLOCK: <strong style="color: #cbd5e1;">{now_str}</strong></span>
            </div>
        </div>
    </div>
    """

    st.markdown(clean_html(header_html), unsafe_allow_html=True)
