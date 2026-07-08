# -*- coding: utf-8 -*-

import sys
import types
from types import SimpleNamespace

import dash
import pytest


class _DashBootstrapComponentsSentinel:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.color = kwargs.get("color")

    def __call__(self, *args, **kwargs):
        return _DashBootstrapComponentsSentinel(*args, **kwargs)

    def __getattr__(self, name):
        return self


class _DashBootstrapComponentsStub(types.ModuleType):
    def __getattr__(self, name):
        return _DashBootstrapComponentsSentinel


sys.modules.setdefault(
    "dash_bootstrap_components",
    _DashBootstrapComponentsStub("dash_bootstrap_components"),
)

from RosettaX.workflow.peak.callbacks import mutation


class _StubPageState:
    def __init__(self, payload=None):
        self._payload = dict(payload or {})

    def to_dict(self):
        return dict(self._payload)


class _StubAdapter:
    def __init__(self):
        self.calls = []

    def get_backend(self, *, uploaded_fcs_path):
        return SimpleNamespace(uploaded_fcs_path=uploaded_fcs_path)

    def apply_peak_process_result_to_table(self, *, table_data, result, context, logger):
        self.calls.append(
            {
                "table_data": table_data,
                "result": result,
                "context": dict(context),
            }
        )

        if getattr(result, "clear_existing_table_peaks", False) and not hasattr(
            result,
            "new_peak_positions",
        ):
            return [{"measured_peak_position": ""}]

        return [{"measured_peak_position": 123.0}]

    def update_peak_lines_payload(self, *, page_state, peak_lines_payload):
        return page_state

    def get_page_state_payload(self, *, page_state):
        if hasattr(page_state, "to_dict"):
            return page_state.to_dict()

        return dict(page_state or {})

    def build_page_state(self, *, payload):
        return _StubPageState(payload)


class _StubProcess:
    supports_automatic_action = True
    process_name = "automatic_1d_peaks"


@pytest.mark.parametrize("starting_rows", [[{"measured_peak_position": 9.9}], None])
def test_handle_run_action_appends_using_cleared_rows(monkeypatch, starting_rows):
    adapter = _StubAdapter()

    result = SimpleNamespace(
        peak_lines_payload={"positions": [123.0]},
        status="ok",
        new_peak_positions=[123.0],
        clear_existing_table_peaks=False,
    )

    monkeypatch.setattr(
        mutation,
        "context_is_valid_for_process",
        lambda **kwargs: True,
    )

    monkeypatch.setattr(
        mutation,
        "call_run_automatic_action_with_supported_arguments",
        lambda **kwargs: result,
    )

    page_state = _StubPageState({})

    _page_state_dict, table_result, _status_children = mutation.handle_run_action(
        page=SimpleNamespace(),
        adapter=adapter,
        process=_StubProcess(),
        target_process_name="automatic_1d_peaks",
        page_state=page_state,
        uploaded_fcs_path="/tmp/example.fcs",
        detector_channels={"x": "FSC-A"},
        process_setting_ids=[],
        process_setting_values=[],
        max_events_for_plots=1000,
        table_data=starting_rows,
        mie_model="Solid Sphere",
        runtime_config_data={},
        status_component_ids=[],
    )

    assert table_result == [{"measured_peak_position": 123.0}]
    assert len(adapter.calls) == 2

    first_call = adapter.calls[0]
    second_call = adapter.calls[1]

    assert first_call["context"]["replace_existing_table_peaks"] is True
    assert second_call["context"]["replace_existing_table_peaks"] is True
    assert second_call["table_data"] == [{"measured_peak_position": ""}]


def test_handle_run_action_syncs_reference_table_rows_in_page_state(monkeypatch):
    adapter = _StubAdapter()

    result = SimpleNamespace(
        peak_lines_payload={"positions": [123.0]},
        status="ok",
        new_peak_positions=[123.0],
        clear_existing_table_peaks=False,
    )

    monkeypatch.setattr(
        mutation,
        "context_is_valid_for_process",
        lambda **kwargs: True,
    )

    monkeypatch.setattr(
        mutation,
        "call_run_automatic_action_with_supported_arguments",
        lambda **kwargs: result,
    )

    page_state = _StubPageState(
        {
            "reference_table_rows": [{"measured_peak_position": 9.9}],
        }
    )

    page_state_dict, table_result, _status_children = mutation.handle_run_action(
        page=SimpleNamespace(),
        adapter=adapter,
        process=_StubProcess(),
        target_process_name="automatic_1d_peaks",
        page_state=page_state,
        uploaded_fcs_path="/tmp/example.fcs",
        detector_channels={"x": "FSC-A"},
        process_setting_ids=[],
        process_setting_values=[],
        max_events_for_plots=1000,
        table_data=[{"measured_peak_position": 9.9}],
        mie_model="Solid Sphere",
        runtime_config_data={},
        status_component_ids=[],
    )

    assert table_result == [{"measured_peak_position": 123.0}]
    assert page_state_dict["reference_table_rows"] == table_result


def test_handle_manual_graph_click_ignores_empty_selection_reset(monkeypatch):
    manual_process = SimpleNamespace(
        supports_manual_click=True,
        process_name="manual_2d_click",
    )

    monkeypatch.setattr(
        mutation.registry,
        "resolve_process_name",
        lambda process_name: process_name,
    )
    monkeypatch.setattr(
        mutation.registry,
        "get_process_instance",
        lambda **kwargs: manual_process,
    )

    page_state_result, table_result, status_children = mutation.handle_manual_graph_click(
        ids=SimpleNamespace(),
        adapter=SimpleNamespace(),
        triggered_graph_property="selectedData",
        click_data=None,
        selected_data=None,
        process_name="manual_2d_click",
        page_state=SimpleNamespace(),
        detector_dropdown_ids=[],
        detector_dropdown_values=[],
        process_setting_ids=[],
        process_setting_values=[],
        data_filter_value=None,
        axis_scale_toggle_values=None,
        table_data=[],
        mie_model=None,
        runtime_config_data={},
        status_component_ids=[{"process": "manual_2d_click"}],
    )

    assert page_state_result is dash.no_update
    assert table_result is dash.no_update
    assert status_children == [dash.no_update]


def test_handle_manual_graph_click_ignores_empty_selection_reset_with_stale_click_data(
    monkeypatch,
):
    manual_process = SimpleNamespace(
        supports_manual_click=True,
        process_name="manual_2d_click",
    )

    monkeypatch.setattr(
        mutation.registry,
        "resolve_process_name",
        lambda process_name: process_name,
    )
    monkeypatch.setattr(
        mutation.registry,
        "get_process_instance",
        lambda **kwargs: manual_process,
    )

    page_state_result, table_result, status_children = mutation.handle_manual_graph_click(
        ids=SimpleNamespace(),
        adapter=SimpleNamespace(),
        triggered_graph_property="selectedData",
        click_data={
            "points": [
                {
                    "x": 123.0,
                    "y": 456.0,
                }
            ]
        },
        selected_data=None,
        process_name="manual_2d_click",
        page_state=SimpleNamespace(),
        detector_dropdown_ids=[],
        detector_dropdown_values=[],
        process_setting_ids=[],
        process_setting_values=[],
        data_filter_value=None,
        axis_scale_toggle_values=None,
        table_data=[],
        mie_model=None,
        runtime_config_data={},
        status_component_ids=[{"process": "manual_2d_click"}],
    )

    assert page_state_result is dash.no_update
    assert table_result is dash.no_update
    assert status_children == [dash.no_update]


def test_handle_manual_graph_click_ignores_empty_selection_payload_dict(
    monkeypatch,
):
    manual_process = SimpleNamespace(
        supports_manual_click=True,
        process_name="manual_2d_click",
        extract_selected_xy_range=lambda payload: None,
    )

    monkeypatch.setattr(
        mutation.registry,
        "resolve_process_name",
        lambda process_name: process_name,
    )
    monkeypatch.setattr(
        mutation.registry,
        "get_process_instance",
        lambda **kwargs: manual_process,
    )

    page_state_result, table_result, status_children = mutation.handle_manual_graph_click(
        ids=SimpleNamespace(),
        adapter=SimpleNamespace(),
        triggered_graph_property="selectedData",
        click_data=None,
        selected_data={"points": []},
        process_name="manual_2d_click",
        page_state=SimpleNamespace(),
        detector_dropdown_ids=[],
        detector_dropdown_values=[],
        process_setting_ids=[],
        process_setting_values=[],
        data_filter_value=None,
        axis_scale_toggle_values=None,
        table_data=[],
        mie_model=None,
        runtime_config_data={},
        status_component_ids=[{"process": "manual_2d_click"}],
    )

    assert page_state_result is dash.no_update
    assert table_result is dash.no_update
    assert status_children == [dash.no_update]
