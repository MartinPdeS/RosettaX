# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any, Optional

import dash
import dash_bootstrap_components as dbc
import numpy as np
import plotly.graph_objs as go

from RosettaX.utils import styling


@dataclass(frozen=True)
class Scatter2DGraphIds:
    """
    Component IDs used by a reusable 2D scatter graph block.
    """

    graph: str
    axis_scale_toggle: str


@dataclass(frozen=True)
class Scatter2DTrace:
    """
    Input data for one 2D scatter trace.
    """

    x_values: Any
    y_values: Any
    name: str = ""
    text_values: Optional[Any] = None
    customdata: Optional[Any] = None
    marker_size: Optional[float] = None
    marker_opacity: float = 0.75
    mode: str = "markers"


class Scatter2DGraph:
    """
    Shared 2D scatter graph builder.

    Responsibilities
    ----------------
    - Apply consistent Plotly formatting to all 2D scatter plots.
    - Put the legend inside the graph when traces have names.
    - Provide a compact x log and y log toggle box below the graph.
    - Convert Dash toggle values into Plotly axis scale settings.

    Intended usage
    --------------
    Use ``build_component`` in page layouts.

    Use ``build_figure`` inside callbacks that construct the scatter plot.
    """

    x_log_value = "x_log"
    y_log_value = "y_log"

    default_height = "52vh"
    default_marker_size = 5.0
    default_font_size = 14
    default_tick_size = 12

    @classmethod
    def build_component(
        cls,
        *,
        component_ids: Scatter2DGraphIds,
        figure: Optional[go.Figure] = None,
        x_log_enabled: bool = False,
        y_log_enabled: bool = False,
        graph_style: Optional[dict[str, Any]] = None,
    ) -> dash.html.Div:
        """
        Build a reusable graph block with axis scale controls below it.
        """
        toggle_values: list[str] = []

        if x_log_enabled:
            toggle_values.append(
                cls.x_log_value,
            )

        if y_log_enabled:
            toggle_values.append(
                cls.y_log_value,
            )

        resolved_graph_style = {
            **styling.PLOTLY_GRAPH_STYLE,
            "height": cls.default_height,
        }

        if isinstance(graph_style, dict):
            resolved_graph_style.update(
                graph_style,
            )

        return dash.html.Div(
            [
                dash.dcc.Graph(
                    id=component_ids.graph,
                    figure=figure if figure is not None else cls.build_empty_figure(),
                    style=resolved_graph_style,
                    config=styling.PLOTLY_GRAPH_CONFIG,
                ),
                cls.build_axis_scale_control(
                    component_id=component_ids.axis_scale_toggle,
                    value=toggle_values,
                ),
            ]
        )

    @classmethod
    def build_axis_scale_control(
        cls,
        *,
        component_id: str,
        value: Optional[list[str]] = None,
    ) -> dbc.Card:
        """
        Build the compact x log and y log toggle box below the graph.
        """
        return dbc.Card(
            dbc.CardBody(
                [
                    dbc.Checklist(
                        id=component_id,
                        options=[
                            {
                                "label": "x log",
                                "value": cls.x_log_value,
                            },
                            {
                                "label": "y log",
                                "value": cls.y_log_value,
                            },
                        ],
                        value=value if isinstance(value, list) else [],
                        inline=True,
                        switch=True,
                        persistence=True,
                        persistence_type="session",
                    ),
                ],
                style={
                    "padding": "8px 10px",
                },
            ),
            style={
                "display": "inline-block",
                "marginTop": "8px",
                "borderRadius": "8px",
                "opacity": 0.95,
            },
        )

    @classmethod
    def axis_scale_from_toggle_values(
        cls,
        toggle_values: Any,
    ) -> tuple[str, str]:
        """
        Convert checklist values into x and y axis scale strings.
        """
        resolved_toggle_values = toggle_values if isinstance(toggle_values, list) else []

        x_axis_type = (
            "log"
            if cls.x_log_value in resolved_toggle_values
            else "linear"
        )

        y_axis_type = (
            "log"
            if cls.y_log_value in resolved_toggle_values
            else "linear"
        )

        return x_axis_type, y_axis_type

    @classmethod
    def build_figure(
        cls,
        *,
        traces: list[Scatter2DTrace],
        title: str,
        x_axis_title: str,
        y_axis_title: str,
        axis_scale_toggle_values: Any = None,
        show_grid: bool = True,
        hovermode: str = "closest",
        uirevision: str = "shared_scatter_2d",
    ) -> go.Figure:
        """
        Build a consistently formatted 2D scatter figure.
        """
        x_axis_type, y_axis_type = cls.axis_scale_from_toggle_values(
            axis_scale_toggle_values,
        )

        figure = go.Figure()

        for trace in traces:
            x_values = np.asarray(
                trace.x_values,
                dtype=float,
            ).reshape(-1)

            y_values = np.asarray(
                trace.y_values,
                dtype=float,
            ).reshape(-1)

            if x_values.size != y_values.size:
                raise ValueError(
                    f'Scatter trace "{trace.name}" has different x and y lengths.'
                )

            finite_mask = (
                np.isfinite(x_values)
                & np.isfinite(y_values)
            )

            if x_axis_type == "log":
                finite_mask &= x_values > 0.0

            if y_axis_type == "log":
                finite_mask &= y_values > 0.0

            x_values = x_values[finite_mask]
            y_values = y_values[finite_mask]

            text_values = None
            if trace.text_values is not None:
                text_values_array = np.asarray(
                    trace.text_values,
                    dtype=object,
                ).reshape(-1)

                if text_values_array.size == finite_mask.size:
                    text_values = text_values_array[finite_mask]

            customdata = None
            if trace.customdata is not None:
                customdata_array = np.asarray(
                    trace.customdata,
                    dtype=object,
                )

                if customdata_array.shape[0] == finite_mask.size:
                    customdata = customdata_array[finite_mask]

            figure.add_trace(
                go.Scattergl(
                    x=x_values,
                    y=y_values,
                    mode=trace.mode,
                    name=trace.name,
                    text=text_values,
                    customdata=customdata,
                    marker={
                        "size": (
                            cls.default_marker_size
                            if trace.marker_size is None
                            else float(trace.marker_size)
                        ),
                        "opacity": float(
                            trace.marker_opacity,
                        ),
                    },
                )
            )

        cls.apply_formatting(
            figure=figure,
            title=title,
            x_axis_title=x_axis_title,
            y_axis_title=y_axis_title,
            x_axis_type=x_axis_type,
            y_axis_type=y_axis_type,
            show_grid=show_grid,
            hovermode=hovermode,
            uirevision=uirevision,
        )

        return figure

    @classmethod
    def apply_formatting(
        cls,
        *,
        figure: go.Figure,
        title: str,
        x_axis_title: str,
        y_axis_title: str,
        x_axis_type: str = "linear",
        y_axis_type: str = "linear",
        show_grid: bool = True,
        hovermode: str = "closest",
        uirevision: str = "shared_scatter_2d",
    ) -> go.Figure:
        """
        Apply shared 2D scatter formatting to an existing Plotly figure.
        """
        trace_names = [
            str(trace.name).strip()
            for trace in figure.data
            if str(trace.name).strip()
        ]

        show_legend = len(trace_names) > 0

        figure.update_layout(
            title=title,
            xaxis_title=x_axis_title,
            yaxis_title=y_axis_title,
            hovermode=hovermode,
            uirevision=uirevision,
            separators=".,",
            showlegend=show_legend,
            margin={
                "l": 70,
                "r": 20,
                "t": 55,
                "b": 65,
            },
            font={
                "size": cls.default_font_size,
            },
            legend={
                "x": 0.99,
                "y": 0.99,
                "xanchor": "right",
                "yanchor": "top",
                "bgcolor": "rgba(255, 255, 255, 0.72)",
                "bordercolor": "rgba(0, 0, 0, 0.18)",
                "borderwidth": 1,
            },
        )

        figure.update_xaxes(
            type=x_axis_type,
            showgrid=show_grid,
            zeroline=False,
            tickfont={
                "size": cls.default_tick_size,
            },
        )

        figure.update_yaxes(
            type=y_axis_type,
            showgrid=show_grid,
            zeroline=False,
            tickfont={
                "size": cls.default_tick_size,
            },
        )

        return figure

    @classmethod
    def build_empty_figure(
        cls,
        *,
        message: str = "No 2D scatter data available.",
    ) -> go.Figure:
        """
        Build an empty formatted scatter figure.
        """
        figure = go.Figure()

        figure.add_annotation(
            text=message,
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
        )

        cls.apply_formatting(
            figure=figure,
            title="2D scatter",
            x_axis_title="x",
            y_axis_title="y",
            x_axis_type="linear",
            y_axis_type="linear",
            show_grid=True,
            hovermode="closest",
            uirevision="empty_shared_scatter_2d",
        )

        figure.update_layout(
            showlegend=False,
        )

        return figure