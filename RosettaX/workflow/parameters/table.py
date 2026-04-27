# -*- coding: utf-8 -*-

from typing import Any, Optional

import numpy as np

from RosettaX.workflow.table import services as table_services


MIE_MODEL_SOLID_SPHERE = "Solid Sphere"
MIE_MODEL_CORE_SHELL_SPHERE = "Core/Shell Sphere"

COLUMN_PARTICLE_DIAMETER_NM = "particle_diameter_nm"
COLUMN_CORE_DIAMETER_NM = "core_diameter_nm"
COLUMN_SHELL_THICKNESS_NM = "shell_thickness_nm"
COLUMN_OUTER_DIAMETER_NM = "outer_diameter_nm"
COLUMN_MEASURED_PEAK_POSITION = "measured_peak_position"
COLUMN_EXPECTED_COUPLING = "expected_coupling"


sphere_table_columns = [
    {
        "name": "Particle diameter [nm]",
        "id": COLUMN_PARTICLE_DIAMETER_NM,
        "editable": True,
    },
    {
        "name": "Measured peak position [a.u.]",
        "id": COLUMN_MEASURED_PEAK_POSITION,
        "editable": True,
    },
    {
        "name": "Expected coupling",
        "id": COLUMN_EXPECTED_COUPLING,
        "editable": False,
    },
]

core_shell_table_columns = [
    {
        "name": "Core diameter [nm]",
        "id": COLUMN_CORE_DIAMETER_NM,
        "editable": True,
    },
    {
        "name": "Shell thickness [nm]",
        "id": COLUMN_SHELL_THICKNESS_NM,
        "editable": True,
    },
    {
        "name": "Outer diameter [nm]",
        "id": COLUMN_OUTER_DIAMETER_NM,
        "editable": False,
    },
    {
        "name": "Measured peak position [a.u.]",
        "id": COLUMN_MEASURED_PEAK_POSITION,
        "editable": True,
    },
    {
        "name": "Expected coupling",
        "id": COLUMN_EXPECTED_COUPLING,
        "editable": False,
    },
]


def resolve_mie_model(
    mie_model: Any,
) -> str:
    """
    Normalize a raw Mie model value.

    Unknown or empty values fall back to the solid sphere model.
    """
    mie_model_string = "" if mie_model is None else str(mie_model).strip()

    if mie_model_string == MIE_MODEL_CORE_SHELL_SPHERE:
        return MIE_MODEL_CORE_SHELL_SPHERE

    return MIE_MODEL_SOLID_SPHERE


def get_table_columns_for_model(
    mie_model: Any,
) -> list[dict[str, Any]]:
    """
    Return calibration standard table columns for a Mie model.
    """
    resolved_mie_model = resolve_mie_model(
        mie_model,
    )

    if resolved_mie_model == MIE_MODEL_CORE_SHELL_SPHERE:
        return [
            dict(column)
            for column in core_shell_table_columns
        ]

    return [
        dict(column)
        for column in sphere_table_columns
    ]


def get_user_data_column_ids_for_model(
    mie_model: Any,
) -> list[str]:
    """
    Return the columns that should count as populated table data.
    """
    return table_services.get_column_ids(
        columns=get_table_columns_for_model(
            mie_model,
        )
    )


def build_empty_row_for_model(
    mie_model: Any,
) -> dict[str, str]:
    """
    Build one empty calibration standard table row for a Mie model.
    """
    resolved_mie_model = resolve_mie_model(
        mie_model,
    )

    if resolved_mie_model == MIE_MODEL_CORE_SHELL_SPHERE:
        return {
            COLUMN_CORE_DIAMETER_NM: "",
            COLUMN_SHELL_THICKNESS_NM: "",
            COLUMN_OUTER_DIAMETER_NM: "",
            COLUMN_MEASURED_PEAK_POSITION: "",
            COLUMN_EXPECTED_COUPLING: "",
        }

    return {
        COLUMN_PARTICLE_DIAMETER_NM: "",
        COLUMN_MEASURED_PEAK_POSITION: "",
        COLUMN_EXPECTED_COUPLING: "",
    }


def build_empty_rows_for_model(
    mie_model: Any,
    *,
    row_count: int,
) -> list[dict[str, str]]:
    """
    Build empty calibration standard table rows for a Mie model.
    """
    resolved_row_count = max(
        0,
        int(
            row_count,
        ),
    )

    return [
        build_empty_row_for_model(
            mie_model,
        )
        for _ in range(
            resolved_row_count,
        )
    ]


def normalize_cell_value(
    value: Any,
) -> str:
    """
    Normalize a Dash DataTable cell value into a stripped string.
    """
    if value is None:
        return ""

    return str(
        value,
    ).strip()


def compute_outer_diameter_string(
    *,
    core_diameter_nm: Any,
    shell_thickness_nm: Any,
) -> str:
    """
    Compute the outer diameter string for a core shell standard row.
    """
    try:
        resolved_core_diameter_nm = float(
            core_diameter_nm,
        )

        resolved_shell_thickness_nm = float(
            shell_thickness_nm,
        )

    except Exception:
        return ""

    if resolved_core_diameter_nm <= 0.0:
        return ""

    if resolved_shell_thickness_nm < 0.0:
        return ""

    outer_diameter_nm = resolved_core_diameter_nm + 2.0 * resolved_shell_thickness_nm

    return f"{outer_diameter_nm:.6g}"


def remap_table_rows_to_model(
    *,
    mie_model: Any,
    current_rows: Optional[list[dict[str, Any]]],
) -> list[dict[str, str]]:
    """
    Remap existing table rows to the selected Mie model schema.

    This preserves compatible values when switching between solid sphere and
    core shell sphere table schemas.
    """
    resolved_mie_model = resolve_mie_model(
        mie_model,
    )

    source_rows = table_services.copy_table_rows(
        rows=current_rows,
    )

    row_count = max(
        3,
        len(
            source_rows,
        ),
    )

    if resolved_mie_model == MIE_MODEL_CORE_SHELL_SPHERE:
        return [
            remap_row_to_core_shell_model(
                row=source_rows[row_index] if row_index < len(source_rows) else {},
            )
            for row_index in range(
                row_count,
            )
        ]

    return [
        remap_row_to_solid_sphere_model(
            row=source_rows[row_index] if row_index < len(source_rows) else {},
        )
        for row_index in range(
            row_count,
        )
    ]


def remap_row_to_core_shell_model(
    *,
    row: dict[str, Any],
) -> dict[str, str]:
    """
    Remap one source row to the core shell table schema.
    """
    particle_diameter_nm = normalize_cell_value(
        row.get(
            COLUMN_PARTICLE_DIAMETER_NM,
        )
    )

    core_diameter_nm = normalize_cell_value(
        row.get(
            COLUMN_CORE_DIAMETER_NM,
        )
    )

    shell_thickness_nm = normalize_cell_value(
        row.get(
            COLUMN_SHELL_THICKNESS_NM,
        )
    )

    measured_peak_position = normalize_cell_value(
        row.get(
            COLUMN_MEASURED_PEAK_POSITION,
        )
    )

    expected_coupling = normalize_cell_value(
        row.get(
            COLUMN_EXPECTED_COUPLING,
        )
    )

    if not core_diameter_nm and particle_diameter_nm:
        core_diameter_nm = particle_diameter_nm

    return {
        COLUMN_CORE_DIAMETER_NM: core_diameter_nm,
        COLUMN_SHELL_THICKNESS_NM: shell_thickness_nm,
        COLUMN_OUTER_DIAMETER_NM: compute_outer_diameter_string(
            core_diameter_nm=core_diameter_nm,
            shell_thickness_nm=shell_thickness_nm,
        ),
        COLUMN_MEASURED_PEAK_POSITION: measured_peak_position,
        COLUMN_EXPECTED_COUPLING: expected_coupling,
    }


def remap_row_to_solid_sphere_model(
    *,
    row: dict[str, Any],
) -> dict[str, str]:
    """
    Remap one source row to the solid sphere table schema.
    """
    particle_diameter_nm = normalize_cell_value(
        row.get(
            COLUMN_PARTICLE_DIAMETER_NM,
        )
    )

    core_diameter_nm = normalize_cell_value(
        row.get(
            COLUMN_CORE_DIAMETER_NM,
        )
    )

    outer_diameter_nm = normalize_cell_value(
        row.get(
            COLUMN_OUTER_DIAMETER_NM,
        )
    )

    measured_peak_position = normalize_cell_value(
        row.get(
            COLUMN_MEASURED_PEAK_POSITION,
        )
    )

    expected_coupling = normalize_cell_value(
        row.get(
            COLUMN_EXPECTED_COUPLING,
        )
    )

    if not particle_diameter_nm:
        if outer_diameter_nm:
            particle_diameter_nm = outer_diameter_nm

        elif core_diameter_nm:
            particle_diameter_nm = core_diameter_nm

    return {
        COLUMN_PARTICLE_DIAMETER_NM: particle_diameter_nm,
        COLUMN_MEASURED_PEAK_POSITION: measured_peak_position,
        COLUMN_EXPECTED_COUPLING: expected_coupling,
    }


def normalize_table_rows(
    *,
    mie_model: Any,
    current_rows: Optional[list[dict[str, Any]]],
) -> list[dict[str, str]]:
    """
    Normalize table rows according to the selected Mie model schema.
    """
    resolved_mie_model = resolve_mie_model(
        mie_model,
    )

    source_rows = table_services.copy_table_rows(
        rows=current_rows,
    )

    if resolved_mie_model == MIE_MODEL_CORE_SHELL_SPHERE:
        return [
            normalize_core_shell_row(
                row=row,
            )
            for row in source_rows
        ]

    return [
        normalize_solid_sphere_row(
            row=row,
        )
        for row in source_rows
    ]


def normalize_core_shell_row(
    *,
    row: dict[str, Any],
) -> dict[str, str]:
    """
    Normalize one core shell table row.
    """
    core_diameter_nm = normalize_cell_value(
        row.get(
            COLUMN_CORE_DIAMETER_NM,
        )
    )

    shell_thickness_nm = normalize_cell_value(
        row.get(
            COLUMN_SHELL_THICKNESS_NM,
        )
    )

    return {
        COLUMN_CORE_DIAMETER_NM: core_diameter_nm,
        COLUMN_SHELL_THICKNESS_NM: shell_thickness_nm,
        COLUMN_OUTER_DIAMETER_NM: compute_outer_diameter_string(
            core_diameter_nm=core_diameter_nm,
            shell_thickness_nm=shell_thickness_nm,
        ),
        COLUMN_MEASURED_PEAK_POSITION: normalize_cell_value(
            row.get(
                COLUMN_MEASURED_PEAK_POSITION,
            )
        ),
        COLUMN_EXPECTED_COUPLING: normalize_cell_value(
            row.get(
                COLUMN_EXPECTED_COUPLING,
            )
        ),
    }


def normalize_solid_sphere_row(
    *,
    row: dict[str, Any],
) -> dict[str, str]:
    """
    Normalize one solid sphere table row.
    """
    return {
        COLUMN_PARTICLE_DIAMETER_NM: normalize_cell_value(
            row.get(
                COLUMN_PARTICLE_DIAMETER_NM,
            )
        ),
        COLUMN_MEASURED_PEAK_POSITION: normalize_cell_value(
            row.get(
                COLUMN_MEASURED_PEAK_POSITION,
            )
        ),
        COLUMN_EXPECTED_COUPLING: normalize_cell_value(
            row.get(
                COLUMN_EXPECTED_COUPLING,
            )
        ),
    }


def table_is_effectively_empty(
    *,
    mie_model: Any,
    rows: Optional[list[dict[str, Any]]],
) -> bool:
    """
    Return whether the calibration standard table contains no useful data.
    """
    resolved_mie_model = resolve_mie_model(
        mie_model,
    )

    normalized_rows = normalize_table_rows(
        mie_model=resolved_mie_model,
        current_rows=rows,
    )

    return table_services.table_is_effectively_empty(
        rows=normalized_rows,
        user_data_column_ids=get_user_data_column_ids_for_model(
            resolved_mie_model,
        ),
    )


def as_float_list_from_runtime_value(
    value: Any,
) -> list[float]:
    """
    Convert a runtime configuration value into a finite float list.
    """
    if value in (None, ""):
        return []

    if isinstance(
        value,
        (list, tuple),
    ):
        values = value

    else:
        values = str(
            value,
        ).replace(
            ";",
            ",",
        ).split(
            ",",
        )

    float_values: list[float] = []

    for item in values:
        try:
            parsed_value = float(
                str(
                    item,
                ).strip()
            )

        except Exception:
            continue

        if np.isfinite(
            parsed_value,
        ):
            float_values.append(
                parsed_value,
            )

    return float_values


def populate_table_from_runtime_defaults(
    *,
    mie_model: Any,
    runtime_particle_diameters_nm: Any,
    runtime_core_diameters_nm: Any,
    runtime_shell_thicknesses_nm: Any,
) -> list[dict[str, str]]:
    """
    Populate calibration standard table rows from runtime configuration values.
    """
    resolved_mie_model = resolve_mie_model(
        mie_model,
    )

    if resolved_mie_model == MIE_MODEL_CORE_SHELL_SPHERE:
        return populate_core_shell_rows_from_runtime_defaults(
            runtime_core_diameters_nm=runtime_core_diameters_nm,
            runtime_shell_thicknesses_nm=runtime_shell_thicknesses_nm,
        )

    return populate_solid_sphere_rows_from_runtime_defaults(
        runtime_particle_diameters_nm=runtime_particle_diameters_nm,
    )


def populate_core_shell_rows_from_runtime_defaults(
    *,
    runtime_core_diameters_nm: Any,
    runtime_shell_thicknesses_nm: Any,
) -> list[dict[str, str]]:
    """
    Populate core shell calibration standard rows from runtime defaults.
    """
    core_diameters_nm = as_float_list_from_runtime_value(
        runtime_core_diameters_nm,
    )

    shell_thicknesses_nm = as_float_list_from_runtime_value(
        runtime_shell_thicknesses_nm,
    )

    row_count = max(
        3,
        len(
            core_diameters_nm,
        ),
        len(
            shell_thicknesses_nm,
        ),
    )

    rows: list[dict[str, str]] = []

    for row_index in range(
        row_count,
    ):
        core_diameter_nm = (
            f"{float(core_diameters_nm[row_index]):.6g}"
            if row_index < len(core_diameters_nm)
            else ""
        )

        shell_thickness_nm = (
            f"{float(shell_thicknesses_nm[row_index]):.6g}"
            if row_index < len(shell_thicknesses_nm)
            else ""
        )

        rows.append(
            {
                COLUMN_CORE_DIAMETER_NM: core_diameter_nm,
                COLUMN_SHELL_THICKNESS_NM: shell_thickness_nm,
                COLUMN_OUTER_DIAMETER_NM: compute_outer_diameter_string(
                    core_diameter_nm=core_diameter_nm,
                    shell_thickness_nm=shell_thickness_nm,
                ),
                COLUMN_MEASURED_PEAK_POSITION: "",
                COLUMN_EXPECTED_COUPLING: "",
            }
        )

    return rows


def populate_solid_sphere_rows_from_runtime_defaults(
    *,
    runtime_particle_diameters_nm: Any,
) -> list[dict[str, str]]:
    """
    Populate solid sphere calibration standard rows from runtime defaults.
    """
    particle_diameters_nm = as_float_list_from_runtime_value(
        runtime_particle_diameters_nm,
    )

    row_count = max(
        3,
        len(
            particle_diameters_nm,
        ),
    )

    rows: list[dict[str, str]] = []

    for row_index in range(
        row_count,
    ):
        particle_diameter_nm = (
            f"{float(particle_diameters_nm[row_index]):.6g}"
            if row_index < len(particle_diameters_nm)
            else ""
        )

        rows.append(
            {
                COLUMN_PARTICLE_DIAMETER_NM: particle_diameter_nm,
                COLUMN_MEASURED_PEAK_POSITION: "",
                COLUMN_EXPECTED_COUPLING: "",
            }
        )

    return rows