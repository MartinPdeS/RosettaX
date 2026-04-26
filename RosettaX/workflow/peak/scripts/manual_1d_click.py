# -*- coding: utf-8 -*-

import logging
from typing import Any, Optional

import dash
import dash_bootstrap_components as dbc

from .base import BasePeakProcess, PeakProcessResult


logger = logging.getLogger(__name__)


class Manual1DClickProcess(BasePeakProcess):
    """
    Manual 1D peak picking process.

    The user selects one detector channel, then clicks the 1D histogram to add
    peak positions.

    The graph receives the cumulative list of picked peaks. The calibration
    table receives only the current click delta through new_peak_positions.
    """

    process_name = "Manual 1D"
    process_label = "Manual 1D"
    graph_type = "1d_histogram"
    sort_order = 10

    supports_manual_click = True
    supports_clear = True
    supports_automatic_action = False
    force_graph_visible = True

    dropdown_option_height_px = 50
    dropdown_menu_max_height_px = 500

    def get_required_detector_channels(self) -> list[str]:
        """
        Return detector channels required by this process.

        Returns
        -------
        list[str]
            Required channel names.
        """
        return [
            "primary",
        ]

    def build_controls(
        self,
        *,
        ids: Any,
    ) -> dash.html.Div:
        """
        Build Dash controls for manual 1D peak picking.

        Parameters
        ----------
        ids:
            Peak section id factory.

        Returns
        -------
        dash.html.Div
            Process controls.
        """
        return dash.html.Div(
            [
                self._build_detector_dropdown_block(
                    ids=ids,
                    label="Detector channel",
                    channel_name="primary",
                ),
                self._build_vertical_spacer(height_px=16),
                self._build_action_row(ids=ids),
            ],
            id=ids.process_controls_container(
                process_name=self.process_name,
            ),
            style={
                "display": "none",
                "width": "100%",
                "maxWidth": "100%",
            },
        )

    def _build_vertical_spacer(
        self,
        *,
        height_px: int,
    ) -> dash.html.Div:
        """
        Build a vertical spacer.

        Parameters
        ----------
        height_px:
            Spacer height in pixels.

        Returns
        -------
        dash.html.Div
            Spacer.
        """
        return dash.html.Div(
            style={
                "height": f"{height_px}px",
            },
        )

    def _build_detector_dropdown_block(
        self,
        *,
        ids: Any,
        label: str,
        channel_name: str,
    ) -> dash.html.Div:
        """
        Build one full-width detector dropdown block.

        Parameters
        ----------
        ids:
            Peak section id factory.

        label:
            Display label.

        channel_name:
            Logical detector channel name.

        Returns
        -------
        dash.html.Div
            Detector dropdown block.
        """
        return dash.html.Div(
            [
                dash.html.Div(
                    label,
                    style={
                        "marginBottom": "6px",
                        "fontWeight": 500,
                    },
                ),
                dash.dcc.Dropdown(
                    id=ids.process_detector_dropdown(
                        process_name=self.process_name,
                        channel_name=channel_name,
                    ),
                    placeholder="Select detector channel",
                    optionHeight=self.dropdown_option_height_px,
                    maxHeight=self.dropdown_menu_max_height_px,
                    searchable=True,
                    clearable=False,
                    persistence=True,
                    persistence_type="session",
                    style={
                        "width": "100%",
                    },
                ),
            ],
            style={
                "width": "100%",
                "maxWidth": "100%",
                "display": "block",
            },
        )

    def _build_action_row(
        self,
        *,
        ids: Any,
    ) -> dash.html.Div:
        """
        Build action controls and status output.

        Parameters
        ----------
        ids:
            Peak section id factory.

        Returns
        -------
        dash.html.Div
            Action row.
        """
        return dash.html.Div(
            [
                dbc.Button(
                    "Clear picked peaks",
                    id=ids.process_action_button(
                        process_name=self.process_name,
                        action_name="clear",
                    ),
                    n_clicks=0,
                    color="secondary",
                    outline=True,
                    size="sm",
                ),
                self.build_status_component(
                    ids=ids,
                ),
            ],
            style={
                "display": "flex",
                "alignItems": "center",
                "gap": "12px",
                "flexWrap": "wrap",
                "width": "100%",
            },
        )

    def add_clicked_peak(
        self,
        *,
        click_data: Any,
        existing_peak_lines_payload: Any,
    ) -> Optional[PeakProcessResult]:
        """
        Add one clicked peak to the cumulative peak payload.

        Parameters
        ----------
        click_data:
            Plotly clickData payload.

        existing_peak_lines_payload:
            Existing cumulative peak annotation payload.

        Returns
        -------
        Optional[PeakProcessResult]
            Peak process result, or None if the click is invalid.
        """
        clicked_peak_position = self.extract_clicked_x_position(
            click_data,
        )

        if clicked_peak_position is None:
            logger.debug(
                "Manual 1D click received no valid clicked_peak_position. click_data=%r",
                click_data,
            )

            return None

        clicked_peak_position = float(clicked_peak_position)

        existing_peak_positions = self.extract_peak_positions_from_payload(
            existing_peak_lines_payload,
        )

        next_peak_positions = sorted(
            [
                *existing_peak_positions,
                clicked_peak_position,
            ]
        )

        peak_lines_payload = self.build_peak_lines_payload(
            peak_positions=next_peak_positions,
        )

        status = (
            f"Added peak at {clicked_peak_position:.6g}. "
            f"{len(next_peak_positions)} peak(s) selected."
        )

        logger.debug(
            "Manual 1D click added clicked_peak_position=%r "
            "existing_peak_positions=%r next_peak_positions=%r "
            "peak_lines_payload=%r",
            clicked_peak_position,
            existing_peak_positions,
            next_peak_positions,
            peak_lines_payload,
        )

        return PeakProcessResult(
            peak_positions=next_peak_positions,
            peak_lines_payload=peak_lines_payload,
            status=status,
            new_peak_positions=[
                clicked_peak_position,
            ],
            clear_existing_table_peaks=False,
        )

    def clear_peaks(self) -> PeakProcessResult:
        """
        Clear all manually picked 1D peaks.

        Returns
        -------
        PeakProcessResult
            Empty peak result.
        """
        return PeakProcessResult(
            peak_positions=[],
            peak_lines_payload=self.build_empty_peak_lines_payload(),
            status="Cleared manual 1D peaks.",
            new_peak_positions=[],
            clear_existing_table_peaks=True,
        )

    def build_peak_lines_payload(
        self,
        *,
        peak_positions: list[float],
    ) -> dict[str, list[Any]]:
        """
        Build the graph annotation payload for selected 1D peaks.

        Parameters
        ----------
        peak_positions:
            Cumulative peak positions.

        Returns
        -------
        dict[str, list[Any]]
            Peak line payload.
        """
        return {
            "positions": [
                float(value)
                for value in peak_positions
            ],
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
        """
        Extract cumulative peak positions from an existing payload.

        Parameters
        ----------
        peak_lines_payload:
            Existing peak line payload.

        Returns
        -------
        list[float]
            Existing peak positions.
        """
        if not isinstance(peak_lines_payload, dict):
            return []

        peak_positions: list[float] = []

        for value in peak_lines_payload.get("positions") or []:
            try:
                peak_positions.append(
                    float(value),
                )

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
        """
        Extract the x coordinate from Plotly clickData.

        Parameters
        ----------
        click_data:
            Plotly clickData payload.

        Returns
        -------
        Optional[float]
            Clicked x coordinate, or None.
        """
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