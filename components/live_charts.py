"""
Live Real-Time Plotly Charts Component.
Renders 3 distinct SCADA trend charts with rolling time windows,
subtle gridlines, industrial dark palettes, threshold limit indicators, and hover tooltips.
"""

from typing import Dict, Any
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import config


def render_live_charts(
    history_df: pd.DataFrame,
    window_seconds: int,
    thresholds: Dict[str, float]
):
    """
    Render 3 separate real-time trend charts:
    1. Outlet Temperature Trend (°C)
    2. Flow Rate Trend (L/min)
    3. Burner Power Trend (kW)
    """
    if history_df.empty or len(history_df) < 2:
        st.markdown(
            f"""
            <div style="background: {config.COLOR_BG_CARD}; border: 1px dashed {config.COLOR_BORDER}; border-radius: 8px; padding: 30px; text-align: center; color: #94a3b8;">
                <span style="font-size: 1.5rem;">📊</span>
                <p style="margin: 8px 0 0 0; font-size: 0.9rem;">Awaiting telemetry data to plot trends... (Buffer accumulating)</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        return

    # Filter to rolling time window
    df_plot = _filter_window(history_df, window_seconds)
    if df_plot.empty:
        df_plot = history_df.tail(30)

    # Threshold limits
    t_out_warn = thresholds.get("outlet_high_warn", config.DEFAULT_OUTLET_HIGH_WARN)
    t_out_alarm = thresholds.get("outlet_high_alarm", config.DEFAULT_OUTLET_HIGH_ALARM)
    flow_warn = thresholds.get("flow_low_warn", config.DEFAULT_FLOW_LOW_WARN)
    power_warn = thresholds.get("burner_high_warn", config.DEFAULT_BURNER_HIGH_WARN)

    # 1. Outlet Temperature Trend Chart (Full Width for high-resolution thermal inspection)
    fig_temp = _build_temperature_chart(df_plot, t_out_warn, t_out_alarm)
    st.plotly_chart(fig_temp, use_container_width=True, config=_plotly_config())

    # 2. Flow Rate and Burner Power (Side-by-Side 2 columns)
    col_flow, col_power = st.columns(2)

    with col_flow:
        fig_flow = _build_flow_chart(df_plot, flow_warn)
        st.plotly_chart(fig_flow, use_container_width=True, config=_plotly_config())

    with col_power:
        fig_power = _build_power_chart(df_plot, power_warn)
        st.plotly_chart(fig_power, use_container_width=True, config=_plotly_config())


def _filter_window(df: pd.DataFrame, window_seconds: int) -> pd.DataFrame:
    """Filter records within the rolling time window."""
    if "Timestamp" not in df.columns or df.empty:
        return df

    try:
        # Convert to datetime if string
        if not pd.api.types.is_datetime64_any_dtype(df["Timestamp"]):
            ts_series = pd.to_datetime(df["Timestamp"])
        else:
            ts_series = df["Timestamp"]

        latest_time = ts_series.max()
        cutoff = latest_time - pd.Timedelta(seconds=window_seconds)
        mask = ts_series >= cutoff
        return df.loc[mask]
    except Exception:
        # Fallback to tail
        return df.tail(window_seconds)


def _plotly_config():
    """Optimized Plotly configuration for industrial SCADA performance."""
    return {
        "displayModeBar": True,
        "displaylogo": False,
        "modeBarButtonsToRemove": [
            "lasso2d",
            "select2d",
            "zoomIn2d",
            "zoomOut2d",
            "autoScale2d"
        ],
        "responsive": True
    }


def _common_layout(title: str, y_title: str, y_range=None) -> dict:
    """Standardized dark SCADA styling for all trend charts."""
    return dict(
        title=dict(
            text=f"<b>{title}</b>",
            font=dict(family=config.FONT_SANS, size=13, color="#f1f5f9"),
            x=0.01,
            y=0.96
        ),
        paper_bgcolor="rgba(18, 26, 41, 0.95)",
        plot_bgcolor="#0b101b",
        margin=dict(l=45, r=20, t=38, b=32),
        height=270,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=0.99,
            font=dict(family=config.FONT_SANS, size=10, color="#94a3b8"),
            bgcolor="rgba(0,0,0,0)"
        ),
        xaxis=dict(
            title="",
            showgrid=True,
            gridcolor="#1e293b",
            gridwidth=1,
            tickfont=dict(family=config.FONT_MONO, size=10, color="#94a3b8"),
            linecolor="#334155"
        ),
        yaxis=dict(
            title=dict(
                text=y_title,
                font=dict(family=config.FONT_SANS, size=11, color="#94a3b8")
            ),
            showgrid=True,
            gridcolor="#1e293b",
            gridwidth=1,
            tickfont=dict(family=config.FONT_MONO, size=10, color="#94a3b8"),
            linecolor="#334155",
            range=y_range
        ),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="#0f172a",
            bordercolor="#334155",
            font=dict(family=config.FONT_MONO, size=11, color="#f8fafc")
        )
    )


def _build_temperature_chart(df: pd.DataFrame, warn_val: float, alarm_val: float) -> go.Figure:
    """Chart 1: Outlet Temperature Trend (+ Heat Cell reference)."""
    fig = go.Figure()

    # Outlet Temperature Main Trace
    fig.add_trace(go.Scatter(
        x=df["Timestamp"],
        y=df["Outlet_Temp"],
        name="Outlet Temp (TT-101)",
        mode="lines",
        line=dict(color=config.COLOR_OUTLET_TEMP, width=2.4),
        hovertemplate="%{y:.2f} °C"
    ))

    # Heat Cell Temperature Reference Trace (subtle dashed trace)
    if "Heat_Cell_Temp" in df.columns:
        fig.add_trace(go.Scatter(
            x=df["Timestamp"],
            y=df["Heat_Cell_Temp"],
            name="Heat Cell (TT-102)",
            mode="lines",
            line=dict(color="#a855f7", width=1.5, dash="dash"),
            hovertemplate="%{y:.2f} °C",
            opacity=0.85
        ))

    # Threshold horizontal lines
    fig.add_hline(
        y=warn_val,
        line=dict(color=config.COLOR_WARNING, width=1.2, dash="dot"),
        annotation_text=f"HI WARN ({warn_val:.0f}°C)",
        annotation_position="top right",
        annotation_font=dict(size=9, color=config.COLOR_WARNING)
    )

    fig.add_hline(
        y=alarm_val,
        line=dict(color=config.COLOR_ALARM, width=1.5, dash="dash"),
        annotation_text=f"HI-HI ALARM ({alarm_val:.0f}°C)",
        annotation_position="top right",
        annotation_font=dict(size=9, color=config.COLOR_ALARM)
    )

    y_min = max(0.0, df["Outlet_Temp"].min() - 5.0)
    y_max = max(alarm_val + 5.0, df["Outlet_Temp"].max() + 5.0)

    fig.update_layout(_common_layout(
        title="CHART 1: OUTLET TEMPERATURE TREND",
        y_title="Temperature (°C)",
        y_range=[y_min, y_max]
    ))

    return fig


def _build_flow_chart(df: pd.DataFrame, warn_low: float) -> go.Figure:
    """Chart 2: Flow Rate Trend."""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["Timestamp"],
        y=df["Flow_Rate"],
        name="Flow Rate (FT-101)",
        mode="lines",
        line=dict(color=config.COLOR_FLOW_RATE, width=2.2),
        fill="tozeroy",
        fillcolor="rgba(6, 182, 212, 0.08)",
        hovertemplate="%{y:.2f} L/min"
    ))

    # Flow switch threshold line (1.8 L/min)
    fig.add_hline(
        y=config.FLOW_SWITCH_TRIP,
        line=dict(color="#f43f5e", width=1.2, dash="dot"),
        annotation_text="SWITCH TRIP (1.8 L/min)",
        annotation_position="bottom right",
        annotation_font=dict(size=9, color="#f43f5e")
    )

    # Low flow warning line
    fig.add_hline(
        y=warn_low,
        line=dict(color=config.COLOR_WARNING, width=1.0, dash="dash"),
        annotation_text=f"LOW WARN ({warn_low:.1f} L/min)",
        annotation_position="top right",
        annotation_font=dict(size=9, color=config.COLOR_WARNING)
    )

    y_max = max(10.0, df["Flow_Rate"].max() + 2.0)

    fig.update_layout(_common_layout(
        title="CHART 2: FLOW RATE TREND",
        y_title="Flow Rate (L/min)",
        y_range=[0.0, y_max]
    ))

    return fig


def _build_power_chart(df: pd.DataFrame, warn_val: float) -> go.Figure:
    """Chart 3: Burner Power Trend."""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["Timestamp"],
        y=df["Burner_Power"],
        name="Burner Thermal Power (PT-101)",
        mode="lines",
        line=dict(color=config.COLOR_BURNER_POWER, width=2.2),
        fill="tozeroy",
        fillcolor="rgba(249, 115, 22, 0.08)",
        hovertemplate="%{y:.2f} kW"
    ))

    # High warning threshold
    fig.add_hline(
        y=warn_val,
        line=dict(color=config.COLOR_WARNING, width=1.2, dash="dash"),
        annotation_text=f"HI WARN ({warn_val:.0f} kW)",
        annotation_position="top right",
        annotation_font=dict(size=9, color=config.COLOR_WARNING)
    )

    y_max = max(28.0, df["Burner_Power"].max() + 3.0)

    fig.update_layout(_common_layout(
        title="CHART 3: BURNER POWER TREND",
        y_title="Burner Power (kW)",
        y_range=[0.0, y_max]
    ))

    return fig
