"""Rosetta bead validation workflow step."""

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from RosettaX.ui import WorkflowStep
from typing import Any


def build_validation_results(*, figure: go.Figure | None = None) -> dash.html.Div:
    """Render validation criteria and the fit statistics for plotted diameters."""
    metrics = []
    if figure is not None:
        summary = figure.layout.meta
        r_squared = summary["r_squared"]
        metrics = [
            dash.html.H6("Fit for the plotted diameters"),
            dash.html.Ul([
                dash.html.Li(f"Peaks plotted: {summary['point_count']}"),
                dash.html.Li(f"Zero-intercept fit R²: {r_squared:.3f}" if r_squared is not None else "Zero-intercept fit R²: unavailable"),
                dash.html.Li(f"Largest absolute scatter difference: {summary['max_percent_difference']:.1f}%"),
            ]),
            dash.html.P("These values summarize the diameters in the plot. Validation can also try other assignments.", className="small"),
        ]
    checks = [
        dash.html.H6("Validation checks"),
        dash.html.Ul([
            dash.html.Li("After scaling, each matched peak must agree with its prediction within a factor of 1.20."),
            dash.html.Li("When a peak is left out of the scale estimate, its prediction must agree within a factor of 1.25."),
            dash.html.Li("The overall zero-intercept fit must have R² greater than 0.90."),
            dash.html.Li("Identities must agree across plausible assignments, the original peak fit, and three bootstrap repeats."),
        ], className="mb-0"),
    ]
    summary_panel = dash.html.Div([*metrics, *checks], className="small border rounded p-3")
    if figure is None:
        return summary_panel
    return dbc.Row([
        dbc.Col(dash.dcc.Graph(figure=figure), xs=12, lg=8, xl=9),
        dbc.Col(summary_panel, xs=12, lg=4, xl=3),
    ], className="g-3 align-items-start")


class RosettaValidation:
    """Render the Rosetta validation controls as a numbered workflow step."""

    workflow_step = WorkflowStep(
        title="Validate bead assignments (optional)",
        description="Check Rosetta diameters against measured scatter and detector predictions.",
    )

    def __init__(self, *, page: Any, section_number: int, card_color: str) -> None:
        self.ids = page.ids.Calibration
        self.section_number = section_number
        self.card_color = card_color

    def get_layout(self) -> dbc.Card:
        """Build the validation controls and results area."""
        return dbc.Card([
            dbc.CardHeader(f"{self.section_number}. {self.workflow_step.title}"),
            dbc.CardBody([
                dash.dcc.Store(id=self.ids.rosetta_validation_review),
                dash.html.P("Validation is optional. Create calibration uses the diameters currently in the table."),
                dbc.Button("Validate bead assignments", id=self.ids.rosetta_validate_btn, color="primary"),
                dbc.Button("Apply suggested changes", id=self.ids.rosetta_apply_btn, color="secondary", disabled=True, className="ms-2"),
                dash.html.Div(id=self.ids.rosetta_model_status, role="status", className="mt-2"),
                dash.html.Div(build_validation_results(), id=self.ids.rosetta_validation_plot, className="mt-3"),
            ]),
        ])

    def register_callbacks(self) -> None:
        """The table section registers the shared modeling and validation callback."""
