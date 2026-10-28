"""
Top Industrial KPI Cards Component.
Renders four high-density, premium SCADA metric cards with live values,
engineering units, visual range indicators, alarm state badges, and min/max statistics.
Supports clean waiting states in LIVE mode when awaiting ESP32 packets.
"""

from typing import Dict, Any, List
import pandas as pd
import streamlit as st
import config
from utils.helpers import format_value, clean_html


def render_kpi_cards(
    latest_data: Dict[str, Any],
    history_df: pd.DataFrame,
    thresholds: Dict[str, float],
    mode: str = "DEMO"
):
    """
    Render 4 industrial KPI cards in a 4-column layout.
    """
    col1, col2, col3, col4 = st.columns(4)

    # Fallback default values
    t_out = latest_data.get("outlet_temp") if latest_data else None
    flow = latest_data.get("flow_rate") if latest_data else None
    power = latest_data.get("burner_power") if latest_data else None
    t_cell = latest_data.get("heat_cell_temp") if latest_data else None

    # Thresholds
    t_out_warn = thresholds.get("outlet_high_warn", config.DEFAULT_OUTLET_HIGH_WARN)
    t_out_alarm = thresholds.get("outlet_high_alarm", config.DEFAULT_OUTLET_HIGH_ALARM)
    flow_warn = thresholds.get("flow_low_warn", config.DEFAULT_FLOW_LOW_WARN)
    power_warn = thresholds.get("burner_high_warn", config.DEFAULT_BURNER_HIGH_WARN)
    cell_warn = thresholds.get("heat_cell_high_warn", config.DEFAULT_HEAT_CELL_HIGH_WARN)

    # 1. Outlet Temperature Card
    with col1:
        _render_single_kpi(
            tag=config.TAG_OUTLET_TEMP,
            title="Outlet Temperature",
            icon="🌡️",
            value=t_out,
            unit=config.UNIT_OUTLET_TEMP,
            val_range=config.RANGE_OUTLET_TEMP,
            accent_color=config.COLOR_OUTLET_TEMP,
            warn_high=t_out_warn,
            alarm_high=t_out_alarm,
            history_col="Outlet_Temp" if "Outlet_Temp" in history_df.columns else None,
            history_df=history_df,
            mode=mode
        )

    # 2. Flow Rate Card
    with col2:
        _render_single_kpi(
            tag=config.TAG_FLOW_RATE,
            title="Water Flow Rate",
            icon="💧",
            value=flow,
            unit=config.UNIT_FLOW_RATE,
            val_range=config.RANGE_FLOW_RATE,
            accent_color=config.COLOR_FLOW_RATE,
            warn_low=flow_warn,
            history_col="Flow_Rate" if "Flow_Rate" in history_df.columns else None,
            history_df=history_df,
            mode=mode
        )

    # 3. Burner Power Card
    with col3:
        _render_single_kpi(
            tag=config.TAG_BURNER_POWER,
            title="Burner Thermal Power",
            icon="🔥",
            value=power,
            unit=config.UNIT_BURNER_POWER,
            val_range=config.RANGE_BURNER_POWER,
            accent_color=config.COLOR_BURNER_POWER,
            warn_high=power_warn,
            history_col="Burner_Power" if "Burner_Power" in history_df.columns else None,
            history_df=history_df,
            mode=mode
        )

    # 4. Heat Cell Temperature Card
    with col4:
        _render_single_kpi(
            tag=config.TAG_HEAT_CELL_TEMP,
            title="Heat Cell Temp",
            icon="⚡",
            value=t_cell,
            unit=config.UNIT_HEAT_CELL_TEMP,
            val_range=config.RANGE_HEAT_CELL_TEMP,
            accent_color=config.COLOR_HEAT_CELL_TEMP,
            warn_high=cell_warn,
            history_col="Heat_Cell_Temp" if "Heat_Cell_Temp" in history_df.columns else None,
            history_df=history_df,
            mode=mode
        )


def _render_single_kpi(
    tag: str,
    title: str,
    icon: str,
    value: Any,
    unit: str,
    val_range: tuple,
    accent_color: str,
    history_col: str = None,
    history_df: pd.DataFrame = None,
    warn_high: float = None,
    alarm_high: float = None,
    warn_low: float = None,
    mode: str = "DEMO"
):
    """Generate HTML card for an individual process parameter."""
    min_val, max_val = val_range
    num_val = float(value) if value is not None else None

    # Status detection
    state_badge = '<span style="color: #10b981; font-weight: 600;">● NORMAL</span>'
    border_color = config.COLOR_BORDER
    fill_color = accent_color

    if num_val is not None:
        if alarm_high is not None and num_val >= alarm_high:
            state_badge = '<span style="color: #ef4444; font-weight: 700;">■ ALARM (HI-HI)</span>'
            border_color = "#ef4444"
            fill_color = "#ef4444"
        elif warn_high is not None and num_val >= warn_high:
            state_badge = '<span style="color: #f59e0b; font-weight: 700;">▲ HIGH WARN</span>'
            border_color = "#f59e0b"
            fill_color = "#f59e0b"
        elif warn_low is not None and 0.05 < num_val < warn_low:
            state_badge = '<span style="color: #f59e0b; font-weight: 700;">▼ LOW WARN</span>'
            border_color = "#f59e0b"
            fill_color = "#f59e0b"

        # Percentage for visual range bar
        pct = max(0.0, min(100.0, ((num_val - min_val) / (max_val - min_val)) * 100))
        val_str = format_value(num_val, decimals=2, default="--")
    else:
        if mode == "LIVE":
            state_badge = '<span style="color: #fbbf24; font-weight: 600;">⏳ WAITING FOR ESP32</span>'
        else:
            state_badge = '<span style="color: #64748b;">○ NO DATA</span>'
        pct = 0.0
        val_str = "--"

    # Min/Max in window
    min_str = "--"
    max_str = "--"
    if history_df is not None and not history_df.empty and history_col and history_col in history_df.columns:
        col_series = history_df[history_col].dropna()
        if not col_series.empty:
            min_str = f"{col_series.min():.2f}"
            max_str = f"{col_series.max():.2f}"

    html = f"""
    <div class="kpi-card" style="border-top: 3px solid {accent_color}; border-color: {border_color};">
        <div class="kpi-header">
            <span class="kpi-title">{icon} {title}</span>
            <span class="kpi-tag">{tag}</span>
        </div>
        <div class="kpi-value-container">
            <span class="kpi-value" style="color: {fill_color if num_val is not None else '#64748b'};">{val_str}</span>
            <span class="kpi-unit">{unit}</span>
        </div>
        <div class="kpi-bar-bg">
            <div class="kpi-bar-fill" style="width: {pct:.1f}%; background: {fill_color};"></div>
        </div>
        <div class="kpi-footer">
            <div>{state_badge}</div>
            <div style="font-family: {config.FONT_MONO}; font-size: 0.72rem;">
                MIN: <span style="color: #cbd5e1;">{min_str}</span> | MAX: <span style="color: #cbd5e1;">{max_str}</span>
            </div>
        </div>
    </div>
    """
    st.markdown(clean_html(html), unsafe_allow_html=True)
