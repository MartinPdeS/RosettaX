"""Control synchronization updates changed values without redundant cascades."""

# Run pytest before application imports so the suite loads its own dependency setup.
if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))


from types import SimpleNamespace

import dash
import pytest

from RosettaX.pages.p03_scattering.ids import Ids
from RosettaX.pages.p03_scattering.sections.s03_model import (
    callbacks,
    detector_callbacks,
)
from RosettaX.pages.p03_scattering.sections.s03_model.main import Model
from RosettaX.workflow.parameters.refractive_index import (
    calculate_sellmeier_refractive_index,
)


@pytest.fixture
def registered_callbacks(monkeypatch):
    """Capture registered callbacks and their specifications for testing."""
    registered = {}

    def register(*_args, **_kwargs):
        """Capture the callback registration requested by the test."""
        def decorate(callback):
            """Record the decorated callback and return it unchanged."""
            registered[callback.__name__] = callback
            return callback

        return decorate

    monkeypatch.setattr(dash, "callback", register)
    section = Model(page=SimpleNamespace(ids=Ids()), section_number=3)
    callbacks.register_refractive_index_callbacks(section)
    detector_callbacks.register_detector_configuration_callbacks(section)
    return registered


def test_material_sync_preserves_manual_values_and_skips_equal_presets(
    registered_callbacks,
):
    """Check material sync preserves manual values and skips equal presets."""
    update = registered_callbacks["apply_refractive_index_presets"]
    assert update(None, 1.59, None, None, 488, 1.333, 1.59, 1.5, 1.4) == (
        dash.no_update,
        dash.no_update,
        dash.no_update,
        dash.no_update,
    )
    assert update(None, 1.6, None, None, 488, 1.333, 1.59, 1.5, 1.4) == (
        dash.no_update,
        1.6,
        dash.no_update,
        dash.no_update,
    )


def test_material_sync_recomputes_dispersion_when_wavelength_changes(
    registered_callbacks,
):
    """Check material sync recomputes dispersion when wavelength changes."""
    update = registered_callbacks["apply_refractive_index_presets"]
    old_water = calculate_sellmeier_refractive_index("water", wavelength_nm=488)
    new_water = calculate_sellmeier_refractive_index("water", wavelength_nm=700)
    values = update("water", None, None, None, 700, old_water, 1.59, 1.5, 1.4)
    assert values == (new_water, dash.no_update, dash.no_update, dash.no_update)


def test_detector_sync_skips_equal_controls_but_applies_cache_clamp(
    registered_callbacks,
):
    """Check detector sync skips equal controls but applies cache clamp."""
    update = registered_callbacks["apply_detector_configuration_preset"]
    assert (
        update("Generic detector", 488, 0.4, 0.1, 0.05, 250, 20, 30)
        == (dash.no_update,) * 7
    )
    values = update("Generic detector", 488, 0.4, 0.8, 0.05, 250, 20, 30)
    assert values[2] == pytest.approx(0.399999)
    assert values[:2] == (dash.no_update,) * 2
    assert values[3:] == (dash.no_update,) * 4
