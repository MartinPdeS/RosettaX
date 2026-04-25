# -*- coding: utf-8 -*-

import logging
from typing import Any, Optional

import dash
import dash_bootstrap_components as dbc

from .base import BasePeakProcess
from .base import PeakProcessResult


logger = logging.getLogger(__name__)


class Manual2DClickProcess(BasePeakProcess):
    """
    Manual 2D peak picking process.

    The user selects an x detector channel and a y detector channel, then clicks
    points in the 2D scatter plot to add peak positions.

    The graph receives the cumulative list of picked points. The calibration
    table receives only the current click delta through new_peak_positions.
    """

    process_name = "2D manual click"
    process_label = "2D manual click"
    graph_type = "2d_scatter"
    sort_order = 30

    supports_manual_click = True
    supports_clear = True
    supports_automatic_action = False
    force_graph_visible = True

    dropdown_min_height_px = 72
    dropdown_option_height_px = 88
    dropdown_menu_max_height_px = 620

    def get_required_detector_channels(self) -> list[str]:
        """
        Return detector channels required by this process.

        Returns
        -------
        list[str]
            Required channel names.
        """
        return [
            "x",
            "y",
        ]

    def build_controls(
        self,
        *,
        ids: Any,
    ) -> dash.html.Div:
        """
        Build Dash controls for manual 2D peak picking.

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
                    label="X detector channel",
                    channel_name="x",
                ),
                self._build_vertical_spacer(height_px=16),
                self._build_detector_dropdown_block(
                    ids=ids,
                    label="Y detector channel",
                    channel_name="y",
                ),
                self._build_vertical_spacer(height_px=18),
                self._build_display_options(ids=ids),
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
                    placeholder=f"Select {channel_name} channel",
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

    def _build_display_options(
        self,
        *,
        ids: Any,
    ) -> dash.html.Div:
        """
        Build display option switches.

        Parameters
        ----------
        ids:
            Peak section id factory.

        Returns
        -------
        dash.html.Div
            Display options block.
        """
        return dash.html.Div(
            [
                self._build_log_scale_switch(
                    ids=ids,
                    label="Log x scale",
                    setting_name="x_log_scale",
                ),
                self._build_vertical_spacer(height_px=8),
                self._build_log_scale_switch(
                    ids=ids,
                    label="Log y scale",
                    setting_name="y_log_scale",
                ),
            ],
            style={
                "display": "block",
                "width": "100%",
            },
        )

    def _build_log_scale_switch(
        self,
        *,
        ids: Any,
        label: str,
        setting_name: str,
    ) -> dbc.Checklist:
        """
        Build one log scale switch.

        Parameters
        ----------
        ids:
            Peak section id factory.

        label:
            Display label.

        setting_name:
            Logical process setting name.

        Returns
        -------
        dbc.Checklist
            Bootstrap switch.
        """
        return dbc.Checklist(
            id=ids.process_setting(
                process_name=self.process_name,
                setting_name=setting_name,
            ),
            options=[
                {
                    "label": label,
                    "value": "enabled",
                }
            ],
            value=[],
            switch=True,
            persistence=True,
            persistence_type="session",
            style={
                "display": "block",
                "width": "fit-content",
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
        Add one clicked 2D point to the cumulative peak payload.

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
        logger.debug(
            "Manual 2D add_clicked_peak called with click_data=%r "
            "existing_peak_lines_payload=%r",
            click_data,
            existing_peak_lines_payload,
        )

        clicked_peak_position = self.extract_clicked_xy_position(
            click_data,
        )

        if clicked_peak_position is None:
            logger.debug("No valid 2D clicked peak position could be extracted.")
            return None

        existing_peak_positions = self.extract_peak_positions_from_payload(
            existing_peak_lines_payload,
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
            "existing_peak_positions=%r next_peak_positions=%r "
            "peak_lines_payload=%r status=%r",
            clicked_peak_position,
            existing_peak_positions,
            next_peak_positions,
            peak_lines_payload,
            status,
        )

        return PeakProcessResult(
            peak_positions=next_peak_positions,
            peak_lines_payload=peak_lines_payload,
            status=status,
            new_peak_positions=[
                {
                    "x": float(clicked_peak_position["x"]),
                    "y": float(clicked_peak_position["y"]),
                }
            ],
            clear_existing_table_peaks=False,
        )

    def clear_peaks(self) -> PeakProcessResult:
        """
        Clear all manually picked 2D peaks.

        Returns
        -------
        PeakProcessResult
            Empty peak result.
        """
        return PeakProcessResult(
            peak_positions=[],
            peak_lines_payload=self.build_empty_peak_lines_payload(),
            status="Cleared manual 2D peaks.",
            new_peak_positions=[],
            clear_existing_table_peaks=True,
        )

    def build_peak_lines_payload(
        self,
        *,
        peak_positions: list[dict[str, float]],
    ) -> dict[str, list[Any]]:
        """
        Build the graph annotation payload for selected 2D peaks.

        Parameters
        ----------
        peak_positions:
            Cumulative 2D peak positions.

        Returns
        -------
        dict[str, list[Any]]
            Peak annotation payload.
        """
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
        """
        Extract cumulative 2D peak positions from an existing payload.

        Parameters
        ----------
        peak_lines_payload:
            Existing peak line payload.

        Returns
        -------
        list[dict[str, float]]
            Existing 2D peak positions.
        """
        if not isinstance(peak_lines_payload, dict):
            return []

        points = peak_lines_payload.get("points")

        if isinstance(points, list):
            return self.extract_peak_positions_from_point_payload(
                points,
            )

        return self.extract_peak_positions_from_xy_payload(
            x_values=peak_lines_payload.get("x_positions"),
            y_values=peak_lines_payload.get("y_positions"),
        )

    def extract_peak_positions_from_point_payload(
        self,
        points: list[Any],
    ) -> list[dict[str, float]]:
        """
        Extract 2D peak positions from a list of point dictionaries.

        Parameters
        ----------
        points:
            Point payload list.

        Returns
        -------
        list[dict[str, float]]
            Parsed 2D peak positions.
        """
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
        """
        Extract 2D peak positions from separate x and y arrays.

        Parameters
        ----------
        x_values:
            X coordinate values.

        y_values:
            Y coordinate values.

        Returns
        -------
        list[dict[str, float]]
            Parsed 2D peak positions.
        """
        if not isinstance(x_values, list) or not isinstance(y_values, list):
            return []

        peak_positions: list[dict[str, float]] = []

        for x_value, y_value in zip(
            x_values,
            y_values,
            strict=False,
        ):
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
        """
        Extract x and y coordinates from Plotly clickData.

        Parameters
        ----------
        click_data:
            Plotly clickData payload.

        Returns
        -------
        Optional[dict[str, float]]
            Clicked 2D position, or None.
        """
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