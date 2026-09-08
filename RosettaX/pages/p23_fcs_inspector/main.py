# -*- coding: utf-8 -*-
from pathlib import Path
from typing import Any

import dash
import dash_bootstrap_components as dbc
import pandas as pd
from dash import dcc, html

from RosettaX.ui import WorkflowStep, build_workflow_page_header, build_workflow_section_card
from RosettaX.utils import styling, ui_forms
from RosettaX.utils.reader import FCSFile
from RosettaX.workflow.upload import services as upload_services


class FCSInspectorPage:
    """Inspect FCS metadata and channel definitions without loading event data."""

    prefix = "fcs-inspector"

    def layout(self) -> dbc.Container:
        return dbc.Container(
            [
                build_workflow_page_header(
                    title="FCS Inspector",
                    description="Review file metadata, acquisition details, and channel definitions before downstream work.",
                    steps=[
                        WorkflowStep("1", "Upload FCS file", "Select one FCS file to inspect.", "yellow"),
                        WorkflowStep("2", "Review metadata", "Check file details and channel definitions.", "blue"),
                    ],
                ),
                build_workflow_section_card(
                    section_number=1,
                    title="Upload FCS file",
                    subtitle="The inspector reads metadata only; event measurements remain unloaded.",
                    body_children=[
                        ui_forms.build_upload_widget(
                            upload_id=f"{self.prefix}-upload",
                            prompt_text="Select an FCS file",
                            accepted_file_extensions=".fcs",
                            multiple=False,
                        ),
                        ui_forms.build_upload_status(
                            status_id=f"{self.prefix}-status",
                            initial_text="No file loaded.",
                        ),
                    ],
                ),
                build_workflow_section_card(
                    section_number=2,
                    title="File details",
                    subtitle="Upload an FCS file to view its metadata.",
                    body_children=html.Div(id=f"{self.prefix}-report"),
                ),
            ],
            fluid=True,
            style={**styling.PAGE, "paddingBottom": "48px"},
        )

    def register_callbacks(self) -> "FCSInspectorPage":
        @dash.callback(
            dash.Output(f"{self.prefix}-status", "children"),
            dash.Output(f"{self.prefix}-status", "color"),
            dash.Output(f"{self.prefix}-report", "children"),
            dash.Input(f"{self.prefix}-upload", "contents"),
            dash.State(f"{self.prefix}-upload", "filename"),
            prevent_initial_call=True,
        )
        def inspect_file(contents: Any, filename: Any):
            try:
                saved_path = upload_services.save_uploaded_file(
                    contents=contents,
                    filename=filename,
                    upload_directory=upload_services.DEFAULT_UPLOAD_DIRECTORY / "fcs-inspector",
                )
                with FCSFile(saved_path, writable=False) as fcs_file:
                    metadata = fcs_file.get_metadata()
                    rows = [
                        {
                            "Channel": channel,
                            "Detector voltage": metadata.detector_voltages.get(channel),
                        }
                        for channel in metadata.column_names
                    ]
                    summary = [
                        ("File", Path(str(filename)).name),
                        ("FCS version", metadata.fcs_version or "Not specified"),
                        ("Events", metadata.number_of_events or "Not specified"),
                        ("Parameters", metadata.number_of_parameters or "Not specified"),
                    ]
                return (
                    f"Loaded file: {Path(str(filename)).name}",
                    "success",
                    html.Div(
                        [
                            dbc.Table(
                                [html.Tbody([html.Tr([html.Th(key), html.Td(str(value))]) for key, value in summary])],
                                bordered=True,
                                size="sm",
                            ),
                            html.H6("Channels", style={"marginTop": "18px"}),
                            dbc.Table.from_dataframe(
                                pd.DataFrame(rows),
                                striped=True,
                                bordered=True,
                                hover=True,
                                size="sm",
                            ),
                        ]
                    ),
                )
            except (OSError, ValueError, KeyError) as error:
                return (
                    upload_services.build_upload_error_text(error),
                    "danger",
                    html.Div("No readable FCS metadata is available.", style={"opacity": 0.76}),
                )


_page = FCSInspectorPage().register_callbacks()
layout = _page.layout

dash.register_page(__name__, path="/fcs-inspector", name="FCS Inspector", order=23, layout=layout)
