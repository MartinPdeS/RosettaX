"""Identify the cytometer for FCS calibration workflows."""

import dash
from dash import dcc, html
from RosettaX.utils.reader import FCSFile
from RosettaX.workflow.detector.catalog import (
    load_instrument_catalog,
    match_recording_instrument,
)
from RosettaX.workflow.peak.core.detectors import extract_instrument_name_from_metadata


def build_system_selector(*, ids) -> html.Div:
    """Build the cytometer selector for the upload card."""
    instruments = load_instrument_catalog()["instruments"]
    options = [{"label": "Unknown cytometer", "value": ""}]
    options.extend(sorted(
        ({"label": f"{entry['manufacturer']} {entry['model']}", "value": key}
         for key, entry in instruments.items() if entry.get("instrument_aliases")),
        key=lambda option: option["label"].casefold(),
    ))
    return html.Div([
        dcc.Store(id=ids.system_file, storage_type="session"),
        html.Label("Cytometer model", htmlFor=ids.system_model),
        dcc.Dropdown(id=ids.system_model, options=options, clearable=False,
                     persistence=True, persistence_type="session"),
        html.Div(id=ids.system_status, className="small mt-2", role="status"),
    ], className="mt-3")


def register_system_detection(*, ids) -> None:
    """Detect the model when the FCS file changes."""

    @dash.callback(
        dash.Output(ids.system_model, "value"),
        dash.Output(ids.system_file, "data"),
        dash.Output(ids.system_status, "children"),
        dash.Input(ids.page_state_store, "data"),
        dash.State(ids.system_file, "data"),
    )
    def detect_system(page_state, previous_file):
        file_path = (page_state or {}).get("uploaded_fcs_path")
        if not file_path:
            return None, None, "Upload a bead FCS file to identify the cytometer."
        if file_path == previous_file:
            return dash.no_update, dash.no_update, dash.no_update
        try:
            with FCSFile(file_path) as recording:
                metadata = recording.get_metadata()
                match = match_recording_instrument(
                    instrument_name=extract_instrument_name_from_metadata(metadata=metadata),
                    channel_names=metadata.column_names,
                )
        except (OSError, ValueError):
            match = None
        if match:
            status = "Standard layout assumed. Select Modified if this instrument has MALS." if match.get("mals_variant") else ""
            return match["catalog_key"], file_path, status
        return "", file_path, "No unique instrument match. Choose the model or leave it as Unknown."
