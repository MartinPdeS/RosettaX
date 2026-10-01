"""Construct every page with real Dash and Bootstrap property validation."""

import json

import dash
import dash_bootstrap_components as dbc
import pytest
from dash.development.base_component import Component
from plotly.utils import PlotlyJSONEncoder

from RosettaX.application.pages import PAGE_MODULES


@pytest.mark.parametrize("module", PAGE_MODULES)
def test_registered_page_layout_uses_real_components(application, module):
    assert issubclass(dbc.Button, Component)
    page = dash.page_registry[module]
    with application.server.test_request_context(page["path"]):
        layout = page["layout"]
        component = layout() if callable(layout) else layout
        assert isinstance(component, Component)
        serialized = json.loads(json.dumps(component, cls=PlotlyJSONEncoder))
        assert "props" in serialized


@pytest.mark.parametrize("path", ["/", "/_dash-layout", "/_dash-dependencies"])
def test_real_dash_application_endpoints(application, path):
    response = application.server.test_client().get(path)
    assert response.status_code == 200
    if path != "/":
        assert response.is_json
