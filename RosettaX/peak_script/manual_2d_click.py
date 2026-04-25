# -*- coding: utf-8 -*-

from typing import Any, Optional
import logging

import dash
import dash_bootstrap_components as dbc

from .base import BasePeakProcess
from .base import PeakProcessResult


logger = logging.getLogger(__name__)


class Manual2DClickProcess(BasePeakProcess):
    """
    Manual 2D peak picking process.

    The user selects an x channel and a y channel, then clicks points in the 2D
    scatter plot to add peak positions.

    Only the x coordinate is written to the calibration table, because the
    calibration reference table expects one measured peak position.
    """

    process_name = "2D manual click"
    process_label = "2D manual click"
    graph_type = "2d_scatter"
    sort_order = 30

    supports_manual_click = True
    supports_clear = True
    supports_automatic_action = False
    force_graph_visible = True

    def get_required_detector_channels(self) -> list[str]:
        return ["x", "y"]

    def build_controls(
        self,
        *,
        ids: Any,
    ) -> dash.html.Div:
        return dash.html.Div(
            [
                dash.html.Div(
                    [
                        dash.html.Div(
                            "X detector channel:",
                            style={
                                "marginBottom": "6px",
                                "fontWeight": 500,
                            },
                        ),
                        dash.dcc.Dropdown(
                            id=ids.process_detector_dropdown(
                                process_name=self.process_name,
                                channel_name="x",
                            ),
                            style={
                                "width": "500px",
                            },
                            optionHeight=50,
                            maxHeight=500,
                            searchable=True,
                            persistence=True,
                            persistence_type="session",
                        ),
                    ],
                    style={
                        "marginBottom": "12px",
                    },
                ),
                dash.html.Div(
                    [
                        dash.html.Div(
                            "Y detector channel:",
                            style={
                                "marginBottom": "6px",
                                "fontWeight": 500,
                            },
                        ),
                        dash.dcc.Dropdown(
                            id=ids.process_detector_dropdown(
                                process_name=self.process_name,
                                channel_name="y",
                            ),
                            style={
                                "width": "500px",
                            },
                            optionHeight=50,
                            maxHeight=500,
                            searchable=True,
                            persistence=True,
                            persistence_type="session",
                        ),
                    ],
                    style={
                        "marginBottom": "12px",
                    },
                ),
                dash.html.Div(
                    [
                        dbc.Checklist(
                            id=ids.process_setting(
                                process_name=self.process_name,
                                setting_name="x_log_scale",
                            ),
                            options=[
                                {
                                    "label": "Log x scale",
                                    "value": "enabled",
                                }
                            ],
                            value=[],
                            switch=True,
                            persistence=True,
                            persistence_type="session",
                            style={
                                "marginRight": "18px",
                            },
                        ),
                        dbc.Checklist(
                            id=ids.process_setting(
                                process_name=self.process_name,
                                setting_name="y_log_scale",
                            ),
                            options=[
                                {
                                    "label": "Log y scale",
                                    "value": "enabled",
                                }
                            ],
                            value=[],
                            switch=True,
                            persistence=True,
                            persistence_type="session",
                        ),
                    ],
                    style={
                        "display": "flex",
                        "alignItems": "center",
                        "marginBottom": "12px",
                    },
                ),
                dash.html.Div(
                    [
                        dash.html.Button(
                            "Clear",
                            id=ids.process_action_button(
                                process_name=self.process_name,
                                action_name="clear",
                            ),
                            n_clicks=0,
                        ),
                        self.build_status_component(
                            ids=ids,
                        ),
                    ],
                    style={
                        "display": "flex",
                        "alignItems": "center",
                    },
                ),
            ],
            id=ids.process_controls_container(
                process_name=self.process_name,
            ),
            style={"display": "none"},
        )

    def add_clicked_peak(
        self,
        *,
        click_data: Any,
        existing_peak_lines_payload: Any,
    ) -> Optional[PeakProcessResult]:
        logger.debug(
            "Manual 2D add_clicked_peak called with click_data=%r "
            "existing_peak_lines_payload=%r",
            click_data,
            existing_peak_lines_payload,
        )

        clicked_peak_position = self.extract_clicked_xy_position(click_data)

        if clicked_peak_position is None:
            logger.debug("No valid 2D clicked peak position could be extracted.")
            return None

        existing_peak_positions = self.extract_peak_positions_from_payload(
            existing_peak_lines_payload
        )

        next_peak_positions = [
            *existing_peak_positions,
            clicked_peak_position,
        ]

        peak_lines_payload = self.build_peak_lines_payload(
            peak_positions=next_peak_positions,
        )

        status = (
            f"Added peak at "
            f"x={clicked_peak_position['x']:.6g}, "
            f"y={clicked_peak_position['y']:.6g}. "
            f"{len(next_peak_positions)} peak(s) selected."
        )

        logger.debug(
            "Manual 2D click added clicked_peak_position=%r "
            "next_peak_positions=%r peak_lines_payload=%r status=%r",
            clicked_peak_position,
            next_peak_positions,
            peak_lines_payload,
            status,
        )

        return PeakProcessResult(
            peak_positions=next_peak_positions,
            peak_lines_payload=peak_lines_payload,
            status=status,
        )

    def clear_peaks(self) -> PeakProcessResult:
        return PeakProcessResult(
            peak_positions=[],
            peak_lines_payload=self.build_peak_lines_payload(
                peak_positions=[],
            ),
            status="Cleared manual 2D peaks.",
        )

    def build_peak_lines_payload(
        self,
        *,
        peak_positions: list[dict[str, float]],
    ) -> dict[str, list[Any]]:
        x_positions = [
            float(position["x"])
            for position in peak_positions
        ]

        y_positions = [
            float(position["y"])
            for position in peak_positions
        ]

        labels = [
            f"Manual 2D peak {index + 1}"
            for index in range(len(peak_positions))
        ]

        return {
            "positions": x_positions,
            "x_positions": x_positions,
            "y_positions": y_positions,
            "points": [
                {
                    "x": float(position["x"]),
                    "y": float(position["y"]),
                }
                for position in peak_positions
            ],
            "labels": labels,
        }

    def extract_peak_positions_from_payload(
        self,
        peak_lines_payload: Any,
    ) -> list[dict[str, float]]:
        if not isinstance(peak_lines_payload, dict):
            return []

        points = peak_lines_payload.get("points")

        if isinstance(points, list):
            return self.extract_peak_positions_from_point_payload(points)

        return self.extract_peak_positions_from_xy_payload(
            x_values=peak_lines_payload.get("x_positions"),
            y_values=peak_lines_payload.get("y_positions"),
        )

    def extract_peak_positions_from_point_payload(
        self,
        points: list[Any],
    ) -> list[dict[str, float]]:
        peak_positions: list[dict[str, float]] = []

        for point in points:
            if not isinstance(point, dict):
                logger.debug(
                    "Ignoring non mapping 2D peak point=%r",
                    point,
                )
                continue

            try:
                peak_positions.append(
                    {
                        "x": float(point["x"]),
                        "y": float(point["y"]),
                    }
                )
            except Exception:
                logger.debug(
                    "Ignoring invalid 2D peak point=%r",
                    point,
                )

        return peak_positions

    def extract_peak_positions_from_xy_payload(
        self,
        *,
        x_values: Any,
        y_values: Any,
    ) -> list[dict[str, float]]:
        if not isinstance(x_values, list) or not isinstance(y_values, list):
            return []

        peak_positions: list[dict[str, float]] = []

        for x_value, y_value in zip(x_values, y_values, strict=False):
            try:
                peak_positions.append(
                    {
                        "x": float(x_value),
                        "y": float(y_value),
                    }
                )
            except Exception:
                logger.debug(
                    "Ignoring invalid 2D peak coordinate x=%r y=%r",
                    x_value,
                    y_value,
                )

        return peak_positions

    def extract_clicked_xy_position(
        self,
        click_data: Any,
    ) -> Optional[dict[str, float]]:
        logger.debug("Manual 2D received click_data=%r", click_data)

        if not isinstance(click_data, dict):
            return None

        points = click_data.get("points")

        if not isinstance(points, list) or not points:
            return None

        first_point = points[0]

        if not isinstance(first_point, dict):
            return None

        if "x" not in first_point or "y" not in first_point:
            logger.debug(
                "Plotly clickData point does not contain x/y coordinates: %r",
                first_point,
            )
            return None

        try:
            return {
                "x": float(first_point["x"]),
                "y": float(first_point["y"]),
            }
        except Exception:
            logger.debug(
                "Could not convert Plotly click x/y values to float: x=%r y=%r",
                first_point.get("x"),
                first_point.get("y"),
            )
            return None


PROCESS = Manual2DClickProcess()