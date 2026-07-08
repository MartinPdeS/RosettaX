from typing import Any

from . import particle_presets, table
from .table import (
    sphere_table_columns,
    core_shell_table_columns,
    resolve_mie_model,
    get_table_columns_for_model,
    populate_table_from_runtime_defaults,
    remap_table_rows_to_model,
    normalize_table_rows
)

from .model import compute_model_for_rows



def build_optical_configuration_preview_figure(*args: Any, **kwargs: Any):
    """
    Lazily import the scattering optical preview helper.

    Importing the page module at package import time creates a circular import
    with the scattering workflow package during test collection.
    """
    from ...pages.p03_scattering.sections.s03_model.optical_preview import (
        build_optical_configuration_preview_figure as _build_optical_configuration_preview_figure,
    )

    return _build_optical_configuration_preview_figure(
        *args,
        **kwargs,
    )

__all__ = [
    "sphere_table_columns",
    "core_shell_table_columns",
    "resolve_mie_model",
    "get_table_columns_for_model",
    "populate_table_from_runtime_defaults",
    "remap_table_rows_to_model",
    "normalize_table_rows",
    "build_optical_configuration_preview_figure",
    "compute_model_for_rows",
    "table",
    "particle_presets",
]
