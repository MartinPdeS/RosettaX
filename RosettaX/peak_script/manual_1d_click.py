# -*- coding: utf-8 -*-

from typing import Any, Optional
import logging

import dash

from .base import BasePeakProcess
from .base import PeakProcessResult


logger = logging.getLogger(__name__)


class Manual1DClickProcess(BasePeakProcess):
    """
    Manual 1D peak picking process.

    The user selects one detector channel, then clicks the 1D histogram to add
    peak positions.
    """

    process_name = "1D manual click"
    process_label = "1D manual click"
    graph_type = "1d_histogram"
    sort_order = 10

    supports_manual_click = True
    supports_clear = True
    supports_automatic_action = False
    force_graph_visible = True

    def get_required_detector_channels(self) -> list[str]:
        return ["primary"]

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
                            "Detector channel:",
                            style={
                                "marginBottom": "6px",
                                "fontWeight": 500,
                            },
                        ),
                        dash.dcc.Dropdown(
                            id=ids.process_detector_dropdown(
                                process_name=self.process_name,
                                channel_name="primary",
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
                        dash.html.Button(
                            "Clear picked peaks",
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
        clicked_peak_position = self.extract_clicked_x_position(click_data)

        if clicked_peak_position is None:
            logger.debug(
                "Manual 1D click received no valid clicked_peak_position. click_data=%r",
                click_data,
            )
            return None

        existing_peak_positions = self.extract_peak_positions_from_payload(
            existing_peak_lines_payload
        )

        next_peak_positions = sorted(
            [
                *existing_peak_positions,
                float(clicked_peak_position),
            ]
        )

        peak_lines_payload = self.build_peak_lines_payload(
            peak_positions=next_peak_positions,
        )

        status = (
            f"Added peak at {float(clicked_peak_position):.6g}. "
            f"{len(next_peak_positions)} peak(s) selected."
        )

        logger.debug(
            "Manual 1D click added clicked_peak_position=%r "
            "next_peak_positions=%r peak_lines_payload=%r",
            clicked_peak_position,
            next_peak_positions,
            peak_lines_payload,
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
            status="Cleared manual 1D peaks.",
        )

    def build_peak_lines_payload(
        self,
        *,
        peak_positions: list[float],
    ) -> dict[str, list[Any]]:
        return {
            "positions": [float(value) for value in peak_positions],
            "labels": [
                f"Manual peak {index + 1}"
                for index in range(len(peak_positions))
            ],
            "x_positions": [],
            "y_positions": [],
            "points": [],
        }

    def extract_peak_positions_from_payload(
        self,
        peak_lines_payload: Any,
    ) -> list[float]:
        if not isinstance(peak_lines_payload, dict):
            return []

        peak_positions: list[float] = []

        for value in peak_lines_payload.get("positions") or []:
            try:
                peak_positions.append(float(value))
            except Exception:
                logger.debug(
                    "Ignoring non numeric manual 1D peak position value=%r",
                    value,
                )

        return peak_positions

    def extract_clicked_x_position(
        self,
        click_data: Any,
    ) -> Optional[float]:
        if not isinstance(click_data, dict):
            return None

        points = click_data.get("points")

        if not isinstance(points, list) or not points:
            return None

        first_point = points[0]

        if not isinstance(first_point, dict):
            return None

        if "x" not in first_point:
            logger.debug(
                "Plotly clickData point does not contain x coordinate: %r",
                first_point,
            )
            return None

        try:
            return float(first_point["x"])
        except Exception:
            logger.debug(
                "Could not convert Plotly click x value to float: %r",
                first_point.get("x"),
            )
            return None


PROCESS = Manual1DClickProcess()