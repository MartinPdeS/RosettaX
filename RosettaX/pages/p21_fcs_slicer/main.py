# -*- coding: utf-8 -*-

from typing import Any

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html

from RosettaX.ui import (
    WorkflowStep,
    build_workflow_page_header,
    build_workflow_section_card,
)
from RosettaX.utils import styling, ui_forms
from RosettaX.workflow.calibration_cards import make_collapsible_section_card
from RosettaX.workflow.file_selection import UploadedFile, UploadedFileBatch

from .ids import Ids
from . import services


class FCSSlicerPage:
    """Slice the same detector-channel subset from multiple compatible FCS files."""

    def __init__(self) -> None:
        self.ids = Ids()

    def layout(self) -> dbc.Container:
        return dbc.Container(
            [
                dcc.Store(id=self.ids.file_store, data=None, storage_type="session"),
                dcc.Download(id=self.ids.download),
                self._build_header_card(),
                self._build_upload_card(),
                self._build_selection_card(),
                self._build_export_card(),
            ],
            fluid=True,
            style={
                **styling.PAGE,
                "paddingLeft": "0px",
                "paddingRight": "0px",
                "paddingBottom": "48px",
            },
        )

    def _build_header_card(self) -> dbc.Card:
        return build_workflow_page_header(
            title="Slicing",
            description=(
                "Upload a compatible batch, choose the detector channels to keep, "
                "and download sliced FCS copies with every event preserved."
            ),
            steps=self._build_header_steps(),
        )

    def _build_header_steps(self) -> list[WorkflowStep]:
        """Build the FCS slicing workflow overview shown in the page header."""
        return [
            WorkflowStep(
                number="1",
                title="Upload compatible files",
                description=(
                    "Load one or more FCS files. RosettaX checks that their channels, "
                    "FCS versions, and detector voltages match."
                ),
                color_name=styling.get_workflow_section_color(1),
            ),
            WorkflowStep(
                number="2",
                title="Choose channels",
                description=(
                    "Select the detector channels to retain. The original channel order "
                    "and every recorded event are preserved."
                ),
                color_name=styling.get_workflow_section_color(2),
            ),
            WorkflowStep(
                number="3",
                title="Download sliced files",
                description=(
                    "Export the sliced FCS copies together in one ZIP package while "
                    "keeping the selected channel metadata."
                ),
                color_name=styling.get_workflow_section_color(3),
            ),
        ]

    def _build_upload_card(self) -> dbc.Card:
        return self._build_section_card(
            number=1,
            title="Upload FCS files",
            subtitle=(
                "Files must have the same channels, FCS version, and detector voltages."
            ),
            children=[
                ui_forms.build_upload_widget(
                    upload_id=self.ids.upload,
                    prompt_text="Select one or more FCS files",
                    accepted_file_extensions=".fcs",
                    multiple=True,
                ),
                dcc.Loading(
                    ui_forms.build_upload_status(
                        status_id=self.ids.upload_feedback,
                        initial_text="No files loaded.",
                    ),
                    type="default",
                ),
            ],
        )

    def _build_selection_card(self) -> dbc.Card:
        return self._build_section_card(
            number=2,
            title="Select detector channels",
            subtitle="The selected channel order follows the original FCS files.",
            children=[
                dcc.Dropdown(
                    id=self.ids.channels,
                    options=[],
                    value=[],
                    multi=True,
                    placeholder="Upload a compatible FCS batch first",
                ),
                html.Div(
                    "No channels available.",
                    id=self.ids.selection_feedback,
                    style={"marginTop": "10px", "opacity": 0.76},
                ),
            ],
        )

    def _build_export_card(self) -> dbc.Card:
        return self._build_section_card(
            number=3,
            title="Export sliced files",
            subtitle="RosettaX packages the sliced FCS copies in one ZIP download.",
            children=[
                dbc.Button(
                    "Download sliced FCS files",
                    id=self.ids.export_button,
                    color="primary",
                    disabled=True,
                ),
                html.Div(
                    id=self.ids.export_feedback,
                    style={"marginTop": "10px", "opacity": 0.76},
                ),
            ],
        )

    def _build_section_card(
        self,
        *,
        number: int,
        title: str,
        subtitle: str,
        children: list[Any],
    ) -> dbc.Card:
        card = build_workflow_section_card(
            section_number=number,
            title=title,
            subtitle=subtitle,
            body_children=children,
            style_overrides={"marginBottom": "16px"},
        )
        return make_collapsible_section_card(
            card,
            page_name=self.ids.page_prefix,
            section_key=str(number),
            initially_collapsed=True,
        )

    def register_callbacks(self) -> "FCSSlicerPage":
        @dash.callback(
            dash.Output(self.ids.file_store, "data"),
            dash.Output(self.ids.channels, "options"),
            dash.Output(self.ids.channels, "value"),
            dash.Output(self.ids.upload_feedback, "children"),
            dash.Output(self.ids.upload_feedback, "color"),
            dash.Input(self.ids.upload, "contents"),
            dash.State(self.ids.upload, "filename"),
            prevent_initial_call=True,
        )
        def load_fcs_batch(contents: Any, filenames: Any):
            try:
                saved_paths, safe_filenames = services.save_uploaded_batch(
                    contents=contents,
                    filenames=filenames,
                )
                report = services.inspect_compatible_fcs_batch(saved_paths)
                message, color = services.build_upload_feedback(
                    filenames=safe_filenames,
                    consistency_report=report,
                )
                if not report.get("are_all_files_consistent", False):
                    return None, [], [], message, color

                channels = [str(name) for name in report["reference_column_names"]]
                options = [{"label": channel, "value": channel} for channel in channels]
                store_data = UploadedFileBatch(
                    files=tuple(
                        UploadedFile(path=str(path), filename=filename)
                        for path, filename in zip(saved_paths, safe_filenames, strict=True)
                    ),
                    reference_column_names=tuple(channels),
                ).to_dict()
                return store_data, options, channels, message, color
            except Exception as exception:
                return (
                    None,
                    [],
                    [],
                    f"Could not load FCS files: {type(exception).__name__}: {exception}",
                    "danger",
                )

        @dash.callback(
            dash.Output(self.ids.export_button, "disabled"),
            dash.Output(self.ids.selection_feedback, "children"),
            dash.Input(self.ids.file_store, "data"),
            dash.Input(self.ids.channels, "value"),
        )
        def update_export_state(file_store: Any, selected_channels: Any):
            if not isinstance(file_store, dict):
                return True, "No channels available."

            batch = UploadedFileBatch.from_dict(file_store)
            available_channels = list(batch.reference_column_names)
            try:
                selected = services.validate_selected_channels(
                    selected_channels=selected_channels,
                    available_channels=available_channels,
                )
            except ValueError as exception:
                return True, str(exception)

            return False, f"{len(selected)} of {len(available_channels)} channels selected."

        @dash.callback(
            dash.Output(self.ids.download, "data"),
            dash.Output(self.ids.export_feedback, "children"),
            dash.Input(self.ids.export_button, "n_clicks"),
            dash.State(self.ids.file_store, "data"),
            dash.State(self.ids.channels, "value"),
            prevent_initial_call=True,
        )
        def export_sliced_batch(n_clicks: Any, file_store: Any, selected_channels: Any):
            if not n_clicks or not isinstance(file_store, dict):
                return dash.no_update, dash.no_update

            try:
                batch = UploadedFileBatch.from_dict(file_store)
                payload = services.build_sliced_fcs_zip(
                    file_paths=[file.path for file in batch.files],
                    filenames=[file.filename for file in batch.files],
                    selected_channels=selected_channels,
                    available_channels=list(batch.reference_column_names),
                )
                file_count = len(batch.files)
                return (
                    dcc.send_bytes(payload, "rosettax_sliced_fcs_files.zip"),
                    f"Prepared {file_count} sliced FCS file{'s' if file_count != 1 else ''}.",
                )
            except Exception as exception:
                return (
                    dash.no_update,
                    f"Export failed: {type(exception).__name__}: {exception}",
                )

        return self


_page = FCSSlicerPage().register_callbacks()
layout = _page.layout

dash.register_page(
    __name__,
    path="/fcs-slicer",
    name="Slicing",
    order=8,
    layout=layout,
)
