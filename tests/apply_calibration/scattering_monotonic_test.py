"""Regression tests for apply calibration scattering monotonic."""

# Run pytest before application imports so the suite loads its own dependency setup.
if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))


import sys
import types

import numpy as np


class _DashBootstrapComponentsSentinel:
    """Callable component sentinel for lightweight Dash Bootstrap test setup."""

    def __call__(self, *args, **kwargs):
        """Provide the callable behavior required by this test double."""
        return None

    def __getattr__(self, name):
        """Handle dynamic attribute lookup for this test double."""
        return self


class _DashBootstrapComponentsStub(types.ModuleType):
    """Minimal Dash Bootstrap components used by the unit tests."""

    def __getattr__(self, name):
        """Handle dynamic attribute lookup for this test double."""
        return _DashBootstrapComponentsSentinel()


class _PyMieSimStub(types.ModuleType):
    """Minimal PyMieSim module used by the unit tests."""

    experiment = types.SimpleNamespace()


class _PyMieSimUnitsStub(types.ModuleType):
    """Minimal PyMieSim units module used by the unit tests."""

    ureg = types.SimpleNamespace()


sys.modules.setdefault(
    "dash_bootstrap_components",
    _DashBootstrapComponentsStub("dash_bootstrap_components"),
)
sys.modules.setdefault(
    "PyMieSim",
    _PyMieSimStub("PyMieSim"),
)
sys.modules.setdefault(
    "PyMieSim.units",
    _PyMieSimUnitsStub("PyMieSim.units"),
)

from RosettaX.workflow.apply_calibration.scattering.models import (
    ScatteringTargetModelParameters,
)
from RosettaX.workflow.apply_calibration.scattering.monotonic import (
    resolve_monotonic_target_mie_relation,
)
from RosettaX.workflow.scattering.mie_relation import build_mie_relation_from_arrays


class Test_ApplyCalibrationScatteringMonotonic:
    """Regression checks for apply calibration scattering monotonic."""

    def test_target_model_parameters_default_smoothing_sigma_is_twenty_points(self) -> None:
        """Check target model parameters default smoothing sigma is twenty points."""
        target_model_parameters = ScatteringTargetModelParameters.from_raw_values(
            target_mie_model="Solid Sphere",
            target_medium_refractive_index=1.333,
            target_particle_refractive_index=1.39,
            target_diameter_min_nm=1.0,
            target_diameter_max_nm=6.0,
            target_diameter_count=6,
            monotonic_smoothing_sigma_points=None,
        )

        assert target_model_parameters.monotonic_smoothing_sigma_points == 20.0

    def test_resolve_monotonic_target_mie_relation_builds_increasing_envelope(self) -> None:
        """Check resolve monotonic target Mie relation builds increasing envelope."""
        target_mie_relation = build_mie_relation_from_arrays(
            diameter_nm=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
            theoretical_coupling=[1.0, 2.0, 3.0, 2.5, 3.5, 4.5],
            mie_model="Solid Sphere",
            relation_role="target_particle",
        )

        relation_resolution = resolve_monotonic_target_mie_relation(
            target_mie_relation=target_mie_relation,
        )

        assert relation_resolution.used_auto_largest_branch is True
        assert relation_resolution.selected_interval is not None
        assert relation_resolution.selected_interval.start_index == 0
        assert relation_resolution.selected_interval.end_index == 2
        assert np.allclose(
            relation_resolution.target_mie_relation.theoretical_coupling,
            [1.0, 2.0, 3.0, 3.0, 3.5, 4.5],
        )
        assert np.all(
            np.diff(relation_resolution.target_mie_relation.theoretical_coupling) >= 0.0
        )

    def test_resolve_monotonic_target_mie_relation_builds_decreasing_envelope(self) -> None:
        """Check resolve monotonic target Mie relation builds decreasing envelope."""
        target_mie_relation = build_mie_relation_from_arrays(
            diameter_nm=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
            theoretical_coupling=[6.0, 5.0, 4.0, 4.5, 3.5, 2.5],
            mie_model="Solid Sphere",
            relation_role="target_particle",
        )

        relation_resolution = resolve_monotonic_target_mie_relation(
            target_mie_relation=target_mie_relation,
        )

        assert relation_resolution.used_auto_largest_branch is True
        assert relation_resolution.selected_interval is not None
        assert relation_resolution.selected_interval.start_index == 0
        assert relation_resolution.selected_interval.end_index == 2
        assert np.allclose(
            relation_resolution.target_mie_relation.theoretical_coupling,
            [6.0, 5.0, 4.0, 4.0, 3.5, 2.5],
        )
        assert np.all(
            np.diff(relation_resolution.target_mie_relation.theoretical_coupling) <= 0.0
        )

    def test_resolve_monotonic_target_mie_relation_can_smooth_non_monotonic_transition(self) -> None:
        """Check resolve monotonic target Mie relation can smooth non monotonic transition."""
        target_mie_relation = build_mie_relation_from_arrays(
            diameter_nm=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
            theoretical_coupling=[1.0, 2.0, 3.0, 2.5, 3.5, 4.5],
            mie_model="Solid Sphere",
            relation_role="target_particle",
        )

        target_model_parameters = ScatteringTargetModelParameters.from_raw_values(
            target_mie_model="Solid Sphere",
            target_medium_refractive_index=1.333,
            target_particle_refractive_index=1.39,
            target_diameter_min_nm=1.0,
            target_diameter_max_nm=6.0,
            target_diameter_count=6,
            advanced_monotonic_mode_enabled=["enabled"],
            use_monotonic_smoothing_kernel=["enabled"],
            monotonic_smoothing_sigma_points=0.8,
        )

        relation_resolution = resolve_monotonic_target_mie_relation(
            target_mie_relation=target_mie_relation,
            target_model_parameters=target_model_parameters,
        )

        assert relation_resolution.used_auto_largest_branch is True
        assert relation_resolution.selected_interval is not None
        assert np.all(
            np.diff(relation_resolution.target_mie_relation.theoretical_coupling) >= 0.0
        )

        selected_interval = relation_resolution.selected_interval
        original_coupling = np.asarray(target_mie_relation.theoretical_coupling, dtype=float)
        resolved_coupling = np.asarray(
            relation_resolution.target_mie_relation.theoretical_coupling,
            dtype=float,
        )
        assert np.allclose(
            resolved_coupling[
                selected_interval.start_index : selected_interval.end_index + 1
            ],
            original_coupling[
                selected_interval.start_index : selected_interval.end_index + 1
            ],
        )

        assert not np.allclose(
            relation_resolution.target_mie_relation.theoretical_coupling,
            [1.0, 2.0, 3.0, 3.0, 3.5, 4.5],
        )
        assert "Gaussian smoothing kernel" in relation_resolution.warnings[0]
