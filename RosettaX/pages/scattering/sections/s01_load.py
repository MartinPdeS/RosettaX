import base64
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import logging

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html

from RosettaX.pages import styling
from RosettaX.pages.fluorescence.backend import BackEnd


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LoadResult:
    uploaded_fcs_path_store: Any = dash.no_update
    scattering_detector_options: Any = dash.no_update
    scattering_detector_value: Any = dash.no_update
    fluorescence_detector_options: Any = dash.no_update
    fluorescence_detector_value: Any = dash.no_update

    def to_tuple(self) -> tuple:
        return (
            self.uploaded_fcs_path_store,
            self.scattering_detector_options,
            self.scattering_detector_value,
            self.fluorescence_detector_options,
            self.fluorescence_detector_value,
        )


class LoadSection:
    def __init__(self, page) -> None:
        self.page = page
        logger.debug("Initialized legacy LoadSection with page=%r", page)

    def _get_layout(self):
        logger.debug("Building legacy load section layout.")

        widget = dcc.Upload(
            id=self.page.ids.Upload.upload,
            children=html.Div(["Drag and Drop or ", html.A("Select Bead File")]),
            style=styling.UPLOAD,
            multiple=False,
            accept=".fcs",
        )

        return dbc.Card(
            [
                dbc.CardHeader("1. Upload FCS File"),
                dbc.CardBody(
                    [
                        widget,
                        html.Div(id=self.page.ids.Upload.filename),
                    ],
                    style=self.page.style["card_body_scroll"],
                ),
            ]
        )

    @staticmethod
    def write_upload_to_tempfile(*, contents: str, filename: str) -> str:
        logger.debug(
            "write_upload_to_tempfile called with filename=%r contents_prefix=%r",
            filename,
            contents[:64] if isinstance(contents, str) else contents,
        )

        header, b64data = contents.split(",", 1)
        logger.debug("Parsed upload header=%r", header)

        raw = base64.b64decode(b64data)

        suffix = Path(filename).suffix or ".bin"
        tmp_dir = Path(tempfile.gettempdir()) / "rosettax_uploads"
        tmp_dir.mkdir(parents=True, exist_ok=True)

        output_path = tmp_dir / f"{next(tempfile._get_candidate_names())}{suffix}"
        output_path.write_bytes(raw)

        logger.debug(
            "Upload written successfully to output_path=%r byte_count=%r",
            str(output_path),
            len(raw),
        )
        return str(output_path)

    def register_callbacks(self):
        logger.debug("Registering legacy load section callbacks.")

        @callback(
            Output(self.page.ids.Upload.filename, "children"),
            Input(self.page.ids.Upload.upload, "filename"),
            prevent_initial_call=True,
        )
        def show_filename(name):
            logger.debug("show_filename called with name=%r", name)

            if name:
                logger.debug("Displaying uploaded filename=%r", name)
                return str(name)

            logger.debug("No filename provided. Returning empty string.")
            return ""

        @callback(
            Output(self.page.ids.Upload.fcs_path_store, "data"),
            Output(self.page.ids.scattering_detector_dropdown, "options"),
            Output(self.page.ids.scattering_detector_dropdown, "value"),
            Output(self.page.ids.fluorescence_detector_dropdown, "options"),
            Output(self.page.ids.fluorescence_detector_dropdown, "value"),
            Input(self.page.ids.Upload.upload, "contents"),
            State(self.page.ids.Upload.upload, "filename"),
            State(self.page.ids.scattering_detector_dropdown, "value"),
            State(self.page.ids.fluorescence_detector_dropdown, "value"),
            prevent_initial_call=True,
        )
        def handle_upload(
            contents,
            filename,
            current_scattering_detector_value,
            current_fluorescence_detector_value,
        ):
            logger.debug(
                "handle_upload called with contents_type=%s filename=%r "
                "current_scattering_detector_value=%r current_fluorescence_detector_value=%r",
                type(contents).__name__,
                filename,
                current_scattering_detector_value,
                current_fluorescence_detector_value,
            )

            if not contents or not filename:
                logger.debug("Missing contents or filename. Returning empty detector outputs.")
                return LoadResult(
                    scattering_detector_options=[],
                    scattering_detector_value=None,
                    fluorescence_detector_options=[],
                    fluorescence_detector_value=None,
                ).to_tuple()

            try:
                temporary_fcs_path = self.write_upload_to_tempfile(
                    contents=contents,
                    filename=filename,
                )
                logger.debug(
                    "Temporary upload save succeeded with filename=%r temporary_fcs_path=%r",
                    filename,
                    temporary_fcs_path,
                )

            except Exception:
                logger.exception(
                    "Failed to write uploaded file to temporary path for filename=%r",
                    filename,
                )
                return LoadResult(
                    scattering_detector_options=[],
                    scattering_detector_value=None,
                    fluorescence_detector_options=[],
                    fluorescence_detector_value=None,
                ).to_tuple()

            try:
                self.page.backend = BackEnd(temporary_fcs_path)
                logger.debug(
                    "BackEnd initialized successfully for temporary_fcs_path=%r",
                    temporary_fcs_path,
                )

            except Exception:
                logger.exception(
                    "Failed to initialize BackEnd for temporary_fcs_path=%r",
                    temporary_fcs_path,
                )
                return LoadResult(
                    uploaded_fcs_path_store=temporary_fcs_path,
                    scattering_detector_options=[],
                    scattering_detector_value=None,
                    fluorescence_detector_options=[],
                    fluorescence_detector_value=None,
                ).to_tuple()

            try:
                channels = self.page.service.channels_from_file(temporary_fcs_path)
                logger.debug(
                    "Channel extraction succeeded for temporary_fcs_path=%r channels=%r",
                    temporary_fcs_path,
                    channels,
                )

            except Exception:
                logger.exception(
                    "Saved uploaded file but failed to read channels from temporary_fcs_path=%r",
                    temporary_fcs_path,
                )
                return LoadResult(
                    uploaded_fcs_path_store=temporary_fcs_path,
                    scattering_detector_options=[],
                    scattering_detector_value=None,
                    fluorescence_detector_options=[],
                    fluorescence_detector_value=None,
                ).to_tuple()

            scattering_detector_options = list(channels.scatter_options or [])
            fluorescence_detector_options = list(channels.fluorescence_options or [])

            logger.debug(
                "Resolved detector options counts: scattering=%r fluorescence=%r",
                len(scattering_detector_options),
                len(fluorescence_detector_options),
            )

            allowed_scattering_values = {
                str(option["value"])
                for option in scattering_detector_options
                if "value" in option
            }
            allowed_fluorescence_values = {
                str(option["value"])
                for option in fluorescence_detector_options
                if "value" in option
            }

            logger.debug(
                "Allowed detector values: scattering=%r fluorescence=%r",
                allowed_scattering_values,
                allowed_fluorescence_values,
            )

            scattering_detector_value = (
                str(current_scattering_detector_value)
                if current_scattering_detector_value is not None
                and str(current_scattering_detector_value) in allowed_scattering_values
                else channels.scatter_value
            )
            if scattering_detector_value not in allowed_scattering_values:
                scattering_detector_value = (
                    scattering_detector_options[0]["value"]
                    if scattering_detector_options
                    else None
                )

            fluorescence_detector_value = (
                str(current_fluorescence_detector_value)
                if current_fluorescence_detector_value is not None
                and str(current_fluorescence_detector_value) in allowed_fluorescence_values
                else channels.fluorescence_value
            )
            if fluorescence_detector_value not in allowed_fluorescence_values:
                fluorescence_detector_value = (
                    fluorescence_detector_options[0]["value"]
                    if fluorescence_detector_options
                    else None
                )

            logger.debug(
                "Final detector selection resolved to scattering_detector_value=%r fluorescence_detector_value=%r",
                scattering_detector_value,
                fluorescence_detector_value,
            )

            result = LoadResult(
                uploaded_fcs_path_store=temporary_fcs_path,
                scattering_detector_options=scattering_detector_options,
                scattering_detector_value=scattering_detector_value,
                fluorescence_detector_options=fluorescence_detector_options,
                fluorescence_detector_value=fluorescence_detector_value,
            )

            logger.debug("handle_upload returning LoadResult=%r", result)
            return result.to_tuple()