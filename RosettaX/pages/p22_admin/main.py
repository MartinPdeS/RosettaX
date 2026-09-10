
import logging
from typing import Any

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, dash_table, dcc, html

from RosettaX.utils import styling, ui_forms

from . import services
from .ids import Ids

logger = logging.getLogger(__name__)


REFRESH_INTERVAL_MILLISECONDS = 30_000


class AdminPage:
    """
    Hidden administration dashboard with usage analytics graphs.

    The page is not linked from the sidebar. It is served at /admin and is
    only rendered when the request carries the token configured through the
    ROSETTAX_ADMIN_TOKEN environment variable.
    """

    def __init__(self) -> None:
        self.ids = Ids()

    def layout(
        self,
        token: str | None = None,
        **_kwargs,
    ) -> dbc.Container:
        if not services.is_admin_access_granted(token):
            return self._access_denied_layout()

        return self._dashboard_layout()

    def register_callbacks(self) -> "AdminPage":
        @dash.callback(
            Output(self.ids.stat_total_visits, "children"),
            Output(self.ids.stat_unique_visitors, "children"),
            Output(self.ids.stat_visits_today, "children"),
            Output(self.ids.stat_unique_visitors_today, "children"),
            Output(self.ids.stat_apply_clicks, "children"),
            Output(self.ids.stat_calibrated_files, "children"),
            Output(self.ids.visits_over_time_graph, "figure"),
            Output(self.ids.page_breakdown_graph, "figure"),
            Output(self.ids.recent_visits_table, "data"),
            Output(self.ids.last_updated, "children"),
            Input(self.ids.refresh_interval, "n_intervals"),
            Input(self.ids.refresh_button, "n_clicks"),
            Input("theme-store", "data"),
            prevent_initial_call=False,
        )
        def refresh_admin_dashboard(
            _n_intervals: Any,
            _n_clicks: Any,
            theme_store_data: Any,
        ):
            theme = "dark"

            if isinstance(theme_store_data, dict):
                theme = str(theme_store_data.get("theme", "dark"))

            dashboard_state = self._resolve_dashboard_state(theme=theme)

            return (
                dashboard_state["total_visits"],
                dashboard_state["unique_visitors"],
                dashboard_state["visits_today"],
                dashboard_state["unique_visitors_today"],
                dashboard_state["apply_clicks"],
                dashboard_state["calibrated_files"],
                dashboard_state["visits_over_time_figure"],
                dashboard_state["page_breakdown_figure"],
                dashboard_state["recent_visit_rows"],
                dashboard_state["last_updated"],
            )

        return self

    def _resolve_dashboard_state(self, *, theme: str) -> dict[str, Any]:
        dashboard_data = services.collect_admin_dashboard_data()
        visit_summary = dashboard_data.visit_summary
        metrics = dashboard_data.metrics

        return {
            "total_visits": str(visit_summary.total_visits),
            "unique_visitors": str(visit_summary.unique_visitor_count),
            "visits_today": str(visit_summary.visits_today),
            "unique_visitors_today": str(visit_summary.unique_visitors_today),
            "apply_clicks": str(metrics.apply_button_click_count),
            "calibrated_files": str(metrics.total_calibrated_files),
            "visits_over_time_figure": services.build_visits_over_time_figure(
                visit_summary=visit_summary,
                theme=theme,
            ),
            "page_breakdown_figure": services.build_page_breakdown_figure(
                visit_summary=visit_summary,
                theme=theme,
            ),
            "recent_visit_rows": services.build_recent_visit_rows(
                visit_summary=visit_summary,
            ),
            "last_updated": f"Last updated: {dashboard_data.generated_at}",
        }

    def _dashboard_layout(self) -> dbc.Container:
        dashboard_state = self._resolve_dashboard_state(theme="dark")

        return dbc.Container(
            [
                dcc.Interval(
                    id=self.ids.refresh_interval,
                    interval=REFRESH_INTERVAL_MILLISECONDS,
                    n_intervals=0,
                ),
                self._build_header(),
                self._build_stat_cards(dashboard_state=dashboard_state),
                self._build_graph_card(
                    title="Traffic",
                    subtitle="Daily page visits and unique visitors over time.",
                    graph_id=self.ids.visits_over_time_graph,
                    figure=dashboard_state["visits_over_time_figure"],
                ),
                self._build_graph_card(
                    title="Pages",
                    subtitle="Total recorded visits per page.",
                    graph_id=self.ids.page_breakdown_graph,
                    figure=dashboard_state["page_breakdown_figure"],
                ),
                self._build_recent_visits_card(
                    recent_visit_rows=dashboard_state["recent_visit_rows"],
                ),
            ],
            fluid=True,
            style={
                "display": "flex",
                "flexDirection": "column",
                "gap": styling.get_spacing_token("lg"),
            },
        )

    def _build_header(self) -> html.Div:
        return html.Div(
            [
                ui_forms.build_section_intro(
                    title="Administration",
                    title_component="H2",
                    description=(
                        "Server-side usage analytics: page visits, unique visitors, "
                        "and calibration counters. Local visits (127.0.0.1, localhost, "
                        "private network IPs) are excluded so local desktop usage is not tracked."
                    ),
                ),
                html.Div(
                    [
                        html.Span(
                            id=self.ids.last_updated,
                            style={
                                "fontSize": "0.88rem",
                                "opacity": 0.72,
                                "alignSelf": "center",
                            },
                        ),
                        dbc.Button(
                            "Refresh",
                            id=self.ids.refresh_button,
                            color="primary",
                            outline=True,
                            size="sm",
                        ),
                    ],
                    style={
                        "display": "flex",
                        "justifyContent": "space-between",
                        "gap": "12px",
                    },
                ),
            ]
        )

    def _build_stat_cards(self, *, dashboard_state: dict[str, Any]) -> dbc.Row:
        tiles = [
            (self.ids.stat_total_visits, dashboard_state["total_visits"], "Total visits"),
            (self.ids.stat_unique_visitors, dashboard_state["unique_visitors"], "Unique visitors"),
            (self.ids.stat_visits_today, dashboard_state["visits_today"], "Visits today"),
            (self.ids.stat_unique_visitors_today, dashboard_state["unique_visitors_today"], "Unique visitors today"),
            (self.ids.stat_apply_clicks, dashboard_state["apply_clicks"], "Apply button clicks"),
            (self.ids.stat_calibrated_files, dashboard_state["calibrated_files"], "Calibrated files"),
        ]

        return dbc.Row(
            [
                dbc.Col(
                    self._stat_tile(
                        value_id=value_id,
                        initial_value=initial_value,
                        label=label,
                    ),
                    md=6,
                    lg=4,
                    xl=2,
                )
                for value_id, initial_value, label in tiles
            ],
            className="g-3",
        )

    def _stat_tile(
        self,
        *,
        value_id: str,
        initial_value: str,
        label: str,
    ) -> html.Div:
        return html.Div(
            [
                html.Div(
                    initial_value,
                    id=value_id,
                    style={
                        "fontSize": "2rem",
                        "fontWeight": "800",
                        "lineHeight": "1.0",
                    },
                ),
                html.Div(
                    label,
                    style={
                        "fontSize": "0.92rem",
                        "opacity": 0.76,
                        "marginTop": "6px",
                    },
                ),
            ],
            style={
                "padding": "18px",
                "borderRadius": "12px",
                "border": "1px solid rgba(13, 110, 253, 0.16)",
                "background": "rgba(13, 110, 253, 0.04)",
                "height": "100%",
            },
        )

    def _build_graph_card(
        self,
        *,
        title: str,
        subtitle: str,
        graph_id: str,
        figure: Any,
    ) -> dbc.Card:
        card = dbc.Card(
            [
                dbc.CardHeader(
                    [
                        html.Div(
                            title,
                            style={
                                "fontWeight": "750",
                                "fontSize": "1.02rem",
                            },
                        ),
                        html.Div(
                            subtitle,
                            style={
                                "fontSize": "0.9rem",
                                "opacity": 0.72,
                            },
                        ),
                    ]
                ),
                dbc.CardBody(
                    dcc.Loading(
                        dcc.Graph(
                            id=graph_id,
                            figure=figure,
                            config={"displayModeBar": False},
                        ),
                        type="default",
                    ),
                ),
            ]
        )

        return ui_forms.apply_workflow_section_card_style(card=card)

    def _build_recent_visits_card(
        self,
        *,
        recent_visit_rows: list[dict[str, str]],
    ) -> dbc.Card:
        card = dbc.Card(
            [
                dbc.CardHeader(
                    [
                        html.Div(
                            "Recent visits",
                            style={
                                "fontWeight": "750",
                                "fontSize": "1.02rem",
                            },
                        ),
                        html.Div(
                            "Most recent page visits with client IP address and user agent.",
                            style={
                                "fontSize": "0.9rem",
                                "opacity": 0.72,
                            },
                        ),
                    ]
                ),
                dbc.CardBody(
                    dash_table.DataTable(
                        id=self.ids.recent_visits_table,
                        columns=[
                            {"name": "Time (UTC)", "id": "visited_at"},
                            {"name": "IP address", "id": "ip_address"},
                            {"name": "Page", "id": "path"},
                            {"name": "User agent", "id": "user_agent"},
                        ],
                        data=recent_visit_rows,
                        page_size=10,
                        style_table={"overflowX": "auto"},
                        style_header={
                            "fontWeight": "700",
                            "backgroundColor": "transparent",
                            "border": "1px solid rgba(128, 128, 128, 0.25)",
                        },
                        style_cell={
                            "textAlign": "left",
                            "fontFamily": "inherit",
                            "fontSize": "0.9rem",
                            "padding": "8px 12px",
                            "backgroundColor": "transparent",
                            "color": "inherit",
                            "border": "1px solid rgba(128, 128, 128, 0.18)",
                            "overflow": "hidden",
                            "textOverflow": "ellipsis",
                            "maxWidth": "320px",
                        },
                        style_cell_conditional=[
                            {
                                "if": {"column_id": "user_agent"},
                                "maxWidth": "420px",
                            },
                        ],
                    ),
                ),
            ]
        )

        return ui_forms.apply_workflow_section_card_style(card=card)

    def _access_denied_layout(self) -> dbc.Container:
        return dbc.Container(
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H4(
                            "Page not available",
                            style={"fontWeight": "700"},
                        ),
                        html.Div(
                            "The requested page is not available on this server.",
                            style={"opacity": 0.72},
                        ),
                    ]
                ),
                style={"maxWidth": "540px", "margin": "48px auto"},
            ),
            fluid=True,
        )


_page = AdminPage().register_callbacks()
layout = _page.layout


dash.register_page(
    __name__,
    path="/admin",
    name="Admin",
    layout=layout,
)
