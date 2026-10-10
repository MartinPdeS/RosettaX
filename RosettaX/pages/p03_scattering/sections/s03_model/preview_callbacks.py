from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

import dash
import numpy as np

from RosettaX.workflow import detector

if TYPE_CHECKING:
    from .main import Model

from . import services
from .models import OpticalPreviewControls

logger = logging.getLogger(__name__)


def register_optical_configuration_preview_callback(section: Model) -> None:
    """
    Register optical configuration preview callback.
    """

    @dash.callback(
        dash.Output(
            section.ids.optical_configuration_preview,
            "figure",
        ),
        dash.Output(section.ids.optical_configuration_preview_signature_store, "data"),
        dash.Input(section.ids.detector_numerical_aperture, "value"),
        dash.Input(section.ids.detector_cache_numerical_aperture, "value"),
        dash.Input(section.ids.blocker_bar_numerical_aperture, "value"),
        dash.Input(section.ids.medium_refractive_index_custom, "value"),
        dash.Input(section.ids.detector_phi_angle_degree, "value"),
        dash.Input(section.ids.detector_gamma_angle_degree, "value"),
        dash.Input(section.ids.detector_sampling, "value"),
        dash.Input(section.ids.detector_configuration_preset, "value"),
        dash.Input(section.ids.detector_angular_weighting_json, "value"),
        dash.State(section.ids.optical_configuration_preview, "relayoutData"),
        dash.State(section.ids.optical_configuration_preview_signature_store, "data"),
        prevent_initial_call=False,
    )
    def update_optical_configuration_preview(
        detector_numerical_aperture: Any,
        detector_cache_numerical_aperture: Any,
        blocker_bar_numerical_aperture: Any,
        medium_refractive_index: Any,
        detector_phi_angle_degree: Any,
        detector_gamma_angle_degree: Any,
        detector_sampling: Any,
        detector_configuration_preset: Any,
        detector_angular_weighting_json: Any,
        relayout_data: Any,
        previous_signature: Any,
    ):
        logger.debug(
            "update_optical_configuration_preview called with "
            "detector_numerical_aperture=%r detector_cache_numerical_aperture=%r "
            "blocker_bar_numerical_aperture=%r "
            "medium_refractive_index=%r detector_phi_angle_degree=%r "
            "detector_gamma_angle_degree=%r detector_sampling=%r "
            "detector_configuration_preset=%r detector_angular_weighting_json=%r relayout_data=%r",
            detector_numerical_aperture,
            detector_cache_numerical_aperture,
            blocker_bar_numerical_aperture,
            medium_refractive_index,
            detector_phi_angle_degree,
            detector_gamma_angle_degree,
            detector_sampling,
            detector_configuration_preset,
            detector_angular_weighting_json,
            relayout_data,
        )

        controls = OpticalPreviewControls(
            detector_numerical_aperture=detector_numerical_aperture,
            detector_cache_numerical_aperture=detector_cache_numerical_aperture,
            blocker_bar_numerical_aperture=blocker_bar_numerical_aperture,
            medium_refractive_index=medium_refractive_index,
            detector_phi_angle_degree=detector_phi_angle_degree,
            detector_gamma_angle_degree=detector_gamma_angle_degree,
            detector_sampling=detector_sampling,
            detector_configuration_preset=detector_configuration_preset,
            detector_angular_weighting_json=detector_angular_weighting_json,
        )
        update = services.build_optical_preview_update(
            controls,
            previous_signature=previous_signature,
            relayout_data=relayout_data,
            configuration=section.model_configuration,
        )
        return (
            update.to_callback_values()
            if update is not None
            else (dash.no_update, dash.no_update)
        )

    @dash.callback(
        dash.Output(section.ids.detector_angular_weighting_alert, "children"),
        dash.Output(section.ids.detector_angular_weighting_alert, "is_open"),
        dash.Output(section.ids.detector_angular_weighting_alert, "color"),
        dash.Input(section.ids.detector_angular_weighting_json, "value"),
        dash.Input(section.ids.detector_configuration_preset, "value"),
        dash.Input(section.ids.detector_numerical_aperture, "value"),
        dash.Input(section.ids.detector_cache_numerical_aperture, "value"),
        dash.Input(section.ids.blocker_bar_numerical_aperture, "value"),
        dash.Input(section.ids.medium_refractive_index_custom, "value"),
        dash.Input(section.ids.detector_phi_angle_degree, "value"),
        dash.Input(section.ids.detector_gamma_angle_degree, "value"),
        dash.Input(section.ids.detector_sampling, "value"),
        prevent_initial_call=False,
    )
    def validate_detector_angular_weighting_json(
        detector_angular_weighting_json: Any,
        detector_configuration_preset: Any,
        detector_numerical_aperture: Any,
        detector_cache_numerical_aperture: Any,
        blocker_bar_numerical_aperture: Any,
        medium_refractive_index: Any,
        detector_phi_angle_degree: Any,
        detector_gamma_angle_degree: Any,
        detector_sampling: Any,
    ) -> tuple[str, bool, str]:
        if (
            str(detector_configuration_preset or "").strip()
            != section.model_configuration.custom_detector_preset_name
        ):
            return "", False, "warning"

        if detector_angular_weighting_json in (None, ""):
            return "", False, "warning"

        try:
            parsed_payload = json.loads(str(detector_angular_weighting_json))
        except json.JSONDecodeError as exc:
            return (
                f"Invalid detector angular weighting JSON: {exc.msg}.",
                True,
                "warning",
            )

        if not isinstance(parsed_payload, dict):
            return (
                "Detector angular weighting JSON must define an object.",
                True,
                "warning",
            )

        try:
            detector_angular_weights = detector.resolve_detector_angular_weights(
                preset_name=detector_configuration_preset,
                detector_sampling=detector_sampling,
                current_detector_numerical_aperture=detector_numerical_aperture,
                current_detector_cache_numerical_aperture=detector_cache_numerical_aperture,
                current_blocker_bar_numerical_aperture=blocker_bar_numerical_aperture,
                current_detector_phi_angle_degree=detector_phi_angle_degree,
                current_detector_gamma_angle_degree=detector_gamma_angle_degree,
                current_medium_refractive_index=medium_refractive_index,
                current_detector_angular_weighting=parsed_payload,
            )
        except Exception as exc:
            return f"Detector angular weighting is invalid: {exc}", True, "warning"

        if detector_angular_weights is None:
            return (
                "Custom detector angular weighting is loaded, but no detector geometry is available to display yet.",
                True,
                "info",
            )

        weight_array = np.asarray(
            detector_angular_weights,
            dtype=np.complex128,
        ).reshape(-1)
        kept_count = int(np.count_nonzero(weight_array != 0.0))
        total_count = int(weight_array.size)
        kept_fraction = 0.0 if total_count == 0 else kept_count / total_count

        return (
            f"Custom detector angular weighting is active: keeping {kept_count}/{total_count} angular samples ({kept_fraction:.1%}).",
            True,
            "info",
        )
