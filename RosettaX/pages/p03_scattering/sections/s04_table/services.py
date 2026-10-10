"""Workflow table exports and local section assembly."""

from RosettaX.workflow.table.scattering import (
    ScatteringCalibrationStandardTable as ScatteringCalibrationStandardTable,
)
from RosettaX.workflow.table.scattering import (
    add_empty_row_for_model as add_empty_row_for_model,
)
from RosettaX.workflow.table.scattering import (
    build_scattering_parameters_payload as build_scattering_parameters_payload,
)
from RosettaX.workflow.table.scattering import (
    build_table_state_from_runtime_config as build_table_state_from_runtime_config,
)
from RosettaX.workflow.table.scattering import (
    compute_model_for_rows as compute_model_for_rows,
)
from RosettaX.workflow.table.scattering import (
    core_shell_table_columns as core_shell_table_columns,
)
from RosettaX.workflow.table.scattering import (
    get_user_data_column_ids_for_model as get_user_data_column_ids_for_model,
)
from RosettaX.workflow.table.scattering import (
    should_rebuild_table_from_runtime_config as should_rebuild_table_from_runtime_config,
)
from RosettaX.workflow.table.scattering import (
    sphere_table_columns as sphere_table_columns,
)
from RosettaX.workflow.table.scattering import (
    table_is_effectively_empty as table_is_effectively_empty,
)


def build_section(*args, **kwargs):
    """
    Build the scattering s04_table section instance.
    """
    from .main import ReferenceTable

    return ReferenceTable(*args, **kwargs)
