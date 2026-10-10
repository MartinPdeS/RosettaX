"""Optical preview rendering, initialization, and duplicate update behavior."""

from types import SimpleNamespace

import dash
import numpy as np
import pytest

from RosettaX.pages.p03_scattering.ids import Ids as ScatteringIds
from RosettaX.pages.p03_scattering.sections.s03_model import preview_callbacks
from RosettaX.pages.p03_scattering.sections.s03_model.main import (
    Model as ScatteringModel,
)
from RosettaX.workflow.detector.mesh import build_pymiesim_photodiode_mesh_coordinates
from RosettaX.workflow.plotting import optical_preview
from RosettaX.workflow.plotting.optical_preview import (
    _rotate_preview_display_coordinate_array,
    build_optical_configuration_preview_signature,
)
from RosettaX.workflow.scattering import ModelConfiguration


def _find_component_by_id(component, target_id: str):
    component_id = getattr(component, "id", None)

    if component_id == target_id:
        return component

    children = getattr(component, "children", None)

    if children is None:
        return None

    if isinstance(children, (list, tuple)):
        for child in children:
            found_component = _find_component_by_id(child, target_id)

            if found_component is not None:
                return found_component

        return None

    return _find_component_by_id(children, target_id)


class Test_ScatteringOpticalPreviewInitialization:
    @pytest.mark.parametrize("detector_preset", ["", "Generic detector"])
    def test_preview_is_built_only_by_callback_from_active_controls(
        self,
        monkeypatch,
        detector_preset,
    ) -> None:
        section = ScatteringModel(
            page=SimpleNamespace(ids=ScatteringIds()),
            section_number=3,
        )
        preview_calls = []
        preview_figure = {"data": [], "layout": {"title": "Active optical preview"}}

        def build_preview(**parameters):
            preview_calls.append(parameters)
            return preview_figure

        monkeypatch.setattr(
            optical_preview,
            "build_optical_configuration_preview_figure",
            build_preview,
        )
        layout = section.get_layout()
        preview = _find_component_by_id(
            layout, section.ids.optical_configuration_preview
        )
        assert preview is not None
        assert preview.figure["data"] == []
        assert preview_calls == []
        signature_store = _find_component_by_id(
            layout,
            section.ids.optical_configuration_preview_signature_store,
        )
        assert signature_store.storage_type == "memory"

        callbacks = []
        callback_options = []

        def register_callback(*args, **kwargs):
            callback_options.append(kwargs)

            def decorate(callback):
                callbacks.append(callback)
                return callback

            return decorate

        monkeypatch.setattr(dash, "callback", register_callback)
        preview_callbacks.register_optical_configuration_preview_callback(section)
        assert callback_options[0]["prevent_initial_call"] is False

        camera_eye = {"x": 1.0, "y": 2.0, "z": 3.0}
        controls = {
            "detector_numerical_aperture": 0.45,
            "detector_cache_numerical_aperture": 0.0,
            "blocker_bar_numerical_aperture": 0.0,
            "medium_refractive_index": 1.34,
            "detector_phi_angle_degree": 15.0,
            "detector_gamma_angle_degree": 25.0,
            "detector_sampling": 600,
            "detector_configuration_preset": detector_preset,
            "detector_angular_weighting_json": None,
            "relayout_data": {"scene.camera": {"eye": camera_eye}},
            "previous_signature": None,
        }
        result, signature = callbacks[0](**controls)

        assert result is preview_figure
        assert len(preview_calls) == 1
        assert preview_calls[0] == {
            "detector_numerical_aperture": 0.45 if detector_preset else None,
            "blocker_bar_numerical_aperture": 0.0 if detector_preset else None,
            "medium_refractive_index": 1.34,
            "detector_phi_angle_degree": 15.0 if detector_preset else None,
            "detector_gamma_angle_degree": 25.0 if detector_preset else None,
            "polarization_angle_degree": 0.0,
            "detector_sampling": 600 if detector_preset else None,
            "detector_angular_weights": None,
            "include_geometry": bool(detector_preset),
            "camera": {
                "eye": camera_eye,
                "up": {"x": 0.0, "y": 0.0, "z": 1.0},
                "center": {"x": 0.0, "y": 0.0, "z": 0.0},
            },
        }

        controls["previous_signature"] = signature
        controls["relayout_data"] = {
            "scene.camera": {"eye": {"x": 4.0, "y": 5.0, "z": 6.0}}
        }
        assert callbacks[0](**controls) == (dash.no_update, dash.no_update)
        assert len(preview_calls) == 1

        controls["detector_numerical_aperture"] = 0.5
        if detector_preset:
            result, next_signature = callbacks[0](**controls)
            assert result is preview_figure
            assert next_signature != signature
            assert preview_calls[-1]["camera"]["eye"] == {"x": 4.0, "y": 5.0, "z": 6.0}
        else:
            assert callbacks[0](**controls) == (dash.no_update, dash.no_update)

        controls["previous_signature"] = None
        assert callbacks[0](**controls)[0] is preview_figure


class Test_OpticalPreviewRendering:
    def test_optical_preview_uses_resolved_preset_sampling_when_current_sampling_is_missing(
        self,
    ):
        figure = ModelConfiguration.build_optical_configuration_preview_figure(
            detector_numerical_aperture=None,
            detector_cache_numerical_aperture=None,
            blocker_bar_numerical_aperture=None,
            medium_refractive_index=1.333,
            detector_phi_angle_degree=None,
            detector_gamma_angle_degree=None,
            detector_sampling=None,
            detector_configuration_preset="Apogee - Side",
        )

        assert len(figure.data) >= 3

    def test_optical_preview_omits_geometry_when_detector_preset_is_empty(self):
        figure = ModelConfiguration.build_optical_configuration_preview_figure(
            detector_numerical_aperture=0.2,
            detector_cache_numerical_aperture=0.0,
            blocker_bar_numerical_aperture=0.0,
            medium_refractive_index=1.333,
            detector_phi_angle_degree=0.0,
            detector_gamma_angle_degree=0.0,
            detector_sampling=200,
            detector_configuration_preset="",
        )

        assert len(figure.data) == 8
        assert figure.layout.scene is not None
        assert figure.data[0].type == "surface"
        assert figure.data[1].type == "surface"
        assert not any(
            trace.type == "scatter3d" and getattr(trace, "mode", None) == "markers"
            for trace in figure.data
        )
        assert figure.layout.scene.xaxis.showgrid is False
        assert figure.layout.scene.xaxis.showline is False
        assert figure.layout.scene.xaxis.showbackground is False
        assert figure.layout.scene.xaxis.showspikes is False
        assert figure.layout.scene.xaxis.ticks == ""

    def test_optical_preview_incident_wave_aligns_with_default_detector_axis(self):
        figure = ModelConfiguration.build_optical_configuration_preview_figure(
            detector_numerical_aperture=0.45,
            detector_cache_numerical_aperture=0.0,
            blocker_bar_numerical_aperture=0.0,
            medium_refractive_index=1.333,
            detector_phi_angle_degree=0.0,
            detector_gamma_angle_degree=0.0,
            detector_sampling=256,
            detector_configuration_preset="Generic detector",
        )

        incident_wave_trace = next(
            trace
            for trace in figure.data
            if trace.type == "scatter3d"
            and getattr(trace, "mode", None) == "lines"
            and getattr(getattr(trace, "line", None), "color", None) == "#d62728"
        )
        incident_wave_vector = np.asarray(
            [
                float(incident_wave_trace.x[1] - incident_wave_trace.x[0]),
                float(incident_wave_trace.y[1] - incident_wave_trace.y[0]),
                float(incident_wave_trace.z[1] - incident_wave_trace.z[0]),
            ],
            dtype=float,
        )
        incident_wave_vector = incident_wave_vector / np.linalg.norm(
            incident_wave_vector
        )

        coordinate_array = build_pymiesim_photodiode_mesh_coordinates(
            detector_numerical_aperture=0.45,
            medium_refractive_index=1.333,
            detector_phi_angle_degree=0.0,
            detector_gamma_angle_degree=0.0,
            detector_sampling=256,
        )
        detector_axis = coordinate_array.mean(axis=0)
        detector_axis = _rotate_preview_display_coordinate_array(
            detector_axis.reshape(1, 3)
        ).reshape(3)
        detector_axis = detector_axis / np.linalg.norm(detector_axis)

        assert np.allclose(incident_wave_vector, detector_axis, atol=5e-3)


class Test_OpticalPreviewSignature:
    @pytest.fixture
    def preview_parameters(self):
        return ModelConfiguration.resolve_optical_configuration_preview_parameters(
            detector_numerical_aperture=0.45,
            detector_cache_numerical_aperture=0.0,
            blocker_bar_numerical_aperture=0.0,
            medium_refractive_index=1.333,
            detector_phi_angle_degree=0.0,
            detector_gamma_angle_degree=0.0,
            detector_sampling=4,
            detector_configuration_preset="Generic detector",
            detector_angular_weighting_json='{"mode":"explicit","weights":[1,0,0.5,0]}',
        )

    def test_numeric_text_and_weight_amplitudes_keep_same_visible_geometry(
        self, preview_parameters
    ):
        original = build_optical_configuration_preview_signature(preview_parameters)
        changed = {
            **preview_parameters,
            "detector_numerical_aperture": "0.45",
            "detector_sampling": "4",
            "detector_angular_weights": np.array([2.0j, 0.0, -3.0, 0.0]),
            "camera": {"eye": {"x": 1.0, "y": 2.0, "z": 3.0}},
        }
        assert build_optical_configuration_preview_signature(changed) == original

    @pytest.mark.parametrize(
        "field,value",
        [
            ("detector_numerical_aperture", 0.5),
            ("blocker_bar_numerical_aperture", 0.1),
            ("medium_refractive_index", 1.4),
            ("detector_phi_angle_degree", 15.0),
            ("detector_gamma_angle_degree", 25.0),
            ("polarization_angle_degree", 45.0),
            ("detector_sampling", 8),
            ("detector_angular_weights", np.array([1.0, 0.0, 0.0, 0.0])),
            ("include_geometry", False),
        ],
    )
    def test_changed_geometry_invalidates_signature(
        self, preview_parameters, field, value
    ):
        original = build_optical_configuration_preview_signature(preview_parameters)
        changed = {**preview_parameters, field: value}
        assert build_optical_configuration_preview_signature(changed) != original

    def test_empty_preset_ignores_controls_that_are_not_rendered(
        self, preview_parameters
    ):
        empty = {**preview_parameters, "include_geometry": False}
        changed = {
            **empty,
            "medium_refractive_index": 1.5,
            "detector_numerical_aperture": 0.9,
            "detector_sampling": 1000,
            "detector_angular_weights": None,
        }
        assert build_optical_configuration_preview_signature(
            changed
        ) == build_optical_configuration_preview_signature(empty)

    def test_named_preset_overrides_transient_control_values(self):
        controls = {
            "detector_numerical_aperture": None,
            "detector_cache_numerical_aperture": None,
            "blocker_bar_numerical_aperture": None,
            "medium_refractive_index": 1.333,
            "detector_phi_angle_degree": None,
            "detector_gamma_angle_degree": None,
            "detector_sampling": None,
            "detector_configuration_preset": "Apogee - Side",
        }
        before = ModelConfiguration.resolve_optical_configuration_preview_parameters(
            **controls
        )
        after = ModelConfiguration.resolve_optical_configuration_preview_parameters(
            **{
                **controls,
                "detector_numerical_aperture": 0.8,
                "blocker_bar_numerical_aperture": 0.2,
                "detector_sampling": 999,
            }
        )
        assert build_optical_configuration_preview_signature(
            before
        ) == build_optical_configuration_preview_signature(after)
