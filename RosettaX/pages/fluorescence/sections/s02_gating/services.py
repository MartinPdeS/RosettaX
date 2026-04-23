# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any, Optional
import logging

import dash
import plotly.graph_objs as go

from RosettaX.utils import casting
from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.utils.reader import FCSFile
from RosettaX.utils import plottings


@dataclass(frozen=True)
class CallbackInputs:
    triggered_id: Any
    debug_enabled: bool
    scattering_channel: str
    nbins: int
    max_events: int
    yscale_selection: Any
    manual_threshold: Optional[float]
    stored_threshold: Optional[float]
    must_estimate: bool


@dataclass(frozen=True)
class ParsedScatteringLimits:
    max_events: int
    nbins: int


@dataclass(frozen=True)
class RuntimeDefaults:
    yscale_value: list[str]
    debug_switch_value: list[str]
    nbins_value: int
    max_events_value: int

    def to_tuple(self) -> tuple[Any, Any, Any, Any]:
        return (
            self.yscale_value,
            self.debug_switch_value,
            self.nbins_value,
            self.max_events_value,
        )


@dataclass(frozen=True)
class VisualizationDefaults:
    marker_size: float
    line_width: float
    font_size: float
    tick_size: float
    show_grid: bool


@dataclass
class GatingResult:
    figure: Any = dash.no_update
    scattering_threshold_store: Any = dash.no_update
    scattering_threshold_input_value: Any = dash.no_update

    def to_tuple(self) -> tuple[Any, Any, Any]:
        return (
            self.figure,
            self.scattering_threshold_store,
            self.scattering_threshold_input_value,
        )


def is_switch_enabled(switch_value: Any) -> bool:
    return isinstance(switch_value, list) and ("enabled" in switch_value)


def clean_channel_name(scattering_channel: Any) -> str:
    if scattering_channel is None:
        return ""

    scattering_channel_clean = str(scattering_channel).strip()

    if scattering_channel_clean.lower() == "none":
        return ""

    return scattering_channel_clean


def extract_stored_threshold(scattering_threshold_store_data: Any) -> Optional[float]:
    if not isinstance(scattering_threshold_store_data, dict):
        return None

    return casting.as_float(scattering_threshold_store_data.get("threshold"))


def build_threshold_store_payload(
    *,
    scattering_channel: str,
    threshold_value: float,
    nbins: int,
) -> dict[str, Any]:
    return {
        "scattering_channel": scattering_channel or None,
        "threshold": float(threshold_value),
        "nbins": int(nbins),
    }


def parse_limits(
    *,
    max_events_for_plots: Any,
    scattering_nbins: Any,
    default_max_events: int,
    default_nbins: int,
) -> ParsedScatteringLimits:
    resolved_max_events = casting.as_int(
        max_events_for_plots if max_events_for_plots is not None else default_max_events,
        default=default_max_events,
        min_value=1_000,
        max_value=5_000_000,
    )

    resolved_nbins = casting.as_int(
        scattering_nbins,
        default=default_nbins,
        min_value=10,
        max_value=5000,
    )

    return ParsedScatteringLimits(
        max_events=resolved_max_events,
        nbins=resolved_nbins,
    )


def resolve_runtime_defaults(runtime_config_data: Any) -> RuntimeDefaults:
    runtime_config = RuntimeConfig.from_dict(
        runtime_config_data if isinstance(runtime_config_data, dict) else None
    )

    histogram_scale = runtime_config.get_str("calibration.histogram_scale", default="log")
    resolved_show_graphs = runtime_config.get_show_graphs(default=True)
    resolved_nbins = runtime_config.get_int("calibration.n_bins_for_plots", default=100)
    resolved_max_events = runtime_config.get_int("calibration.max_events_for_analysis", default=10000)

    return RuntimeDefaults(
        yscale_value=["log"] if histogram_scale == "log" else [],
        debug_switch_value=["enabled"] if resolved_show_graphs else [],
        nbins_value=resolved_nbins,
        max_events_value=resolved_max_events,
    )


def resolve_visualization_defaults(runtime_config_data: Any) -> VisualizationDefaults:
    runtime_config = RuntimeConfig.from_dict(
        runtime_config_data if isinstance(runtime_config_data, dict) else None
    )

    return VisualizationDefaults(
        marker_size=runtime_config.get_float("visualization.default_marker_size", default=8.0),
        line_width=runtime_config.get_float("visualization.default_line_width", default=2.0),
        font_size=runtime_config.get_float("visualization.default_font_size", default=14.0),
        tick_size=runtime_config.get_float("visualization.default_tick_size", default=12.0),
        show_grid=runtime_config.get_bool("visualization.show_grid_by_default", default=True),
    )


def build_debug_container_style(
    debug_switch_value: Any,
    *,
    logger: logging.Logger,
) -> dict[str, str]:
    debug_enabled = is_switch_enabled(debug_switch_value)

    logger.debug(
        "build_debug_container_style called with debug_switch_value=%r resolved_debug_enabled=%r",
        debug_switch_value,
        debug_enabled,
    )

    return {"display": "block"} if debug_enabled else {"display": "none"}


def parse_callback_inputs(
    *,
    threshold_input_value: Any,
    scattering_channel: Any,
    scattering_nbins: Any,
    yscale_selection: Any,
    debug_switch_value: Any,
    scattering_threshold_store_data: Any,
    max_events_for_plots: Any,
    runtime_config_data: Any,
    find_threshold_button_id: str,
    detector_dropdown_id: str,
    nbins_input_id: str,
) -> CallbackInputs:
    triggered_id = dash.callback_context.triggered_id
    debug_enabled = is_switch_enabled(debug_switch_value)

    runtime_config = RuntimeConfig.from_dict(
        runtime_config_data if isinstance(runtime_config_data, dict) else None
    )

    default_max_events = runtime_config.get_int("calibration.max_events_for_analysis", default=10000)
    default_nbins = runtime_config.get_int("calibration.n_bins_for_plots", default=100)

    parsed_scattering_limits = parse_limits(
        max_events_for_plots=max_events_for_plots,
        scattering_nbins=scattering_nbins,
        default_max_events=default_max_events,
        default_nbins=default_nbins,
    )

    scattering_channel_clean = clean_channel_name(scattering_channel)
    stored_threshold = extract_stored_threshold(scattering_threshold_store_data)
    manual_threshold = casting.as_float(threshold_input_value)

    must_estimate = triggered_id in {
        find_threshold_button_id,
        detector_dropdown_id,
        nbins_input_id,
    }

    return CallbackInputs(
        triggered_id=triggered_id,
        debug_enabled=debug_enabled,
        scattering_channel=scattering_channel_clean,
        nbins=parsed_scattering_limits.nbins,
        max_events=parsed_scattering_limits.max_events,
        yscale_selection=yscale_selection,
        manual_threshold=manual_threshold,
        stored_threshold=stored_threshold,
        must_estimate=must_estimate,
    )


def resolve_threshold(
    *,
    page_backend: Any,
    must_estimate: bool,
    scattering_channel: str,
    nbins: int,
    max_events: int,
    manual_threshold: Optional[float],
    stored_threshold: Optional[float],
    logger: logging.Logger,
) -> tuple[float, Any]:
    logger.debug(
        "resolve_threshold called with must_estimate=%r scattering_channel=%r nbins=%r "
        "max_events=%r manual_threshold=%r stored_threshold=%r",
        must_estimate,
        scattering_channel,
        nbins,
        max_events,
        manual_threshold,
        stored_threshold,
    )

    if must_estimate:
        if page_backend is None:
            logger.debug("resolve_threshold cannot estimate because page_backend is None.")
            return 0.0, dash.no_update

        if not scattering_channel:
            logger.debug("resolve_threshold cannot estimate because scattering_channel is empty.")
            return 0.0, dash.no_update

        try:
            response = page_backend.process_scattering(
                {
                    "operation": "estimate_scattering_threshold",
                    "column": scattering_channel,
                    "nbins": int(nbins),
                    "number_of_points": int(max_events),
                }
            )
        except Exception:
            logger.exception(
                "Backend threshold estimation failed for scattering_channel=%r nbins=%r max_events=%r",
                scattering_channel,
                nbins,
                max_events,
            )
            raise

        resolved_threshold_value = casting.as_float(response.get("threshold")) or 0.0

        logger.debug(
            "resolve_threshold estimated threshold_value=%r from response=%r",
            resolved_threshold_value,
            response,
        )
        return float(resolved_threshold_value), f"{float(resolved_threshold_value):.6g}"

    if manual_threshold is not None:
        logger.debug("resolve_threshold using manual_threshold=%r", manual_threshold)
        return float(manual_threshold), dash.no_update

    if stored_threshold is not None:
        logger.debug("resolve_threshold using stored_threshold=%r", stored_threshold)
        return float(stored_threshold), dash.no_update

    logger.debug("resolve_threshold fell back to default threshold=0.0")
    return 0.0, dash.no_update


def build_scattering_histogram(
    *,
    page_backend: Any,
    debug_enabled: bool,
    scattering_channel: str,
    nbins: int,
    max_events: int,
    yscale_selection: Any,
    threshold_value: float,
    runtime_config_data: Any,
    logger: logging.Logger,
) -> go.Figure:
    logger.debug(
        "build_scattering_histogram called with debug_enabled=%r scattering_channel=%r "
        "nbins=%r max_events=%r yscale_selection=%r threshold_value=%r",
        debug_enabled,
        scattering_channel,
        nbins,
        max_events,
        yscale_selection,
        threshold_value,
    )

    visualization_defaults = resolve_visualization_defaults(runtime_config_data)

    logger.debug(
        "Resolved visualization defaults: marker_size=%r line_width=%r font_size=%r "
        "tick_size=%r show_grid=%r",
        visualization_defaults.marker_size,
        visualization_defaults.line_width,
        visualization_defaults.font_size,
        visualization_defaults.tick_size,
        visualization_defaults.show_grid,
    )

    if not debug_enabled:
        return plottings._make_info_figure(
            "Debug graph is disabled.",
            font_size=visualization_defaults.font_size,
        )

    if page_backend is None:
        return plottings._make_info_figure(
            "Backend is not available.",
            font_size=visualization_defaults.font_size,
        )

    file_path = getattr(page_backend, "file_path", None)
    if not file_path:
        file_path = getattr(page_backend, "fcs_file_path", None)

    if not scattering_channel:
        return plottings._make_info_figure(
            "Select a scattering detector first.",
            font_size=visualization_defaults.font_size,
        )

    if not file_path:
        return plottings._make_info_figure(
            "No FCS file is loaded.",
            font_size=visualization_defaults.font_size,
        )

    use_log_scale = isinstance(yscale_selection, list) and ("log" in yscale_selection)

    try:
        with FCSFile(str(file_path), writable=False) as fcs_file:
            scattering_values = fcs_file.column_copy(
                scattering_channel,
                dtype=float,
                n=max_events,
            )
    except Exception:
        logger.exception(
            "Failed to read scattering histogram values from file_path=%r channel=%r max_events=%r",
            file_path,
            scattering_channel,
            max_events,
        )
        raise

    if scattering_values is None or len(scattering_values) == 0:
        return plottings._make_info_figure(
            "No data available for the selected detector.",
            font_size=visualization_defaults.font_size,
        )

    figure = plottings.make_histogram_with_lines(
        values=scattering_values,
        nbins=nbins,
        xaxis_title="Scattering (a.u.)",
        line_positions=[float(threshold_value)],
        line_labels=[f"{float(threshold_value):.3g}"],
        line_width=visualization_defaults.line_width,
        font_size=visualization_defaults.font_size,
        tick_size=visualization_defaults.tick_size,
    )

    figure.update_yaxes(type="log" if use_log_scale else "linear")
    figure.update_layout(
        separators=".,",
        uirevision=f"fluorescence_gating|{file_path}|{scattering_channel}",
    )

    figure = plottings.apply_default_visual_style(
        figure,
        marker_size=visualization_defaults.marker_size,
        line_width=visualization_defaults.line_width,
        font_size=visualization_defaults.font_size,
        tick_size=visualization_defaults.tick_size,
        show_grid=visualization_defaults.show_grid,
    )

    return figure


def run_gating_callback(
    *,
    callback_inputs: CallbackInputs,
    page_backend: Any,
    runtime_config_data: Any,
    logger: logging.Logger,
) -> GatingResult:
    logger.debug("run_gating_callback called with callback_inputs=%r", callback_inputs)

    try:
        threshold_value, threshold_input_output = resolve_threshold(
            page_backend=page_backend,
            must_estimate=callback_inputs.must_estimate,
            scattering_channel=callback_inputs.scattering_channel,
            nbins=callback_inputs.nbins,
            max_events=callback_inputs.max_events,
            manual_threshold=callback_inputs.manual_threshold,
            stored_threshold=callback_inputs.stored_threshold,
            logger=logger,
        )

        threshold_store_payload = build_threshold_store_payload(
            scattering_channel=callback_inputs.scattering_channel,
            threshold_value=threshold_value,
            nbins=callback_inputs.nbins,
        )

        figure = build_scattering_histogram(
            page_backend=page_backend,
            debug_enabled=callback_inputs.debug_enabled,
            scattering_channel=callback_inputs.scattering_channel,
            nbins=callback_inputs.nbins,
            max_events=callback_inputs.max_events,
            yscale_selection=callback_inputs.yscale_selection,
            threshold_value=threshold_value,
            runtime_config_data=runtime_config_data,
            logger=logger,
        )

    except Exception:
        logger.exception(
            "Failed in run_gating_callback for callback_inputs=%r",
            callback_inputs,
        )
        raise

    result = GatingResult(
        figure=figure,
        scattering_threshold_store=threshold_store_payload,
        scattering_threshold_input_value=threshold_input_output,
    )

    logger.debug("run_gating_callback returning result=%r", result)
    return result