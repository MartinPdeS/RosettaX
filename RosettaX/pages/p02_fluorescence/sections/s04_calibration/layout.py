# -*- coding: utf-8 -*-

from typing import Any
import logging

import dash
import dash_bootstrap_components as dbc

from RosettaX.utils import styling
from RosettaX.utils import ui_forms
from RosettaX.utils.runtime_config import RuntimeConfig


logger = logging.getLogger(__name__)


def get_layout(section) -> dbc.Card:
    """
    Build the calibration section layout.
    """
    logger.debug("Building calibration section layout.")

    return dbc.Card(
        [
            _build_header(section),
            _build_collapse(section),
        ],
        style=ui_forms.build_workflow_section_card_style(
            color_name=section.card_color,
        ),
    )


def _build_header(section) -> dbc.CardHeader:
    """
    Build the card header.
    """
    return dbc.CardHeader(
        [
            ui_forms.build_title_with_info(
                title=f"{section.section_number}. Calibration",
                tooltip_target_id=section.section_tooltip_target_id,
                tooltip_id=section.section_tooltip_id,
                tooltip_text=(
                    "This section creates the fluorescence calibration from the "
                    "measured bead peak positions and the known MESF values in the "
                    "reference table."
                ),
            ),
            dash.html.Div(
                "Fit the fluorescence response from reference MESF values and measured bead peaks.",
                style=ui_forms.build_workflow_section_subtitle_style(),
            ),
        ],
        style=ui_forms.build_workflow_section_header_style(
            color_name=section.card_color,
        ),
    )


def _build_collapse(section) -> dbc.Collapse:
    """
    Build the collapsible section body.
    """
    return dbc.Collapse(
        _build_body(section),
        id=section.ids.collapse,
        is_open=True,
    )


def _build_body(section) -> dbc.CardBody:
    """
    Build the card body.
    """
    return dbc.CardBody(
        [
            _build_graph_store(section),
            _build_calibration_store(section),
            _build_action_panel(section),
            dash.html.Div(
                style={
                    "height": "18px",
                },
            ),
            _build_graph_block(section),
            dash.html.Div(
                style={
                    "height": "12px",
                },
            ),
            _build_status_block(section),
        ],
        style=ui_forms.build_workflow_section_body_style(),
    )


def _build_graph_store(section) -> dash.dcc.Store:
    """
    Build the graph store.
    """
    return dash.dcc.Store(
        id=section.ids.graph_store,
        storage_type="session",
    )


def _build_calibration_store(section) -> dash.dcc.Store:
    """
    Build the calibration store.
    """
    return dash.dcc.Store(
        id=section.ids.calibration_store,
        storage_type="session",
    )


def _build_action_panel(section) -> dbc.Card:
    """
    Build calibration action controls.
    """
    return dbc.Card(
        dbc.CardBody(
            [
                dash.html.Div(
                    [
                        dash.html.Div(
                            [
                                dash.html.Div(
                                    "Fluorescence calibration fit",
                                    style={
                                        "fontWeight": "700",
                                        "fontSize": "1rem",
                                    },
                                ),
                                dash.html.Div(
                                    (
                                        "Create the calibration by matching measured "
                                        "fluorescence peak positions to known MESF "
                                        "reference values."
                                    ),
                                    style={
                                        "opacity": 0.72,
                                        "fontSize": "0.9rem",
                                        "marginTop": "2px",
                                    },
                                ),
                            ],
                            style={
                                "flex": "1 1 auto",
                            },
                        ),
                        dash.html.Div(
                            [
                                dbc.Button(
                                    "Create calibration",
                                    id=section.ids.calibrate_btn,
                                    n_clicks=0,
                                    color="primary",
                                ),
                                ui_forms.build_info_badge(
                                    tooltip_target_id=section.create_calibration_tooltip_target_id,
                                ),
                                dbc.Tooltip(
                                    (
                                        "Create the fluorescence calibration by matching the measured "
                                        "fluorescence peak positions to the known MESF values from "
                                        "the reference table."
                                    ),
                                    id=section.create_calibration_tooltip_id,
                                    target=section.create_calibration_tooltip_target_id,
                                    placement="right",
                                ),
                            ],
                            style={
                                "display": "flex",
                                "alignItems": "center",
                                "gap": "0px",
                                "flex": "0 0 auto",
                            },
                        ),
                    ],
                    style={
                        "display": "flex",
                        "alignItems": "center",
                        "justifyContent": "space-between",
                        "gap": "16px",
                        "flexWrap": "wrap",
                    },
                ),
            ],
            style={
                "padding": "14px 16px",
            },
        ),
        style=ui_forms.build_workflow_panel_style(
            color_name=section.card_color,
            background=styling.build_rgba(
                section.card_color,
                0.04,
            ),
        ),
    )


def _build_graph_block(section) -> dash.html.Div:
    """
    Build the calibration graph panel.
    """
    return dash.html.Div(
        [
            _build_graph_panel_card(
                section=section,
                title="Fluorescence calibration fit",
                subtitle="Measured fluorescence intensity mapped to calibrated MESF units.",
                graph_id=section.ids.graph_calibration,
                footer_content=_build_calibration_footer(section),
            ),
        ],
        style={
            "display": "flex",
            "gap": "18px",
            "alignItems": "stretch",
            "width": "100%",
            "overflowX": "auto",
            "overflowY": "visible",
        },
    )


def _build_graph_panel_card(
    section,
    *,
    title: str,
    subtitle: str,
    graph_id: str,
    footer_content: Any,
) -> dbc.Card:
    """
    Build one self contained graph panel card.
    """
    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    ui_forms.build_title_with_info(
                        title=title,
                        tooltip_target_id=section.graph_tooltip_target_id,
                        tooltip_id=section.graph_tooltip_id,
                        tooltip_text=(
                            "This graph shows the fitted relation between measured "
                            "fluorescence intensity and calibrated fluorescence units. "
                            "Review the fit before saving the calibration."
                        ),
                        title_style_overrides={
                            "fontSize": "0.98rem",
                        },
                    ),
                    dash.html.Div(
                        subtitle,
                        style=ui_forms.build_workflow_section_subtitle_style(
                            font_size="0.84rem",
                        ),
                    ),
                ],
                style=ui_forms.build_workflow_subpanel_header_style(
                    color_name=section.card_color,
                ),
            ),
            dbc.CardBody(
                [
                    dash.dcc.Loading(
                        dash.dcc.Graph(
                            id=graph_id,
                            style=_build_graph_style(section),
                            config=styling.PLOTLY_GRAPH_CONFIG,
                        ),
                        type="default",
                    ),
                ],
                style={
                    "padding": "14px",
                    "overflow": "visible",
                },
            ),
            dbc.CardFooter(
                footer_content,
                style={
                    "opacity": 0.95,
                    "padding": "12px 14px",
                    "borderTop": "1px solid rgba(128, 128, 128, 0.18)",
                    "background": "rgba(128, 128, 128, 0.04)",
                },
            ),
        ],
        style={
            **ui_forms.build_workflow_subpanel_card_style(
                color_name=section.card_color,
            ),
            "flex": "1 1 0",
            "minWidth": f"{section.graph_min_width_px}px",
        },
        class_name="h-100",
    )


def _build_graph_style(section) -> dict[str, Any]:
    """
    Build the Plotly graph CSS style.

    The graph height is controlled by the runtime profile setting
    ``visualization.graph_height``.
    """
    graph_style = dict(styling.PLOTLY_GRAPH_STYLE)
    graph_style["height"] = _get_default_graph_height()
    graph_style["width"] = "100%"
    graph_style["display"] = "block"

    return graph_style


def _get_default_graph_height() -> str:
    """
    Return the default graph height from the runtime profile.
    """
    runtime_config = RuntimeConfig.from_default_profile()

    graph_height = runtime_config.get_str(
        "visualization.graph_height",
        default="850px",
    )

    graph_height = str(graph_height or "").strip()

    if not graph_height:
        return "850px"

    return graph_height


def _build_calibration_footer(section) -> dash.html.Div:
    """
    Build the calibration graph footer with fit outputs.
    """
    return dash.html.Div(
        [
            _build_fit_metric("Slope", section.ids.slope_out),
            _build_fit_metric("Intercept", section.ids.intercept_out),
            _build_fit_metric("R²", section.ids.r_squared_out),
        ],
        style={
            "display": "grid",
            "gridTemplateColumns": "repeat(3, minmax(120px, 1fr))",
            "gap": "10px",
            "alignItems": "stretch",
        },
    )


def _build_fit_metric(
    label: str,
    output_id: str,
) -> dash.html.Div:
    """
    Build one compact fit metric box.
    """
    return dash.html.Div(
        [
            dash.html.Div(
                label,
                style={
                    "fontWeight": "600",
                    "fontSize": "0.9rem",
                    "opacity": 0.85,
                },
            ),
            dash.html.Div(
                "",
                id=output_id,
                style={
                    "fontFamily": "monospace",
                    "fontSize": "0.95rem",
                    "marginTop": "2px",
                },
            ),
        ],
        style=ui_forms.build_metric_box_style(),
    )


def _build_status_block(section) -> dash.html.Div:
    """
    Build the status output.
    """
    return dash.html.Div(
        id=section.ids.apply_status,
        style={
            "marginTop": "8px",
        },
    )
