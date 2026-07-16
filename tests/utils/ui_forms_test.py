# -*- coding: utf-8 -*-

import dash_bootstrap_components as dbc
from dash import dcc

from RosettaX.utils import ui_forms
from RosettaX.utils.upload_limits import format_upload_size, get_max_upload_bytes


def _collect_text(component) -> list[str]:
    if isinstance(component, str):
        return [component]

    children = getattr(component, "children", None)
    if children is None:
        return []
    if isinstance(children, (list, tuple)):
        return [text for child in children for text in _collect_text(child)]
    return _collect_text(children)


def test_upload_widget_shows_the_standard_file_information() -> None:
    upload = ui_forms.build_upload_widget(
        upload_id="test-upload",
        prompt_text="Select FCS files",
        accepted_file_extensions=".fcs",
        multiple=True,
    )

    assert isinstance(upload, dcc.Upload)
    assert upload.accept == ".fcs"
    assert upload.multiple is True
    assert upload.max_size == get_max_upload_bytes()
    assert " ".join(_collect_text(upload)) == (
        "Select FCS files Multiple files allowed · Accepted: .fcs · "
        f"Maximum file size: {format_upload_size()}"
    )


def test_upload_status_uses_the_standard_alert_format() -> None:
    status = ui_forms.build_upload_status(
        status_id="test-status",
        initial_text="No file loaded.",
    )

    assert isinstance(status, dbc.Alert)
    assert status.children == "No file loaded."
    assert status.color == "secondary"
    status_properties = getattr(status, "kwargs", None)
    if status_properties is None:
        status_properties = status.to_plotly_json()["props"]
    assert status_properties["is_open"] is True
    assert status_properties["className"] == "mb-0 mt-3"
