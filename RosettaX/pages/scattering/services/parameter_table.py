# -*- coding: utf-8 -*-

from typing import Any, Optional

import numpy as np


sphere_table_columns = [
    {"name": "Particle diameter [nm]", "id": "particle_diameter_nm", "editable": True},
    {"name": "Measured peak position [a.u.]", "id": "measured_peak_position", "editable": True},
    {"name": "Expected coupling", "id": "expected_coupling", "editable": False},
]

core_shell_table_columns = [
    {"name": "Core diameter [nm]", "id": "core_diameter_nm", "editable": True},
    {"name": "Shell thickness [nm]", "id": "shell_thickness_nm", "editable": True},
    {"name": "Outer diameter [nm]", "id": "outer_diameter_nm", "editable": False},
    {"name": "Measured peak position [a.u.]", "id": "measured_peak_position", "editable": True},
    {"name": "Expected coupling", "id": "expected_coupling", "editable": False},
]


def resolve_mie_model(mie_model: Any) -> str:
    mie_model_string = "" if mie_model is None else str(mie_model).strip()
    return "Core/Shell Sphere" if mie_model_string == "Core/Shell Sphere" else "Solid Sphere"


def get_table_columns_for_model(mie_model: str) -> list[dict[str, Any]]:
    return list(core_shell_table_columns) if mie_model == "Core/Shell Sphere" else list(sphere_table_columns)


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


def build_empty_rows_for_model(mie_model: str, row_count: int) -> list[dict[str, str]]:
    return [build_empty_row_for_model(mie_model) for _ in range(int(row_count))]


def normalize_editable_cell(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def normalize_readonly_cell(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def compute_outer_diameter_string(
    *,
    core_diameter_nm: Any,
    shell_thickness_nm: Any,
) -> str:
    try:
        resolved_core_diameter_nm = float(core_diameter_nm)
        resolved_shell_thickness_nm = float(shell_thickness_nm)
    except Exception:
        return ""

    if resolved_core_diameter_nm <= 0.0 or resolved_shell_thickness_nm < 0.0:
        return ""

    outer_diameter_nm = resolved_core_diameter_nm + 2.0 * resolved_shell_thickness_nm
    return f"{outer_diameter_nm:.6g}"


def remap_table_rows_to_model(
    *,
    mie_model: str,
    current_rows: Optional[list[dict[str, Any]]],
) -> list[dict[str, str]]:
    resolved_current_rows = [dict(row) for row in (current_rows or [])]
    row_count = max(3, len(resolved_current_rows))
    remapped_rows: list[dict[str, str]] = []

    if mie_model == "Core/Shell Sphere":
        for row_index in range(row_count):
            source_row = resolved_current_rows[row_index] if row_index < len(resolved_current_rows) else {}

            particle_diameter_nm = normalize_editable_cell(source_row.get("particle_diameter_nm"))
            core_diameter_nm = normalize_editable_cell(source_row.get("core_diameter_nm"))
            shell_thickness_nm = normalize_editable_cell(source_row.get("shell_thickness_nm"))
            measured_peak_position = normalize_editable_cell(source_row.get("measured_peak_position"))
            expected_coupling = normalize_readonly_cell(source_row.get("expected_coupling"))

            if not core_diameter_nm and particle_diameter_nm:
                core_diameter_nm = particle_diameter_nm

            outer_diameter_nm = compute_outer_diameter_string(
                core_diameter_nm=core_diameter_nm,
                shell_thickness_nm=shell_thickness_nm,
            )

            remapped_rows.append(
                {
                    "core_diameter_nm": core_diameter_nm,
                    "shell_thickness_nm": shell_thickness_nm,
                    "outer_diameter_nm": outer_diameter_nm,
                    "measured_peak_position": measured_peak_position,
                    "expected_coupling": expected_coupling,
                }
            )

        return remapped_rows

    for row_index in range(row_count):
        source_row = resolved_current_rows[row_index] if row_index < len(resolved_current_rows) else {}

        particle_diameter_nm = normalize_editable_cell(source_row.get("particle_diameter_nm"))
        core_diameter_nm = normalize_editable_cell(source_row.get("core_diameter_nm"))
        outer_diameter_nm = normalize_editable_cell(source_row.get("outer_diameter_nm"))
        measured_peak_position = normalize_editable_cell(source_row.get("measured_peak_position"))
        expected_coupling = normalize_readonly_cell(source_row.get("expected_coupling"))

        if not particle_diameter_nm:
            if outer_diameter_nm:
                particle_diameter_nm = outer_diameter_nm
            elif core_diameter_nm:
                particle_diameter_nm = core_diameter_nm

        remapped_rows.append(
            {
                "particle_diameter_nm": particle_diameter_nm,
                "measured_peak_position": measured_peak_position,
                "expected_coupling": expected_coupling,
            }
        )

    return remapped_rows


def normalize_table_rows(
    *,
    mie_model: str,
    current_rows: Optional[list[dict[str, Any]]],
) -> list[dict[str, str]]:
    resolved_current_rows = [dict(row) for row in (current_rows or [])]

    if mie_model == "Core/Shell Sphere":
        normalized_rows: list[dict[str, str]] = []

        for source_row in resolved_current_rows:
            core_diameter_nm = normalize_editable_cell(source_row.get("core_diameter_nm"))
            shell_thickness_nm = normalize_editable_cell(source_row.get("shell_thickness_nm"))
            measured_peak_position = normalize_editable_cell(source_row.get("measured_peak_position"))
            expected_coupling = normalize_readonly_cell(source_row.get("expected_coupling"))

            outer_diameter_nm = compute_outer_diameter_string(
                core_diameter_nm=core_diameter_nm,
                shell_thickness_nm=shell_thickness_nm,
            )

            normalized_rows.append(
                {
                    "core_diameter_nm": core_diameter_nm,
                    "shell_thickness_nm": shell_thickness_nm,
                    "outer_diameter_nm": outer_diameter_nm,
                    "measured_peak_position": measured_peak_position,
                    "expected_coupling": expected_coupling,
                }
            )

        return normalized_rows

    normalized_rows: list[dict[str, str]] = []

    for source_row in resolved_current_rows:
        normalized_rows.append(
            {
                "particle_diameter_nm": normalize_editable_cell(source_row.get("particle_diameter_nm")),
                "measured_peak_position": normalize_editable_cell(source_row.get("measured_peak_position")),
                "expected_coupling": normalize_readonly_cell(source_row.get("expected_coupling")),
            }
        )

    return normalized_rows


def table_is_effectively_empty(
    *,
    mie_model: str,
    rows: Optional[list[dict[str, Any]]],
) -> bool:
    normalized_rows = normalize_table_rows(
        mie_model=mie_model,
        current_rows=rows,
    )

    if not normalized_rows:
        return True

    if mie_model == "Core/Shell Sphere":
        for row in normalized_rows:
            if (
                str(row.get("core_diameter_nm", "")).strip()
                or str(row.get("shell_thickness_nm", "")).strip()
                or str(row.get("measured_peak_position", "")).strip()
                or str(row.get("expected_coupling", "")).strip()
            ):
                return False
        return True

    for row in normalized_rows:
        if (
            str(row.get("particle_diameter_nm", "")).strip()
            or str(row.get("measured_peak_position", "")).strip()
            or str(row.get("expected_coupling", "")).strip()
        ):
            return False

    return True


def as_float_list_from_runtime_value(value: Any) -> list[float]:
    if value in (None, ""):
        return []

    if isinstance(value, (list, tuple)):
        result: list[float] = []
        for item in value:
            try:
                parsed_value = float(item)
            except Exception:
                continue
            if np.isfinite(parsed_value):
                result.append(float(parsed_value))
        return result

    text = str(value).replace(";", ",")
    result: list[float] = []

    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            parsed_value = float(part)
        except Exception:
            continue
        if np.isfinite(parsed_value):
            result.append(float(parsed_value))

    return result


def populate_table_from_runtime_defaults(
    *,
    mie_model: str,
    runtime_particle_diameters_nm: Any,
    runtime_core_diameters_nm: Any,
    runtime_shell_thicknesses_nm: Any,
) -> list[dict[str, str]]:
    if mie_model == "Core/Shell Sphere":
        core_diameters_nm = as_float_list_from_runtime_value(runtime_core_diameters_nm)
        shell_thicknesses_nm = as_float_list_from_runtime_value(runtime_shell_thicknesses_nm)

        row_count = max(3, len(core_diameters_nm), len(shell_thicknesses_nm))
        rows: list[dict[str, str]] = []

        for index in range(row_count):
            core_value = (
                f"{float(core_diameters_nm[index]):.6g}"
                if index < len(core_diameters_nm)
                else ""
            )
            shell_value = (
                f"{float(shell_thicknesses_nm[index]):.6g}"
                if index < len(shell_thicknesses_nm)
                else ""
            )

            rows.append(
                {
                    "core_diameter_nm": core_value,
                    "shell_thickness_nm": shell_value,
                    "outer_diameter_nm": compute_outer_diameter_string(
                        core_diameter_nm=core_value,
                        shell_thickness_nm=shell_value,
                    ),
                    "measured_peak_position": "",
                    "expected_coupling": "",
                }
            )

        return rows

    particle_diameters_nm = as_float_list_from_runtime_value(runtime_particle_diameters_nm)
    row_count = max(3, len(particle_diameters_nm))
    rows: list[dict[str, str]] = []

    for index in range(row_count):
        particle_value = (
            f"{float(particle_diameters_nm[index]):.6g}"
            if index < len(particle_diameters_nm)
            else ""
        )
        rows.append(
            {
                "particle_diameter_nm": particle_value,
                "measured_peak_position": "",
                "expected_coupling": "",
            }
        )

    return rows