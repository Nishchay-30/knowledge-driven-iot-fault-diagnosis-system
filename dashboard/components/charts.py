"""
Plotly Chart Components for Industrial Monitoring.
Dark theme styling matching industrial SCADA / APM dashboards.
"""

from typing import List, Optional
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


CHART_LAYOUT_DEFAULTS = dict(
    template="plotly_dark",
    paper_bgcolor="#0d1117",
    plot_bgcolor="#161b22",
    margin=dict(l=40, r=30, t=40, b=40),
    font=dict(color="#f0f6fc", family="Inter, -apple-system, sans-serif"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)


def create_live_telemetry_chart(df: pd.DataFrame) -> go.Figure:
    """Creates a 4-row synchronized time-series subplot for Temp, Vibration, Current, RPM."""
    if df.empty:
        fig = go.Figure()
        fig.update_layout(**CHART_LAYOUT_DEFAULTS, title="No Telemetry Data Available")
        return fig

    # Ensure timestamp conversion
    timestamps = pd.to_datetime(
    df["timestamp"],
    format="ISO8601",
    utc=True,
    errors="coerce"
)

    fig = make_subplots(
        rows=4,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.06,
        subplot_titles=(
            "Temperature (°C)",
            "Vibration RMS (g)",
            "Motor Current (A)",
            "Speed (RPM)",
        ),
    )

    # 1. Temperature
    fig.add_trace(
        go.Scatter(
            x=timestamps,
            y=df["temperature_c"],
            mode="lines",
            name="Temperature",
            line=dict(color="#f85149", width=2),
        ),
        row=1,
        col=1,
    )

    # 2. Vibration
    fig.add_trace(
        go.Scatter(
            x=timestamps,
            y=df["vibration_rms_g"],
            mode="lines",
            name="Vibration",
            line=dict(color="#39c5bb", width=2),
        ),
        row=2,
        col=1,
    )

    # 3. Current
    fig.add_trace(
        go.Scatter(
            x=timestamps,
            y=df["current_a"],
            mode="lines",
            name="Current",
            line=dict(color="#d29922", width=2),
        ),
        row=3,
        col=1,
    )

    # 4. RPM
    fig.add_trace(
        go.Scatter(
            x=timestamps,
            y=df["rpm"],
            mode="lines",
            name="RPM",
            line=dict(color="#58a6ff", width=2),
        ),
        row=4,
        col=1,
    )

    layout_config = {
        **CHART_LAYOUT_DEFAULTS,
        "height": 650,
        "showlegend": False,
    }
    fig.update_layout(**layout_config)
    return fig


def create_gauge(
    value: float,
    min_val: float,
    max_val: float,
    title: str,
    unit: str,
    warning_thresh: float,
    crit_thresh: float,
) -> go.Figure:
    """Builds a circular gauge indicator with consolidated layout and ordered threshold zones."""
    # Handle both normal thresholds (higher is worse) and inverted thresholds (lower is worse, e.g. RPM)
    if warning_thresh < crit_thresh:
        # Standard: Normal [min -> warn], Warning [warn -> crit], Critical [crit -> max]
        steps = [
            {"range": [min_val, warning_thresh], "color": "rgba(63, 185, 80, 0.25)"},
            {"range": [warning_thresh, crit_thresh], "color": "rgba(210, 153, 34, 0.35)"},
            {"range": [crit_thresh, max_val], "color": "rgba(248, 81, 73, 0.45)"},
        ]
    else:
        # Inverted (e.g. RPM): Critical [min -> crit], Warning [crit -> warn], Normal [warn -> max]
        steps = [
            {"range": [min_val, crit_thresh], "color": "rgba(248, 81, 73, 0.45)"},
            {"range": [crit_thresh, warning_thresh], "color": "rgba(210, 153, 34, 0.35)"},
            {"range": [warning_thresh, max_val], "color": "rgba(63, 185, 80, 0.25)"},
        ]

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            title={"text": f"{title} ({unit})", "font": {"size": 15, "color": "#8b949e"}},
            number={"suffix": f" {unit}", "font": {"size": 22, "color": "#f0f6fc"}},
            gauge={
                "axis": {"range": [min_val, max_val], "tickcolor": "#8b949e"},
                "bar": {"color": "#58a6ff"},
                "bgcolor": "#161b22",
                "borderwidth": 1,
                "bordercolor": "#30363d",
                "steps": steps,
            },
        )
    )

    # Consolidate layout configuration: override defaults in dict to guarantee single 'margin' argument
    gauge_layout = {
        **CHART_LAYOUT_DEFAULTS,
        "height": 180,
        "margin": dict(l=20, r=20, t=30, b=10),
    }
    fig.update_layout(**gauge_layout)
    return fig


def create_confusion_matrix_heatmap(labels: List[str], matrix: List[List[int]]) -> go.Figure:
    """Renders confusion matrix heatmap."""
    fig = go.Figure(
        data=go.Heatmap(
            z=matrix,
            x=labels,
            y=labels,
            colorscale="Blues",
            showscale=True,
            text=matrix,
            texttemplate="%{text}",
            textfont={"size": 12, "color": "white"},
        )
    )
    heatmap_layout = {
        **CHART_LAYOUT_DEFAULTS,
        "title": "Confusion Matrix (Evaluation Holdout Set)",
        "xaxis_title": "Predicted Label",
        "yaxis_title": "True Ground-Truth Label",
        "height": 450,
    }
    fig.update_layout(**heatmap_layout)
    return fig

