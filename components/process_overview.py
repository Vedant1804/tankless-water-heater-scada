"""
Industrial Process Overview Component.
Renders an interactive, vector-accurate SCADA Process Flow Schematic (PFD)
representing the exact physical layout of the Simulink digital model:
Water Flow -> Flow Switch -> Burner / Ignition -> Heat Cell -> Pipe -> Outlet Temp Sensor.
Supports waiting states in LIVE mode when awaiting ESP32 packets.
"""

from typing import Dict, Any, Optional
import streamlit as st
import config
from utils.helpers import format_value, clean_html


def render_process_overview(data: Optional[Dict[str, Any]], mode: str = "DEMO"):
    """
    Render vector-based industrial schematic with dynamic live readings and component states.
    In LIVE mode without packets, displays clean waiting indicators rather than fake data.
    """
    has_data = data is not None

    if has_data:
        t_out = data.get("outlet_temp")
        flow = data.get("flow_rate", 0.0)
        power = data.get("burner_power", 0.0)
        t_cell = data.get("heat_cell_temp")

        # Flow switch status
        flow_active = flow >= config.FLOW_SWITCH_TRIP
        fs_color = config.COLOR_NORMAL if flow_active else "#64748b"
        fs_label = "CLOSED (FLOW OK)" if flow_active else "OPEN (NO FLOW)"
        fs_stroke = "#10b981" if flow_active else "#475569"

        # Burner status
        burner_active = power > 0.1
        flame_display = "block" if burner_active else "none"
        burner_border = "#f97316" if burner_active else "#334155"
        burner_label = "FIRING ACTIVE" if burner_active else "OFF (STANDBY)"
        burner_status_color = "#f97316" if burner_active else "#64748b"

        # Heat cell color mapping
        norm_temp = max(0.0, min(1.0, ((t_cell or 20.0) - 20.0) / 60.0))
        cell_glow = f"rgba({int(30 + norm_temp * 210)}, {int(58 + (1 - norm_temp) * 60)}, {int(138 - norm_temp * 100)}, 0.45)"

        # Outlet temp status color
        if t_out is not None and t_out >= config.DEFAULT_OUTLET_HIGH_ALARM:
            t_out_color = config.COLOR_ALARM
        elif t_out is not None and t_out >= config.DEFAULT_OUTLET_HIGH_WARN:
            t_out_color = config.COLOR_WARNING
        else:
            t_out_color = config.COLOR_OUTLET_TEMP

        anim_duration = "1.5s" if flow > 4.0 else ("2.8s" if flow > 1.0 else "0s")
        anim_opacity = "1" if flow > 0.1 else "0"

        flow_str = f"{format_value(flow, 2)} L/min"
        power_str = f"{format_value(power, 2)} kW"
        cell_str = f"{format_value(t_cell, 2)} °C"
        outlet_str = f"{format_value(t_out, 2)} °C"
        status_tag = "SIMULINK DIGITAL MODEL" if mode == "DEMO" else "LIVE ESP32 TELEMETRY"
        tag_color = "#38bdf8" if mode == "DEMO" else "#34d399"

    else:
        # WAITING STATE (Live mode before UDP packet arrival)
        t_out = None
        flow = 0.0
        power = 0.0
        t_cell = None

        flow_active = False
        fs_color = "#f59e0b"
        fs_label = "AWAITING ESP32"
        fs_stroke = "#475569"

        burner_active = False
        flame_display = "none"
        burner_border = "#334155"
        burner_label = "STANDBY / AWAITING DATA"
        burner_status_color = "#64748b"
        cell_glow = "rgba(30, 41, 59, 0.4)"
        t_out_color = "#64748b"

        anim_duration = "0s"
        anim_opacity = "0"

        flow_str = "-- L/min"
        power_str = "-- kW"
        cell_str = "-- °C"
        outlet_str = "-- °C"
        status_tag = "WAITING FOR ESP32 (UDP: 5005)"
        tag_color = "#fbbf24"

    svg_schematic = f"""
<div class="scada-panel">
<div class="scada-panel-title">
<span>🏭 DIGITAL PROCESS SCHEMATIC • HEAT CELL & SENSING TRAIN</span>
<span style="font-family: {config.FONT_MONO}; font-size: 0.72rem; color: {tag_color}; margin-left: auto;">{status_tag}</span>
</div>
<div class="pfd-container">
<svg viewBox="0 0 1000 320" width="100%" height="100%" style="overflow: visible;" xmlns="http://www.w3.org/2000/svg">
<defs>
<linearGradient id="pipeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
<stop offset="0%" stop-color="#0284c7" stop-opacity="0.8" />
<stop offset="30%" stop-color="#0284c7" stop-opacity="0.8" />
<stop offset="60%" stop-color="#ea580c" stop-opacity="0.8" />
<stop offset="100%" stop-color="#e11d48" stop-opacity="0.9" />
</linearGradient>
<radialGradient id="heatCellCore" cx="50%" cy="50%" r="60%">
<stop offset="0%" stop-color="#f97316" stop-opacity="0.9" />
<stop offset="60%" stop-color="#ea580c" stop-opacity="0.6" />
<stop offset="100%" stop-color="#431407" stop-opacity="0.8" />
</radialGradient>
<radialGradient id="flameGrad" cx="50%" cy="80%" r="70%">
<stop offset="0%" stop-color="#fef08a" />
<stop offset="35%" stop-color="#f97316" />
<stop offset="80%" stop-color="#dc2626" />
<stop offset="100%" stop-color="#7f1d1d" stop-opacity="0.2" />
</radialGradient>
<marker id="flowArrow" markerWidth="6" markerHeight="6" refX="4" refY="3" orient="auto">
<polygon points="0 0, 6 3, 0 6" fill="#38bdf8" />
</marker>
<marker id="hotArrow" markerWidth="6" markerHeight="6" refX="4" refY="3" orient="auto">
<polygon points="0 0, 6 3, 0 6" fill="#f87171" />
</marker>
</defs>
<path d="M 30 160 L 220 160" stroke="#1e293b" stroke-width="26" stroke-linecap="round" fill="none" />
<path d="M 30 160 L 220 160" stroke="#0284c7" stroke-width="14" stroke-linecap="round" fill="none" />
<g opacity="{anim_opacity}">
<path d="M 60 160 L 90 160" stroke="#e0f2fe" stroke-width="4" stroke-dasharray="8 8" marker-end="url(#flowArrow)">
<animate attributeName="stroke-dashoffset" from="32" to="0" dur="{anim_duration}" repeatCount="indefinite" />
</path>
<path d="M 120 160 L 150 160" stroke="#e0f2fe" stroke-width="4" stroke-dasharray="8 8" marker-end="url(#flowArrow)">
<animate attributeName="stroke-dashoffset" from="32" to="0" dur="{anim_duration}" repeatCount="indefinite" />
</path>
</g>
<g transform="translate(30, 80)">
<rect width="120" height="48" rx="6" fill="#0f172a" stroke="#0284c7" stroke-width="1.5" />
<text x="60" y="20" fill="#94a3b8" font-size="10" font-family="{config.FONT_SANS}" font-weight="600" text-anchor="middle">WATER INLET</text>
<text x="60" y="38" fill="#38bdf8" font-size="13" font-family="{config.FONT_MONO}" font-weight="700" text-anchor="middle">Tin: 20.0 °C</text>
</g>
<g transform="translate(220, 105)">
<rect width="130" height="110" rx="6" fill="#0f172a" stroke="{fs_stroke}" stroke-width="1.5" />
<rect width="130" height="24" rx="6" fill="#1e293b" />
<text x="65" y="16" fill="#cbd5e1" font-size="10" font-family="{config.FONT_MONO}" font-weight="700" text-anchor="middle">FLOW SWITCH [FS-101]</text>
<circle cx="65" cy="55" r="18" fill="#1e293b" stroke="{fs_stroke}" stroke-width="2" />
<line x1="65" y1="55" x2="{65 if flow_active else 78}" y2="{40 if flow_active else 44}" stroke="{fs_color}" stroke-width="3" stroke-linecap="round" />
<circle cx="65" cy="55" r="3" fill="#ffffff" />
<text x="65" y="86" fill="{fs_color}" font-size="9" font-family="{config.FONT_SANS}" font-weight="700" text-anchor="middle">{fs_label}</text>
<text x="65" y="102" fill="#00e5ff" font-size="12" font-family="{config.FONT_MONO}" font-weight="700" text-anchor="middle">{flow_str}</text>
</g>
<path d="M 350 160 L 440 160" stroke="#1e293b" stroke-width="26" fill="none" />
<path d="M 350 160 L 440 160" stroke="#0284c7" stroke-width="14" fill="none" />
<g transform="translate(440, 60)">
<rect width="180" height="160" rx="8" fill="#0f172a" stroke="#475569" stroke-width="2" />
<rect width="180" height="24" rx="8" fill="#1e293b" />
<text x="90" y="16" fill="#f8fafc" font-size="10" font-family="{config.FONT_MONO}" font-weight="700" text-anchor="middle">HEAT CELL [HX-101]</text>
<rect x="15" y="32" width="150" height="85" rx="4" fill="{cell_glow}" stroke="#ea580c" stroke-width="1.2" />
<g stroke="#ffffff" stroke-width="2.5" opacity="0.75" fill="none">
<path d="M 25 45 C 45 45, 45 65, 65 65 C 85 65, 85 45, 105 45 C 125 45, 125 65, 145 65" />
<path d="M 25 80 C 45 80, 45 100, 65 100 C 85 100, 85 80, 105 80 C 125 80, 125 100, 145 100" />
</g>
<rect x="25" y="122" width="130" height="28" rx="4" fill="#0b0f19" stroke="#334155" />
<text x="90" y="134" fill="#94a3b8" font-size="8" font-family="{config.FONT_SANS}" font-weight="600" text-anchor="middle">CELL CORE TEMP</text>
<text x="90" y="146" fill="#a855f7" font-size="12" font-family="{config.FONT_MONO}" font-weight="700" text-anchor="middle">{cell_str}</text>
</g>
<g transform="translate(440, 230)">
<rect width="180" height="75" rx="6" fill="#0f172a" stroke="{burner_border}" stroke-width="1.5" />
<rect width="180" height="20" rx="6" fill="#1e293b" />
<text x="90" y="14" fill="#fed7aa" font-size="9" font-family="{config.FONT_MONO}" font-weight="700" text-anchor="middle">BURNER / IGNITION [BN-101]</text>
<g style="display: {flame_display};" transform="translate(55, -22)">
<path d="M 15 25 Q 5 10 15 0 Q 25 10 15 25" fill="url(#flameGrad)">
<animate attributeName="d" values="M 15 25 Q 5 10 15 0 Q 25 10 15 25; M 15 25 Q 8 8 16 -3 Q 23 8 15 25; M 15 25 Q 5 10 15 0 Q 25 10 15 25" dur="0.4s" repeatCount="indefinite" />
</path>
<path d="M 35 25 Q 25 8 35 -4 Q 45 8 35 25" fill="url(#flameGrad)">
<animate attributeName="d" values="M 35 25 Q 25 8 35 -4 Q 45 8 35 25; M 35 25 Q 28 5 36 -1 Q 42 6 35 25; M 35 25 Q 25 8 35 -4 Q 45 8 35 25" dur="0.35s" repeatCount="indefinite" />
</path>
<path d="M 55 25 Q 45 10 55 0 Q 65 10 55 25" fill="url(#flameGrad)">
<animate attributeName="d" values="M 55 25 Q 45 10 55 0 Q 65 10 55 25; M 55 25 Q 48 8 56 -3 Q 63 8 55 25; M 55 25 Q 45 10 55 0 Q 65 10 55 25" dur="0.45s" repeatCount="indefinite" />
</path>
</g>
<text x="90" y="38" fill="{burner_status_color}" font-size="9" font-family="{config.FONT_SANS}" font-weight="700" text-anchor="middle">{burner_label}</text>
<text x="90" y="58" fill="#f97316" font-size="14" font-family="{config.FONT_MONO}" font-weight="700" text-anchor="middle">{power_str}</text>
</g>
<g stroke="#f97316" stroke-width="2" stroke-dasharray="3 3" opacity="{1.0 if burner_active else 0.2}">
<line x1="480" y1="230" x2="480" y2="220" />
<line x1="530" y1="230" x2="530" y2="220" />
<line x1="580" y1="230" x2="580" y2="220" />
</g>
<path d="M 620 160 L 760 160" stroke="#1e293b" stroke-width="26" fill="none" />
<path d="M 620 160 L 760 160" stroke="#ea580c" stroke-width="14" fill="none" />
<g opacity="{anim_opacity}">
<path d="M 640 160 L 680 160" stroke="#ffedd5" stroke-width="4" stroke-dasharray="8 8" marker-end="url(#hotArrow)">
<animate attributeName="stroke-dashoffset" from="32" to="0" dur="{anim_duration}" repeatCount="indefinite" />
</path>
<path d="M 700 160 L 740 160" stroke="#ffedd5" stroke-width="4" stroke-dasharray="8 8" marker-end="url(#hotArrow)">
<animate attributeName="stroke-dashoffset" from="32" to="0" dur="{anim_duration}" repeatCount="indefinite" />
</path>
</g>
<g transform="translate(640, 110)">
<rect width="80" height="24" rx="4" fill="#0f172a" stroke="#334155" />
<text x="40" y="16" fill="#94a3b8" font-size="9" font-family="{config.FONT_MONO}" text-anchor="middle">PIPE [PP-101]</text>
</g>
<g transform="translate(760, 95)">
<rect width="130" height="125" rx="6" fill="#0f172a" stroke="{t_out_color}" stroke-width="1.8" />
<rect width="130" height="24" rx="6" fill="#1e293b" />
<text x="65" y="16" fill="#cbd5e1" font-size="9" font-family="{config.FONT_MONO}" font-weight="700" text-anchor="middle">OUTLET SENSOR [TT-101]</text>
<rect x="61" y="24" width="8" height="42" fill="#94a3b8" rx="2" />
<circle cx="65" cy="65" r="7" fill="{t_out_color}" />
<text x="65" y="88" fill="#94a3b8" font-size="9" font-family="{config.FONT_SANS}" font-weight="600" text-anchor="middle">OUTLET FLUID TEMP</text>
<text x="65" y="112" fill="{t_out_color}" font-size="15" font-family="{config.FONT_MONO}" font-weight="700" text-anchor="middle">{outlet_str}</text>
</g>
<path d="M 890 160 L 970 160" stroke="#1e293b" stroke-width="26" stroke-linecap="round" fill="none" />
<path d="M 890 160 L 970 160" stroke="#e11d48" stroke-width="14" stroke-linecap="round" fill="none" />
<g transform="translate(895, 80)">
<rect width="90" height="48" rx="6" fill="#0f172a" stroke="#e11d48" stroke-width="1.5" />
<text x="45" y="20" fill="#94a3b8" font-size="9" font-family="{config.FONT_SANS}" font-weight="600" text-anchor="middle">HOT WATER</text>
<text x="45" y="38" fill="#f43f5e" font-size="12" font-family="{config.FONT_MONO}" font-weight="700" text-anchor="middle">DISCHARGE</text>
</g>
</svg>
</div>
</div>
"""
    st.markdown(clean_html(svg_schematic), unsafe_allow_html=True)
