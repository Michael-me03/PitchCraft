"""
Chart Engine v2.0 – PitchCraft
==============================
Three best-in-class chart engines for PowerPoint-ready PNG at 1920×1080:

  Engine 1 – PLOTLY     : Primary engine · 17 chart types · "PitchCraft" template
  Engine 2 – MATPLOTLIB : Infographic engine · KPI cards · Progress rings · Glassmorphism
  Engine 3 – ALTAIR     : Statistical engine · Distributions · Box plots · Density plots

All outputs: PNG bytes at configurable resolution (default 1920×1080, 16:9).
Slot-aware rendering: pass render_width/render_height to render_chart() for exact fit.
"""

import io
import math
import threading
from typing import Any

# ── Engine 1: Plotly ────────────────────────────────────────────────────────
import plotly.graph_objects as go
import plotly.io as pio

# ── Engine 2: Matplotlib ────────────────────────────────────────────────────
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from matplotlib.patches import FancyBboxPatch

# ── Engine 3: Altair / Vega-Lite ────────────────────────────────────────────
try:
    import altair as alt
    import pandas as pd
    try:
        import vl_convert as vlc
        _ALTAIR_OK = True
    except ImportError:
        _ALTAIR_OK = False
except ImportError:
    alt = None
    _ALTAIR_OK = False


# ════════════════════════════════════════════════════════════════════
# DESIGN TOKENS
# ════════════════════════════════════════════════════════════════════

DPI  = 200
W_PX = 1920
H_PX = 1080

# Thread-local context: inject slot dimensions into render helpers
_ctx = threading.local()

# Vibrant 10-colour palette (Indigo-first for brand consistency)
PALETTE = [
    "#6366F1",  # Indigo   — primary
    "#06B6D4",  # Cyan
    "#10B981",  # Emerald
    "#F59E0B",  # Amber
    "#EC4899",  # Pink
    "#8B5CF6",  # Violet
    "#3B82F6",  # Blue
    "#EF4444",  # Red
    "#14B8A6",  # Teal
    "#F97316",  # Orange
]

# Semantic tokens
CLR = {
    "positive":  "#10B981",
    "negative":  "#EF4444",
    "neutral":   "#94A3B8",
    "primary":   "#6366F1",
    "highlight": "#F59E0B",
}

# Gray-scale tokens (Tailwind Slate)
G = {
    "bg":     "#FFFFFF",
    "subtle": "#F8FAFC",
    "border": "#E2E8F0",
    "grid":   "#F1F5F9",
    "900":    "#0F172A",
    "700":    "#334155",
    "500":    "#64748B",
    "400":    "#94A3B8",
    "300":    "#CBD5E1",
    "200":    "#E2E8F0",
    "100":    "#F1F5F9",
}

FONT = "Inter, Helvetica Neue, Arial, sans-serif"

# Legacy alias used by older code paths
MPL_PALETTE = {
    "blue":    "#3B82F6",  "cyan":    "#06B6D4",
    "emerald": "#10B981",  "violet":  "#8B5CF6",
    "orange":  "#F59E0B",  "pink":    "#EC4899",
    "indigo":  "#6366F1",  "red":     "#EF4444",
    "slate":   "#64748B",  "dark":    G["900"],
    "body":    G["700"],   "muted":   G["400"],
    "grid":    G["100"],   "white":   "#FFFFFF",
}

_COLOR_MAP = {
    "blue":    PALETTE[6],  "cyan":    PALETTE[1],
    "emerald": PALETTE[2],  "violet":  PALETTE[5],
    "orange":  PALETTE[3],  "pink":    PALETTE[4],
    "indigo":  PALETTE[0],  "red":     PALETTE[7],
    "teal":    PALETTE[8],
}


# ════════════════════════════════════════════════════════════════════
# ENGINE 1 – PLOTLY  ("PitchCraft" custom template)
# ════════════════════════════════════════════════════════════════════

_df_template = go.layout.Template(
    layout=go.Layout(
        font=dict(family=FONT, color=G["700"], size=13),
        paper_bgcolor=G["bg"],
        plot_bgcolor=G["bg"],
        colorway=PALETTE,
        title=dict(
            font=dict(size=22, color=G["900"], family=FONT),
            x=0.02, xanchor="left",
            pad=dict(t=12, b=8),
        ),
        xaxis=dict(
            showgrid=False, zeroline=False,
            linecolor=G["200"], tickcolor=G["300"],
            tickfont=dict(color=G["500"], size=12),
            title_font=dict(color=G["500"], size=12),
        ),
        yaxis=dict(
            gridcolor=G["100"], gridwidth=1,
            zeroline=False, linecolor=G["200"],
            tickcolor=G["300"],
            tickfont=dict(color=G["500"], size=12),
            title_font=dict(color=G["500"], size=12),
        ),
        margin=dict(l=72, r=56, t=108, b=64),
        legend=dict(
            font=dict(size=13, color=G["700"]),
            bgcolor="rgba(0,0,0,0)",
            borderwidth=0,
            orientation="h",
            yanchor="bottom", y=1.06,
            xanchor="right", x=1,
        ),
        hoverlabel=dict(
            bgcolor=G["900"], font_color="white",
            bordercolor=G["900"],
            font=dict(family=FONT, size=13),
        ),
    )
)
pio.templates["pitchcraft"] = _df_template
pio.templates.default = "pitchcraft"


def _hex_rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, gv, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{gv},{b},{alpha})"


def _plotly_to_png(fig: go.Figure) -> bytes:
    """Render Plotly figure at slot-aware dimensions."""
    rw = getattr(_ctx, "render_w", W_PX)
    rh = getattr(_ctx, "render_h", H_PX)
    scale = min(rw / W_PX, rh / H_PX)
    ms = max(0.45, min(1.0, scale))
    fig.update_layout(margin=dict(l=round(72*ms), r=round(56*ms),
                                   t=round(88*ms), b=round(64*ms)))
    return fig.to_image(format="png", width=rw, height=rh, scale=2)


# ── 1.1  Bar Chart ───────────────────────────────────────────────────────────

def bar_chart(
    categories: list[str],
    values: list[float],
    title: str = "",
    ylabel: str = "",
    color_mode: str = "multi",
    value_prefix: str = "",
    value_suffix: str = "",
    horizontal: bool = False,
) -> bytes:
    """Rounded-corner bar chart with value labels above each bar."""
    colors = PALETTE[:len(categories)] if color_mode == "multi" else [PALETTE[0]] * len(categories)

    def fmt(v):
        return (f"{value_prefix}{v:,.1f}{value_suffix}" if v != int(v)
                else f"{value_prefix}{int(v):,}{value_suffix}")
    text = [fmt(v) for v in values]

    if horizontal:
        fig = go.Figure(go.Bar(
            y=categories, x=values, orientation="h",
            marker=dict(color=colors, line=dict(width=0), cornerradius=6),
            text=text, textposition="outside",
            textfont=dict(size=14, color=G["700"], family=FONT),
        ))
        fig.update_layout(
            title=title,
            xaxis=dict(title=ylabel, showgrid=True, gridcolor=G["100"]),
            yaxis=dict(autorange="reversed", showgrid=False),
            showlegend=False, bargap=0.30,
        )
    else:
        max_v = max(values) * 1.18 if values else 1
        fig = go.Figure(go.Bar(
            x=categories, y=values,
            marker=dict(color=colors, line=dict(width=0), cornerradius=6),
            text=text, textposition="outside",
            textfont=dict(size=14, color=G["700"], family=FONT),
        ))
        fig.update_layout(
            title=title,
            yaxis=dict(title=ylabel, range=[0, max_v],
                       showgrid=True, gridcolor=G["100"]),
            xaxis=dict(showgrid=False),
            showlegend=False, bargap=0.35,
        )
    return _plotly_to_png(fig)


# ── 1.2  Line Chart ──────────────────────────────────────────────────────────

def line_chart(
    categories: list[str],
    values: list[float],
    title: str = "",
    ylabel: str = "",
    fill: bool = True,
    smooth: bool = True,
    show_markers: bool = True,
    value_prefix: str = "",
    value_suffix: str = "",
) -> bytes:
    """Smooth spline line with gradient area fill and annotated endpoint."""
    shape = "spline" if smooth else "linear"
    color = PALETTE[0]

    fig = go.Figure(go.Scatter(
        x=categories, y=values,
        mode="lines+markers" if show_markers else "lines",
        line=dict(color=color, width=3.5, shape=shape, smoothing=1.2),
        marker=dict(size=10, color="white", symbol="circle",
                    line=dict(width=2.5, color=color)),
        fill="tozeroy" if fill else None,
        fillcolor=_hex_rgba(color, 0.10),
        hovertemplate=f"%{{x}}<br><b>{value_prefix}%{{y:,.0f}}{value_suffix}</b><extra></extra>",
    ))

    if values:
        last_val = f"{value_prefix}{values[-1]:,.0f}{value_suffix}"
        fig.add_annotation(
            x=categories[-1], y=values[-1],
            text=f"<b>{last_val}</b>",
            showarrow=False, xanchor="left", xshift=14,
            font=dict(size=14, color=color, family=FONT),
        )

    fig.update_layout(
        title=title,
        yaxis=dict(title=ylabel, showgrid=True, gridcolor=G["100"]),
        xaxis=dict(showgrid=False),
        showlegend=False,
    )
    return _plotly_to_png(fig)


# ── 1.3  Multi-Line Chart  (NEW) ─────────────────────────────────────────────

def multi_line_chart(
    categories: list[str],
    series: dict[str, list[float]],
    title: str = "",
    ylabel: str = "",
    smooth: bool = True,
) -> bytes:
    """Multiple line series with distinct colours and open-circle markers."""
    shape = "spline" if smooth else "linear"
    fig = go.Figure()
    for i, (name, vals) in enumerate(series.items()):
        color = PALETTE[i % len(PALETTE)]
        fig.add_trace(go.Scatter(
            x=categories, y=vals, name=name,
            mode="lines+markers",
            line=dict(color=color, width=3, shape=shape, smoothing=1.2),
            marker=dict(size=9, color="white", line=dict(width=2.5, color=color)),
        ))
    fig.update_layout(
        title=title,
        yaxis=dict(title=ylabel, showgrid=True, gridcolor=G["100"]),
        xaxis=dict(showgrid=False),
    )
    return _plotly_to_png(fig)


# ── 1.4  Area Chart  (NEW) ───────────────────────────────────────────────────

def area_chart(
    categories: list[str],
    series: dict[str, list[float]],
    title: str = "",
    ylabel: str = "",
    stacked: bool = False,
) -> bytes:
    """Stacked or overlapping semi-transparent area chart."""
    fig = go.Figure()
    for i, (name, vals) in enumerate(series.items()):
        color = PALETTE[i % len(PALETTE)]
        fig.add_trace(go.Scatter(
            x=categories, y=vals, name=name,
            mode="lines",
            line=dict(color=color, width=2.5),
            fill="tonexty" if (stacked and i > 0) else "tozeroy",
            fillcolor=_hex_rgba(color, 0.38 if stacked else 0.14),
            stackgroup="one" if stacked else None,
        ))
    fig.update_layout(
        title=title,
        yaxis=dict(title=ylabel, showgrid=True, gridcolor=G["100"]),
        xaxis=dict(showgrid=False),
    )
    return _plotly_to_png(fig)


# ── 1.5  Pie / Donut Chart ───────────────────────────────────────────────────

def pie_chart(
    categories: list[str],
    values: list[float],
    title: str = "",
    show_percentage: bool = True,
    donut: bool = False,
    explode_max: bool = False,
) -> bytes:
    """Pie or donut with optional centre-total annotation."""
    pull = [0.0] * len(values)
    if explode_max and values:
        pull[values.index(max(values))] = 0.07

    hole = 0.52 if donut else 0
    textinfo = "percent+label" if show_percentage else "label"

    fig = go.Figure(go.Pie(
        labels=categories, values=values, hole=hole, pull=pull,
        marker=dict(colors=PALETTE[:len(categories)],
                    line=dict(color="white", width=3)),
        textinfo=textinfo,
        textfont=dict(size=14, family=FONT),
        insidetextorientation="radial" if not donut else "auto",
        hovertemplate="<b>%{label}</b><br>%{value:,.0f} (%{percent})<extra></extra>",
    ))

    if donut and values:
        fig.add_annotation(
            text=(f"<b style='font-size:24px'>{sum(values):,.0f}</b>"
                  f"<br><span style='color:{G['500']};font-size:13px'>Total</span>"),
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=18, color=G["900"], family=FONT),
        )

    fig.update_layout(
        title=title, showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.20,
                    xanchor="center", x=0.5),
    )
    return _plotly_to_png(fig)


# ── 1.6  Stacked Bar ─────────────────────────────────────────────────────────

def stacked_bar_chart(
    categories: list[str],
    series: dict[str, list[float]],
    title: str = "",
    ylabel: str = "",
    horizontal: bool = False,
) -> bytes:
    """Stacked bar chart."""
    fig = go.Figure()
    for i, (name, vals) in enumerate(series.items()):
        color = PALETTE[i % len(PALETTE)]
        kw = dict(name=name, marker=dict(color=color, line=dict(width=0), cornerradius=4))
        if horizontal:
            fig.add_trace(go.Bar(y=categories, x=vals, orientation="h", **kw))
        else:
            fig.add_trace(go.Bar(x=categories, y=vals, **kw))
    fig.update_layout(
        barmode="stack", title=title,
        yaxis=dict(title=ylabel, showgrid=True, gridcolor=G["100"]),
        xaxis=dict(showgrid=False),
        bargap=0.28,
    )
    return _plotly_to_png(fig)


# ── 1.7  Grouped Bar ─────────────────────────────────────────────────────────

def grouped_bar_chart(
    categories: list[str],
    series: dict[str, list[float]],
    title: str = "",
    ylabel: str = "",
) -> bytes:
    """Side-by-side grouped bar chart."""
    fig = go.Figure()
    all_vals = [v for vals in series.values() for v in vals]
    max_v = max(all_vals) * 1.20 if all_vals else 1
    for i, (name, vals) in enumerate(series.items()):
        color = PALETTE[i % len(PALETTE)]
        fig.add_trace(go.Bar(
            x=categories, y=vals, name=name,
            marker=dict(color=color, line=dict(width=0), cornerradius=4),
            text=[f"{v:,.0f}" for v in vals],
            textposition="outside",
            textfont=dict(size=11, color=G["700"], family=FONT),
        ))
    fig.update_layout(
        barmode="group", title=title,
        yaxis=dict(title=ylabel, showgrid=True, gridcolor=G["100"], range=[0, max_v]),
        xaxis=dict(showgrid=False),
        bargap=0.24, bargroupgap=0.08,
    )
    return _plotly_to_png(fig)


# ── 1.8  Waterfall ───────────────────────────────────────────────────────────

def waterfall_chart(
    categories: list[str],
    values: list[float],
    title: str = "",
    ylabel: str = "",
    value_prefix: str = "",
    value_suffix: str = "",
) -> bytes:
    """Waterfall chart with colour-coded increase / decrease / total bars."""
    measures = ["absolute"] + ["relative"] * (len(values) - 2) + ["total"]
    text = [f"{value_prefix}{v:,.0f}{value_suffix}" for v in values]

    fig = go.Figure(go.Waterfall(
        x=categories, y=values, measure=measures,
        text=text, textposition="outside",
        textfont=dict(size=13, color=G["700"], family=FONT),
        increasing=dict(marker=dict(color=CLR["positive"], line=dict(width=0))),
        decreasing=dict(marker=dict(color=CLR["negative"], line=dict(width=0))),
        totals=dict(marker=dict(color=PALETTE[0], line=dict(width=0))),
        connector=dict(line=dict(color=G["300"], width=1.5, dash="dot")),
    ))
    fig.update_layout(
        title=title,
        yaxis=dict(title=ylabel, showgrid=True, gridcolor=G["100"]),
        xaxis=dict(showgrid=False),
        showlegend=False,
    )
    return _plotly_to_png(fig)


# ── 1.9  Gauge ───────────────────────────────────────────────────────────────

def gauge_chart(
    value: float,
    max_value: float = 100,
    title: str = "",
    label: str = "",
    suffix: str = "%",
) -> bytes:
    """Gauge with dynamic colour zones and threshold marker."""
    ratio = value / max_value if max_value else 0
    bar_color = (
        CLR["positive"]  if ratio > 0.75 else
        PALETTE[0]       if ratio > 0.50 else
        CLR["highlight"] if ratio > 0.25 else
        CLR["negative"]
    )
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number=dict(suffix=suffix, font=dict(size=60, color=G["900"], family=FONT)),
        title=dict(text=label, font=dict(size=18, color=G["500"], family=FONT)),
        gauge=dict(
            axis=dict(range=[0, max_value], tickcolor=G["300"], tickwidth=1,
                      tickfont=dict(color=G["500"], size=11)),
            bar=dict(color=bar_color, thickness=0.82),
            bgcolor=G["100"], borderwidth=0,
            steps=[
                dict(range=[0,             max_value * 0.25], color="#FEF2F2"),
                dict(range=[max_value * 0.25, max_value * 0.50], color="#FFFBEB"),
                dict(range=[max_value * 0.50, max_value * 0.75], color="#EFF6FF"),
                dict(range=[max_value * 0.75, max_value],        color="#F0FDF4"),
            ],
            threshold=dict(line=dict(color=bar_color, width=4), value=value),
        ),
    ))
    fig.update_layout(title=title, margin=dict(t=80, b=40, l=60, r=60))
    return _plotly_to_png(fig)


# ── 1.10  Radar ──────────────────────────────────────────────────────────────

def radar_chart(
    categories: list[str],
    values: list[float],
    title: str = "",
    max_value: float = 100,
) -> bytes:
    """Radar / spider chart for multi-dimensional profiling."""
    color = PALETTE[0]
    fig = go.Figure(go.Scatterpolar(
        r=values + [values[0]],
        theta=categories + [categories[0]],
        fill="toself",
        fillcolor=_hex_rgba(color, 0.14),
        line=dict(color=color, width=3),
        marker=dict(size=10, color="white", line=dict(width=2.5, color=color)),
    ))
    fig.update_layout(
        title=title,
        polar=dict(
            radialaxis=dict(visible=True, range=[0, max_value],
                            gridcolor=G["200"], linecolor=G["200"],
                            tickfont=dict(size=10, color=G["400"])),
            angularaxis=dict(gridcolor=G["200"], linecolor=G["200"],
                             tickfont=dict(size=13, color=G["700"])),
            bgcolor=G["bg"],
        ),
        showlegend=False,
    )
    return _plotly_to_png(fig)


# ── 1.11  Funnel ─────────────────────────────────────────────────────────────

def funnel_chart(
    stages: list[str],
    values: list[float],
    title: str = "",
) -> bytes:
    """Funnel for conversion / pipeline stages with drop-off percentages."""
    fig = go.Figure(go.Funnel(
        y=stages, x=values,
        textinfo="value+percent initial",
        textfont=dict(size=14, family=FONT),
        marker=dict(color=PALETTE[:len(stages)], line=dict(width=0)),
        connector=dict(line=dict(color=G["200"], width=1)),
        opacity=0.90,
    ))
    fig.update_layout(title=title, showlegend=False, funnelgap=0.06)
    return _plotly_to_png(fig)


# ── 1.12  Treemap ────────────────────────────────────────────────────────────

def treemap_chart(
    categories: list[str],
    values: list[float],
    title: str = "",
) -> bytes:
    """Treemap – hierarchical proportions as nested coloured rectangles."""
    fig = go.Figure(go.Treemap(
        labels=categories, values=values,
        parents=[""] * len(categories),
        marker=dict(colors=PALETTE[:len(categories)],
                    line=dict(width=3, color="white"),
                    pad=dict(t=6, b=6, l=6, r=6)),
        textinfo="label+value+percent parent",
        textfont=dict(size=16, family=FONT),
        hovertemplate="<b>%{label}</b><br>%{value:,.0f} | %{percentParent}<extra></extra>",
    ))
    fig.update_layout(title=title, margin=dict(t=64, b=12, l=12, r=12))
    return _plotly_to_png(fig)


# ── 1.13  Sunburst ───────────────────────────────────────────────────────────

def sunburst_chart(
    categories: list[str],
    values: list[float],
    parents: list[str] = None,
    title: str = "",
) -> bytes:
    """Sunburst – hierarchical data as concentric colour rings."""
    if parents is None:
        parents = [""] * len(categories)
    fig = go.Figure(go.Sunburst(
        labels=categories, values=values, parents=parents,
        marker=dict(colors=PALETTE[:len(categories)],
                    line=dict(width=2, color="white")),
        textfont=dict(size=14, family=FONT),
        branchvalues="total",
        hovertemplate="<b>%{label}</b><br>%{value:,.0f}<extra></extra>",
    ))
    fig.update_layout(title=title, margin=dict(t=64, b=12, l=12, r=12))
    return _plotly_to_png(fig)


# ── 1.14  Heatmap ────────────────────────────────────────────────────────────

def heatmap_chart(
    x_labels: list[str],
    y_labels: list[str],
    values: list[list[float]],
    title: str = "",
) -> bytes:
    """Heatmap with indigo gradient colourscale."""
    colorscale = [
        [0.00, "#F0F9FF"], [0.25, "#BAE6FD"],
        [0.55, "#6366F1"], [0.80, "#4338CA"], [1.00, "#1E1B4B"],
    ]
    fig = go.Figure(go.Heatmap(
        z=values, x=x_labels, y=y_labels,
        colorscale=colorscale,
        texttemplate="%{z:.0f}",
        textfont=dict(size=13, family=FONT),
        hovertemplate="<b>%{y}</b> × <b>%{x}</b><br>%{z:,.1f}<extra></extra>",
        showscale=True,
        colorbar=dict(thickness=20, len=0.72,
                      tickfont=dict(color=G["500"], size=11), outlinewidth=0),
    ))
    fig.update_layout(
        title=title,
        xaxis=dict(showgrid=False, side="bottom", tickfont=dict(size=12)),
        yaxis=dict(showgrid=False, autorange="reversed", tickfont=dict(size=12)),
    )
    return _plotly_to_png(fig)


# ── 1.15  Scatter / Bubble ───────────────────────────────────────────────────

def scatter_chart(
    x_values: list[float],
    y_values: list[float],
    labels: list[str] = None,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    size: list[float] = None,
) -> bytes:
    """Scatter or bubble chart with per-point sizing and labels."""
    marker_size = [max(10, s ** 0.5 * 3.5) for s in size] if size else 14
    colors = PALETTE[:len(x_values)] if size else [PALETTE[0]] * len(x_values)

    fig = go.Figure(go.Scatter(
        x=x_values, y=y_values,
        mode="markers+text" if labels else "markers",
        marker=dict(size=marker_size, color=colors, opacity=0.85,
                    line=dict(width=2, color="white")),
        text=labels, textposition="top center",
        textfont=dict(size=11, color=G["700"], family=FONT),
    ))
    fig.update_layout(
        title=title, xaxis_title=xlabel, yaxis_title=ylabel,
        xaxis=dict(showgrid=True, gridcolor=G["100"]),
        yaxis=dict(showgrid=True, gridcolor=G["100"]),
        showlegend=False,
    )
    return _plotly_to_png(fig)


# ── 1.16  Bullet Chart  (NEW) ────────────────────────────────────────────────

def bullet_chart(
    categories: list[str],
    values: list[float],
    targets: list[float],
    title: str = "",
    value_suffix: str = "",
) -> bytes:
    """Bullet chart: actual vs target with colour-coded bars."""
    fig = go.Figure()
    for i, (cat, val, tgt) in enumerate(zip(categories, values, targets)):
        color = CLR["positive"] if val >= tgt else CLR["negative"]
        max_range = max(val, tgt) * 1.25

        fig.add_trace(go.Bar(
            x=[max_range], y=[i], orientation="h",
            marker=dict(color=G["100"], line=dict(width=0)),
            showlegend=False, hoverinfo="skip", base=0,
        ))
        fig.add_trace(go.Bar(
            x=[val], y=[i], orientation="h",
            marker=dict(color=color, line=dict(width=0), opacity=0.88),
            text=f"  {val:,.0f}{value_suffix}",
            textposition="outside",
            textfont=dict(size=13, color=G["700"]),
            showlegend=False,
        ))
        fig.add_shape(type="line",
                      x0=tgt, x1=tgt, y0=i - 0.40, y1=i + 0.40,
                      line=dict(color=G["900"], width=3.5))
        fig.add_annotation(
            x=tgt, y=i - 0.50, text=f"Target: {tgt:,.0f}{value_suffix}",
            showarrow=False, yanchor="top",
            font=dict(size=10, color=G["400"], family=FONT),
        )

    fig.update_layout(
        title=title, barmode="overlay",
        yaxis=dict(tickvals=list(range(len(categories))),
                   ticktext=categories, showgrid=False, tickfont=dict(size=13)),
        xaxis=dict(showgrid=True, gridcolor=G["100"]),
        showlegend=False, bargap=0.50,
    )
    return _plotly_to_png(fig)


# ── 1.17  Slope Chart  (NEW) ─────────────────────────────────────────────────

def slope_chart(
    categories: list[str],
    before_values: list[float],
    after_values: list[float],
    before_label: str = "Before",
    after_label: str = "After",
    title: str = "",
    value_suffix: str = "",
) -> bytes:
    """Slope chart – before/after comparison across multiple items."""
    fig = go.Figure()
    for i, (cat, bv, av) in enumerate(zip(categories, before_values, after_values)):
        color = CLR["positive"] if av >= bv else CLR["negative"]
        fig.add_trace(go.Scatter(
            x=[before_label, after_label], y=[bv, av],
            mode="lines+markers+text",
            line=dict(color=color, width=2.5),
            marker=dict(size=13, color="white", line=dict(width=2.5, color=color)),
            text=[f"{bv:,.0f}{value_suffix}", f"{av:,.0f}{value_suffix}"],
            textposition=["middle left", "middle right"],
            textfont=dict(size=12, color=G["700"], family=FONT),
            name=cat,
        ))
    fig.update_layout(
        title=title,
        xaxis=dict(showgrid=False, tickfont=dict(size=16, color=G["900"])),
        yaxis=dict(showgrid=True, gridcolor=G["100"]),
    )
    return _plotly_to_png(fig)


# ════════════════════════════════════════════════════════════════════
# ENGINE 2 – MATPLOTLIB  (Infographic / Glassmorphism Cards)
# ════════════════════════════════════════════════════════════════════

def _mpl_reset():
    plt.rcParams.update({
        "font.family":        "sans-serif",
        "font.sans-serif":    ["Inter", "Helvetica Neue", "Helvetica", "Arial"],
        "font.size":          11,
        "axes.spines.top":    False,
        "axes.spines.right":  False,
        "axes.spines.left":   False,
        "axes.spines.bottom": False,
        "figure.facecolor":   "white",
        "figure.dpi":         DPI,
        "savefig.facecolor":  "white",
    })


def _mpl_to_png(fig) -> bytes:
    """
    Render matplotlib figure at exact slot pixel dimensions.

    Does NOT use bbox_inches='tight' — the figure was already created at the
    correct slot size by each chart function, so saving without auto-crop
    produces an image whose pixel dimensions exactly match the slide slot.
    This prevents aspect-ratio distortion when python-pptx scales the image
    to fill the slot.
    """
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=DPI,
                facecolor="white", edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def _card(ax, x, y, w, h,
          bg="#F8FAFC", border="#E2E8F0",
          radius=0.04, shadow=True, zorder=1):
    """Draw a rounded card with drop shadow on an Axes in transAxes coords."""
    if shadow:
        ax.add_patch(FancyBboxPatch(
            (x + 0.006, y - 0.010), w, h,
            boxstyle=f"round,pad={radius}",
            facecolor="#00000010", edgecolor="none",
            transform=ax.transAxes, zorder=zorder,
        ))
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad={radius}",
        facecolor=bg, edgecolor=border, linewidth=1.5,
        transform=ax.transAxes, zorder=zorder + 1,
    ))


# ── 2.1  KPI Card ────────────────────────────────────────────────────────────

def kpi_card(
    number: str,
    label: str,
    subtitle: str = "",
    trend: str = "",
    color: str = "indigo",
) -> bytes:
    """
    Full-slide KPI card with glassmorphism style, trend arrow, subtitle.
    Font sizes scale with the render slot so the card looks balanced at any
    grid density — from standalone full-body to a cell in a 2×2 dashboard.
    """
    _mpl_reset()
    rw = getattr(_ctx, "render_w", W_PX)
    rh = getattr(_ctx, "render_h", H_PX)

    # ── Slot-aware font scaling ────────────────────────────────────────────────
    scale      = min(1.0, max(0.35, min(rw / W_PX, rh / H_PX)))
    num_size   = max(24, round(76 * scale))
    label_size = max(12, round(22 * scale))
    trend_size = max(10, round(20 * scale))
    sub_size   = max( 9, round(14 * scale))

    fig, ax = plt.subplots(figsize=(rw / DPI, rh / DPI))
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    accent = _COLOR_MAP.get(color, PALETTE[0])
    cx, cy, cw, ch = 0.18, 0.08, 0.64, 0.84

    _card(ax, cx, cy, cw, ch, bg="#F8FAFC", border=G["border"],
          radius=0.06, zorder=1)

    ax.add_patch(FancyBboxPatch(
        (cx + 0.032, cy + 0.16), 0.016, ch * 0.60,
        boxstyle="round,pad=0.003",
        facecolor=accent, edgecolor="none",
        transform=ax.transAxes, zorder=3,
    ))

    ax.text(cx + 0.08, cy + 0.57, number,
            transform=ax.transAxes,
            fontsize=num_size, fontweight="bold", color=G["900"],
            va="center", zorder=4)

    ax.text(cx + 0.08, cy + 0.31, label,
            transform=ax.transAxes,
            fontsize=label_size, color=G["700"], va="center", zorder=4)

    if trend:
        is_pos = trend.startswith("+")
        tc    = CLR["positive"] if is_pos else CLR["negative"]
        arrow = "^" if is_pos else "v"
        ax.text(cx + cw - 0.04, cy + 0.57, f"{arrow}  {trend}",
                transform=ax.transAxes,
                fontsize=trend_size, fontweight="bold", color=tc,
                ha="right", va="center", zorder=4)

    if subtitle:
        ax.text(cx + 0.08, cy + 0.14, subtitle,
                transform=ax.transAxes,
                fontsize=sub_size, color=G["400"], va="center", zorder=4)

    plt.tight_layout(pad=0.3)
    return _mpl_to_png(fig)


# ── 2.2  Multi-KPI Row ───────────────────────────────────────────────────────

def multi_kpi_row(items: list[dict]) -> bytes:
    """
    Row of 2–4 KPI cards in one image.
    Font sizes adapt both to card count and to the render slot dimensions
    so text is legible whether the row fills a full slide or a grid cell.
    """
    _mpl_reset()
    rw = getattr(_ctx, "render_w", W_PX)
    rh = getattr(_ctx, "render_h", H_PX)
    n  = min(len(items), 4)
    fig, axes = plt.subplots(1, n, figsize=(rw / DPI, rh / DPI))
    if n == 1:
        axes = [axes]

    # ── Font sizes: scale by card count AND by slot height ────────────────────
    slot_scale = min(1.0, max(0.4, rh / H_PX))
    num_fs    = round({1: 46, 2: 38, 3: 32, 4: 26}[n] * slot_scale)
    label_fs  = round({1: 16, 2: 14, 3: 13, 4: 11}[n] * slot_scale)
    trend_fs  = round({1: 15, 2: 13, 3: 12, 4: 10}[n] * slot_scale)
    sub_fs    = round({1: 13, 2: 11, 3: 10, 4:  9}[n] * slot_scale)
    bar_w     = {1: 0.022, 2: 0.022, 3: 0.020, 4: 0.018}[n]

    for ax, item in zip(axes, items[:n]):
        ax.axis("off")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        accent = _COLOR_MAP.get(item.get("color", "indigo"), PALETTE[0])

        _card(ax, 0.04, 0.06, 0.92, 0.88, bg="#F8FAFC", border=G["border"],
              radius=0.07, zorder=1)

        ax.add_patch(FancyBboxPatch(
            (0.075, 0.22), bar_w, 0.54,
            boxstyle="round,pad=0.004",
            facecolor=accent, edgecolor="none",
            transform=ax.transAxes, zorder=3,
        ))

        ax.text(0.16, 0.64, item.get("number", ""),
                transform=ax.transAxes,
                fontsize=num_fs, fontweight="bold", color=G["900"],
                va="center", zorder=4, clip_on=True)

        ax.text(0.16, 0.37, item.get("label", ""),
                transform=ax.transAxes,
                fontsize=label_fs, color=G["700"], va="center", zorder=4)

        trend = item.get("trend", "")
        if trend:
            tc    = CLR["positive"] if trend.startswith("+") else CLR["negative"]
            arrow = "^" if trend.startswith("+") else "v"
            ax.text(0.91, 0.18, f"{arrow}  {trend}",
                    transform=ax.transAxes,
                    fontsize=trend_fs, fontweight="bold", color=tc,
                    ha="right", va="center", zorder=4)

        sub = item.get("subtitle", "")
        if sub:
            ax.text(0.16, 0.18, sub,
                    transform=ax.transAxes,
                    fontsize=sub_fs, color=G["400"], va="center", zorder=4)

    plt.tight_layout(pad=0.4)
    return _mpl_to_png(fig)


# ── 2.3  Icon Stat Grid ──────────────────────────────────────────────────────

def icon_stat_grid(items: list[dict]) -> bytes:
    """Grid of stat circles with concentric glow rings."""
    _mpl_reset()
    rw = getattr(_ctx, "render_w", W_PX)
    rh = getattr(_ctx, "render_h", H_PX)
    n    = len(items)
    cols = min(n, 4)
    rows = math.ceil(n / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(rw / DPI, rh / DPI))

    if rows == 1 and cols == 1:
        axes = np.array([[axes]])
    elif rows == 1:
        axes = axes.reshape(1, -1)
    elif cols == 1:
        axes = axes.reshape(-1, 1)

    for idx in range(rows * cols):
        r, c = idx // cols, idx % cols
        ax = axes[r][c]
        ax.axis("off")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)

        if idx < n:
            item       = items[idx]
            accent     = PALETTE[idx % len(PALETTE)]
            slot_scale = min(1.0, max(0.4, min(rw / W_PX, rh / H_PX)))
            num_size   = max(14, round(34 * slot_scale))
            lbl_size   = max( 9, round(13 * slot_scale))
            for ring_alpha, ring_r in [(0.05, 0.38), (0.10, 0.30), (0.20, 0.23)]:
                ax.add_patch(plt.Circle(
                    (0.5, 0.60), ring_r, color=accent, alpha=ring_alpha,
                    transform=ax.transAxes, zorder=2,
                ))
            ax.text(0.5, 0.61, item.get("number", ""),
                    transform=ax.transAxes,
                    fontsize=num_size, fontweight="bold", color=accent,
                    ha="center", va="center", zorder=3)
            ax.text(0.5, 0.20, item.get("label", ""),
                    transform=ax.transAxes,
                    fontsize=lbl_size, color=G["700"],
                    ha="center", va="center", zorder=3)

    plt.tight_layout(pad=0.8)
    return _mpl_to_png(fig)


# ── 2.4  Progress Rings  (NEW) ───────────────────────────────────────────────

def progress_ring(
    items: list[dict],
    title: str = "",
) -> bytes:
    """
    1–4 circular progress rings.
    Each item: {value: float, max?: float, label: str, color?: str}

    Y-axis extends to –2.0 / +1.6 so the ring (top at 1.05) and the label
    (at –1.58) both sit well clear of the frame edges.
    """
    _mpl_reset()
    rw = getattr(_ctx, "render_w", W_PX)
    rh = getattr(_ctx, "render_h", H_PX)

    # ── Slot-aware font scaling ────────────────────────────────────────────────
    scale      = min(1.0, max(0.4, min(rw / W_PX, rh / H_PX)))
    num_size   = max(14, round(30 * scale))
    pct_size   = max( 9, round(16 * scale))
    label_size = max( 8, round(14 * scale))
    title_size = max(12, round(18 * scale))

    n = min(len(items), 4)
    fig, axes = plt.subplots(1, n, figsize=(rw / DPI, rh / DPI))
    if n == 1:
        axes = [axes]

    for ax, item, idx in zip(axes, items[:n], range(n)):
        val   = float(item.get("value", 0))
        max_v = float(item.get("max", 100))
        label = item.get("label", "")
        color = item.get("color", PALETTE[idx % len(PALETTE)])
        pct   = min(val / max_v, 1.0) if max_v else 0

        ax.set_xlim(-1.4, 1.4)
        ax.set_ylim(-2.0, 1.6)   # symmetric padding: 0.42 below label, 0.55 above ring
        ax.set_aspect("equal")
        ax.axis("off")

        # ── Background track ──────────────────────────────────────────────────
        ax.add_patch(mpatches.Wedge(
            (0, 0), 1.05, 0, 360,
            width=0.28, facecolor=G["100"], edgecolor="none",
        ))

        # ── Progress arc (counter-clockwise from top) ─────────────────────────
        if pct > 0:
            end_angle = 90 - pct * 360
            ax.add_patch(mpatches.Wedge(
                (0, 0), 1.05, end_angle, 90,
                width=0.28, facecolor=color, edgecolor="none", alpha=0.92,
            ))
            # Rounded cap at progress tip
            tip_rad = math.radians(90 - pct * 360)
            cap_x   = 0.915 * math.cos(tip_rad)
            cap_y   = 0.915 * math.sin(tip_rad)
            ax.add_patch(plt.Circle((cap_x, cap_y), 0.14, color=color, zorder=3))

        ax.text(0,     0.12, f"{val:,.0f}",
                ha="center", va="center",
                fontsize=num_size, fontweight="bold", color=G["900"])
        ax.text(0,    -0.30, f"{pct * 100:.0f}%",
                ha="center", va="center",
                fontsize=pct_size, color=G["500"])
        ax.text(0,    -1.60, label,
                ha="center", va="center",
                fontsize=label_size, color=G["700"])

    if title:
        plt.subplots_adjust(top=0.88)
        fig.suptitle(title, fontsize=title_size, fontweight="bold",
                     color=G["900"], y=0.97)

    plt.tight_layout(pad=0.5)
    return _mpl_to_png(fig)


# ── 2.5  Comparison Card  (NEW) ──────────────────────────────────────────────

def comparison_card(
    items: list[dict],
    title: str = "",
    label_a: str = "A",
    label_b: str = "B",
) -> bytes:
    """
    A-vs-B horizontal bar comparison with delta arrows.
    Each item: {label: str, value_a: float, value_b: float}
    """
    _mpl_reset()
    rw = getattr(_ctx, "render_w", W_PX)
    rh = getattr(_ctx, "render_h", H_PX)

    # ── Slot-aware font scaling ────────────────────────────────────────────────
    scale      = min(1.0, max(0.4, min(rw / W_PX, rh / H_PX)))
    lbl_size   = max( 9, round(14 * scale))
    bar_size   = max( 8, round(11 * scale))
    val_size   = max( 9, round(12 * scale))
    delta_size = max(10, round(14 * scale))
    title_size = max(12, round(18 * scale))

    n = len(items)
    fig, ax = plt.subplots(figsize=(rw / DPI, rh / DPI))
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.3, n + 0.1)

    for i, item in enumerate(reversed(items)):
        y     = float(i)
        lbl   = item.get("label", "")
        va_   = float(item.get("value_a", 0))
        vb_   = float(item.get("value_b", 0))
        max_v = max(va_, vb_, 1)

        ax.text(0.01, y + 0.5, lbl,
                va="center", fontsize=lbl_size, fontweight="bold", color=G["900"])

        # ── Bar A ─────────────────────────────────────────────────────────────
        bw_a = (va_ / max_v) * 0.44
        ax.barh([y + 0.66], [bw_a], left=0.28, height=0.24,
                color=PALETTE[0], alpha=0.88)
        ax.text(0.27, y + 0.66, label_a, va="center", ha="right",
                fontsize=bar_size, color=G["500"])
        ax.text(0.28 + bw_a + 0.012, y + 0.66, f"{va_:,.0f}",
                va="center", fontsize=val_size, color=PALETTE[0], fontweight="bold")

        # ── Bar B ─────────────────────────────────────────────────────────────
        bw_b = (vb_ / max_v) * 0.44
        ax.barh([y + 0.34], [bw_b], left=0.28, height=0.24,
                color=PALETTE[2], alpha=0.88)
        ax.text(0.27, y + 0.34, label_b, va="center", ha="right",
                fontsize=bar_size, color=G["500"])
        ax.text(0.28 + bw_b + 0.012, y + 0.34, f"{vb_:,.0f}",
                va="center", fontsize=val_size, color=PALETTE[2], fontweight="bold")

        # ── Delta arrow ───────────────────────────────────────────────────────
        delta = vb_ - va_
        dc    = CLR["positive"] if delta >= 0 else CLR["negative"]
        arrow = "^" if delta >= 0 else "v"
        ax.text(0.94, y + 0.5, f"{arrow}  {abs(delta):,.0f}",
                va="center", ha="right",
                fontsize=delta_size, fontweight="bold", color=dc)

        if i < n - 1:
            ax.axhline(y + 1.0, color=G["200"], linewidth=0.8,
                       xmin=0.01, xmax=0.99)

    if title:
        plt.subplots_adjust(top=0.88)
        fig.suptitle(title, fontsize=title_size, fontweight="bold",
                     color=G["900"], y=0.97)

    plt.tight_layout(pad=0.4)
    return _mpl_to_png(fig)


# ════════════════════════════════════════════════════════════════════
# ENGINE 3 – ALTAIR / VEGA-LITE  (Statistical Charts)
# ════════════════════════════════════════════════════════════════════

_ALTAIR_CFG = dict(
    background="#FFFFFF",
    font=FONT,
    title=dict(font=FONT, fontSize=20, color=G["900"], anchor="start", dy=-10),
    axis=dict(
        labelFont=FONT, labelFontSize=12, labelColor=G["500"],
        titleFont=FONT, titleFontSize=12, titleColor=G["500"],
        gridColor=G["100"], domainColor=G["200"], tickColor=G["300"],
    ),
    legend=dict(labelFont=FONT, labelFontSize=12,
                titleFont=FONT, titleFontSize=13, orient="bottom"),
    range=dict(category=PALETTE),
    view=dict(stroke="transparent"),
)


def _altair_to_png(chart) -> bytes:
    """Render Altair chart at exact slot dimensions by patching the Vega-Lite spec."""
    if not _ALTAIR_OK:
        raise RuntimeError(
            "vl-convert-python not installed. Run: pip install vl-convert-python"
        )
    rw = getattr(_ctx, "render_w", W_PX)
    rh = getattr(_ctx, "render_h", H_PX)
    spec = chart.to_dict()
    # Override chart dimensions to match render slot.
    # Subtract approximate padding consumed by axes, title, and legends.
    spec["width"]  = max(200, rw - 80)
    spec["height"] = max(150, rh - 100)
    return vlc.vegalite_to_png(spec, scale=1, vl_version="5.20")


# ── 3.1  Histogram ───────────────────────────────────────────────────────────

def histogram_chart(
    values: list[float],
    title: str = "",
    xlabel: str = "Value",
    bins: int = 20,
    color: str = None,
) -> bytes:
    """Histogram. Uses Altair when available, Matplotlib fallback."""
    color = color or PALETTE[0]

    if _ALTAIR_OK:
        df = pd.DataFrame({"value": values})
        chart = (
            alt.Chart(df, title=title)
            .mark_bar(color=color, opacity=0.85,
                      cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
            .encode(
                x=alt.X("value:Q", bin=alt.Bin(maxbins=bins), title=xlabel),
                y=alt.Y("count():Q", title="Count"),
                tooltip=["count():Q"],
            )
            .properties(width=820, height=440)
            .configure(**_ALTAIR_CFG)
        )
        return _altair_to_png(chart)

    # ── Matplotlib fallback ─────────────────────────────────────────
    _mpl_reset()
    fig, ax = plt.subplots(figsize=(W_PX / DPI, H_PX / DPI))
    ax.hist(values, bins=bins, color=color, edgecolor="white", linewidth=1.5)
    ax.set_title(title, fontsize=20, fontweight="bold", color=G["900"], pad=14)
    ax.set_xlabel(xlabel, color=G["500"])
    ax.set_ylabel("Count", color=G["500"])
    ax.yaxis.grid(True, color=G["100"], linewidth=0.8)
    ax.set_facecolor("white")
    for sp in ax.spines.values():
        sp.set_visible(False)
    return _mpl_to_png(fig)


# ── 3.2  Box Plot ────────────────────────────────────────────────────────────

def box_plot(
    data: dict[str, list[float]],
    title: str = "",
    ylabel: str = "Value",
) -> bytes:
    """Box-and-whisker per category. Altair or Matplotlib fallback."""
    if _ALTAIR_OK:
        rows = [{"category": cat, "value": v}
                for cat, vals in data.items() for v in vals]
        df = pd.DataFrame(rows)
        chart = (
            alt.Chart(df, title=title)
            .mark_boxplot(size=52, outliers={"size": 6, "opacity": 0.45})
            .encode(
                x=alt.X("category:N", title="",
                        axis=alt.Axis(labelFontSize=14)),
                y=alt.Y("value:Q", title=ylabel),
                color=alt.Color("category:N",
                                scale=alt.Scale(range=PALETTE), legend=None),
            )
            .properties(width=820, height=440)
            .configure(**_ALTAIR_CFG)
        )
        return _altair_to_png(chart)

    # ── Matplotlib fallback ─────────────────────────────────────────
    _mpl_reset()
    fig, ax = plt.subplots(figsize=(W_PX / DPI, H_PX / DPI))
    cats = list(data.keys())
    bp = ax.boxplot(
        [data[c] for c in cats],
        patch_artist=True, widths=0.55,
        medianprops=dict(color="white", linewidth=2.5),
    )
    for patch, c in zip(bp["boxes"], PALETTE):
        patch.set_facecolor(c)
        patch.set_alpha(0.85)
    ax.set_xticks(range(1, len(cats) + 1))
    ax.set_xticklabels(cats, fontsize=13)
    ax.set_ylabel(ylabel, color=G["500"])
    ax.set_title(title, fontsize=20, fontweight="bold", color=G["900"], pad=14)
    ax.yaxis.grid(True, color=G["100"], linewidth=0.8)
    ax.set_facecolor("white")
    for sp in ax.spines.values():
        sp.set_visible(False)
    return _mpl_to_png(fig)


# ── 3.3  Density Plot ────────────────────────────────────────────────────────

def density_plot(
    data: dict[str, list[float]],
    title: str = "",
    xlabel: str = "Value",
) -> bytes:
    """KDE density curves. Altair or scipy/Matplotlib fallback."""
    if _ALTAIR_OK:
        rows = [{"category": cat, "value": v}
                for cat, vals in data.items() for v in vals]
        df = pd.DataFrame(rows)
        chart = (
            alt.Chart(df, title=title)
            .transform_density("value", as_=["value", "density"],
                               groupby=["category"])
            .mark_area(opacity=0.55)
            .encode(
                x=alt.X("value:Q", title=xlabel),
                y=alt.Y("density:Q", title="Density", stack=None),
                color=alt.Color("category:N",
                                scale=alt.Scale(range=PALETTE)),
            )
            .properties(width=820, height=440)
            .configure(**_ALTAIR_CFG)
        )
        return _altair_to_png(chart)

    # ── Matplotlib + scipy fallback ─────────────────────────────────
    from scipy.stats import gaussian_kde
    _mpl_reset()
    fig, ax = plt.subplots(figsize=(W_PX / DPI, H_PX / DPI))
    for i, (cat, vals) in enumerate(data.items()):
        arr = np.array(vals, dtype=float)
        if len(arr) < 2:
            continue
        kde = gaussian_kde(arr, bw_method=0.35)
        x_range = np.linspace(arr.min(), arr.max(), 300)
        c = PALETTE[i % len(PALETTE)]
        ax.fill_between(x_range, kde(x_range), alpha=0.25, color=c)
        ax.plot(x_range, kde(x_range), color=c, linewidth=2.5, label=cat)
    ax.set_title(title, fontsize=20, fontweight="bold", color=G["900"], pad=14)
    ax.set_xlabel(xlabel, color=G["500"])
    ax.set_ylabel("Density", color=G["500"])
    ax.legend(fontsize=12)
    ax.yaxis.grid(True, color=G["100"], linewidth=0.8)
    ax.set_facecolor("white")
    for sp in ax.spines.values():
        sp.set_visible(False)
    return _mpl_to_png(fig)


# ════════════════════════════════════════════════════════════════════
# CHART REGISTRY  (AI-facing catalogue)
# ════════════════════════════════════════════════════════════════════

AVAILABLE_CHARTS: dict[str, dict] = {

    # ── Engine 1: Plotly ─────────────────────────────────────────────
    "bar_chart": {
        "function": bar_chart, "engine": "plotly",
        "description": "Bar/column chart – compare discrete categories. Use for rankings or period comparisons.",
        "params": {
            "categories": "list[str]", "values": "list[float]",
            "title": "str", "ylabel": "str",
            "color_mode": "str: multi|single",
            "value_prefix": "str", "value_suffix": "str",
            "horizontal": "bool",
        },
    },
    "line_chart": {
        "function": line_chart, "engine": "plotly",
        "description": "Line chart with gradient fill – single-series trend over time.",
        "params": {
            "categories": "list[str]", "values": "list[float]",
            "title": "str", "ylabel": "str",
            "fill": "bool", "smooth": "bool", "show_markers": "bool",
            "value_prefix": "str", "value_suffix": "str",
        },
    },
    "multi_line_chart": {
        "function": multi_line_chart, "engine": "plotly",
        "description": "Multi-series line chart – compare 2+ trends on the same time axis.",
        "params": {
            "categories": "list[str]",
            "series": "dict[str, list[float]] — {series_name: values}",
            "title": "str", "ylabel": "str", "smooth": "bool",
        },
    },
    "area_chart": {
        "function": area_chart, "engine": "plotly",
        "description": "Stacked or overlapping area chart – volume over time for multiple series.",
        "params": {
            "categories": "list[str]",
            "series": "dict[str, list[float]]",
            "title": "str", "ylabel": "str", "stacked": "bool",
        },
    },
    "pie_chart": {
        "function": pie_chart, "engine": "plotly",
        "description": "Pie or donut chart – proportions of a whole. Set donut=True for modern ring style with centre total.",
        "params": {
            "categories": "list[str]", "values": "list[float]",
            "title": "str", "donut": "bool",
            "explode_max": "bool", "show_percentage": "bool",
        },
    },
    "stacked_bar_chart": {
        "function": stacked_bar_chart, "engine": "plotly",
        "description": "Stacked bar chart – composition changes across categories or time.",
        "params": {
            "categories": "list[str]",
            "series": "dict[str, list[float]]",
            "title": "str", "ylabel": "str", "horizontal": "bool",
        },
    },
    "grouped_bar_chart": {
        "function": grouped_bar_chart, "engine": "plotly",
        "description": "Grouped bar chart – compare multiple series side by side per category.",
        "params": {
            "categories": "list[str]",
            "series": "dict[str, list[float]]",
            "title": "str", "ylabel": "str",
        },
    },
    "waterfall_chart": {
        "function": waterfall_chart, "engine": "plotly",
        "description": "Waterfall chart – sequential incremental changes leading to a total.",
        "params": {
            "categories": "list[str]", "values": "list[float]",
            "title": "str", "ylabel": "str",
            "value_prefix": "str", "value_suffix": "str",
        },
    },
    "gauge_chart": {
        "function": gauge_chart, "engine": "plotly",
        "description": "Gauge/indicator – single KPI value vs maximum (e.g. 73% completion).",
        "params": {
            "value": "float", "max_value": "float",
            "title": "str", "label": "str", "suffix": "str",
        },
    },
    "radar_chart": {
        "function": radar_chart, "engine": "plotly",
        "description": "Radar/spider chart – multi-dimensional profile comparison.",
        "params": {
            "categories": "list[str]", "values": "list[float]",
            "title": "str", "max_value": "float",
        },
    },
    "funnel_chart": {
        "function": funnel_chart, "engine": "plotly",
        "description": "Funnel – conversion or pipeline stages with drop-off percentages.",
        "params": {
            "stages": "list[str]", "values": "list[float]", "title": "str",
        },
    },
    "treemap_chart": {
        "function": treemap_chart, "engine": "plotly",
        "description": "Treemap – hierarchical proportions as nested coloured rectangles.",
        "params": {
            "categories": "list[str]", "values": "list[float]", "title": "str",
        },
    },
    "sunburst_chart": {
        "function": sunburst_chart, "engine": "plotly",
        "description": "Sunburst – hierarchical data as concentric colour rings.",
        "params": {
            "categories": "list[str]", "values": "list[float]",
            "parents": "list[str] (optional – empty string for root nodes)",
            "title": "str",
        },
    },
    "heatmap_chart": {
        "function": heatmap_chart, "engine": "plotly",
        "description": "Heatmap – 2-D matrix with indigo colour intensity (correlations, schedules).",
        "params": {
            "x_labels": "list[str]", "y_labels": "list[str]",
            "values": "list[list[float]]", "title": "str",
        },
    },
    "scatter_chart": {
        "function": scatter_chart, "engine": "plotly",
        "description": "Scatter or bubble chart – relationship between two numeric variables.",
        "params": {
            "x_values": "list[float]", "y_values": "list[float]",
            "labels": "list[str] (optional)",
            "title": "str", "xlabel": "str", "ylabel": "str",
            "size": "list[float] (optional – bubble sizes)",
        },
    },
    "bullet_chart": {
        "function": bullet_chart, "engine": "plotly",
        "description": "Bullet chart – actual values vs targets for multiple KPIs in one view.",
        "params": {
            "categories": "list[str]",
            "values": "list[float]",
            "targets": "list[float]",
            "title": "str", "value_suffix": "str",
        },
    },
    "slope_chart": {
        "function": slope_chart, "engine": "plotly",
        "description": "Slope chart – before-vs-after change across multiple items.",
        "params": {
            "categories": "list[str]",
            "before_values": "list[float]",
            "after_values": "list[float]",
            "before_label": "str", "after_label": "str",
            "title": "str", "value_suffix": "str",
        },
    },

    # ── Engine 2: Matplotlib ──────────────────────────────────────────
    "kpi_card": {
        "function": kpi_card, "engine": "matplotlib",
        "description": "Full-slide KPI card – large number, label, trend arrow (+12%), optional subtitle.",
        "params": {
            "number": "str (e.g. '$4.2M' or '73%')",
            "label": "str",
            "subtitle": "str (optional context line)",
            "trend": "str (e.g. '+12%' or '-3%')",
            "color": "str: indigo|blue|cyan|emerald|violet|orange|red|teal|pink",
        },
    },
    "multi_kpi_row": {
        "function": multi_kpi_row, "engine": "matplotlib",
        "description": "Row of 2–4 KPI cards in one image – dashboard overview slide.",
        "params": {
            "items": (
                "list[dict] – each: "
                "{number: str, label: str, trend?: str, color?: str, subtitle?: str}"
            ),
        },
    },
    "icon_stat_grid": {
        "function": icon_stat_grid, "engine": "matplotlib",
        "description": "Grid of glowing stat circles – overview of 2–8 metrics at a glance.",
        "params": {
            "items": "list[dict] – each: {number: str, label: str}",
        },
    },
    "progress_ring": {
        "function": progress_ring, "engine": "matplotlib",
        "description": "1–4 circular progress rings – completion rate, utilisation, NPS, quota attainment.",
        "params": {
            "items": (
                "list[dict] – each: "
                "{value: float, max?: float (default 100), label: str, color?: str hex}"
            ),
            "title": "str",
        },
    },
    "comparison_card": {
        "function": comparison_card, "engine": "matplotlib",
        "description": "A-vs-B horizontal bar comparison with delta arrows – e.g. last year vs this year.",
        "params": {
            "items": "list[dict] – each: {label: str, value_a: float, value_b: float}",
            "title": "str",
            "label_a": "str (default 'A')",
            "label_b": "str (default 'B')",
        },
    },

    # ── Engine 3: Altair ──────────────────────────────────────────────
    "histogram_chart": {
        "function": histogram_chart, "engine": "altair",
        "description": "Histogram – frequency distribution of a numeric variable.",
        "params": {
            "values": "list[float]",
            "title": "str", "xlabel": "str",
            "bins": "int (default 20)", "color": "str hex (optional)",
        },
    },
    "box_plot": {
        "function": box_plot, "engine": "altair",
        "description": "Box-and-whisker plot – distribution spread per category (median, IQR, outliers).",
        "params": {
            "data": "dict[str, list[float]] – {category: values}",
            "title": "str", "ylabel": "str",
        },
    },
    "density_plot": {
        "function": density_plot, "engine": "altair",
        "description": "KDE density plot – smooth overlapping distributions per category.",
        "params": {
            "data": "dict[str, list[float]] – {category: values}",
            "title": "str", "xlabel": "str",
        },
    },
}


def get_chart_schema_for_ai() -> list[dict]:
    """Return the chart registry as a list of dicts for the AI system prompt."""
    return [
        {
            "chart_function": name,
            "engine":        info["engine"],
            "description":   info["description"],
            "parameters":    info["params"],
        }
        for name, info in AVAILABLE_CHARTS.items()
    ]


def render_chart(
    chart_function: str,
    params: dict,
    render_width: int = W_PX,
    render_height: int = H_PX,
) -> bytes:
    """
    Render a chart at the given pixel dimensions.

    render_width / render_height should match the target slide slot so the
    image fills the slot without letterboxing.
    """
    if chart_function not in AVAILABLE_CHARTS:
        raise ValueError(
            f"Unknown chart '{chart_function}'. "
            f"Available: {list(AVAILABLE_CHARTS.keys())}"
        )
    _ctx.render_w = max(120, render_width)
    _ctx.render_h = max(80, render_height)
    try:
        return AVAILABLE_CHARTS[chart_function]["function"](**params)
    finally:
        _ctx.render_w = W_PX
        _ctx.render_h = H_PX
