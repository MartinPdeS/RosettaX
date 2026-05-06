# -*- coding: utf-8 -*-

from dataclasses import asdict, dataclass
from typing import Any, Callable, Optional

import numpy as np


@dataclass(frozen=True)
class MieRelation:
    """
    Diameter to theoretical coupling relation generated from a Mie model.

    This object can represent either:
    - the calibration standard relation used to build an instrument response
    - the target particle relation used when applying a scattering calibration

    The relation is stored as diameter_nm -> theoretical_coupling.
    """

    diameter_nm: list[float]
    theoretical_coupling: list[float]
    mie_model: str
    parameters: dict[str, Any]
    is_monotonic: bool
    relation_role: str
    valid_min_diameter_nm: Optional[float] = None
    valid_max_diameter_nm: Optional[float] = None
    valid_min_coupling: Optional[float] = None
    valid_max_coupling: Optional[float] = None
    inversion_method: str = "linear_interpolation"

    def coupling_to_diameter(
        self,
        coupling_values: np.ndarray,
    ) -> np.ndarray:
        """
        Convert theoretical coupling values into equivalent diameters.

        This inversion is physically unambiguous only when theoretical coupling
        is monotonic over the stored diameter range.
        """
        coupling_array = np.asarray(
            coupling_values,
            dtype=float,
        )

        diameter_grid = np.asarray(
            self.diameter_nm,
            dtype=float,
        )

        coupling_grid = np.asarray(
            self.theoretical_coupling,
            dtype=float,
        )

        diameter_grid, coupling_grid = sanitize_relation_arrays(
            diameter_nm=diameter_grid,
            theoretical_coupling=coupling_grid,
        )

        if diameter_grid.size < 2:
            return np.full_like(
                coupling_array,
                np.nan,
                dtype=float,
            )

        if not relation_is_monotonic(
            values=coupling_grid,
        ):
            return np.full_like(
                coupling_array,
                np.nan,
                dtype=float,
            )

        sorted_coupling_grid, sorted_diameter_grid = prepare_unique_interpolation_grid(
            x_values=coupling_grid,
            y_values=diameter_grid,
        )

        if sorted_coupling_grid.size < 2:
            return np.full_like(
                coupling_array,
                np.nan,
                dtype=float,
            )

        return np.interp(
            coupling_array,
            sorted_coupling_grid,
            sorted_diameter_grid,
            left=np.nan,
            right=np.nan,
        )

    def diameter_to_coupling(
        self,
        diameter_values_nm: np.ndarray,
    ) -> np.ndarray:
        """
        Convert diameters into theoretical coupling values by interpolation.
        """
        diameter_array = np.asarray(
            diameter_values_nm,
            dtype=float,
        )

        diameter_grid = np.asarray(
            self.diameter_nm,
            dtype=float,
        )

        coupling_grid = np.asarray(
            self.theoretical_coupling,
            dtype=float,
        )

        diameter_grid, coupling_grid = sanitize_relation_arrays(
            diameter_nm=diameter_grid,
            theoretical_coupling=coupling_grid,
        )

        if diameter_grid.size < 2:
            return np.full_like(
                diameter_array,
                np.nan,
                dtype=float,
            )

        sorted_diameter_grid, sorted_coupling_grid = prepare_unique_interpolation_grid(
            x_values=diameter_grid,
            y_values=coupling_grid,
        )

        if sorted_diameter_grid.size < 2:
            return np.full_like(
                diameter_array,
                np.nan,
                dtype=float,
            )

        return np.interp(
            diameter_array,
            sorted_diameter_grid,
            sorted_coupling_grid,
            left=np.nan,
            right=np.nan,
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the Mie relation into a JSON serializable dictionary.
        """
        return asdict(
            self,
        )

    @classmethod
    def from_dict(
        cls,
        payload: dict[str, Any],
    ) -> "MieRelation":
        """
        Build a Mie relation from a dictionary payload.
        """
        if not isinstance(payload, dict):
            raise TypeError("MieRelation payload must be a dictionary.")

        diameter_values = payload.get(
            "diameter_nm",
            [],
        )

        coupling_values = payload.get(
            "theoretical_coupling",
            [],
        )

        diameter_nm = [
            float(value)
            for value in diameter_values
        ]

        theoretical_coupling = [
            float(value)
            for value in coupling_values
        ]

        valid_min_diameter_nm = payload.get(
            "valid_min_diameter_nm",
            None,
        )

        valid_max_diameter_nm = payload.get(
            "valid_max_diameter_nm",
            None,
        )

        valid_min_coupling = payload.get(
            "valid_min_coupling",
            None,
        )

        valid_max_coupling = payload.get(
            "valid_max_coupling",
            None,
        )

        return cls(
            diameter_nm=diameter_nm,
            theoretical_coupling=theoretical_coupling,
            mie_model=str(
                payload.get(
                    "mie_model",
                    "",
                )
            ),
            parameters=dict(
                payload.get(
                    "parameters",
                    {},
                )
            ),
            is_monotonic=bool(
                payload.get(
                    "is_monotonic",
                    relation_is_monotonic(
                        values=theoretical_coupling,
                    ),
                )
            ),
            relation_role=str(
                payload.get(
                    "relation_role",
                    "",
                )
            ),
            valid_min_diameter_nm=optional_float(
                valid_min_diameter_nm,
            ),
            valid_max_diameter_nm=optional_float(
                valid_max_diameter_nm,
            ),
            valid_min_coupling=optional_float(
                valid_min_coupling,
            ),
            valid_max_coupling=optional_float(
                valid_max_coupling,
            ),
            inversion_method=str(
                payload.get(
                    "inversion_method",
                    "linear_interpolation",
                )
            ),
        )


def optional_float(
    value: Any,
) -> Optional[float]:
    """
    Convert a value to float unless it is None.
    """
    if value is None:
        return None

    return float(
        value,
    )


def build_diameter_grid(
    *,
    diameter_min_nm: Any,
    diameter_max_nm: Any,
    diameter_count: Any,
) -> np.ndarray:
    """
    Build a diameter grid in nanometers.
    """
    resolved_diameter_min_nm = float(
        diameter_min_nm,
    )

    resolved_diameter_max_nm = float(
        diameter_max_nm,
    )

    resolved_diameter_count = int(
        diameter_count,
    )

    if resolved_diameter_count < 2:
        raise ValueError("diameter_count must be at least 2.")

    if resolved_diameter_min_nm <= 0.0:
        raise ValueError("diameter_min_nm must be positive.")

    if resolved_diameter_max_nm <= resolved_diameter_min_nm:
        raise ValueError("diameter_max_nm must be greater than diameter_min_nm.")

    return np.linspace(
        resolved_diameter_min_nm,
        resolved_diameter_max_nm,
        resolved_diameter_count,
    )


def sanitize_relation_arrays(
    *,
    diameter_nm: Any,
    theoretical_coupling: Any,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Convert relation arrays to finite one dimensional arrays sorted by diameter.
    """
    diameter_array = np.asarray(
        diameter_nm,
        dtype=float,
    )

    coupling_array = np.asarray(
        theoretical_coupling,
        dtype=float,
    )

    if diameter_array.ndim != 1:
        diameter_array = diameter_array.ravel()

    if coupling_array.ndim != 1:
        coupling_array = coupling_array.ravel()

    if diameter_array.size != coupling_array.size:
        raise ValueError("diameter_nm and theoretical_coupling must have the same length.")

    finite_mask = (
        np.isfinite(
            diameter_array,
        )
        & np.isfinite(
            coupling_array,
        )
    )

    diameter_array = diameter_array[finite_mask]
    coupling_array = coupling_array[finite_mask]

    if diameter_array.size == 0:
        return diameter_array, coupling_array

    sorting_indices = np.argsort(
        diameter_array,
    )

    return (
        diameter_array[sorting_indices],
        coupling_array[sorting_indices],
    )


def prepare_unique_interpolation_grid(
    *,
    x_values: Any,
    y_values: Any,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Prepare a finite sorted interpolation grid with unique x values.
    """
    x_array = np.asarray(
        x_values,
        dtype=float,
    )

    y_array = np.asarray(
        y_values,
        dtype=float,
    )

    if x_array.ndim != 1:
        x_array = x_array.ravel()

    if y_array.ndim != 1:
        y_array = y_array.ravel()

    if x_array.size != y_array.size:
        raise ValueError("x_values and y_values must have the same length.")

    finite_mask = (
        np.isfinite(
            x_array,
        )
        & np.isfinite(
            y_array,
        )
    )

    x_array = x_array[finite_mask]
    y_array = y_array[finite_mask]

    if x_array.size == 0:
        return x_array, y_array

    sorting_indices = np.argsort(
        x_array,
    )

    sorted_x_values = x_array[sorting_indices]
    sorted_y_values = y_array[sorting_indices]

    unique_x_values, unique_indices = np.unique(
        sorted_x_values,
        return_index=True,
    )

    unique_y_values = sorted_y_values[unique_indices]

    return unique_x_values, unique_y_values


def relation_is_monotonic(
    *,
    values: Any,
) -> bool:
    """
    Return whether a sequence is monotonic increasing or decreasing.
    """
    value_array = np.asarray(
        values,
        dtype=float,
    )

    value_array = value_array[
        np.isfinite(
            value_array,
        )
    ]

    if value_array.size < 2:
        return False

    differences = np.diff(
        value_array,
    )

    return bool(
        np.all(
            differences >= 0.0,
        )
        or np.all(
            differences <= 0.0,
        )
    )


def relation_is_strictly_monotonic(
    *,
    values: Any,
) -> bool:
    """
    Return whether a sequence is strictly monotonic increasing or decreasing.
    """
    value_array = np.asarray(
        values,
        dtype=float,
    )

    value_array = value_array[
        np.isfinite(
            value_array,
        )
    ]

    if value_array.size < 2:
        return False

    differences = np.diff(
        value_array,
    )

    return bool(
        np.all(
            differences > 0.0,
        )
        or np.all(
            differences < 0.0,
        )
    )


def build_mie_relation_from_arrays(
    *,
    diameter_nm: Any,
    theoretical_coupling: Any,
    mie_model: str,
    parameters: Optional[dict[str, Any]] = None,
    relation_role: str,
    inversion_method: str = "linear_interpolation",
) -> MieRelation:
    """
    Build a Mie relation from precomputed diameter and coupling arrays.
    """
    diameter_array, coupling_array = sanitize_relation_arrays(
        diameter_nm=diameter_nm,
        theoretical_coupling=theoretical_coupling,
    )

    if diameter_array.size < 2:
        raise ValueError("At least two finite diameter and coupling points are required.")

    return MieRelation(
        diameter_nm=[
            float(value)
            for value in diameter_array
        ],
        theoretical_coupling=[
            float(value)
            for value in coupling_array
        ],
        mie_model=str(
            mie_model,
        ),
        parameters=dict(
            parameters or {},
        ),
        is_monotonic=relation_is_monotonic(
            values=coupling_array,
        ),
        relation_role=str(
            relation_role,
        ),
        valid_min_diameter_nm=float(
            np.min(
                diameter_array,
            )
        ),
        valid_max_diameter_nm=float(
            np.max(
                diameter_array,
            )
        ),
        valid_min_coupling=float(
            np.min(
                coupling_array,
            )
        ),
        valid_max_coupling=float(
            np.max(
                coupling_array,
            )
        ),
        inversion_method=str(
            inversion_method,
        ),
    )


def build_mie_relation_from_callable(
    *,
    diameter_nm: Any,
    coupling_function: Callable[[np.ndarray], np.ndarray],
    mie_model: str,
    parameters: Optional[dict[str, Any]] = None,
    relation_role: str,
    inversion_method: str = "linear_interpolation",
) -> MieRelation:
    """
    Build a Mie relation from a function that maps diameter to coupling.

    The callable should accept a one dimensional NumPy array of diameters in nm
    and return a one dimensional NumPy array of theoretical coupling values.
    """
    diameter_array = np.asarray(
        diameter_nm,
        dtype=float,
    )

    if diameter_array.ndim != 1:
        diameter_array = diameter_array.ravel()

    theoretical_coupling = np.asarray(
        coupling_function(
            diameter_array,
        ),
        dtype=float,
    )

    return build_mie_relation_from_arrays(
        diameter_nm=diameter_array,
        theoretical_coupling=theoretical_coupling,
        mie_model=mie_model,
        parameters=parameters,
        relation_role=relation_role,
        inversion_method=inversion_method,
    )


def build_empty_mie_relation(
    *,
    mie_model: str = "",
    parameters: Optional[dict[str, Any]] = None,
    relation_role: str = "",
) -> MieRelation:
    """
    Build an empty Mie relation placeholder.
    """
    return MieRelation(
        diameter_nm=[],
        theoretical_coupling=[],
        mie_model=mie_model,
        parameters=dict(
            parameters or {},
        ),
        is_monotonic=False,
        relation_role=relation_role,
        valid_min_diameter_nm=None,
        valid_max_diameter_nm=None,
        valid_min_coupling=None,
        valid_max_coupling=None,
        inversion_method="linear_interpolation",
    )


def build_mie_parameter_payload(
    *,
    mie_model: Any,
    medium_refractive_index: Any,
    particle_refractive_index: Any = None,
    core_refractive_index: Any = None,
    shell_refractive_index: Any = None,
    wavelength_nm: Any = None,
    detector_numerical_aperture: Any = None,
    detector_cache_numerical_aperture: Any = None,
    blocker_bar_numerical_aperture: Any = None,
    detector_sampling: Any = None,
    detector_phi_angle_degree: Any = None,
    detector_gamma_angle_degree: Any = None,
    diameter_min_nm: Any = None,
    diameter_max_nm: Any = None,
    diameter_count: Any = None,
) -> dict[str, Any]:
    """
    Build a serializable Mie parameter payload.

    This helper intentionally performs no physical validation. It only captures
    the model configuration used to build a relation.
    """
    return {
        "mie_model": mie_model,
        "medium_refractive_index": medium_refractive_index,
        "particle_refractive_index": particle_refractive_index,
        "core_refractive_index": core_refractive_index,
        "shell_refractive_index": shell_refractive_index,
        "wavelength_nm": wavelength_nm,
        "detector_numerical_aperture": detector_numerical_aperture,
        "detector_cache_numerical_aperture": detector_cache_numerical_aperture,
        "blocker_bar_numerical_aperture": blocker_bar_numerical_aperture,
        "detector_sampling": detector_sampling,
        "detector_phi_angle_degree": detector_phi_angle_degree,
        "detector_gamma_angle_degree": detector_gamma_angle_degree,
        "diameter_min_nm": diameter_min_nm,
        "diameter_max_nm": diameter_max_nm,
        "diameter_count": diameter_count,
    }