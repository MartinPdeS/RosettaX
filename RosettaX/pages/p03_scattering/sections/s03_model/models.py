"""Named state exchanged by optical configuration services and Dash callbacks."""

from dataclasses import asdict, astuple, dataclass
from typing import Any

from RosettaX.workflow.scattering.model import ScatteringModelDefaults


@dataclass(frozen=True)
class DetectorGeometryValues:
    detector_numerical_aperture: Any
    detector_cache_numerical_aperture: Any
    blocker_bar_numerical_aperture: Any
    detector_sampling: Any
    detector_phi_angle_degree: Any
    detector_gamma_angle_degree: Any

    def to_callback_values(self) -> tuple[Any, ...]:
        return astuple(self)


@dataclass(frozen=True)
class ProfileParameterState:
    detector_preset: str
    scatterer_preset: str
    values: ScatteringModelDefaults

    def to_callback_values(self) -> tuple[Any, ...]:
        """Translate named profile state into the registered Dash output order."""
        return (
            self.detector_preset,
            self.scatterer_preset,
            *self.values.to_callback_values(),
        )


@dataclass(frozen=True)
class OpticalPreviewControls:
    detector_numerical_aperture: Any
    detector_cache_numerical_aperture: Any
    blocker_bar_numerical_aperture: Any
    medium_refractive_index: Any
    detector_phi_angle_degree: Any
    detector_gamma_angle_degree: Any
    detector_sampling: Any
    detector_configuration_preset: Any
    detector_angular_weighting_json: Any

    def to_workflow_parameters(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OpticalPreviewUpdate:
    figure: Any
    signature: str

    def to_callback_values(self) -> tuple[Any, str]:
        return self.figure, self.signature
