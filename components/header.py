"""
Industrial SCADA Header Component.
Displays plant metadata, system operational state, active data mode,
communication link status, and high-precision system clock.
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

    # Communication status badge
    if mode == "DEMO":
        comm_badge = '<span style="background: rgba(14, 165, 233, 0.15); color: #38bdf8; border: 1px solid rgba(14, 165, 233, 0.4); padding: 4px 10px; border-radius: 4px; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.5px;">SOURCE: DEMO SIMULATION</span>'
    else:
        c_status = comm_stats.get("status", "OFFLINE")
        if c_status == "CONNECTED":
            hz = comm_stats.get("sample_rate_hz", 0.0)
            comm_badge = f'<span style="background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.4); padding: 4px 10px; border-radius: 4px; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.5px;">LIVE UDP: {comm_stats.get("port", config.DEFAULT_UDP_PORT)} ({hz} Hz)</span>'
        elif c_status == "STALE":
            comm_badge = '<span style="background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.4); padding: 4px 10px; border-radius: 4px; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.5px;">UDP: STALE DATA</span>'
        elif c_status == "COMMUNICATION_LOSS":
            comm_badge = '<span style="background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.4); padding: 4px 10px; border-radius: 4px; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.5px;">UDP: COMM LOSS</span>'
        else:
            comm_badge = '<span style="background: rgba(100, 116, 139, 0.15); color: #94a3b8; border: 1px solid rgba(100, 116, 139, 0.4); padding: 4px 10px; border-radius: 4px; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.5px;">UDP: LISTENING...</span>'

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
                <span>LAST UPDATE: <strong style="color: #f1f5f9;">{update_str}</strong></span>
                <span>SYS CLOCK: <strong style="color: #cbd5e1;">{now_str}</strong></span>
            </div>
        </div>
    </div>
    """

    st.markdown(clean_html(header_html), unsafe_allow_html=True)
