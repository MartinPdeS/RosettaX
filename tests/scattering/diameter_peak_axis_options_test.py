"""Shared axis controls for the scattering diameter plots."""

if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))

import dash
import plotly.graph_objs as go
import pytest
from RosettaX.pages.p03_scattering.ids import Ids
from RosettaX.pages.p03_scattering.sections.s05_calibration.main import Calibration
from types import SimpleNamespace


@pytest.mark.parametrize("options, expected_x, expected_y", [
    ([], "linear", "linear"),
    (["x_log"], "log", "linear"),
    (["y_log"], "linear", "log"),
    (["x_log", "y_log"], "log", "log"),
])
def test_diameter_graphs_share_axis_options(monkeypatch, options, expected_x, expected_y):
    """Apply the same scale settings while retaining each saved graph’s data."""
    callbacks = {}
    specifications = {}

    def capture(*args, **kwargs):
        """Record the graph callback and its Dash dependencies."""
        def decorate(function):
            callbacks[function.__name__] = function
            specifications[function.__name__] = args
            return function
        return decorate

    monkeypatch.setattr(dash, "callback", capture)
    section = Calibration(page=SimpleNamespace(ids=Ids()), section_number=5)
    section._register_right_graph_callback()
    section._register_diameter_peak_position_graph_callback()

    graph_payloads = {
        "update_right_graph": ("calibration_model_graph_payload", [0.1, 0.2]),
        "update_diameter_peak_position_graph": ("calibration_diameter_peak_graph_payload", [10, 100]),
    }
    for callback_name, (payload_key, y_values) in graph_payloads.items():
        dependencies = specifications[callback_name]
        assert any(item.component_id == section.ids.mie_relation_plot_options for item in dependencies)
        stored = go.Figure(data=[go.Scatter(x=[100, 200], y=y_values)]).to_dict()
        figure = callbacks[callback_name]({payload_key: stored}, options, {})
        assert figure.layout.xaxis.type == expected_x
        assert figure.layout.yaxis.type == expected_y
        assert list(figure.data[0].x) == [100, 200]
        assert list(figure.data[0].y) == y_values
