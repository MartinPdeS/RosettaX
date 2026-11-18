"""Compatibility imports for the focused scattering calibration modules."""

from . import mie_relation
from .application import (
    apply_scattering_calibration,
)
from .calibration_builder import (
    build_calibration_standard_mie_relation,
    build_core_shell_scattering_calibration_from_standard_data,
    build_scattering_calibration,
    build_solid_sphere_scattering_calibration_from_standard_data,
)
from .calibration_models import (
    DEFAULT_SOURCE_POLARIZATION_ANGLE_DEGREE,
    OpticalParameters,
    ParsedCoreShellStandardRows,
    ParsedSphereStandardRows,
    ScatteringApplicationResult,
    ScatteringCalibration,
    ScatteringCalibrationBuildResult,
    ScatteringInstrumentResponse,
)
from .fitting import (
    compute_r_squared,
    fit_linear_instrument_response,
)
from .numerical_arrays import (
    _as_flat_float_array,  # noqa: F401
    _log_array_summary,  # noqa: F401
    _validate_same_size,  # noqa: F401
)
from .optical_parameters import (
    parse_optical_parameters,
    resolve_mie_model,
)
from .standard_rows import (
    build_reference_table_from_rows,
    parse_core_shell_rows_for_fit,
    parse_sphere_rows_for_fit,
    write_expected_coupling_into_sphere_table,
    write_expected_coupling_into_table,
)

__all__ = [
    "mie_relation",
    "OpticalParameters",
    "ParsedSphereStandardRows",
    "ParsedCoreShellStandardRows",
    "ScatteringInstrumentResponse",
    "ScatteringCalibration",
    "ScatteringCalibrationBuildResult",
    "ScatteringApplicationResult",
    "resolve_mie_model",
    "parse_optical_parameters",
    "parse_sphere_rows_for_fit",
    "parse_core_shell_rows_for_fit",
    "write_expected_coupling_into_table",
    "write_expected_coupling_into_sphere_table",
    "build_reference_table_from_rows",
    "fit_linear_instrument_response",
    "compute_r_squared",
    "build_calibration_standard_mie_relation",
    "build_scattering_calibration",
    "build_solid_sphere_scattering_calibration_from_standard_data",
    "build_core_shell_scattering_calibration_from_standard_data",
    "apply_scattering_calibration",
    "DEFAULT_SOURCE_POLARIZATION_ANGLE_DEGREE",
]
