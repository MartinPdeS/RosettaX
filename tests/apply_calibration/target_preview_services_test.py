"""Target preview selection, inversion policy, and errors are service behavior."""

from dataclasses import replace

import pytest

from RosettaX.pages.p04_calibrate.sections.s02_calibration_picker import services
from RosettaX.pages.p04_calibrate.sections.s02_calibration_picker.models import (
    TargetMiePreviewControls,
)
from RosettaX.workflow.apply_calibration import scattering
from RosettaX.workflow.scattering.mie_relation import build_mie_relation_from_arrays


@pytest.fixture
def controls():
    return TargetMiePreviewControls(
        selected_calibration_summary={
            "requires_target_model": True,
            "file_name": "scattering.json",
            "calibration_payload": {"calibration_type": "scattering"},
        },
        target_mie_model="Solid Sphere",
        target_medium_refractive_index=1.333,
        target_particle_refractive_index=1.59,
        target_solid_sphere_diameter_min_nm=100,
        target_solid_sphere_diameter_max_nm=400,
        target_solid_sphere_diameter_count=50,
        target_core_refractive_index=1.5,
        target_shell_refractive_index=1.45,
        target_shell_thickness_nm=10,
        target_core_shell_core_diameter_min_nm=80,
        target_core_shell_core_diameter_max_nm=200,
        target_core_shell_core_diameter_count=40,
        target_model_preset="Custom",
        advanced_monotonic_mode_enabled=False,
        use_monotonic_smoothing_kernel=False,
        monotonic_smoothing_sigma_points=1,
        axis_scale_toggle_values=[],
    )


def test_preview_requires_calibration_and_target_selection(controls):
    result = services.build_target_mie_relation_preview(
        replace(controls, selected_calibration_summary=None)
    )
    assert result.color == "secondary"
    assert "Select a scattering calibration" in result.status
    result = services.build_target_mie_relation_preview(
        replace(controls, target_model_preset="")
    )
    assert result.color == "secondary"
    assert "Select a target model preset" in result.status


@pytest.mark.parametrize(
    "mie_model,minimum,maximum,count",
    [
        ("Solid Sphere", 100, 400, 50),
        ("Core/Shell Sphere", 80, 200, 40),
    ],
)
def test_preview_resolves_model_specific_ranges_and_full_monotonic_relation(
    controls,
    monkeypatch,
    mie_model,
    minimum,
    maximum,
    count,
):
    captured = []

    def build_relation(*, calibration_payload, target_model_parameters):
        captured.append(target_model_parameters)
        return build_mie_relation_from_arrays(
            diameter_nm=[100, 200, 300, 400],
            theoretical_coupling=[1, 2, 3, 4],
            mie_model=mie_model,
            relation_role="target",
        )

    monkeypatch.setattr(scattering, "build_target_mie_relation", build_relation)
    result = services.build_target_mie_relation_preview(
        replace(controls, target_mie_model=mie_model)
    )
    assert result.color == "success"
    assert "Full range" in result.status
    parameters = captured[0]
    # Core-shell controls specify core diameter; the model stores outer diameter.
    offset = 20 if mie_model == "Core/Shell Sphere" else 0
    assert parameters.diameter_min_nm == minimum + offset
    assert parameters.diameter_max_nm == maximum + offset
    assert parameters.diameter_count == count
    assert len(result.figure.data) > 0


def test_non_monotonic_preview_reports_selected_branch(controls, monkeypatch):
    monkeypatch.setattr(
        scattering,
        "build_target_mie_relation",
        lambda **kwargs: build_mie_relation_from_arrays(
            diameter_nm=[100, 200, 300, 400, 500],
            theoretical_coupling=[1, 2, 3, 2, 1],
            mie_model="Solid Sphere",
            relation_role="target",
        ),
    )
    result = services.build_target_mie_relation_preview(controls)
    assert result.color == "warning"
    assert "left-most monotonic branch" in result.status


def test_preview_errors_produce_diagnostic_result(controls, monkeypatch):
    def fail(**kwargs):
        raise ValueError("Invalid geometry")

    monkeypatch.setattr(scattering, "build_target_mie_relation", fail)
    result = services.build_target_mie_relation_preview(controls)
    assert result.color == "danger"
    assert result.status.endswith("ValueError: Invalid geometry")
