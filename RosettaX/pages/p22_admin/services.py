# -*- coding: utf-8 -*-

import hmac
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import plotly.graph_objects as go

from RosettaX.utils import usage_metrics

logger = logging.getLogger(__name__)


ROSETTAX_ADMIN_TOKEN_ENV_VAR = "ROSETTAX_ADMIN_TOKEN"

_VISITS_BAR_COLOR = "#0d6efd"
_UNIQUE_VISITORS_LINE_COLOR = "#20c997"


@dataclass(frozen=True)
class AdminDashboardData:
    """
    Snapshot of all server-side data shown on the admin dashboard.
    """

    metrics: usage_metrics.UsageMetrics = field(
        default_factory=usage_metrics.UsageMetrics,
    )
    visit_summary: usage_metrics.VisitSummary = field(
        default_factory=usage_metrics.VisitSummary,
    )
    generated_at: str = ""


def get_configured_admin_token() -> str:
    """
    Resolve the admin access token configured on the server.
    """
    return str(os.getenv(ROSETTAX_ADMIN_TOKEN_ENV_VAR, "")).strip()


def is_admin_access_granted(provided_token: Any) -> bool:
    """
    Grant admin access only when a token is configured and matches exactly.

    When no token is configured the admin page stays disabled entirely.
    """
    configured_token = get_configured_admin_token()

    if not configured_token:
        return False

    candidate_token = str(provided_token or "").strip()

    if not candidate_token:
        return False

    return hmac.compare_digest(configured_token, candidate_token)


def collect_admin_dashboard_data() -> AdminDashboardData:
    """
    Load usage counters and visit events and aggregate them for display.
    """
    try:
        metrics = usage_metrics.load_usage_metrics()
    except Exception:
        logger.exception("Failed to load usage metrics for the admin dashboard.")
        metrics = usage_metrics.UsageMetrics()

    try:
        visit_events = usage_metrics.load_visit_events()
    except Exception:
        logger.exception("Failed to load visit events for the admin dashboard.")
        visit_events = []

    visit_summary = usage_metrics.summarize_visit_events(visit_events)

    return AdminDashboardData(
        metrics=metrics,
        visit_summary=visit_summary,
        generated_at=_current_utc_display_timestamp(),
    )


def build_visits_over_time_figure(
    *,
    visit_summary: usage_metrics.VisitSummary,
    theme: str = "dark",
) -> go.Figure:
    """
    Build the daily visits and unique visitors graph.
    """
    daily = visit_summary.daily

    figure = go.Figure()
    figure.add_bar(
        x=daily.dates,
        y=daily.visit_counts,
        name="Visits",
        marker_color=_VISITS_BAR_COLOR,
        hovertemplate="%{x}<br>%{y} visit(s)<extra></extra>",
    )
    figure.add_scatter(
        x=daily.dates,
        y=daily.unique_visitor_counts,
        name="Unique visitors",
        mode="lines+markers",
        line={"color": _UNIQUE_VISITORS_LINE_COLOR, "width": 2},
        hovertemplate="%{x}<br>%{y} unique visitor(s)<extra></extra>",
    )

    if not daily.dates:
        figure.add_annotation(
            text="No visits recorded yet.",
            showarrow=False,
            font={"size": 14},
        )

    figure.update_layout(
        title="Visits over time",
        xaxis_title="Date (UTC)",
        yaxis_title="Visits",
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "left",
            "x": 0,
        },
    )

    return _apply_admin_figure_style(figure, theme=theme)


def build_page_breakdown_figure(
    *,
    visit_summary: usage_metrics.VisitSummary,
    theme: str = "dark",
) -> go.Figure:
    """
    Build the per-page visit count horizontal bar graph.
    """
    page_visit_counts = visit_summary.page_visit_counts
    paths = [path for path, _count in page_visit_counts][::-1]
    counts = [count for _path, count in page_visit_counts][::-1]

    figure = go.Figure(
        go.Bar(
            x=counts,
            y=paths,
            orientation="h",
            marker_color=_VISITS_BAR_COLOR,
            hovertemplate="%{y}<br>%{x} visit(s)<extra></extra>",
        )
    )

    if not page_visit_counts:
        figure.add_annotation(
            text="No visits recorded yet.",
            showarrow=False,
            font={"size": 14},
        )

    figure.update_layout(
        title="Visits per page",
        xaxis_title="Visits",
        yaxis_title="Page",
    )

    return _apply_admin_figure_style(figure, theme=theme)


def build_recent_visit_rows(
    *,
    visit_summary: usage_metrics.VisitSummary,
) -> list[dict[str, str]]:
    """
    Convert the most recent visit events into DataTable rows.
    """
    return [
        {
            "visited_at": format_visit_timestamp_for_display(event.visited_at),
            "ip_address": event.ip_address or "unknown",
            "path": event.path,
            "user_agent": event.user_agent or "unknown",
        }
        for event in visit_summary.recent_visits
    ]


def format_visit_timestamp_for_display(visited_at: str) -> str:
    """
    Format an ISO visit timestamp for the recent visits table.
    """
    try:
        parsed_timestamp = datetime.fromisoformat(str(visited_at))
    except (TypeError, ValueError):
        return str(visited_at or "")

    return f"{parsed_timestamp.strftime('%Y-%m-%d %H:%M:%S')} UTC"


def _current_utc_display_timestamp() -> str:
    return f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC"


def _apply_admin_figure_style(figure: go.Figure, *, theme: str) -> go.Figure:
    is_dark_theme = str(theme).strip().lower() == "dark"

    font_color = (
        "rgba(255, 255, 255, 0.85)" if is_dark_theme else "rgba(0, 0, 0, 0.85)"
    )
    grid_color = (
        "rgba(255, 255, 255, 0.12)" if is_dark_theme else "rgba(0, 0, 0, 0.12)"
    )

    figure.update_layout(
        template="plotly_dark" if is_dark_theme else "plotly_white",
        paper_bgcolor="rgba(0, 0, 0, 0)",
        plot_bgcolor="rgba(0, 0, 0, 0)",
        font={"color": font_color},
        margin={"l": 60, "r": 30, "t": 70, "b": 50},
    )
    figure.update_xaxes(gridcolor=grid_color)
    figure.update_yaxes(gridcolor=grid_color)

    return figure
