# -*- coding: utf-8 -*-

from typing import Any

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html

from RosettaX.ui import (
    WorkflowStep,
    build_workflow_page_header,
)
from RosettaX.utils import styling, ui_forms
from RosettaX.workflow.calibration_cards import (
    build_fcs_tool_card_stack,
    build_profile_aware_workflow_section_card,
)
from RosettaX.workflow.file_selection import UploadedFile, UploadedFileBatch
from RosettaX.workflow.upload import services as upload_services

from . import services
from .ids import Ids


class FCSMergePage:
    """Merge compatible FCS files by concatenating their events."""

    def __init__(self) -> None:
        self.ids = Ids()

    def layout(self) -> dbc.Container:
        return dbc.Container(
            [
                build_fcs_tool_card_stack(
                    [
                        dcc.Store(id=self.ids.file_store, data=None, storage_type="session"),
                        dcc.Download(id=self.ids.download),
                        self._build_header_card(),
                        self._build_upload_card(),
                        self._build_export_card(),
                    ]
                ),
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
            title="FCS Merge",
            description=(
                "Upload compatible FCS files and download one file containing all "
                "events in the uploaded order."
            ),
            steps=[
                WorkflowStep(
                    number="1",
                    title="Upload compatible files",
                    description=(
                        "RosettaX checks that channels, FCS versions, and detector "
                        "voltages match."
                    ),
                    color_name=styling.get_workflow_section_color(1),
                ),
                WorkflowStep(
                    number="2",
                    title="Download merged file",
                    description=(
                        "All events are concatenated in input order, using the first "
                        "file as the metadata template."
                    ),
                    color_name=styling.get_workflow_section_color(2),
                ),
            ],
            step_target_page_name=self.ids.page_prefix,
            style_overrides={"marginBottom": "0px"},
        )

    def _build_upload_card(self) -> dbc.Card:
        return self._build_section_card(
            number=1,
            title="Upload FCS files",
            subtitle=(
                "Select at least two files with matching channels, FCS version, and "
                "detector voltages."
            ),
            children=[
                ui_forms.build_upload_widget(
                    upload_id=self.ids.upload,
                    prompt_text="Select FCS files to merge",
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

    def _build_export_card(self) -> dbc.Card:
        return self._build_section_card(
            number=2,
            title="Download merged FCS file",
            subtitle="The merged file preserves the first file's metadata and all input events.",
            children=[
                dbc.Button(
                    "Download merged FCS file",
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
        return build_profile_aware_workflow_section_card(
            page_name=self.ids.page_prefix,
            section_number=number,
            title=title,
            subtitle=subtitle,
            body_children=children,
        )

    def register_callbacks(self) -> "FCSMergePage":
        @dash.callback(
            dash.Output(self.ids.file_store, "data"),
            dash.Output(self.ids.upload_feedback, "children"),
            dash.Output(self.ids.upload_feedback, "color"),
            dash.Output(self.ids.export_button, "disabled"),
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
                saved_paths, consistency_report = services.validate_merge_input_paths(
                    saved_paths,
                )
                message, color = upload_services.build_upload_feedback(
                    filenames=safe_filenames,
                    consistency_report=consistency_report,
                )
                store_data = UploadedFileBatch(
                    files=tuple(
                        UploadedFile(path=str(path), filename=filename)
                        for path, filename in zip(saved_paths, safe_filenames, strict=True)
                    ),
                    reference_column_names=tuple(
                        str(name)
                        for name in consistency_report["reference_column_names"]
                    ),
                ).to_dict()
                return store_data, message, color, False
            except Exception as exception:
                return (
                    None,
                    f"Could not load FCS files: {type(exception).__name__}: {exception}",
                    "danger",
                    True,
                )

        @dash.callback(
            dash.Output(self.ids.download, "data"),
            dash.Output(self.ids.export_feedback, "children"),
            dash.Input(self.ids.export_button, "n_clicks"),
            dash.State(self.ids.file_store, "data"),
            prevent_initial_call=True,
        )
        def export_merged_file(n_clicks: Any, file_store: Any):
            if not n_clicks or not isinstance(file_store, dict):
                return dash.no_update, dash.no_update

            try:
                batch = UploadedFileBatch.from_dict(file_store)
                payload = services.build_merged_fcs_bytes(
                    file_paths=[file.path for file in batch.files],
                )
                return (
                    dcc.send_bytes(
                        payload,
                        services.build_merged_export_filename(batch.files[0].filename),
                    ),
                    f"Prepared merged FCS file with {len(batch.files)} inputs.",
                )
            except Exception as exception:
                return (
                    dash.no_update,
                    f"Merge failed: {type(exception).__name__}: {exception}",
                )

        return self


_page = FCSMergePage().register_callbacks()
layout = _page.layout

dash.register_page(
    __name__,
    path="/fcs-merge",
    name="Merge FCS files",
    order=24,
    layout=layout,
)
