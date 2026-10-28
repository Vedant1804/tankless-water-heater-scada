"""
Industrial Alarm and Annunciation Panel.
Displays real-time process limits, communication integrity alarms,
and historical alarm events with ISA-18.2 compliant color categorizations.
"""

from typing import List, Dict, Any
import streamlit as st
import config
from utils.helpers import clean_html


def render_alarm_panel(
    overall_status: str,
    active_alarms: List[Dict[str, Any]],
    mode: str
):
    """
    Render industrial alarm matrix and active alarms list in a single clean HTML DOM block.
    """
    num_alarms = sum(1 for a in active_alarms if a.get("severity") == "ALARM")
    num_warnings = sum(1 for a in active_alarms if a.get("severity") == "WARNING")
    num_normal = 4 - (num_alarms + num_warnings)  # 4 process loops

    # Build rows HTML if alarms exist
    if active_alarms:
        rows_html = ""
        for a in active_alarms:
            sev = a.get("severity", "NORMAL")
            if sev == "ALARM":
                sev_badge = '<span style="background: #ef4444; color: #ffffff; padding: 2px 8px; border-radius: 3px; font-weight: 800; font-size: 0.7rem;">ALARM</span>'
            elif sev == "WARNING":
                sev_badge = '<span style="background: #f59e0b; color: #000000; padding: 2px 8px; border-radius: 3px; font-weight: 800; font-size: 0.7rem;">WARNING</span>'
            else:
                sev_badge = '<span style="background: #64748b; color: #ffffff; padding: 2px 8px; border-radius: 3px; font-weight: 700; font-size: 0.7rem;">OFFLINE</span>'

            tag = a.get("tag", "--")
            cat = '<span style="color: #38bdf8;">COMM LINK</span>' if "COMM" in tag else '<span style="color: #e2e8f0;">PROCESS</span>'

            rows_html += f"""
<tr>
<td style="font-family: {config.FONT_MONO};">{a.get('time', '--')}</td>
<td>{sev_badge}</td>
<td>{cat}</td>
<td style="font-family: {config.FONT_MONO}; font-weight: 700;">{tag}</td>
<td>{a.get('param', '--')}</td>
<td style="font-family: {config.FONT_MONO}; font-weight: 700; color: {a.get('color', '#fff')};">{a.get('value', '--')}</td>
<td style="font-family: {config.FONT_MONO}; color: #94a3b8;">{a.get('limit', '--')}</td>
<td>{a.get('msg', '--')}</td>
</tr>
"""
        content_section = f"""
<div style="overflow-x: auto;">
<table class="alarm-table">
<thead>
<tr>
<th>TIME</th>
<th>SEVERITY</th>
<th>CLASS</th>
<th>TAG</th>
<th>PARAMETER</th>
<th>READING</th>
<th>LIMIT</th>
<th>ANNUNCIATION MESSAGE</th>
</tr>
</thead>
<tbody>
{rows_html}
</tbody>
</table>
</div>
"""
    else:
        content_section = """
<div style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: 6px; padding: 12px 16px; display: flex; align-items: center; gap: 10px;">
<span class="led-dot led-green"></span>
<span style="font-size: 0.85rem; color: #34d399; font-weight: 600;">All monitored parameters and communication links operating within nominal limits. Zero active alarms.</span>
</div>
"""

    demo_section = ""
    if mode == "DEMO":
        demo_section = """
<div style="margin-top: 10px; font-size: 0.72rem; color: #38bdf8; background: rgba(14, 165, 233, 0.08); border-left: 3px solid #0284c7; padding: 6px 10px; border-radius: 0 4px 4px 0;">
ℹ️ <strong>DEMO MODE NOTICE:</strong> Alarms are driven by simulated process physics for UI validation. Does not represent actual live hardware.
</div>
"""

    panel_html = f"""
<div class="scada-panel">
<div class="scada-panel-title">
<span>🚨 ALARM & ANNUNCIATION MANAGEMENT</span>
<span style="font-family: {config.FONT_MONO}; font-size: 0.72rem; color: #64748b; margin-left: auto;">ANNUNCIATOR RACK 01</span>
</div>
<div style="display: flex; gap: 12px; margin-bottom: 14px; flex-wrap: wrap;">
<div style="flex: 1; min-width: 130px; background: rgba(239, 68, 68, 0.12); border: 1px solid rgba(239, 68, 68, 0.4); border-radius: 6px; padding: 8px 12px; display: flex; align-items: center; justify-content: space-between;">
<span style="font-size: 0.78rem; font-weight: 700; color: #f87171;">CRITICAL ALARMS</span>
<span style="font-family: {config.FONT_MONO}; font-size: 1.25rem; font-weight: 800; color: #f87171;">{num_alarms}</span>
</div>
<div style="flex: 1; min-width: 130px; background: rgba(245, 158, 11, 0.12); border: 1px solid rgba(245, 158, 11, 0.4); border-radius: 6px; padding: 8px 12px; display: flex; align-items: center; justify-content: space-between;">
<span style="font-size: 0.78rem; font-weight: 700; color: #fbbf24;">PROCESS WARNINGS</span>
<span style="font-family: {config.FONT_MONO}; font-size: 1.25rem; font-weight: 800; color: #fbbf24;">{num_warnings}</span>
</div>
<div style="flex: 1; min-width: 130px; background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.4); border-radius: 6px; padding: 8px 12px; display: flex; align-items: center; justify-content: space-between;">
<span style="font-size: 0.78rem; font-weight: 700; color: #34d399;">HEALTHY LOOPS</span>
<span style="font-family: {config.FONT_MONO}; font-size: 1.25rem; font-weight: 800; color: #34d399;">{max(0, num_normal)}</span>
</div>
</div>
{content_section}
{demo_section}
<div style="margin-top: 8px; font-size: 0.70rem; color: #64748b; font-style: italic;">
Disclaimer: Academic digital twin interface. Alarm logic is designed for academic demonstration and supervisory monitoring; not certified for safety-critical emergency shutdown (ESD) systems.
</div>
</div>
"""
    st.markdown(clean_html(panel_html), unsafe_allow_html=True)
