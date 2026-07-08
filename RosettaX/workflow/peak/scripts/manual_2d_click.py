# -*- coding: utf-8 -*-

import logging
from typing import Any, Optional

import dash
import dash_bootstrap_components as dbc
import numpy as np

from .base import (
    BasePeakProcess,
    PeakProcessResult,
    filter_edge_artifact_pairs,
    resolve_edge_artifact_filter_enabled,
)
from RosettaX.utils.io import column_copy
from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.workflow.plotting.scatter2d import Scatter2DGraph


logger = logging.getLogger(__name__)


class Manual2DClickProcess(BasePeakProcess):
    """
    Manual 2D peak picking process.

    The user selects an x detector channel and a y detector channel, then clicks
    points in the 2D scatter plot to add peak positions.

    The graph receives the cumulative list of picked points. The calibration
    table receives only the current click delta through new_peak_positions.
    """

    process_name = "Manual 2D"
    process_label = "Manual 2D"
    graph_type = "2d_scatter"
    sort_order = 30

    supports_manual_click = True
    supports_clear = True
    supports_automatic_action = False
    force_graph_visible = True

    dropdown_min_height_px = 72
    dropdown_option_height_px = 88
    dropdown_menu_max_height_px = 620
    default_snap_to_local_mode = True
    default_max_events_for_snap = 100_000

    def get_settings(self) -> list[dict[str, Any]]:
        """
        Return advanced settings for manual 2D peak picking.
        """
        return [
            {
                "name": "snap_to_local_mode",
                "label": "Snap click to local mode",
                "kind": "select",
                "default_value": "enabled" if self.default_snap_to_local_mode else "disabled",
                "options": [
                    {
                        "label": "Enabled",
                        "value": "enabled",
                    },
                    {
                        "label": "Disabled",
                        "value": "disabled",
                    },
                ],
                "help": (
                    "When enabled, a click is adjusted to the local density mode nearby "
                    "instead of using the raw click position."
                ),
            },
        ]

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
                self._build_vertical_spacer(height_px=8),
                self._build_log_scale_switch(
                    ids=ids,
                    label="Snap click to local mode",
                    setting_name="snap_to_local_mode",
                    enabled_by_default=self.default_snap_to_local_mode,
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
        enabled_by_default: bool = False,
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
            value=["enabled"] if enabled_by_default else [],
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
        selected_data: Any = None,
        existing_peak_lines_payload: Any,
        backend: Any = None,
        detector_channels: Optional[dict[str, Any]] = None,
        process_settings: Optional[dict[str, Any]] = None,
        runtime_config_data: Any = None,
        axis_scale_toggle_values: Any = None,
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
            "Manual 2D add_clicked_peak called with click_data=%r selected_data=%r "
            "existing_peak_lines_payload=%r",
            click_data,
            selected_data,
            existing_peak_lines_payload,
        )

        clicked_peak_position = self.extract_clicked_xy_position(click_data)
        selected_xy_range = self.extract_selected_xy_range(selected_data)

        if clicked_peak_position is None and selected_xy_range is None:
            logger.debug("No valid 2D clicked peak position or selection could be extracted.")
            return None

        reference_peak_position = (
            dict(clicked_peak_position)
            if clicked_peak_position is not None
            else {
                "x": float(
                    0.5 * (
                        selected_xy_range["x"][0]
                        + selected_xy_range["x"][1]
                    )
                ),
                "y": float(
                    0.5 * (
                        selected_xy_range["y"][0]
                        + selected_xy_range["y"][1]
                    )
                ),
            }
        )

        snapped_peak_position = dict(
            reference_peak_position,
        )
        snap_was_applied = False

        if self._snap_to_local_mode_is_enabled(
            process_settings=process_settings,
        ):
            resolved_peak_position = self.snap_clicked_peak_position(
                backend=backend,
                detector_channels=detector_channels,
                clicked_peak_position=reference_peak_position,
                selected_xy_range=selected_xy_range,
                process_settings=process_settings,
                runtime_config_data=runtime_config_data,
                axis_scale_toggle_values=axis_scale_toggle_values,
            )

            if resolved_peak_position is not None:
                snapped_peak_position = resolved_peak_position
                snap_was_applied = not (
                    np.isclose(
                        snapped_peak_position["x"],
                        reference_peak_position["x"],
                        rtol=1e-6,
                        atol=0.0,
                    )
                    and np.isclose(
                        snapped_peak_position["y"],
                        reference_peak_position["y"],
                        rtol=1e-6,
                        atol=0.0,
                    )
                )

        existing_peak_positions = self.extract_peak_positions_from_payload(
            existing_peak_lines_payload,
        )

        for existing_peak_position in existing_peak_positions:
            if (
                np.isclose(
                    existing_peak_position["x"],
                    snapped_peak_position["x"],
                    rtol=1e-9,
                    atol=0.0,
                )
                and np.isclose(
                    existing_peak_position["y"],
                    snapped_peak_position["y"],
                    rtol=1e-9,
                    atol=0.0,
                )
            ):
                return PeakProcessResult(
                    peak_positions=existing_peak_positions,
                    peak_lines_payload=self.build_peak_lines_payload(
                        peak_positions=existing_peak_positions,
                    ),
                    status=(
                        "Peak at "
                        f"x={snapped_peak_position['x']:.6g}, "
                        f"y={snapped_peak_position['y']:.6g} is already selected."
                    ),
                    new_peak_positions=[],
                    clear_existing_table_peaks=False,
                )

        next_peak_positions = [
            *existing_peak_positions,
            snapped_peak_position,
        ]

        peak_lines_payload = self.build_peak_lines_payload(
            peak_positions=next_peak_positions,
        )

        if snap_was_applied:
            status = (
                f"Added peak at "
                f"x={snapped_peak_position['x']:.6g}, "
                f"y={snapped_peak_position['y']:.6g} "
                f"(selected around x={reference_peak_position['x']:.6g}, "
                f"y={reference_peak_position['y']:.6g}). "
                f"{len(next_peak_positions)} peak(s) selected."
            )
        else:
            status = (
                f"Added peak at "
                f"x={snapped_peak_position['x']:.6g}, "
                f"y={snapped_peak_position['y']:.6g}. "
                f"{len(next_peak_positions)} peak(s) selected."
            )

        logger.debug(
            "Manual 2D click added clicked_peak_position=%r "
            "existing_peak_positions=%r next_peak_positions=%r "
            "peak_lines_payload=%r status=%r",
            snapped_peak_position,
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
                    "x": float(snapped_peak_position["x"]),
                    "y": float(snapped_peak_position["y"]),
                }
            ],
            clear_existing_table_peaks=False,
        )

    def _snap_to_local_mode_is_enabled(
        self,
        *,
        process_settings: Optional[dict[str, Any]],
    ) -> bool:
        """
        Return whether local snap mode is enabled.
        """
        if not isinstance(process_settings, dict):
            return self.default_snap_to_local_mode

        value = process_settings.get(
            "snap_to_local_mode",
            None,
        )

        if isinstance(value, str):
            return value == "enabled"

        if isinstance(value, (list, tuple, set)):
            return "enabled" in value

        if isinstance(value, bool):
            return value

        return self.default_snap_to_local_mode

    def snap_clicked_peak_position(
        self,
        *,
        backend: Any,
        detector_channels: Optional[dict[str, Any]],
        clicked_peak_position: dict[str, float],
        selected_xy_range: Optional[dict[str, tuple[float, float]]],
        process_settings: Optional[dict[str, Any]],
        runtime_config_data: Any,
        axis_scale_toggle_values: Any,
    ) -> Optional[dict[str, float]]:
        """
        Snap one clicked 2D position to the local modal density nearby.
        """
        if backend is None or not hasattr(backend, "fcs_file_path"):
            return None

        resolved_detector_channels = detector_channels or {}
        x_detector_column = resolved_detector_channels.get("x")
        y_detector_column = resolved_detector_channels.get("y")

        if not str(x_detector_column or "").strip():
            return None

        if not str(y_detector_column or "").strip():
            return None

        max_events = self._resolve_max_events_for_snap(
            runtime_config_data=runtime_config_data,
        )

        x_values = column_copy(
            fcs_file_path=backend.fcs_file_path,
            detector_column=str(x_detector_column),
            dtype=float,
            n=max_events,
        )
        y_values = column_copy(
            fcs_file_path=backend.fcs_file_path,
            detector_column=str(y_detector_column),
            dtype=float,
            n=max_events,
        )

        x_values = np.asarray(
            x_values,
            dtype=float,
        )
        y_values = np.asarray(
            y_values,
            dtype=float,
        )

        finite_mask = np.isfinite(x_values) & np.isfinite(y_values)
        x_values = x_values[finite_mask]
        y_values = y_values[finite_mask]

        if resolve_edge_artifact_filter_enabled(
            process_settings=process_settings,
            default=True,
        ):
            x_values, y_values = filter_edge_artifact_pairs(
                x_values=x_values,
                y_values=y_values,
                remove_x_min=True,
                remove_x_max=True,
                remove_y_min=True,
                remove_y_max=False,
            )

        if x_values.size < 16 or y_values.size < 16:
            return None

        use_log_x = self._x_axis_is_log(
            process_settings=process_settings,
            axis_scale_toggle_values=axis_scale_toggle_values,
            axis="x",
            clicked_value=clicked_peak_position["x"],
        )
        use_log_y = self._x_axis_is_log(
            process_settings=process_settings,
            axis_scale_toggle_values=axis_scale_toggle_values,
            axis="y",
            clicked_value=clicked_peak_position["y"],
        )

        positive_mask = np.ones(
            x_values.shape,
            dtype=bool,
        )

        if use_log_x:
            positive_mask &= x_values > 0.0

        if use_log_y:
            positive_mask &= y_values > 0.0

        x_values = x_values[positive_mask]
        y_values = y_values[positive_mask]

        if x_values.size < 16 or y_values.size < 16:
            return None

        if use_log_x and clicked_peak_position["x"] <= 0.0:
            return None

        if use_log_y and clicked_peak_position["y"] <= 0.0:
            return None

        working_x_values = np.log10(x_values) if use_log_x else x_values
        working_y_values = np.log10(y_values) if use_log_y else y_values
        working_clicked_x = float(
            np.log10(clicked_peak_position["x"])
            if use_log_x
            else clicked_peak_position["x"]
        )
        working_clicked_y = float(
            np.log10(clicked_peak_position["y"])
            if use_log_y
            else clicked_peak_position["y"]
        )

        histogram_bins = self._resolve_snap_histogram_bins(
            runtime_config_data=runtime_config_data,
        )
        histogram, x_edges, y_edges = np.histogram2d(
            working_x_values,
            working_y_values,
            bins=(histogram_bins, histogram_bins),
        )
        x_centers = 0.5 * (x_edges[:-1] + x_edges[1:])
        y_centers = 0.5 * (y_edges[:-1] + y_edges[1:])

        if selected_xy_range is not None:
            working_selected_xy_range = {
                "x": (
                    float(
                        np.log10(selected_xy_range["x"][0])
                        if use_log_x
                        else selected_xy_range["x"][0]
                    ),
                    float(
                        np.log10(selected_xy_range["x"][1])
                        if use_log_x
                        else selected_xy_range["x"][1]
                    ),
                ),
                "y": (
                    float(
                        np.log10(selected_xy_range["y"][0])
                        if use_log_y
                        else selected_xy_range["y"][0]
                    ),
                    float(
                        np.log10(selected_xy_range["y"][1])
                        if use_log_y
                        else selected_xy_range["y"][1]
                    ),
                ),
            }

            snapped_working_point = self._find_histogram_peak_in_selected_range_2d(
                histogram=np.asarray(histogram, dtype=float),
                x_centers=np.asarray(x_centers, dtype=float),
                y_centers=np.asarray(y_centers, dtype=float),
                selected_xy_range=working_selected_xy_range,
                fallback_point={
                    "x": working_clicked_x,
                    "y": working_clicked_y,
                },
            )
        else:
            snapped_working_point = self._find_local_mode_2d(
                x_values=working_x_values,
                y_values=working_y_values,
                clicked_x=working_clicked_x,
                clicked_y=working_clicked_y,
            )

        if snapped_working_point is None:
            return None

        snapped_x = float(
            np.power(10.0, snapped_working_point["x"])
        ) if use_log_x else float(snapped_working_point["x"])
        snapped_y = float(
            np.power(10.0, snapped_working_point["y"])
        ) if use_log_y else float(snapped_working_point["y"])

        if not np.isfinite(snapped_x) or not np.isfinite(snapped_y):
            return None

        return {
            "x": snapped_x,
            "y": snapped_y,
        }

    def _resolve_snap_histogram_bins(
        self,
        *,
        runtime_config_data: Any,
    ) -> int:
        """
        Resolve histogram bins per axis used for manual 2D snapping.
        """
        runtime_config = RuntimeConfig.from_dict(
            runtime_config_data if isinstance(runtime_config_data, dict) else None
        )

        return int(
            max(
                24,
                min(
                    160,
                    runtime_config.get_int(
                        "calibration.n_bins_for_plots",
                        default=100,
                    ),
                ),
            )
        )

    def _resolve_max_events_for_snap(
        self,
        *,
        runtime_config_data: Any,
    ) -> int:
        """
        Resolve the event count used for local snapping.
        """
        runtime_config = RuntimeConfig.from_dict(
            runtime_config_data if isinstance(runtime_config_data, dict) else None
        )

        return int(
            runtime_config.get_int(
                "calibration.max_events_for_analysis",
                default=self.default_max_events_for_snap,
            )
        )

    def _x_axis_is_log(
        self,
        *,
        process_settings: Optional[dict[str, Any]],
        axis_scale_toggle_values: Any,
        axis: str,
        clicked_value: float,
    ) -> bool:
        """
        Return whether one manual 2D axis is currently log scaled.
        """
        if clicked_value <= 0.0:
            return False

        if isinstance(process_settings, dict):
            process_value = process_settings.get(
                f"{axis}_log_scale",
                None,
            )

            if isinstance(process_value, str):
                return process_value == "enabled"

            if isinstance(process_value, (list, tuple, set)):
                return "enabled" in process_value

            if isinstance(process_value, bool):
                return process_value

        expected_toggle = (
            Scatter2DGraph.x_log_value
            if axis == "x"
            else Scatter2DGraph.y_log_value
        )

        if isinstance(axis_scale_toggle_values, str):
            return axis_scale_toggle_values in (
                "log",
                expected_toggle,
            )

        if isinstance(axis_scale_toggle_values, (list, tuple, set)):
            return (
                "log" in axis_scale_toggle_values
                or expected_toggle in axis_scale_toggle_values
            )

        return False

    def _find_local_mode_2d(
        self,
        *,
        x_values: np.ndarray,
        y_values: np.ndarray,
        clicked_x: float,
        clicked_y: float,
    ) -> Optional[dict[str, float]]:
        """
        Estimate a local 2D mode near the clicked position.
        """
        x_values = np.asarray(
            x_values,
            dtype=float,
        )
        y_values = np.asarray(
            y_values,
            dtype=float,
        )

        finite_mask = np.isfinite(x_values) & np.isfinite(y_values)
        x_values = x_values[finite_mask]
        y_values = y_values[finite_mask]

        if x_values.size < 16 or not np.isfinite(clicked_x) or not np.isfinite(clicked_y):
            return None

        distances = np.hypot(
            x_values - float(clicked_x),
            y_values - float(clicked_y),
        )
        neighbor_count = max(
            128,
            min(
                x_values.size,
                int(x_values.size * 0.03),
                4096,
            ),
        )

        radius = float(
            np.partition(
                distances,
                neighbor_count - 1,
            )[neighbor_count - 1]
        )

        if radius <= 0.0 or not np.isfinite(radius):
            radius = float(
                max(
                    np.std(x_values) * 0.02,
                    np.std(y_values) * 0.02,
                    np.finfo(float).eps,
                )
            )

        local_mask = distances <= radius
        local_x_values = x_values[local_mask]
        local_y_values = y_values[local_mask]

        if local_x_values.size < 16:
            return {
                "x": float(clicked_x),
                "y": float(clicked_y),
            }

        x_lower = float(np.min(local_x_values))
        x_upper = float(np.max(local_x_values))
        y_lower = float(np.min(local_y_values))
        y_upper = float(np.max(local_y_values))

        if x_lower == x_upper or y_lower == y_upper:
            return {
                "x": float(np.median(local_x_values)),
                "y": float(np.median(local_y_values)),
            }

        bins_per_axis = int(
            max(
                16,
                min(
                    48,
                    np.sqrt(local_x_values.size),
                ),
            )
        )

        histogram, x_edges, y_edges = np.histogram2d(
            local_x_values,
            local_y_values,
            bins=(bins_per_axis, bins_per_axis),
            range=[
                [x_lower, x_upper],
                [y_lower, y_upper],
            ],
        )

        if histogram.size == 0:
            return {
                "x": float(clicked_x),
                "y": float(clicked_y),
            }

        modal_x_index, modal_y_index = np.unravel_index(
            int(np.argmax(histogram)),
            histogram.shape,
        )

        x_left = float(x_edges[modal_x_index])
        x_right = float(x_edges[modal_x_index + 1])
        y_lower_edge = float(y_edges[modal_y_index])
        y_upper_edge = float(y_edges[modal_y_index + 1])

        x_mask = (
            (local_x_values >= x_left)
            & (
                (local_x_values <= x_right)
                if modal_x_index == histogram.shape[0] - 1
                else (local_x_values < x_right)
            )
        )
        y_mask = (
            (local_y_values >= y_lower_edge)
            & (
                (local_y_values <= y_upper_edge)
                if modal_y_index == histogram.shape[1] - 1
                else (local_y_values < y_upper_edge)
            )
        )
        modal_mask = x_mask & y_mask

        if not np.any(modal_mask):
            return {
                "x": 0.5 * (x_left + x_right),
                "y": 0.5 * (y_lower_edge + y_upper_edge),
            }

        return {
            "x": float(np.median(local_x_values[modal_mask])),
            "y": float(np.median(local_y_values[modal_mask])),
        }

    def _find_histogram_peak_in_selected_range_2d(
        self,
        *,
        histogram: np.ndarray,
        x_centers: np.ndarray,
        y_centers: np.ndarray,
        selected_xy_range: dict[str, tuple[float, float]],
        fallback_point: dict[str, float],
    ) -> Optional[dict[str, float]]:
        """
        Return the densest histogram bin center inside the selected 2D ROI.
        """
        histogram = np.asarray(histogram, dtype=float)
        x_centers = np.asarray(x_centers, dtype=float)
        y_centers = np.asarray(y_centers, dtype=float)

        if (
            histogram.ndim != 2
            or histogram.shape != (x_centers.size, y_centers.size)
            or x_centers.size == 0
            or y_centers.size == 0
        ):
            return None

        x_lower = float(min(selected_xy_range["x"]))
        x_upper = float(max(selected_xy_range["x"]))
        y_lower = float(min(selected_xy_range["y"]))
        y_upper = float(max(selected_xy_range["y"]))

        x_mask = (
            np.isfinite(x_centers)
            & (x_centers >= x_lower)
            & (x_centers <= x_upper)
        )
        y_mask = (
            np.isfinite(y_centers)
            & (y_centers >= y_lower)
            & (y_centers <= y_upper)
        )

        if not np.any(x_mask) or not np.any(y_mask):
            return {
                "x": float(fallback_point["x"]),
                "y": float(fallback_point["y"]),
            }

        x_indices = np.flatnonzero(x_mask)
        y_indices = np.flatnonzero(y_mask)
        roi_histogram = histogram[np.ix_(x_indices, y_indices)]

        if roi_histogram.size == 0 or not np.any(np.isfinite(roi_histogram)):
            return {
                "x": float(fallback_point["x"]),
                "y": float(fallback_point["y"]),
            }

        roi_maximum = float(np.nanmax(roi_histogram))

        if not np.isfinite(roi_maximum):
            return {
                "x": float(fallback_point["x"]),
                "y": float(fallback_point["y"]),
            }

        candidate_offsets = np.argwhere(
            np.isclose(
                roi_histogram,
                roi_maximum,
                rtol=1e-9,
                atol=0.0,
            )
        )

        if candidate_offsets.size == 0:
            return {
                "x": float(fallback_point["x"]),
                "y": float(fallback_point["y"]),
            }

        candidate_points = [
            (
                float(x_centers[x_indices[offset_x]]),
                float(y_centers[y_indices[offset_y]]),
            )
            for offset_x, offset_y in candidate_offsets
        ]

        chosen_x, chosen_y = min(
            candidate_points,
            key=lambda point: (
                (point[0] - float(fallback_point["x"])) ** 2
                + (point[1] - float(fallback_point["y"])) ** 2
            ),
        )

        return {
            "x": chosen_x,
            "y": chosen_y,
        }

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

    def extract_selected_xy_range(
        self,
        selected_data: Any,
    ) -> Optional[dict[str, tuple[float, float]]]:
        """
        Extract x and y selection ranges from Plotly selectedData.
        """
        if not isinstance(selected_data, dict):
            return None

        selected_range = selected_data.get("range")

        if isinstance(selected_range, dict):
            x_range = selected_range.get("x")
            y_range = selected_range.get("y")

            if (
                isinstance(x_range, (list, tuple))
                and len(x_range) >= 2
                and isinstance(y_range, (list, tuple))
                and len(y_range) >= 2
            ):
                try:
                    x_lower = float(x_range[0])
                    x_upper = float(x_range[1])
                    y_lower = float(y_range[0])
                    y_upper = float(y_range[1])
                except Exception:
                    return None

                if (
                    np.isfinite(x_lower)
                    and np.isfinite(x_upper)
                    and np.isfinite(y_lower)
                    and np.isfinite(y_upper)
                ):
                    return {
                        "x": (
                            min(x_lower, x_upper),
                            max(x_lower, x_upper),
                        ),
                        "y": (
                            min(y_lower, y_upper),
                            max(y_lower, y_upper),
                        ),
                    }

        points = selected_data.get("points")

        if not isinstance(points, list) or not points:
            return None

        x_values: list[float] = []
        y_values: list[float] = []

        for point in points:
            if not isinstance(point, dict):
                continue

            if "x" not in point or "y" not in point:
                continue

            try:
                x_value = float(point["x"])
                y_value = float(point["y"])
            except Exception:
                continue

            if np.isfinite(x_value) and np.isfinite(y_value):
                x_values.append(x_value)
                y_values.append(y_value)

        if not x_values or not y_values:
            return None

        return {
            "x": (
                float(min(x_values)),
                float(max(x_values)),
            ),
            "y": (
                float(min(y_values)),
                float(max(y_values)),
            ),
        }


PROCESS = Manual2DClickProcess()
