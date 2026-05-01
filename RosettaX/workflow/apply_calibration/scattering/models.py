# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any, Optional, Union

import numpy as np

from RosettaX.workflow.calibration.mie_relation import MieRelation


SOLID_SPHERE_MODEL_NAME = "Solid Sphere"
CORE_SHELL_SPHERE_MODEL_NAME = "Core/Shell Sphere"


@dataclass(frozen=True)
class SolidSphereTargetModel:
    """
    Target model used when applying a scattering calibration to solid spheres.

    The diameter axis represents the full particle diameter.
    """

    medium_refractive_index: float
    particle_refractive_index: float
    particle_diameter_min_nm: float
    particle_diameter_max_nm: float
    particle_diameter_count: int
    mie_model: str = SOLID_SPHERE_MODEL_NAME

    @property
    def diameter_min_nm(self) -> float:
        """
        Return the generic diameter minimum expected by downstream Mie relation code.
        """
        return self.particle_diameter_min_nm

    @property
    def diameter_max_nm(self) -> float:
        """
        Return the generic diameter maximum expected by downstream Mie relation code.
        """
        return self.particle_diameter_max_nm

    @property
    def diameter_count(self) -> int:
        """
        Return the generic diameter point count expected by downstream Mie relation code.
        """
        return self.particle_diameter_count

    @property
    def diameter_axis(self) -> str:
        """
        Return the semantic diameter axis represented by this model.
        """
        return "particle_diameter_nm"

    def to_parameter_payload(self) -> dict[str, Any]:
        """
        Convert the target model into a serializable parameter payload.
        """
        return {
            "mie_model": self.mie_model,
            "diameter_axis": self.diameter_axis,
            "medium_refractive_index": float(self.medium_refractive_index),
            "particle_refractive_index": float(self.particle_refractive_index),
            "particle_diameter_min_nm": float(self.particle_diameter_min_nm),
            "particle_diameter_max_nm": float(self.particle_diameter_max_nm),
            "particle_diameter_count": int(self.particle_diameter_count),
            "diameter_min_nm": float(self.diameter_min_nm),
            "diameter_max_nm": float(self.diameter_max_nm),
            "diameter_count": int(self.diameter_count),
        }


@dataclass(frozen=True)
class CoreShellSphereTargetModel:
    """
    Target model used when applying a scattering calibration to core shell spheres.

    The diameter axis represents the core diameter. The shell thickness is a
    constant user supplied value.

    The outer diameter is therefore:

        outer_diameter_nm = core_diameter_nm + 2 * shell_thickness_nm
    """

    medium_refractive_index: float
    core_refractive_index: float
    shell_refractive_index: float
    shell_thickness_nm: float
    core_diameter_min_nm: float
    core_diameter_max_nm: float
    core_diameter_count: int
    mie_model: str = CORE_SHELL_SPHERE_MODEL_NAME

    @property
    def diameter_min_nm(self) -> float:
        """
        Return the generic diameter minimum expected by downstream Mie relation code.
        """
        return self.core_diameter_min_nm

    @property
    def diameter_max_nm(self) -> float:
        """
        Return the generic diameter maximum expected by downstream Mie relation code.
        """
        return self.core_diameter_max_nm

    @property
    def diameter_count(self) -> int:
        """
        Return the generic diameter point count expected by downstream Mie relation code.
        """
        return self.core_diameter_count

    @property
    def outer_diameter_min_nm(self) -> float:
        """
        Return the outer diameter corresponding to the minimum core diameter.
        """
        return self.core_diameter_min_nm + 2.0 * self.shell_thickness_nm

    @property
    def outer_diameter_max_nm(self) -> float:
        """
        Return the outer diameter corresponding to the maximum core diameter.
        """
        return self.core_diameter_max_nm + 2.0 * self.shell_thickness_nm

    @property
    def diameter_axis(self) -> str:
        """
        Return the semantic diameter axis represented by this model.
        """
        return "core_diameter_nm"

    def to_parameter_payload(self) -> dict[str, Any]:
        """
        Convert the target model into a serializable parameter payload.
        """
        return {
            "mie_model": self.mie_model,
            "diameter_axis": self.diameter_axis,
            "medium_refractive_index": float(self.medium_refractive_index),
            "core_refractive_index": float(self.core_refractive_index),
            "shell_refractive_index": float(self.shell_refractive_index),
            "shell_thickness_nm": float(self.shell_thickness_nm),
            "core_diameter_min_nm": float(self.core_diameter_min_nm),
            "core_diameter_max_nm": float(self.core_diameter_max_nm),
            "core_diameter_count": int(self.core_diameter_count),
            "outer_diameter_min_nm": float(self.outer_diameter_min_nm),
            "outer_diameter_max_nm": float(self.outer_diameter_max_nm),
            "diameter_min_nm": float(self.diameter_min_nm),
            "diameter_max_nm": float(self.diameter_max_nm),
            "diameter_count": int(self.diameter_count),
        }


ScatteringTargetModel = Union[
    SolidSphereTargetModel,
    CoreShellSphereTargetModel,
]


@dataclass(frozen=True)
class ScatteringTargetModelParameters:
    """
    Backward compatible adapter for target particle model parameters.

    New code should prefer ``SolidSphereTargetModel`` and
    ``CoreShellSphereTargetModel`` directly. This class is kept so existing page
    callbacks can migrate gradually.
    """

    target_model: ScatteringTargetModel

    @property
    def mie_model(self) -> str:
        """
        Return the selected Mie model name.
        """
        return self.target_model.mie_model

    @property
    def medium_refractive_index(self) -> float:
        """
        Return the medium refractive index.
        """
        return self.target_model.medium_refractive_index

    @property
    def diameter_min_nm(self) -> float:
        """
        Return the active diameter axis minimum.
        """
        return self.target_model.diameter_min_nm

    @property
    def diameter_max_nm(self) -> float:
        """
        Return the active diameter axis maximum.
        """
        return self.target_model.diameter_max_nm

    @property
    def diameter_count(self) -> int:
        """
        Return the active diameter axis point count.
        """
        return self.target_model.diameter_count

    @property
    def diameter_axis(self) -> str:
        """
        Return the semantic diameter axis.
        """
        return self.target_model.diameter_axis

    @property
    def particle_refractive_index(self) -> Optional[float]:
        """
        Return the solid sphere particle refractive index, if available.
        """
        if isinstance(
            self.target_model,
            SolidSphereTargetModel,
        ):
            return self.target_model.particle_refractive_index

        return None

    @property
    def core_refractive_index(self) -> Optional[float]:
        """
        Return the core refractive index, if available.
        """
        if isinstance(
            self.target_model,
            CoreShellSphereTargetModel,
        ):
            return self.target_model.core_refractive_index

        return None

    @property
    def shell_refractive_index(self) -> Optional[float]:
        """
        Return the shell refractive index, if available.
        """
        if isinstance(
            self.target_model,
            CoreShellSphereTargetModel,
        ):
            return self.target_model.shell_refractive_index

        return None

    @property
    def shell_thickness_nm(self) -> Optional[float]:
        """
        Return the constant shell thickness, if available.
        """
        if isinstance(
            self.target_model,
            CoreShellSphereTargetModel,
        ):
            return self.target_model.shell_thickness_nm

        return None

    def to_parameter_payload(self) -> dict[str, Any]:
        """
        Convert the wrapped target model into a serializable parameter payload.
        """
        return self.target_model.to_parameter_payload()

    @classmethod
    def from_raw_values(
        cls,
        *,
        target_mie_model: Any,
        target_medium_refractive_index: Any,
        target_particle_refractive_index: Any = None,
        target_core_refractive_index: Any = None,
        target_shell_refractive_index: Any = None,
        target_shell_thickness_nm: Any = None,
        target_diameter_min_nm: Any,
        target_diameter_max_nm: Any,
        target_diameter_count: Any,
    ) -> "ScatteringTargetModelParameters":
        """
        Parse target model values from Dash controls.
        """
        resolved_mie_model = resolve_target_mie_model(
            target_mie_model,
        )

        resolved_medium_refractive_index = parse_positive_float(
            value=target_medium_refractive_index,
            name="target_medium_refractive_index",
        )

        resolved_diameter_min_nm = parse_positive_float(
            value=target_diameter_min_nm,
            name="target_diameter_min_nm",
        )

        resolved_diameter_max_nm = parse_positive_float(
            value=target_diameter_max_nm,
            name="target_diameter_max_nm",
        )

        resolved_diameter_count = parse_positive_int(
            value=target_diameter_count,
            name="target_diameter_count",
        )

        validate_diameter_grid_parameters(
            diameter_min_nm=resolved_diameter_min_nm,
            diameter_max_nm=resolved_diameter_max_nm,
            diameter_count=resolved_diameter_count,
        )

        if resolved_mie_model == SOLID_SPHERE_MODEL_NAME:
            target_model = SolidSphereTargetModel(
                medium_refractive_index=resolved_medium_refractive_index,
                particle_refractive_index=parse_positive_float(
                    value=target_particle_refractive_index,
                    name="target_particle_refractive_index",
                ),
                particle_diameter_min_nm=resolved_diameter_min_nm,
                particle_diameter_max_nm=resolved_diameter_max_nm,
                particle_diameter_count=resolved_diameter_count,
            )

            return cls(
                target_model=target_model,
            )

        target_model = CoreShellSphereTargetModel(
            medium_refractive_index=resolved_medium_refractive_index,
            core_refractive_index=parse_positive_float(
                value=target_core_refractive_index,
                name="target_core_refractive_index",
            ),
            shell_refractive_index=parse_positive_float(
                value=target_shell_refractive_index,
                name="target_shell_refractive_index",
            ),
            shell_thickness_nm=parse_non_negative_float(
                value=target_shell_thickness_nm,
                name="target_shell_thickness_nm",
            ),
            core_diameter_min_nm=resolved_diameter_min_nm,
            core_diameter_max_nm=resolved_diameter_max_nm,
            core_diameter_count=resolved_diameter_count,
        )

        return cls(
            target_model=target_model,
        )


@dataclass(frozen=True)
class ScatteringOutputColumns:
    """
    Output column names produced by scattering calibration application.
    """

    estimated_coupling: str
    mie_equivalent_diameter_nm: str

    def as_list(self) -> list[str]:
        """
        Return output column names.
        """
        return [
            self.estimated_coupling,
            self.mie_equivalent_diameter_nm,
        ]


@dataclass(frozen=True)
class MonotonicDiameterInterval:
    """
    Strictly monotonic diameter interval in a Mie relation.

    The interval is a branch over which coupling to diameter inversion is
    unambiguous.
    """

    diameter_min_nm: float
    diameter_max_nm: float
    coupling_min: float
    coupling_max: float
    point_count: int
    trend: str
    start_index: int
    end_index: int

    @property
    def diameter_width_nm(self) -> float:
        """
        Diameter width of the branch.
        """
        return self.diameter_max_nm - self.diameter_min_nm

    def to_message_fragment(self) -> str:
        """
        Format the interval for user facing messages.
        """
        return (
            f"{self.diameter_min_nm:.6g} to {self.diameter_max_nm:.6g} nm "
            f"({self.trend}, {self.point_count} points)"
        )


@dataclass(frozen=True)
class MonotonicRelationResolution:
    """
    Resolved monotonic target relation used for inversion.
    """

    target_mie_relation: MieRelation
    selected_interval: Optional[MonotonicDiameterInterval]
    used_auto_largest_branch: bool
    warnings: list[str]


@dataclass(frozen=True)
class ScatteringApplyResult:
    """
    Result of applying a scattering calibration to a dataframe.
    """

    dataframe: Any
    output_columns: list[str]
    warnings: list[str]
    target_mie_relation: MieRelation


def resolve_target_mie_model(
    mie_model: Any,
) -> str:
    """
    Normalize target Mie model names.
    """
    mie_model_string = str(
        mie_model or SOLID_SPHERE_MODEL_NAME,
    ).strip()

    normalized_mie_model = mie_model_string.lower()

    if normalized_mie_model in {
        "core/shell sphere",
        "core shell sphere",
        "core-shell sphere",
        "coreshell sphere",
        "core_shell_sphere",
    }:
        return CORE_SHELL_SPHERE_MODEL_NAME

    return SOLID_SPHERE_MODEL_NAME


def parse_positive_float(
    *,
    value: Any,
    name: str,
) -> float:
    """
    Parse a strictly positive finite float.
    """
    parsed_value = parse_finite_float(
        value=value,
        name=name,
    )

    if parsed_value <= 0.0:
        raise ValueError(f"{name} must be positive.")

    return parsed_value


def parse_non_negative_float(
    *,
    value: Any,
    name: str,
) -> float:
    """
    Parse a non negative finite float.
    """
    parsed_value = parse_finite_float(
        value=value,
        name=name,
    )

    if parsed_value < 0.0:
        raise ValueError(f"{name} must be non negative.")

    return parsed_value


def parse_finite_float(
    *,
    value: Any,
    name: str,
) -> float:
    """
    Parse a finite float.
    """
    try:
        parsed_value = float(
            value,
        )
    except Exception as exception:
        raise ValueError(
            f"{name} must be convertible to float. Got {value!r}."
        ) from exception

    if not np.isfinite(
        parsed_value,
    ):
        raise ValueError(f"{name} must be finite.")

    return parsed_value


def parse_positive_int(
    *,
    value: Any,
    name: str,
) -> int:
    """
    Parse a strictly positive integer.
    """
    try:
        parsed_value = int(
            value,
        )
    except Exception as exception:
        raise ValueError(
            f"{name} must be convertible to int. Got {value!r}."
        ) from exception

    if parsed_value <= 0:
        raise ValueError(f"{name} must be positive.")

    return parsed_value


def validate_diameter_grid_parameters(
    *,
    diameter_min_nm: float,
    diameter_max_nm: float,
    diameter_count: int,
) -> None:
    """
    Validate a diameter grid.
    """
    if diameter_min_nm <= 0.0:
        raise ValueError("diameter_min_nm must be positive.")

    if diameter_max_nm <= diameter_min_nm:
        raise ValueError("diameter_max_nm must be greater than diameter_min_nm.")

    if diameter_count < 2:
        raise ValueError("diameter_count must be at least 2.")