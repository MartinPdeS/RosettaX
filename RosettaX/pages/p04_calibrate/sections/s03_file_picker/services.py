# -*- coding: utf-8 -*-

import base64
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import plotly.graph_objects as go

from RosettaX.utils import checks, plottings
from RosettaX.utils.reader import FCSFile
from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.utils.upload_limits import format_upload_size, get_max_upload_bytes
from RosettaX.workflow.apply_calibration.fluorescence import apply_legacy_calibration_to_series
from RosettaX.workflow.apply_calibration.io import resolve_uploaded_fcs_paths
from RosettaX.workflow.plotting.scatter2d import Scatter2DGraph
from RosettaX.pages.p04_calibrate.sections.s02_calibration_picker import services as calibration_picker_services


logger = logging.getLogger(__name__)


_SAVED_UPLOAD_TIMESTAMP = re.compile(r"_\d{8}_\d{6}_\d{6}$")


def build_upload_prompt_text() -> str:
    """
    Build the default FCS upload prompt text.
    """
    return f"Upload one or more FCS files. Maximum file size: {format_upload_size()}."


def build_upload_directory() -> Path:
    """
    Build and create the local upload directory.

    Returns
    -------
    Path
        Local upload directory used by the apply calibration file picker.
    """
    upload_directory = Path.home() / ".rosettax" / "uploads"

    upload_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    logger.debug(
        "Resolved FilePicker upload_directory=%r",
        str(upload_directory),
    )

    return upload_directory


def validate_page_contract(
    *,
    page: Any,
) -> None:
    """
    Validate the page ID contract required by the file picker section.

    Programming errors must fail loudly. Missing IDs indicate an invalid page
    integration.
    """
    required_attributes = [
        "ids",
        "ids.FilePicker",
        "ids.FilePicker.upload",
        "ids.FilePicker.column_consistency_alert",
        "ids.FilePicker.preview_file",
        "ids.FilePicker.preview_channel",
        "ids.FilePicker.preview_graph",
        "ids.FilePicker.preview_status",
        "ids.Stores",
        "ids.Stores.uploaded_fcs_path_store",
    ]

    for required_attribute in required_attributes:
        current_object = page

        for attribute_name in required_attribute.split("."):
            if not hasattr(current_object, attribute_name):
                raise AttributeError(
                    f"FilePicker requires page.{required_attribute}, "
                    f"but missing attribute {attribute_name!r} while resolving "
                    f"{required_attribute!r}."
                )

            current_object = getattr(
                current_object,
                attribute_name,
            )


def validate_checks_contract() -> None:
    """
    Validate the FCS consistency checker contract.

    Programming errors must fail loudly. The file picker relies on the current
    ``FCSMultiFileConsistencyChecker`` API.
    """
    if not hasattr(checks, "FCSMultiFileConsistencyChecker"):
        raise AttributeError(
            "RosettaX.utils.checks must expose FCSMultiFileConsistencyChecker. "
            "The old check_multifiles_consistency helper is no longer used here."
        )

    checker_class = checks.FCSMultiFileConsistencyChecker

    if not hasattr(checker_class, "check_multifiles_consistency"):
        raise AttributeError(
            "FCSMultiFileConsistencyChecker must define "
            "check_multifiles_consistency()."
        )


def validate_upload_payload(
    *,
    contents_list: list[str],
    filenames: list[str],
) -> None:
    """
    Validate Dash upload payload consistency.
    """
    if len(contents_list) != len(filenames):
        raise ValueError(
            "Upload payload is malformed because contents_list and filenames "
            f"have different lengths: {len(contents_list)} != {len(filenames)}."
        )

    for filename in filenames:
        if not str(filename).strip():
            raise ValueError("Upload payload contains an empty filename.")


def save_uploaded_files(
    *,
    upload_directory: Path,
    contents_list: list[str],
    filenames: list[str],
) -> list[Path]:
    """
    Save all uploaded files.

    Parameters
    ----------
    upload_directory:
        Directory where uploaded files are written.
    contents_list:
        Dash upload contents payloads.
    filenames:
        Original upload filenames.

    Returns
    -------
    list[Path]
        Saved local file paths.
    """
    saved_paths: list[Path] = []

    for contents, filename in zip(
        contents_list,
        filenames,
        strict=False,
    ):
        saved_path = save_single_uploaded_file(
            upload_directory=upload_directory,
            contents=contents,
            filename=filename,
        )

        saved_paths.append(
            saved_path,
        )

    if not saved_paths:
        raise RuntimeError("No uploaded FCS files were saved.")

    return saved_paths


def save_single_uploaded_file(
    *,
    upload_directory: Path,
    contents: str,
    filename: str,
) -> Path:
    """
    Save one uploaded file to the local upload directory.
    """
    logger.debug(
        "save_single_uploaded_file called with filename=%r upload_directory=%r",
        filename,
        str(upload_directory),
    )

    if "," not in contents:
        raise ValueError(
            f"Uploaded file {filename!r} has malformed Dash contents payload."
        )

    _, encoded_payload = contents.split(
        ",",
        1,
    )

    raw_bytes = base64.b64decode(
        encoded_payload,
        validate=True,
    )

    if len(raw_bytes) > get_max_upload_bytes():
        raise ValueError(
            "Uploaded file exceeds the maximum supported size of "
            f"{format_upload_size()}."
        )

    original_path = Path(
        str(filename),
    )

    safe_stem = original_path.stem.strip() or "uploaded_file"
    safe_suffix = original_path.suffix if original_path.suffix else ".fcs"

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S_%f",
    )

    output_path = upload_directory / f"{safe_stem}_{timestamp}{safe_suffix}"

    output_path.write_bytes(
        raw_bytes,
    )

    if not output_path.exists():
        raise FileNotFoundError(
            f"Uploaded file was not written successfully: {output_path}"
        )

    if output_path.stat().st_size == 0:
        raise ValueError(
            f"Uploaded file was written but is empty: {output_path}"
        )

    logger.debug(
        "Saved uploaded file successfully to output_path=%r byte_count=%r",
        str(output_path),
        len(raw_bytes),
    )

    return output_path


def check_saved_files_consistency(
    *,
    saved_paths: list[Path],
) -> dict[str, Any]:
    """
    Check uploaded FCS files for consistency.
    """
    validate_checks_contract()

    checker = checks.FCSMultiFileConsistencyChecker(
        file_paths=[
            str(path)
            for path in saved_paths
        ]
    )

    consistency_report = checker.check_multifiles_consistency()

    if not isinstance(consistency_report, dict):
        raise TypeError(
            "FCSMultiFileConsistencyChecker.check_multifiles_consistency() "
            f"must return a dict, got {type(consistency_report).__name__}."
        )

    if "are_all_files_consistent" not in consistency_report:
        raise KeyError(
            "Consistency report is missing required key "
            "'are_all_files_consistent'."
        )

    logger.debug(
        "check_saved_files_consistency returning consistency_report=%r",
        consistency_report,
    )

    return consistency_report


def build_success_alert_payload(
    *,
    saved_paths: list[Path],
    consistency_report: dict[str, Any],
) -> tuple[Any, str, bool]:
    """
    Build the upload success or warning alert payload.
    """
    if not saved_paths:
        raise ValueError("Cannot build upload success payload without saved files.")

    if not consistency_report.get(
        "are_all_files_consistent",
        True,
    ):
        mismatch_details = consistency_report.get(
            "mismatch_details",
            [],
        )

        if mismatch_details:
            preview = ", ".join(
                str(detail)
                for detail in mismatch_details[:3]
            )

        else:
            preview = "Uploaded files are inconsistent."

        return preview, "warning", True

    if len(saved_paths) == 1:
        return f"Uploaded 1 FCS file: {saved_paths[0].name}", "success", True

    return f"Uploaded {len(saved_paths)} FCS files.", "success", True


def build_preview_file_selection(
    uploaded_fcs_paths: Any,
    *,
    current_value: Any = None,
) -> tuple[list[dict[str, str]], str | None]:
    """Build stable file options for one or many uploaded FCS paths."""
    paths = resolve_uploaded_fcs_paths(uploaded_fcs_paths)
    options = [
        {
            "label": _SAVED_UPLOAD_TIMESTAMP.sub("", Path(path).stem) + Path(path).suffix,
            "value": path,
        }
        for path in paths
    ]
    current_path = str(current_value or "").strip()
    selected_path = current_path if current_path in paths else (paths[0] if paths else None)
    return options, selected_path


def resolve_selected_preview_path(
    *,
    selected_file: Any,
    uploaded_fcs_paths: Any,
) -> str | None:
    """Resolve a selected preview path only when it belongs to the upload store."""
    paths = resolve_uploaded_fcs_paths(uploaded_fcs_paths)
    selected_path = str(selected_file or "").strip()
    if selected_path and selected_path in paths:
        return selected_path
    return paths[0] if paths else None


def build_preview_channel_selection(
    *,
    selected_file: Any,
    uploaded_fcs_paths: Any,
    selected_calibration_summary: Any = None,
    current_value: Any = None,
) -> tuple[list[dict[str, str]], str | None]:
    """Read FCS channel names and build the preview channel selection."""
    selected_path = resolve_selected_preview_path(
        selected_file=selected_file,
        uploaded_fcs_paths=uploaded_fcs_paths,
    )
    if selected_path is None:
        return [], None

    try:
        with FCSFile(selected_path) as fcs_file:
            channel_names = [
                str(name) for name in fcs_file.get_column_names() if str(name).strip()
            ]
    except Exception:
        logger.exception("Failed to read preview channels from selected_path=%r", selected_path)
        return [], None

    affected_source_channels = _resolve_preview_source_channels(selected_calibration_summary)

    if affected_source_channels:
        channel_names = [
            name
            for name in channel_names
            if name in affected_source_channels
        ]

    options = [{"label": name, "value": name} for name in channel_names]
    current_channel = str(current_value or "").strip()
    selected_channel = (
        current_channel
        if current_channel in channel_names
        else (channel_names[0] if channel_names else None)
    )
    return options, selected_channel


def build_empty_preview_figure(message: str) -> go.Figure:
    """Build a compact placeholder for the input FCS histogram."""
    figure = go.Figure()
    figure.update_layout(
        template="plotly_white",
        margin={"l": 55, "r": 25, "t": 30, "b": 50},
        xaxis={"visible": False},
        yaxis={"visible": False},
        annotations=[
            {
                "text": str(message),
                "xref": "paper",
                "yref": "paper",
                "x": 0.5,
                "y": 0.5,
                "showarrow": False,
            }
        ],
    )
    return figure


def _resolve_preview_graph_style(runtime_config: RuntimeConfig) -> dict[str, str]:
    return {"height": runtime_config.get_graph_height(default="360px")}


def _resolve_preview_calibration_summaries(calibration_summary_data: Any) -> list[dict[str, Any]]:
    return calibration_picker_services.normalize_calibration_summaries(calibration_summary_data)


def _resolve_preview_source_channels(calibration_summary_data: Any) -> list[str]:
    source_channels: list[str] = []

    for calibration_summary in _resolve_preview_calibration_summaries(calibration_summary_data):
        source_channel = str(calibration_summary.get("source_channel", "")).strip()

        if source_channel and source_channel not in source_channels:
            source_channels.append(source_channel)

    return source_channels


def _resolve_preview_calibration_summary(
    calibration_summary_data: Any,
    *,
    selected_channel: str,
) -> dict[str, Any] | None:
    calibration_summaries = _resolve_preview_calibration_summaries(calibration_summary_data)

    if not calibration_summaries:
        return None

    for calibration_summary in calibration_summaries:
        source_channel = str(calibration_summary.get("source_channel", "")).strip()

        if source_channel and source_channel == selected_channel:
            return calibration_summary

    return calibration_summaries[0]


def _build_histogram_result_from_values(
    values: Any,
    *,
    n_bins_for_plots: int,
    use_log_x_bins: bool,
) -> plottings.HistogramResult:
    values_array = np.asarray(values, dtype=float)
    values_array = values_array[np.isfinite(values_array)]

    if values_array.size == 0:
        raise ValueError("No finite signal values available to build histogram.")

    if use_log_x_bins:
        values_array = values_array[values_array > 0.0]

        if values_array.size == 0:
            raise ValueError("No positive signal values available for logarithmic histogram bins.")

        lower_edge = float(np.min(values_array))
        upper_edge = float(np.max(values_array))

        if not np.isfinite(lower_edge) or not np.isfinite(upper_edge):
            raise ValueError("No finite signal values available to build histogram.")

        if lower_edge == upper_edge:
            upper_edge = lower_edge * 1.01

        edges = np.geomspace(
            lower_edge,
            upper_edge,
            num=int(n_bins_for_plots) + 1,
        )
        counts, edges = np.histogram(values_array, bins=edges)
        centers = np.sqrt(edges[:-1] * edges[1:])

    else:
        counts, edges = np.histogram(values_array, bins=int(n_bins_for_plots))
        centers = 0.5 * (edges[:-1] + edges[1:])

    return plottings.HistogramResult(
        values=np.asarray(values_array, dtype=float),
        counts=np.asarray(counts, dtype=float),
        edges=np.asarray(edges, dtype=float),
        centers=np.asarray(centers, dtype=float),
    )


def resolve_preview_control_defaults(runtime_config_data: Any = None) -> dict[str, Any]:
    """Resolve the file preview control defaults from the active profile."""
    runtime_config = RuntimeConfig.from_dict(
        runtime_config_data if isinstance(runtime_config_data, dict) else None
    )

    calibration_config = (
        runtime_config_data.get("calibration", {})
        if isinstance(runtime_config_data, dict)
        else {}
    )
    if not isinstance(calibration_config, dict):
        calibration_config = {}

    histogram_xscale = str(
        calibration_config.get("histogram_xscale", "log")
    ).strip().lower()
    histogram_yscale = str(
        calibration_config.get(
            "histogram_yscale",
            calibration_config.get("histogram_scale", "log"),
        )
    ).strip().lower()

    return {
        "graph_height": runtime_config.get_graph_height(default="360px"),
        "x_log_values": ["enabled"] if histogram_xscale == "log" else [],
        "y_log_values": ["enabled"] if histogram_yscale == "log" else [],
        "n_bins_for_plots": _resolve_histogram_bin_count(
            calibration_config.get("n_bins_for_plots", 200),
            default=200,
        ),
    }


def _resolve_histogram_bin_count(value: Any, *, default: int) -> int:
    try:
        resolved_value = int(float(value))
    except Exception:
        return int(default)

    return max(1, resolved_value)


def build_preview_histogram_payload(
    *,
    selected_file: Any,
    selected_channel: Any,
    uploaded_fcs_paths: Any,
    selected_calibration_summary: Any = None,
    runtime_config_data: Any,
    axis_scale_toggle_values: Any = None,
    preview_graph_visibility_toggle_values: Any = None,
    n_bins_for_plots: Any = None,
    target_mie_model: Any = None,
    target_medium_refractive_index: Any = None,
    target_particle_refractive_index: Any = None,
    target_solid_sphere_diameter_min_nm: Any = None,
    target_solid_sphere_diameter_max_nm: Any = None,
    target_solid_sphere_diameter_count: Any = None,
    target_core_refractive_index: Any = None,
    target_shell_refractive_index: Any = None,
    target_shell_thickness_nm: Any = None,
    target_core_shell_core_diameter_min_nm: Any = None,
    target_core_shell_core_diameter_max_nm: Any = None,
    target_core_shell_core_diameter_count: Any = None,
    target_model_preset: Any = None,
    advanced_monotonic_mode_enabled: Any = None,
    use_monotonic_smoothing_kernel: Any = None,
    monotonic_smoothing_sigma_points: Any = None,
) -> tuple[str, go.Figure, dict[str, str], str]:
    """Build a profile-styled histogram for the selected uploaded FCS file."""
    runtime_config = RuntimeConfig.from_dict(
        runtime_config_data if isinstance(runtime_config_data, dict) else None
    )
    graph_style = _resolve_preview_graph_style(runtime_config)
    control_defaults = resolve_preview_control_defaults(runtime_config_data)
    selected_path = resolve_selected_preview_path(
        selected_file=selected_file,
        uploaded_fcs_paths=uploaded_fcs_paths,
    )
    channel = str(selected_channel or "").strip()

    if selected_path is None:
        message = "Upload an FCS file to preview its histogram."
        return "0", build_empty_preview_figure(message), graph_style, message
    if not channel:
        message = "Select a calibration-affected channel to preview its histogram."
        return "0", build_empty_preview_figure(message), graph_style, message

    use_log_x, use_log_y = Scatter2DGraph.axis_scale_from_toggle_values(
        axis_scale_toggle_values,
    )
    histogram_bin_count = _resolve_histogram_bin_count(
        n_bins_for_plots,
        default=control_defaults["n_bins_for_plots"],
    )
    show_preview_graph = isinstance(preview_graph_visibility_toggle_values, list) and (
        "enabled" in preview_graph_visibility_toggle_values
    )

    try:
        calibration_summary = _resolve_preview_calibration_summary(
            selected_calibration_summary,
            selected_channel=channel,
        )

        if calibration_summary is None:
            message = "Select a calibration file to preview the calibrated channel."
            return "0", build_empty_preview_figure(message), graph_style, message

        calibration_payload = calibration_summary.get("calibration_payload", {})
        if not isinstance(calibration_payload, dict) or not calibration_payload:
            raise ValueError("Selected calibration payload is missing.")

        with FCSFile(selected_path) as fcs_file:
            selected_channel_dataframe = fcs_file.dataframe_copy(columns=[channel])

        calibrated_channel_label = str(
            calibration_summary.get("applied_output_channel_name", "")
        ).strip() or channel

        if bool(calibration_summary.get("requires_target_model")):
            from RosettaX.pages.p04_calibrate.sections.s04_apply import services as apply_services
            from RosettaX.workflow.apply_calibration.scattering import apply_scattering_calibration_to_dataframe

            target_model_parameters = apply_services.build_scattering_target_model_parameters_if_required(
                selected_calibration_summary=selected_calibration_summary,
                target_mie_model=target_mie_model,
                target_medium_refractive_index=target_medium_refractive_index,
                target_particle_refractive_index=target_particle_refractive_index,
                target_solid_sphere_diameter_min_nm=target_solid_sphere_diameter_min_nm,
                target_solid_sphere_diameter_max_nm=target_solid_sphere_diameter_max_nm,
                target_solid_sphere_diameter_count=target_solid_sphere_diameter_count,
                target_core_refractive_index=target_core_refractive_index,
                target_shell_refractive_index=target_shell_refractive_index,
                target_shell_thickness_nm=target_shell_thickness_nm,
                target_core_shell_core_diameter_min_nm=target_core_shell_core_diameter_min_nm,
                target_core_shell_core_diameter_max_nm=target_core_shell_core_diameter_max_nm,
                target_core_shell_core_diameter_count=target_core_shell_core_diameter_count,
                advanced_monotonic_mode_enabled=advanced_monotonic_mode_enabled,
                use_monotonic_smoothing_kernel=use_monotonic_smoothing_kernel,
                monotonic_smoothing_sigma_points=monotonic_smoothing_sigma_points,
            )

            if target_model_parameters is None:
                raise ValueError("Target model parameters are required for scattering calibration preview.")

            scattering_result = apply_scattering_calibration_to_dataframe(
                dataframe=selected_channel_dataframe,
                source_channel=channel,
                calibration_payload=calibration_payload,
                target_model_parameters=target_model_parameters,
            )

            calibrated_values = scattering_result.dataframe[
                scattering_result.output_columns[-1]
            ].to_numpy(copy=True)

            calibrated_channel_label = scattering_result.output_columns[-1]

        else:
            calibrated_values = apply_legacy_calibration_to_series(
                values=selected_channel_dataframe[channel].to_numpy(copy=True),
                calibration_payload=calibration_payload,
                source_channel=channel,
            )

        histogram = _build_histogram_result_from_values(
            calibrated_values,
            n_bins_for_plots=histogram_bin_count,
            use_log_x_bins=use_log_x == "log",
        )
        figure = plottings.build_histogram_figure(
            detector_column=calibrated_channel_label,
            histogram_result=histogram,
            use_log_counts=use_log_y == "log",
        )
        visual_settings = plottings.resolve_runtime_visualization_settings(runtime_config)
        plottings.apply_default_visual_style(
            figure,
            marker_size=visual_settings["default_marker_size"],
            line_width=visual_settings["default_line_width"],
            font_size=visual_settings["default_font_size"],
            tick_size=visual_settings["default_tick_size"],
            show_grid=visual_settings["show_grid"],
        )
        figure.update_xaxes(type=use_log_x)
        figure.update_layout(
            uirevision=repr((
                selected_path,
                channel,
                calibrated_channel_label,
                use_log_x,
                use_log_y,
                histogram_bin_count,
                str(calibration_summary.get("file_name", "")),
            )),
            margin={"l": 60, "r": 25, "t": 30, "b": 60},
        )

        if not show_preview_graph:
            graph_style = {**graph_style, "display": "none"}
    except Exception as exception:
        logger.exception(
            "Failed to build calibrated input FCS preview for path=%r channel=%r",
            selected_path,
            channel,
        )
        message = f"Could not render calibrated preview: {type(exception).__name__}: {exception}"
        return "0", build_empty_preview_figure(message), graph_style, message

    return (
        str(int(histogram.values.size)),
        figure,
        graph_style,
        f"Showing calibrated preview for {Path(selected_path).name} · {channel} -> {calibrated_channel_label}",
    )
