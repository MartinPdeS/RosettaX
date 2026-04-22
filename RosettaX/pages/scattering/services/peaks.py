# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any, Optional

from RosettaX.utils import casting
from RosettaX.utils.service import build_channel_options_from_file
from RosettaX.utils.runtime_config import RuntimeConfig


@dataclass(frozen=True)
class ScatteringCallbackInputs:
    graph_enabled: bool
    scattering_channel: str
    nbins: int
    max_events: int
    yscale_selection: Any


def is_enabled(value: Any) -> bool:
    return isinstance(value, list) and ("enabled" in value)


def clean_optional_string(value: Any) -> str:
    if value is None:
        return ""

    cleaned_value = str(value).strip()
    if cleaned_value.lower() == "none":
        return ""

    return cleaned_value


def resolve_mie_model(mie_model: Any) -> str:
    mie_model_string = clean_optional_string(mie_model)
    return "Core/Shell Sphere" if mie_model_string == "Core/Shell Sphere" else "Solid Sphere"


def build_empty_row_for_model(mie_model: str) -> dict[str, str]:
    if mie_model == "Core/Shell Sphere":
        return {
            "core_diameter_nm": "",
            "shell_thickness_nm": "",
            "outer_diameter_nm": "",
            "measured_peak_position": "",
            "expected_coupling": "",
        }

    return {
        "particle_diameter_nm": "",
        "measured_peak_position": "",
        "expected_coupling": "",
    }


def build_empty_peak_lines_payload() -> dict[str, list[Any]]:
    return {"positions": [], "labels": []}


def populate_scattering_detector_dropdown(
    *,
    uploaded_fcs_path: Any,
    current_detector_value: Any,
    logger: Any,
) -> tuple[list[dict[str, Any]], Any]:
    uploaded_fcs_path_clean = clean_optional_string(uploaded_fcs_path)

    if not uploaded_fcs_path_clean:
        logger.debug("No uploaded FCS path available. Returning empty detector dropdown.")
        return [], None

    try:
        channels = build_channel_options_from_file(
            uploaded_fcs_path_clean,
            preferred_scatter=current_detector_value,
        )
    except Exception:
        logger.exception(
            "Failed to extract scattering channels from uploaded_fcs_path=%r",
            uploaded_fcs_path_clean,
        )
        return [], None

    scattering_detector_options = list(channels.scatter_options or [])
    scattering_detector_value = channels.scatter_value

    logger.debug(
        "Resolved scattering detector dropdown with option_count=%r value=%r",
        len(scattering_detector_options),
        scattering_detector_value,
    )

    return scattering_detector_options, scattering_detector_value


def parse_scattering_histogram_callback_inputs(
    *,
    graph_toggle_value: Any,
    scattering_channel: Any,
    scattering_nbins: Any,
    yscale_selection: Any,
    max_events_for_plots: Any,
    runtime_config_data: Any,
) -> ScatteringCallbackInputs:
    runtime_config = RuntimeConfig.from_dict(
        runtime_config_data if isinstance(runtime_config_data, dict) else None
    )

    return ScatteringCallbackInputs(
        graph_enabled=is_enabled(graph_toggle_value),
        scattering_channel=clean_optional_string(scattering_channel),
        nbins=casting._as_int(
            scattering_nbins,
            default=runtime_config.get_int("calibration.n_bins_for_plots", default=100),
            min_value=10,
            max_value=5000,
        ),
        max_events=casting._as_int(
            max_events_for_plots,
            default=runtime_config.get_int("calibration.max_events_for_analysis", default=10000),
            min_value=1,
            max_value=5_000_000,
        ),
        yscale_selection=yscale_selection,
    )


def write_measured_peaks_into_table(
    *,
    table_data: Optional[list[dict[str, Any]]],
    peak_positions: list[float],
    mie_model: str,
    logger: Any,
) -> list[dict[str, str]]:
    logger.debug(
        "write_measured_peaks_into_table called with mie_model=%r peak_positions=%r existing_row_count=%r",
        mie_model,
        peak_positions,
        0 if table_data is None else len(table_data),
    )

    updated_rows = [dict(row) for row in (table_data or [])]
    required_row_count = max(len(updated_rows), len(peak_positions), 3)

    while len(updated_rows) < required_row_count:
        updated_rows.append(build_empty_row_for_model(mie_model))

    for row_index, row in enumerate(updated_rows):
        if mie_model == "Core/Shell Sphere":
            normalized_row = {
                "core_diameter_nm": "" if row.get("core_diameter_nm") is None else str(row.get("core_diameter_nm")),
                "shell_thickness_nm": "" if row.get("shell_thickness_nm") is None else str(row.get("shell_thickness_nm")),
                "outer_diameter_nm": "" if row.get("outer_diameter_nm") is None else str(row.get("outer_diameter_nm")),
                "measured_peak_position": "",
                "expected_coupling": "" if row.get("expected_coupling") is None else str(row.get("expected_coupling")),
            }
        else:
            normalized_row = {
                "particle_diameter_nm": "" if row.get("particle_diameter_nm") is None else str(row.get("particle_diameter_nm")),
                "measured_peak_position": "",
                "expected_coupling": "" if row.get("expected_coupling") is None else str(row.get("expected_coupling")),
            }

        if row_index < len(peak_positions):
            normalized_row["measured_peak_position"] = f"{float(peak_positions[row_index]):.6g}"

        updated_rows[row_index] = normalized_row

    logger.debug(
        "write_measured_peaks_into_table returning row_count=%r rows=%r",
        len(updated_rows),
        updated_rows,
    )

    return updated_rows