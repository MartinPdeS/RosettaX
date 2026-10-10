"""Preset synchronization updates selections without repeating unchanged outputs."""

# Run pytest before application imports so the suite loads its own dependency setup.
if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))


from types import SimpleNamespace

import dash
import pytest

from RosettaX.pages.p03_scattering.ids import Ids
from RosettaX.pages.p03_scattering.sections.s03_model import detector_callbacks
from RosettaX.pages.p03_scattering.sections.s03_model.main import Model


@pytest.fixture
def registered_callbacks(monkeypatch):
    """Capture registered callbacks and their specifications for testing."""
    callbacks = {}
    specifications = {}

    def register(*args, **kwargs):
        """Capture the callback registration requested by the test."""
        def decorate(function):
            """Record the decorated callback and return it unchanged."""
            callbacks[function.__name__] = function
            specifications[function.__name__] = args
            return function

        return decorate

    monkeypatch.setattr(dash, "callback", register)
    section = Model(page=SimpleNamespace(ids=Ids()), section_number=3)
    detector_callbacks.register_detector_configuration_callbacks(section)
    return callbacks, specifications, section


def test_preset_changes_with_same_brand_still_update_model_and_type(
    registered_callbacks,
):
    """Check preset changes with same brand still update model and type."""
    callbacks, specifications, section = registered_callbacks
    configuration = section.model_configuration
    configuration.resolve_detector_preset_brand = lambda _: "Brand"
    configuration.resolve_detector_preset_model = lambda _: "New model"
    configuration.build_detector_preset_model_options = lambda _: [
        {"label": "New model", "value": "New model"},
        {"label": "Old model", "value": "Old model"},
    ]
    configuration.build_detector_preset_type_options = lambda **_: [
        {"label": "New preset", "value": "New preset"},
        {"label": "Old preset", "value": "Old preset"},
    ]
    assert (
        callbacks["sync_detector_configuration_brand_from_preset"](
            "New preset", "Brand"
        )
        is dash.no_update
    )
    model = callbacks["sync_detector_configuration_models_for_brand"](
        "Brand", "New preset", "Old model", [], False
    )
    assert model[1] == "New model"
    types = callbacks["sync_detector_configuration_types_for_model"](
        "New model", "Brand", "New preset", "Old preset", [], False
    )
    assert types[1] == "New preset"
    assert (
        callbacks["sync_detector_configuration_preset_from_model"](
            "New preset", "New preset"
        )
        is dash.no_update
    )
    for name in (
        "sync_detector_configuration_models_for_brand",
        "sync_detector_configuration_types_for_model",
    ):
        assert any(
            isinstance(specification, dash.Input)
            and specification.component_id == section.ids.detector_configuration_preset
            for specification in specifications[name]
        )


def test_settled_and_empty_selectors_skip_unchanged_values(registered_callbacks):
    """Check settled and empty selectors skip unchanged values."""
    callbacks, _, section = registered_callbacks
    configuration = section.model_configuration
    options = [{"label": "Only model", "value": "Only model"}]
    configuration.resolve_detector_preset_model = lambda _: "Only model"
    configuration.build_detector_preset_model_options = lambda _: options
    model_callback = callbacks["sync_detector_configuration_models_for_brand"]
    assert model_callback("Brand", "Preset", "Only model", options, False) == (
        dash.no_update,
        dash.no_update,
        dash.no_update,
    )
    configuration.build_detector_preset_model_options = lambda _: []
    assert model_callback("Brand", "Preset", None, [], True) == (
        dash.no_update,
        dash.no_update,
        dash.no_update,
    )
    configuration.build_detector_preset_type_options = lambda **_: []
    assert callbacks["sync_detector_configuration_types_for_model"](
        None, "Brand", "Preset", None, [], True
    ) == (dash.no_update, dash.no_update, dash.no_update)
    assert (
        callbacks["sync_detector_configuration_preset_from_model"](None, "Old preset")
        == ""
    )
