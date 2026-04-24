# -*- coding: utf-8 -*-

from typing import Any
import logging

import dash

from .base import BasePeakProcess
from .base import PeakProcessResult


logger = logging.getLogger(__name__)


class Automatic1DPeaksProcess(BasePeakProcess):
    """
    Automatic 1D peak detection process.
    """

    process_name = "1D automatic peaks"
    process_label = "1D automatic peaks"
    graph_type = "1d_histogram"
    sort_order = 20

    supports_manual_click = False
    supports_clear = False
    supports_automatic_action = True
    force_graph_visible = False

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
                            id=self.build_detector_dropdown_id(
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
                        dash.html.Div(
                            "Number of peaks to look for:",
                            style={
                                "marginRight": "8px",
                            },
                        ),
                        dash.dcc.Input(
                            id=ids.peak_count_input,
                            type="number",
                            min=1,
                            step=1,
                            value=3,
                            style={
                                "width": "120px",
                            },
                            debounce=True,
                            persistence=True,
                            persistence_type="session",
                        ),
                        dash.html.Button(
                            "Find peaks",
                            id=self.build_action_button_id(
                                action_name="run",
                            ),
                            n_clicks=0,
                            style={
                                "marginLeft": "16px",
                            },
                        ),
                        self.build_status_component(),
                    ],
                    style={
                        "display": "flex",
                        "alignItems": "center",
                    },
                ),
            ],
            id=self.build_controls_container_id(),
            style={"display": "none"},
        )

    def run_automatic_action(
        self,
        *,
        backend: Any,
        detector_channels: dict[str, Any],
        peak_count: Any,
        max_events_for_analysis: int,
    ) -> PeakProcessResult | None:
        detector_column = detector_channels.get("primary")

        if backend is None:
            return PeakProcessResult(
                peak_positions=[],
                peak_lines_payload=self.build_peak_lines_payload(
                    peak_positions=[],
                ),
                status="Backend is not initialized.",
            )

        if detector_column is None or str(detector_column).strip() == "":
            return PeakProcessResult(
                peak_positions=[],
                peak_lines_payload=self.build_peak_lines_payload(
                    peak_positions=[],
                ),
                status="Select a detector first.",
            )

        peak_detection_result = backend.find_scattering_peaks(
            detector_column=str(detector_column),
            max_peaks=int(peak_count),
            max_events_for_analysis=int(max_events_for_analysis),
            debug=False,
        )

        peak_positions = [
            float(value)
            for value in peak_detection_result.peak_positions.tolist()
        ]

        return PeakProcessResult(
            peak_positions=peak_positions,
            peak_lines_payload=self.build_peak_lines_payload(
                peak_positions=peak_positions,
            ),
            status=f"Detected {len(peak_positions)} peak(s).",
        )

    def build_peak_lines_payload(
        self,
        *,
        peak_positions: list[float],
    ) -> dict[str, list[Any]]:
        return {
            "positions": [
                float(value)
                for value in peak_positions
            ],
            "labels": [
                f"Peak {index + 1}"
                for index in range(len(peak_positions))
            ],
            "x_positions": [],
            "y_positions": [],
            "points": [],
        }


PROCESS = Automatic1DPeaksProcess()