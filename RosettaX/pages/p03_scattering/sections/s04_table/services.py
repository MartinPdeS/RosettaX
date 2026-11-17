"""Workflow table exports and local section assembly."""

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
