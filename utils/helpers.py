"""
Helper functions for SCADA styling, alarm evaluation, and formatting.
"""

from typing import Dict, Any, List, Tuple
from datetime import datetime
import streamlit as st
import config


def clean_html(raw_html: str) -> str:
    """
    Strips leading and trailing whitespace from every line and removes blank lines.
    Guarantees that CommonMark Markdown parsers never mistake indented HTML lines
    or post-blank-line lines for markdown code blocks (<pre><code>).
    """
    if not raw_html:
        return ""
    lines = [line.strip() for line in raw_html.strip().splitlines() if line.strip()]
    return "\n".join(lines)


def evaluate_alarms(
    data: Dict[str, Any],
    comm_status: str,
    mode: str,
    thresholds: Dict[str, float]
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Evaluate process values and communication status against industrial alarm limits.

    Returns:
        (overall_status, active_alarms_list)
        where overall_status is 'NORMAL', 'WARNING', 'ALARM', or 'OFFLINE'
    """
    active_alarms = []

    # 1. Communication & Link Status Checks (LIVE MODE only)
    if mode == "LIVE":
        if comm_status == "COMMUNICATION_LOSS":
            active_alarms.append({
                "time": datetime.now().strftime("%H:%M:%S"),
                "tag": "COMM-01",
                "param": "UDP Telemetry",
                "value": "NO PACKETS",
                "limit": f"> {config.COMM_TIMEOUT_SEC}s",
                "severity": "ALARM",
                "color": config.COLOR_ALARM,
                "msg": "Communication lost with ESP32 gateway"
            })
        elif comm_status == "STALE":
            active_alarms.append({
                "time": datetime.now().strftime("%H:%M:%S"),
                "tag": "COMM-01",
                "param": "UDP Telemetry",
                "value": "DELAYED",
                "limit": f"> {config.COMM_STALE_SEC}s",
                "severity": "WARNING",
                "color": config.COLOR_WARNING,
                "msg": "Telemetry packets arriving with high latency"
            })
        elif comm_status == "WAITING_FOR_DATA":
            active_alarms.append({
                "time": datetime.now().strftime("%H:%M:%S"),
                "tag": "COMM-01",
                "param": "UDP Telemetry",
                "value": "AWAITING",
                "limit": "--",
                "severity": "OFFLINE",
                "color": config.COLOR_OFFLINE,
                "msg": "Listening on UDP socket, awaiting initial datagram"
            })

    if not data:
        overall = "ALARM" if mode == "LIVE" and comm_status == "COMMUNICATION_LOSS" else "OFFLINE"
        return overall, active_alarms

    outlet_temp = data.get("outlet_temp", 0.0)
    flow_rate = data.get("flow_rate", 0.0)
    burner_power = data.get("burner_power", 0.0)
    heat_cell_temp = data.get("heat_cell_temp", 0.0)

    # 2. Outlet Temperature Checks
    hi_alarm = thresholds.get("outlet_high_alarm", config.DEFAULT_OUTLET_HIGH_ALARM)
    hi_warn = thresholds.get("outlet_high_warn", config.DEFAULT_OUTLET_HIGH_WARN)

    if outlet_temp >= hi_alarm:
        active_alarms.append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "tag": config.TAG_OUTLET_TEMP,
            "param": "Outlet Temp",
            "value": f"{outlet_temp:.2f} °C",
            "limit": f">= {hi_alarm:.1f} °C",
            "severity": "ALARM",
            "color": config.COLOR_ALARM,
            "msg": "High-High outlet temperature limit exceeded (Scald Hazard)"
        })
    elif outlet_temp >= hi_warn:
        active_alarms.append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "tag": config.TAG_OUTLET_TEMP,
            "param": "Outlet Temp",
            "value": f"{outlet_temp:.2f} °C",
            "limit": f">= {hi_warn:.1f} °C",
            "severity": "WARNING",
            "color": config.COLOR_WARNING,
            "msg": "High outlet temperature warning threshold reached"
        })

    # 3. Flow Rate Checks
    low_flow_warn = thresholds.get("flow_low_warn", config.DEFAULT_FLOW_LOW_WARN)
    if flow_rate > 0.05 and flow_rate < low_flow_warn:
        active_alarms.append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "tag": config.TAG_FLOW_RATE,
            "param": "Water Flow",
            "value": f"{flow_rate:.2f} L/min",
            "limit": f"< {low_flow_warn:.1f} L/min",
            "severity": "WARNING",
            "color": config.COLOR_WARNING,
            "msg": "Water flow rate below optimal operating threshold"
        })

    # 4. Burner Power Checks
    burner_warn = thresholds.get("burner_high_warn", config.DEFAULT_BURNER_HIGH_WARN)
    if burner_power >= burner_warn:
        active_alarms.append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "tag": config.TAG_BURNER_POWER,
            "param": "Burner Power",
            "value": f"{burner_power:.2f} kW",
            "limit": f">= {burner_warn:.1f} kW",
            "severity": "WARNING",
            "color": config.COLOR_WARNING,
            "msg": "Burner firing at near-maximum thermal capacity"
        })

    # 5. Heat Cell Core Temperature Checks
    cell_warn = thresholds.get("heat_cell_high_warn", config.DEFAULT_HEAT_CELL_HIGH_WARN)
    if heat_cell_temp >= cell_warn:
        active_alarms.append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "tag": config.TAG_HEAT_CELL_TEMP,
            "param": "Heat Cell Temp",
            "value": f"{heat_cell_temp:.2f} °C",
            "limit": f">= {cell_warn:.1f} °C",
            "severity": "WARNING",
            "color": config.COLOR_WARNING,
            "msg": "Heat cell core operating above thermal warning point"
        })

    # Determine overall status
    has_alarm = any(a["severity"] == "ALARM" for a in active_alarms)
    has_warn = any(a["severity"] == "WARNING" for a in active_alarms)

    if has_alarm:
        overall = "ALARM"
    elif has_warn:
        overall = "WARNING"
    elif comm_status in ["OFFLINE", "WAITING_FOR_DATA"] and mode == "LIVE":
        overall = "OFFLINE"
    else:
        overall = "NORMAL"

    return overall, active_alarms


def format_value(val: Any, decimals: int = 2, default: str = "--") -> str:
    """Format numerical value safely with fixed decimals."""
    if val is None:
        return default
    try:
        return f"{float(val):.{decimals}f}"
    except (ValueError, TypeError):
        return default


def inject_custom_css():
    """Inject industrial SCADA dark styling into Streamlit DOM."""
    css_content = f"""
    <style>
        /* Global SCADA Dark Canvas */
        .stApp {{
            background-color: {config.COLOR_BG_PRIMARY};
            color: #e2e8f0;
            font-family: {config.FONT_SANS};
        }}

        /* Remove excessive Streamlit default top padding for dense SCADA feel */
        .main .block-container {{
            padding-top: 1.2rem;
            padding-bottom: 2rem;
            padding-left: 1.5rem;
            padding-right: 1.5rem;
            max-width: 100%;
        }}

        /* Industrial Header Container */
        .scada-header {{
            background: linear-gradient(135deg, #0d1525 0%, #152238 100%);
            border: 1px solid #1e2e4a;
            border-radius: 8px;
            padding: 14px 20px;
            margin-bottom: 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
        }}

        .scada-title-box h1 {{
            font-size: 1.45rem;
            font-weight: 700;
            color: #f8fafc;
            margin: 0;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }}

        .scada-title-box p {{
            font-size: 0.82rem;
            color: #94a3b8;
            margin: 2px 0 0 0;
            letter-spacing: 0.3px;
        }}

        .scada-status-pill {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 700;
            letter-spacing: 1px;
            text-transform: uppercase;
            border: 1px solid;
        }}

        .status-normal {{
            background: rgba(16, 185, 129, 0.12);
            color: #34d399;
            border-color: rgba(16, 185, 129, 0.4);
        }}

        .status-warning {{
            background: rgba(245, 158, 11, 0.15);
            color: #fbbf24;
            border-color: rgba(245, 158, 11, 0.5);
        }}

        .status-alarm {{
            background: rgba(239, 68, 68, 0.18);
            color: #f87171;
            border-color: rgba(239, 68, 68, 0.6);
        }}

        .status-offline {{
            background: rgba(100, 116, 139, 0.15);
            color: #94a3b8;
            border-color: rgba(100, 116, 139, 0.4);
        }}

        /* LED Indicator Dot */
        .led-dot {{
            width: 9px;
            height: 9px;
            border-radius: 50%;
            display: inline-block;
        }}
        .led-green {{ background: #10b981; box-shadow: 0 0 8px #10b981; }}
        .led-amber {{ background: #f59e0b; box-shadow: 0 0 8px #f59e0b; }}
        .led-red {{ background: #ef4444; box-shadow: 0 0 8px #ef4444; }}
        .led-grey {{ background: #64748b; }}

        /* KPI Industrial Card */
        .kpi-card {{
            background: {config.COLOR_BG_CARD};
            border: 1px solid {config.COLOR_BORDER};
            border-radius: 8px;
            padding: 14px 16px;
            position: relative;
            overflow: hidden;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
            transition: border-color 0.2s ease;
        }}
        .kpi-card:hover {{
            border-color: {config.COLOR_BORDER_ACCENT};
        }}

        .kpi-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }}

        .kpi-tag {{
            font-family: {config.FONT_MONO};
            font-size: 0.72rem;
            color: #94a3b8;
            background: rgba(30, 41, 59, 0.7);
            padding: 2px 6px;
            border-radius: 4px;
            border: 1px solid #334155;
        }}

        .kpi-title {{
            font-size: 0.85rem;
            font-weight: 600;
            color: #cbd5e1;
            margin: 0;
        }}

        .kpi-value-container {{
            display: flex;
            align-items: baseline;
            gap: 8px;
            margin: 6px 0 10px 0;
        }}

        .kpi-value {{
            font-family: {config.FONT_MONO};
            font-size: 2.2rem;
            font-weight: 700;
            line-height: 1;
            letter-spacing: -0.5px;
        }}

        .kpi-unit {{
            font-size: 1.05rem;
            font-weight: 500;
            color: #94a3b8;
        }}

        .kpi-footer {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.75rem;
            color: #64748b;
            border-top: 1px solid rgba(255, 255, 255, 0.06);
            padding-top: 8px;
            margin-top: 6px;
        }}

        /* Range Progress Bar */
        .kpi-bar-bg {{
            width: 100%;
            height: 5px;
            background: #1e293b;
            border-radius: 3px;
            overflow: hidden;
            margin-top: 6px;
        }}

        .kpi-bar-fill {{
            height: 100%;
            border-radius: 3px;
            transition: width 0.4s ease;
        }}

        /* Industrial Section Card */
        .scada-panel {{
            background: {config.COLOR_BG_CARD};
            border: 1px solid {config.COLOR_BORDER};
            border-radius: 8px;
            padding: 16px 18px;
            margin-bottom: 16px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
        }}

        .scada-panel-title {{
            font-size: 0.95rem;
            font-weight: 700;
            color: #f1f5f9;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            margin-bottom: 14px;
            display: flex;
            align-items: center;
            gap: 8px;
            border-bottom: 1px solid #1e293b;
            padding-bottom: 8px;
        }}

        /* Process Overview Diagram Canvas */
        .pfd-container {{
            background: radial-gradient(circle at 50% 50%, #152033 0%, #0d1524 100%);
            border: 1px solid #1e304f;
            border-radius: 8px;
            padding: 18px;
            position: relative;
        }}

        /* Industrial Alarm Table */
        .alarm-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.82rem;
        }}
        .alarm-table th {{
            background: #0f172a;
            color: #94a3b8;
            padding: 8px 12px;
            text-align: left;
            font-weight: 600;
            border-bottom: 1px solid #334155;
            text-transform: uppercase;
            font-size: 0.72rem;
            letter-spacing: 0.5px;
        }}
        .alarm-table td {{
            padding: 8px 12px;
            border-bottom: 1px solid #1e293b;
            color: #e2e8f0;
        }}
        .alarm-table tr:hover td {{
            background: #182236;
        }}

        /* Sidebar SCADA styling */
        [data-testid="stSidebar"] {{
            background-color: #0d131f;
            border-right: 1px solid #1e293b;
        }}

        /* Streamlit button custom styles */
        .stButton > button {{
            border-radius: 6px;
            font-weight: 600;
            letter-spacing: 0.3px;
            transition: all 0.2s ease;
        }}
    </style>
    """
    st.markdown(clean_html(css_content), unsafe_allow_html=True)
