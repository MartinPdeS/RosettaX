"""Workflow table exports and local section assembly."""

import math
from RosettaX.workflow import parameters
from RosettaX.workflow.table.scattering import (
    ScatteringCalibrationStandardTable,
    add_empty_row_for_model,
    build_scattering_parameters_payload,
    build_table_state_from_runtime_config,
    compute_model_for_rows,
    core_shell_table_columns,
    get_user_data_column_ids_for_model,
    should_rebuild_table_from_runtime_config,
    sphere_table_columns,
    table_is_effectively_empty,
)


def add_custom_diameter_rows(*, mie_model, diameters, shell_thicknesses, current_rows):
    """Append custom particle dimensions in nm, validating each input list.

    A single shell thickness applies to every core diameter. Raises ValueError
    when values are invalid or the lists have incompatible lengths.
    """
    def parse_values(value, *, label, allow_zero=False):
        """Parse a comma-separated list of finite dimensions."""
        try:
            values = [float(item.strip()) for item in (value or "").split(",")]
        except (ValueError, AttributeError):
            raise ValueError(f"Enter comma-separated numbers for {label}.") from None
        if any(not math.isfinite(item) or item < 0 or (item == 0 and not allow_zero) for item in values):
            raise ValueError(f"{label.capitalize()} must be {'non-negative' if allow_zero else 'positive'} finite numbers.")
        return values

    diameter_values = parse_values(diameters, label="diameters")
    is_core_shell = parameters.table.resolve_mie_model(mie_model) == parameters.table.MIE_MODEL_CORE_SHELL_SPHERE
    shell_values = []
    if is_core_shell:
        shell_values = parse_values(shell_thicknesses, label="shell thicknesses", allow_zero=True)
        if len(shell_values) == 1:
            shell_values *= len(diameter_values)
        elif len(shell_values) != len(diameter_values):
            raise ValueError("Enter one shell thickness or one for each core diameter.")

    rows = list(current_rows or [])
    for index, diameter in enumerate(diameter_values):
        row = parameters.table.build_empty_row_for_model(mie_model)
        if is_core_shell:
            row[parameters.table.COLUMN_CORE_DIAMETER_NM] = f"{diameter:.12g}"
            row[parameters.table.COLUMN_SHELL_THICKNESS_NM] = f"{shell_values[index]:.12g}"
        else:
            row[parameters.table.COLUMN_PARTICLE_DIAMETER_NM] = f"{diameter:.12g}"
        rows.append(row)
    return ScatteringCalibrationStandardTable.normalize_rows(mie_model=mie_model, rows=rows)

__all__ = [
    "ScatteringCalibrationStandardTable",
    "add_empty_row_for_model",
    "build_scattering_parameters_payload",
    "build_table_state_from_runtime_config",
    "compute_model_for_rows",
    "core_shell_table_columns",
    "get_user_data_column_ids_for_model",
    "should_rebuild_table_from_runtime_config",
    "sphere_table_columns",
    "table_is_effectively_empty",
    "build_section",
]


def build_section(*args, **kwargs):
    """
    Build the scattering s04_table section instance.
    """
    from .main import ReferenceTable

    return ReferenceTable(*args, **kwargs)
