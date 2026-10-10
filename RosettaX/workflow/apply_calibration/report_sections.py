"""Calibration evidence, reference tables, and chart specifications for reports."""

import math
from typing import Any

from .report_helpers import (
    build_saved_payload_section_specs as _build_saved_payload_section_specs_from_payload,
)
from .report_helpers import (
    format_display_value as _format_display_value,
)
from .report_helpers import (
    prettify_label as _prettify_label,
)
from .report_payload import (
    _as_float_or_none,
    _build_calibration_entry,
    _normalize_calibration_summaries,
    _normalize_string_list,
)


def _build_cover_summary_items(
    *,
    report_payload: dict[str, Any],
) -> list[tuple[str, str]]:
    summary = report_payload.get("calibration_summary", {})
    result_payload = report_payload.get("result", {})

    calibration_type = "unknown"
    if isinstance(summary, dict):
        calibration_type = str(
            summary.get("calibration_type") or "unknown"
        ).capitalize()

    file_count = 0
    if isinstance(result_payload, dict):
        file_count = int(result_payload.get("file_count") or 0)

    calibration_count = len(
        _normalize_calibration_summaries(
            report_payload.get("calibration_summaries"),
        )
    )
    output_channels = _normalize_string_list(
        result_payload.get("output_channels")
        if isinstance(result_payload, dict)
        else None,
    )

    return [
        ("Calibration type", calibration_type),
        ("Calibration files", str(calibration_count or 1)),
        ("Input FCS files", str(file_count)),
        ("Output channels", ", ".join(output_channels) if output_channels else "n/a"),
    ]


def _build_apply_overview_items(
    *,
    report_payload: dict[str, Any],
) -> list[tuple[str, str]]:
    result_payload = report_payload.get("result", {})

    if not isinstance(result_payload, dict):
        result_payload = {}

    selected_calibration_files = _normalize_string_list(
        report_payload.get("selected_calibrations"),
    )

    if not selected_calibration_files:
        selected_calibration = str(
            report_payload.get("selected_calibration") or "",
        ).strip()
        if selected_calibration:
            selected_calibration_files = [
                selected_calibration,
            ]

    return [
        ("Generated at", str(report_payload.get("generated_at") or "n/a")),
        (
            "Calibration selection",
            str(report_payload.get("selected_calibration") or "n/a"),
        ),
        (
            "Calibration files",
            ", ".join(selected_calibration_files)
            if selected_calibration_files
            else "n/a",
        ),
        ("Download artifact", str(result_payload.get("download_filename") or "n/a")),
        (
            "Output channels",
            ", ".join(_normalize_string_list(result_payload.get("output_channels")))
            or "None",
        ),
        ("Uploaded FCS files", str(result_payload.get("file_count") or 0)),
        (
            "Extra exported columns",
            ", ".join(_normalize_string_list(report_payload.get("export_columns")))
            or "None",
        ),
        (
            "Report bundled into ZIP",
            "Yes" if bool(result_payload.get("includes_embedded_report")) else "No",
        ),
        ("Status", str(result_payload.get("status") or "n/a")),
        ("Warnings", str(len(_normalize_string_list(result_payload.get("warnings"))))),
    ]


def _build_calibration_metadata_items(
    *,
    report_payload: dict[str, Any],
    calibration_index: int = 0,
) -> list[tuple[str, str]]:
    calibration_entry = _build_calibration_entry(
        report_payload=report_payload,
        calibration_index=calibration_index,
    )
    summary = calibration_entry.get("summary", {})
    details = calibration_entry.get("details", {})

    if not isinstance(summary, dict):
        summary = {}
    if not isinstance(details, dict):
        details = {}

    items = [
        (
            "Calibration file",
            str(
                summary.get("file_name")
                or calibration_entry.get("display_name")
                or "n/a"
            ),
        ),
        ("Calibration type", str(summary.get("calibration_type") or "unknown")),
        (
            "Source channel",
            str(
                summary.get("source_channel") or details.get("source_channel") or "n/a"
            ),
        ),
        (
            "Output quantity",
            str(
                summary.get("output_quantity")
                or details.get("output_quantity")
                or "n/a"
            ),
        ),
        ("Version", _format_display_value(summary.get("version"))),
    ]

    if details.get("calibration_type") == "fluorescence":
        items.extend(
            [
                ("Source bead file", str(details.get("source_file") or "n/a")),
                ("Gating channel", str(details.get("gating_channel") or "n/a")),
                (
                    "Gating threshold",
                    _format_display_value(details.get("gating_threshold")),
                ),
                ("Fit model", str(details.get("fit_model") or "n/a")),
            ]
        )
    elif details.get("calibration_type") == "scattering":
        metadata = details.get("metadata", {})
        if isinstance(metadata, dict):
            for key in (
                "measured_channel",
                "detector_configuration_preset_name",
                "mie_model",
                "wavelength_nm",
            ):
                if key in metadata:
                    items.append(
                        (_prettify_label(key), _format_display_value(metadata.get(key)))
                    )

    file_path = str(summary.get("file_path") or "").strip()
    if file_path:
        items.append(("Calibration path", file_path))

    return items


def _build_selected_calibration_rows(
    *,
    report_payload: dict[str, Any],
) -> list[list[str]]:
    calibration_summaries = _normalize_calibration_summaries(
        report_payload.get("calibration_summaries"),
    )

    if not calibration_summaries:
        calibration_summaries = _normalize_calibration_summaries(
            report_payload.get("calibration_summary"),
        )

    rows: list[list[str]] = []

    for calibration_summary in calibration_summaries:
        rows.append(
            [
                str(
                    calibration_summary.get("file_name")
                    or calibration_summary.get("selected_calibration")
                    or "n/a"
                ),
                str(calibration_summary.get("calibration_type") or "unknown"),
                str(calibration_summary.get("source_channel") or "n/a"),
                str(
                    calibration_summary.get("applied_output_channel_name")
                    or calibration_summary.get("output_quantity")
                    or "n/a"
                ),
            ]
        )

    return rows


def _build_fluorescence_fit_items(
    *,
    report_payload: dict[str, Any],
    calibration_index: int = 0,
) -> list[tuple[str, str]]:
    details = _build_calibration_entry(
        report_payload=report_payload,
        calibration_index=calibration_index,
    ).get("details", {})

    if not isinstance(details, dict):
        return []

    fit_metrics = details.get("fit_metrics", {})
    parameters = details.get("parameters", {})
    axis_definitions = details.get("axis_definitions", {})

    if not isinstance(fit_metrics, dict):
        fit_metrics = {}
    if not isinstance(parameters, dict):
        parameters = {}
    if not isinstance(axis_definitions, dict):
        axis_definitions = {}

    return [
        ("Slope", _format_display_value(parameters.get("slope"))),
        ("Intercept", _format_display_value(parameters.get("intercept"))),
        ("Prefactor", _format_display_value(parameters.get("prefactor"))),
        ("R squared", _format_display_value(fit_metrics.get("r_squared"))),
        ("Point count", _format_display_value(fit_metrics.get("point_count"))),
        ("X definition", str(axis_definitions.get("x_definition") or "n/a")),
        ("Y definition", str(axis_definitions.get("y_definition") or "n/a")),
    ]


def _build_scattering_fit_items(
    *,
    report_payload: dict[str, Any],
    calibration_index: int = 0,
) -> list[tuple[str, str]]:
    details = _build_calibration_entry(
        report_payload=report_payload,
        calibration_index=calibration_index,
    ).get("details", {})

    if not isinstance(details, dict):
        return []

    instrument_response = details.get("instrument_response", {})

    if not isinstance(instrument_response, dict):
        return []

    return [
        (
            "Measured channel",
            _format_display_value(instrument_response.get("measured_channel")),
        ),
        ("Slope", _format_display_value(instrument_response.get("slope"))),
        ("Intercept", _format_display_value(instrument_response.get("intercept"))),
        ("R squared", _format_display_value(instrument_response.get("r_squared"))),
        (
            "Input quantity",
            _format_display_value(instrument_response.get("input_quantity")),
        ),
        (
            "Output quantity",
            _format_display_value(instrument_response.get("output_quantity")),
        ),
        ("Model name", _format_display_value(instrument_response.get("model_name"))),
        (
            "Force zero intercept",
            "Yes" if bool(instrument_response.get("force_zero_intercept")) else "No",
        ),
    ]


def _build_target_model_items(
    *,
    report_payload: dict[str, Any],
) -> list[tuple[str, str]]:
    payload = report_payload.get("scattering_target_model_parameters", None)

    if not isinstance(payload, dict):
        return []

    return [
        (_prettify_label(key), _format_display_value(value))
        for key, value in payload.items()
    ]


def _build_saved_payload_section_specs(
    *,
    report_payload: dict[str, Any],
    calibration_index: int = 0,
) -> list[dict[str, Any]]:
    saved_payload = _build_calibration_entry(
        report_payload=report_payload,
        calibration_index=calibration_index,
    ).get("saved_payload", {})

    return _build_saved_payload_section_specs_from_payload(
        payload=saved_payload,
    )


def _build_reference_table_spec(
    *,
    report_payload: dict[str, Any],
    calibration_index: int = 0,
) -> dict[str, Any] | None:
    details = _build_calibration_entry(
        report_payload=report_payload,
        calibration_index=calibration_index,
    ).get("details", {})

    if not isinstance(details, dict):
        return None

    calibration_type = str(details.get("calibration_type") or "").strip().lower()

    if calibration_type == "fluorescence":
        rows = []
        for index, point in enumerate(details.get("reference_points", []), start=1):
            if not isinstance(point, dict):
                continue
            rows.append(
                [
                    index,
                    _format_display_value(point.get("reference_value")),
                    _format_display_value(point.get("measured_value")),
                ]
            )

        return {
            "title": "MESF and peak positions",
            "headers": ["Point", "Reference value", "Measured peak position"],
            "rows": rows or [["-", "None", "None"]],
            "column_weights": [0.14, 0.36, 0.50],
        }

    if calibration_type == "scattering":
        reference_table = details.get("reference_table", [])
        if not isinstance(reference_table, list):
            return None

        preferred_columns = [
            "measured_peak_position",
            "particle_diameter_nm",
            "core_diameter_nm",
            "shell_thickness_nm",
            "outer_diameter_nm",
        ]
        present_columns = [
            column_name
            for column_name in preferred_columns
            if any(
                isinstance(row, dict) and row.get(column_name) not in (None, "")
                for row in reference_table
            )
        ]

        if (
            not present_columns
            and reference_table
            and isinstance(reference_table[0], dict)
        ):
            present_columns = list(reference_table[0].keys())[:5]

        if not present_columns:
            return None

        rows = []
        for row in reference_table:
            if not isinstance(row, dict):
                continue
            rows.append(
                [
                    _format_display_value(row.get(column_name))
                    for column_name in present_columns
                ]
            )

        return {
            "title": "Scattering reference standards",
            "headers": [
                _prettify_label(column_name) for column_name in present_columns
            ],
            "rows": rows or [["None"] * len(present_columns)],
            "column_weights": [1.0] * len(present_columns),
        }

    return None


def _build_chart_spec(
    *,
    report_payload: dict[str, Any],
    calibration_index: int = 0,
) -> dict[str, Any] | None:
    details = _build_calibration_entry(
        report_payload=report_payload,
        calibration_index=calibration_index,
    ).get("details", {})

    if not isinstance(details, dict):
        return None

    calibration_type = str(details.get("calibration_type") or "").strip().lower()

    if calibration_type == "fluorescence":
        points = [
            point
            for point in details.get("reference_points", [])
            if isinstance(point, dict)
        ]
        x_values: list[float] = []
        y_values: list[float] = []

        for point in points:
            measured_value = _as_float_or_none(point.get("measured_value"))
            reference_value = _as_float_or_none(point.get("reference_value"))
            if measured_value is None or reference_value is None:
                continue
            if measured_value <= 0.0 or reference_value <= 0.0:
                continue
            x_values.append(measured_value)
            y_values.append(reference_value)

        if not x_values or not y_values:
            return None

        line_x_values: list[float] = []
        line_y_values: list[float] = []
        parameters = details.get("parameters", {})

        if isinstance(parameters, dict):
            slope = _as_float_or_none(parameters.get("slope"))
            intercept = _as_float_or_none(parameters.get("intercept"))

            if slope is not None and intercept is not None:
                log_x_min = math.log10(min(x_values))
                log_x_max = math.log10(max(x_values))
                for index in range(60):
                    fraction = index / 59.0
                    current_x = 10.0 ** (
                        log_x_min + ((log_x_max - log_x_min) * fraction)
                    )
                    current_y = (10.0**intercept) * (current_x**slope)
                    line_x_values.append(current_x)
                    line_y_values.append(current_y)

        return {
            "title": "Fluorescence calibration fit",
            "subtitle": "Measured peak positions against saved reference values.",
            "x_label": "Measured peak position [a.u.] (log scale)",
            "y_label": f"{details.get('axis_definitions', {}).get('y_definition') or 'Reference value'} (log scale)",
            "x_values": x_values,
            "y_values": y_values,
            "line_x_values": line_x_values,
            "line_y_values": line_y_values,
            "log_x": True,
            "log_y": True,
        }

    if calibration_type == "scattering":
        reference_table = details.get("reference_table", [])
        if not isinstance(reference_table, list):
            return None

        y_key = None
        for candidate in (
            "expected_coupling",
            "particle_diameter_nm",
            "outer_diameter_nm",
            "core_diameter_nm",
        ):
            if any(
                isinstance(row, dict) and row.get(candidate) not in (None, "")
                for row in reference_table
            ):
                y_key = candidate
                break

        x_values: list[float] = []
        y_values: list[float] = []
        for row in reference_table:
            if not isinstance(row, dict):
                continue
            x_value = _as_float_or_none(row.get("measured_peak_position"))
            y_value = _as_float_or_none(row.get(y_key)) if y_key is not None else None
            if x_value is None or y_value is None:
                continue
            x_values.append(x_value)
            y_values.append(y_value)

        if not x_values or not y_values:
            return None

        paired_points = sorted(
            zip(x_values, y_values, strict=False), key=lambda point: point[0]
        )
        line_x_values = []
        line_y_values = []
        response = details.get("instrument_response", {})
        slope = _as_float_or_none(response.get("slope"))
        intercept = _as_float_or_none(response.get("intercept"))
        if y_key == "expected_coupling" and slope is not None and intercept is not None:
            line_x_values = [paired_points[0][0], paired_points[-1][0]]
            line_y_values = [slope * value + intercept for value in line_x_values]

        return {
            "title": "Scattering instrument response"
            if y_key == "expected_coupling"
            else "Scattering calibration standards",
            "subtitle": "Saved standard peaks used to fit the scattering calibration.",
            "x_label": "Measured peak position",
            "y_label": _prettify_label(y_key or "reference_value"),
            "x_values": [point[0] for point in paired_points],
            "y_values": [point[1] for point in paired_points],
            "line_x_values": line_x_values,
            "line_y_values": line_y_values,
            "log_x": False,
            "log_y": False,
        }

    return None
