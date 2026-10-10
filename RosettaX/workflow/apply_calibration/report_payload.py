"""Apply report payloads, request signatures, and download filenames."""

import re
from datetime import datetime
from pathlib import Path
from typing import Any

from RosettaX.utils.service import build_reproducibility_metadata

from .services import (
    ApplyCalibrationFilesResult,
    ApplyCalibrationRequest,
    resolve_source_channel,
)


def build_apply_report_payload(
    *,
    request: ApplyCalibrationRequest,
    result: ApplyCalibrationFilesResult,
    calibration_summary: Any | None = None,
) -> dict[str, Any]:
    """Build a serializable payload describing one successful apply/export run."""
    calibration_summaries = _normalize_calibration_summaries(
        calibration_summary,
    )
    primary_calibration_summary = (
        calibration_summaries[0] if calibration_summaries else None
    )

    return {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "request_signature": build_apply_report_request_signature(request=request),
        "selected_calibration": _build_selected_calibration_label(
            request=request,
        ),
        "selected_calibrations": [
            str(calibration.selected_calibration)
            for calibration in request.calibrations
        ],
        "calibration_summary": _build_calibration_summary_payload(
            calibration_summary=primary_calibration_summary,
        ),
        "calibration_summaries": [
            _build_calibration_summary_payload(
                calibration_summary=summary,
            )
            for summary in calibration_summaries
        ],
        "calibration_details": _build_calibration_details_payload(
            calibration_payload=(
                request.calibrations[0].calibration_payload
                if request.calibrations
                else {}
            ),
        ),
        "calibration_details_list": [
            _build_calibration_details_payload(
                calibration_payload=calibration.calibration_payload,
            )
            for calibration in request.calibrations
        ],
        "saved_calibration_payload": _sanitize_payload_tree(
            request.calibrations[0].calibration_payload if request.calibrations else {}
        ),
        "saved_calibration_payloads": [
            _sanitize_payload_tree(
                calibration.calibration_payload,
            )
            for calibration in request.calibrations
        ],
        "uploaded_fcs_paths": [str(path) for path in request.uploaded_fcs_paths],
        "export_columns": [str(column) for column in request.export_columns],
        "scattering_target_model_parameters": _build_scattering_target_model_payload(
            request=request,
        ),
        "result": {
            "download_filename": str(result.download_filename),
            "source_channel": str(result.source_channel),
            "output_channels": [str(channel) for channel in result.output_channels],
            "file_count": int(result.file_count),
            "warnings": [str(warning) for warning in result.warnings],
            "status": str(result.status),
            "includes_embedded_report": str(result.download_filename)
            .lower()
            .endswith(".zip"),
        },
    }


def build_apply_report_request_signature(
    *,
    request: ApplyCalibrationRequest,
) -> dict[str, Any]:
    """Build a comparable signature for the current apply request."""
    return {
        "uploaded_fcs_paths": [str(path) for path in request.uploaded_fcs_paths],
        "selected_calibrations": [
            {
                "selected_calibration": str(calibration.selected_calibration),
                "source_channel": resolve_source_channel(
                    calibration.calibration_payload,
                ),
                "calibration_fingerprint": build_reproducibility_metadata(
                    calibration_kind=str(
                        calibration.calibration_payload.get("calibration_type", "")
                    ),
                    payload=calibration.calibration_payload,
                )["fingerprint"],
                "target_model": (
                    calibration.scattering_target_model_parameters.to_parameter_payload()
                    if calibration.scattering_target_model_parameters is not None
                    else None
                ),
            }
            for calibration in request.calibrations
        ],
        "export_columns": [str(column) for column in request.export_columns],
        "scattering_target_model_parameters": _build_scattering_target_model_payload(
            request=request,
        ),
    }


def apply_report_matches_request(
    *,
    report_payload: Any,
    request: ApplyCalibrationRequest,
) -> bool:
    """Return whether report_payload still matches the current request."""
    if not isinstance(report_payload, dict):
        return False

    return report_payload.get(
        "request_signature"
    ) == build_apply_report_request_signature(
        request=request,
    )


def build_apply_report_download_filename(
    *,
    report_payload: dict[str, Any],
) -> str:
    """Build a stable download filename for the PDF report."""
    calibration_entries = _build_calibration_entries(
        report_payload=report_payload,
    )

    if len(calibration_entries) > 1:
        calibration_name = "multi_calibration"
    else:
        calibration_summary = report_payload.get("calibration_summary", {})

        if isinstance(calibration_summary, dict):
            calibration_name = calibration_summary.get(
                "file_name",
                report_payload.get("selected_calibration", "calibration"),
            )
        else:
            calibration_name = report_payload.get("selected_calibration", "calibration")

    calibration_stem = Path(str(calibration_name or "calibration")).stem
    safe_stem = re.sub(r"[^A-Za-z0-9._-]+", "_", calibration_stem).strip("._")

    if not safe_stem:
        safe_stem = "calibration"

    generated_at = str(report_payload.get("generated_at", ""))
    timestamp = re.sub(r"[^0-9]", "", generated_at)[:14]

    if not timestamp:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    return f"rosettax_apply_report_{safe_stem}_{timestamp}.pdf"


def _build_calibration_summary_payload(
    *,
    calibration_summary: dict[str, Any] | None,
) -> dict[str, Any]:
    if not isinstance(calibration_summary, dict):
        return {}

    return {
        "selected_calibration": str(
            calibration_summary.get("selected_calibration", "")
        ),
        "file_name": str(calibration_summary.get("file_name", "")),
        "file_path": str(calibration_summary.get("file_path", "")),
        "calibration_type": str(calibration_summary.get("calibration_type", "")),
        "source_channel": str(calibration_summary.get("source_channel", "")),
        "output_quantity": str(calibration_summary.get("output_quantity", "")),
        "applied_output_channel_name": str(
            calibration_summary.get("applied_output_channel_name", "")
        ),
        "version": calibration_summary.get("version"),
        "requires_target_model": bool(
            calibration_summary.get("requires_target_model", False)
        ),
    }


def _normalize_calibration_summaries(
    calibration_summary: Any,
) -> list[dict[str, Any]]:
    if isinstance(calibration_summary, list):
        return [item for item in calibration_summary if isinstance(item, dict)]

    if isinstance(calibration_summary, dict):
        return [
            calibration_summary,
        ]

    return []


def _build_selected_calibration_label(
    *,
    request: ApplyCalibrationRequest,
) -> str:
    if not request.calibrations:
        return ""

    if len(request.calibrations) == 1:
        return str(request.calibrations[0].selected_calibration)

    return f"{len(request.calibrations)} calibration files"


def _build_calibration_details_payload(
    *,
    calibration_payload: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(calibration_payload, dict):
        return {}

    calibration_type = (
        str(calibration_payload.get("calibration_type", "")).strip().lower()
    )

    if calibration_type == "fluorescence":
        return _build_fluorescence_calibration_details(
            calibration_payload=calibration_payload
        )

    if calibration_type == "scattering":
        return _build_scattering_calibration_details(
            calibration_payload=calibration_payload
        )

    return {
        "calibration_type": calibration_type or "unknown",
        "payload_keys": sorted(calibration_payload.keys()),
    }


def _build_fluorescence_calibration_details(
    *,
    calibration_payload: dict[str, Any],
) -> dict[str, Any]:
    fit_metrics = calibration_payload.get("fit_metrics", {})
    parameters = calibration_payload.get("parameters", {})
    nested_payload = calibration_payload.get("payload", {})
    reference_points = calibration_payload.get("reference_points", [])

    return {
        "calibration_type": "fluorescence",
        "schema_version": str(calibration_payload.get("schema_version", "")),
        "source_file": str(calibration_payload.get("source_file") or ""),
        "source_channel": str(calibration_payload.get("source_channel") or ""),
        "gating_channel": str(calibration_payload.get("gating_channel") or ""),
        "gating_threshold": _as_float_or_none(
            calibration_payload.get("gating_threshold")
        ),
        "fit_model": str(calibration_payload.get("fit_model") or ""),
        "fit_metrics": {
            "r_squared": _as_float_or_none(fit_metrics.get("r_squared")),
            "point_count": _as_int_or_none(fit_metrics.get("point_count")),
        },
        "parameters": {
            "slope": _as_float_or_none(parameters.get("slope")),
            "intercept": _as_float_or_none(parameters.get("intercept")),
            "prefactor": _as_float_or_none(parameters.get("prefactor")),
        },
        "axis_definitions": {
            "x_definition": str(nested_payload.get("x_definition") or ""),
            "y_definition": str(nested_payload.get("y_definition") or ""),
        },
        "reference_points": [
            {
                "reference_value": _as_float_or_none(point.get("reference_value")),
                "measured_value": _as_float_or_none(point.get("measured_value")),
            }
            for point in reference_points
            if isinstance(point, dict)
        ],
    }


def _build_scattering_calibration_details(
    *,
    calibration_payload: dict[str, Any],
) -> dict[str, Any]:
    instrument_response = calibration_payload.get("instrument_response", {})
    metadata = calibration_payload.get("metadata", {})
    reference_table = calibration_payload.get("reference_table", [])

    return {
        "calibration_type": "scattering",
        "version": _as_int_or_none(calibration_payload.get("version")),
        "source_channel": str(calibration_payload.get("source_channel") or ""),
        "output_quantity": str(calibration_payload.get("output_quantity") or ""),
        "instrument_response": {
            "measured_channel": str(instrument_response.get("measured_channel") or ""),
            "slope": _as_float_or_none(instrument_response.get("slope")),
            "intercept": _as_float_or_none(instrument_response.get("intercept")),
            "r_squared": _as_float_or_none(instrument_response.get("r_squared")),
            "force_zero_intercept": bool(
                instrument_response.get("force_zero_intercept", False)
            ),
            "input_quantity": str(instrument_response.get("input_quantity") or ""),
            "output_quantity": str(instrument_response.get("output_quantity") or ""),
            "model_name": str(instrument_response.get("model_name") or ""),
        },
        "reference_table": [
            {str(key): _sanitize_payload_value(value) for key, value in row.items()}
            for row in reference_table
            if isinstance(row, dict)
        ],
        "metadata": {
            str(key): _sanitize_payload_value(value)
            for key, value in metadata.items()
            if _is_supported_payload_value(value)
        },
    }


def _build_scattering_target_model_payload(
    *,
    request: ApplyCalibrationRequest,
) -> dict[str, Any] | None:
    parameters = None

    for calibration in request.calibrations:
        if calibration.scattering_target_model_parameters is not None:
            parameters = calibration.scattering_target_model_parameters
            break

    if parameters is None:
        return None

    return parameters.to_parameter_payload()


def _sanitize_payload_value(value: Any) -> Any:
    if isinstance(value, str | bool | int) or value is None:
        return value

    if isinstance(value, float):
        return float(value)

    if isinstance(value, list):
        return [
            _sanitize_payload_value(item)
            for item in value
            if _is_supported_payload_value(item)
        ]

    return str(value)


def _sanitize_payload_tree(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): _sanitize_payload_tree(item)
            for key, item in value.items()
            if _is_supported_payload_tree_value(item)
        }

    if isinstance(value, list):
        return [
            _sanitize_payload_tree(item)
            for item in value
            if _is_supported_payload_tree_value(item)
        ]

    return _sanitize_payload_value(value)


def _is_supported_payload_value(value: Any) -> bool:
    return isinstance(value, dict | str | bool | int | float | list) or value is None


def _is_supported_payload_tree_value(value: Any) -> bool:
    return isinstance(value, dict | list) or _is_supported_payload_value(value)


def _as_float_or_none(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int_or_none(value: Any) -> int | None:
    try:
        if value in (None, ""):
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _normalize_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []

    return [str(item) for item in value]


def _normalize_dict_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []

    return [item for item in value if isinstance(item, dict)]


def _build_calibration_entries(
    *,
    report_payload: dict[str, Any],
) -> list[dict[str, Any]]:
    summaries = _normalize_calibration_summaries(
        report_payload.get("calibration_summaries"),
    )

    if not summaries:
        summaries = _normalize_calibration_summaries(
            report_payload.get("calibration_summary"),
        )

    details_list = _normalize_dict_list(
        report_payload.get("calibration_details_list"),
    )
    if not details_list:
        details_list = _normalize_dict_list(
            [
                report_payload.get("calibration_details"),
            ]
        )

    payloads = _normalize_dict_list(
        report_payload.get("saved_calibration_payloads"),
    )
    if not payloads:
        payloads = _normalize_dict_list(
            [
                report_payload.get("saved_calibration_payload"),
            ]
        )

    calibration_count = max(
        len(summaries),
        len(details_list),
        len(payloads),
    )

    entries: list[dict[str, Any]] = []

    for calibration_index in range(calibration_count):
        summary = (
            summaries[calibration_index] if calibration_index < len(summaries) else {}
        )
        details = (
            details_list[calibration_index]
            if calibration_index < len(details_list)
            else {}
        )
        saved_payload = (
            payloads[calibration_index] if calibration_index < len(payloads) else {}
        )

        if not details and isinstance(saved_payload, dict) and saved_payload:
            details = _build_calibration_details_payload(
                calibration_payload=saved_payload,
            )

        calibration_type = str(
            details.get("calibration_type") or summary.get("calibration_type") or "",
        )

        display_name = str(
            summary.get("file_name")
            or summary.get("selected_calibration")
            or f"Calibration {calibration_index + 1}",
        )

        entries.append(
            {
                "summary": summary,
                "details": details,
                "saved_payload": saved_payload,
                "display_name": display_name,
                "calibration_type": calibration_type,
            }
        )

    return entries


def _build_calibration_entry(
    *,
    report_payload: dict[str, Any],
    calibration_index: int,
) -> dict[str, Any]:
    entries = _build_calibration_entries(
        report_payload=report_payload,
    )

    if not entries:
        return {
            "summary": {},
            "details": {},
            "saved_payload": {},
            "display_name": "Calibration",
            "calibration_type": "",
        }

    calibration_index = max(calibration_index, 0)

    if calibration_index >= len(entries):
        calibration_index = len(entries) - 1

    return entries[calibration_index]
