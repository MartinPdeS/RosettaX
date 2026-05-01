# -*- coding: utf-8 -*-

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import dash

from . import services


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FilePickerResult:
    """
    Container for the Dash outputs of the file upload callback.
    """

    uploaded_fcs_path_store: Any = dash.no_update
    alert_children: Any = dash.no_update
    alert_color: Any = dash.no_update
    alert_is_open: Any = dash.no_update

    def to_tuple(self) -> tuple:
        """
        Convert the result into callback output order.
        """
        return (
            self.uploaded_fcs_path_store,
            self.alert_children,
            self.alert_color,
            self.alert_is_open,
        )


class FilePickerCallbacks:
    """
    Callback registrar for the input FCS file picker section.
    """

    def __init__(
        self,
        *,
        page: Any,
        upload_directory: Path,
    ) -> None:
        self.page = page
        self.upload_directory = upload_directory

    def register_callbacks(self) -> None:
        """
        Register callbacks for the file picker.
        """
        logger.debug(
            "Registering FilePicker callbacks with upload_directory=%r",
            str(self.upload_directory),
        )

        services.validate_checks_contract()

        self._register_upload_callback()

    def _register_upload_callback(self) -> None:
        """
        Register upload handling callback.
        """

        @dash.callback(
            dash.Output(
                self.page.ids.Stores.uploaded_fcs_path_store,
                "data",
            ),
            dash.Output(
                self.page.ids.FilePicker.column_consistency_alert,
                "children",
            ),
            dash.Output(
                self.page.ids.FilePicker.column_consistency_alert,
                "color",
            ),
            dash.Output(
                self.page.ids.FilePicker.column_consistency_alert,
                "is_open",
            ),
            dash.Input(
                self.page.ids.FilePicker.upload,
                "contents",
            ),
            dash.State(
                self.page.ids.FilePicker.upload,
                "filename",
            ),
            prevent_initial_call=True,
        )
        def handle_upload(
            contents_list: Optional[list[str]],
            filenames: Optional[list[str]],
        ) -> tuple:
            logger.debug(
                "handle_upload called with contents_count=%r filenames=%r",
                None if contents_list is None else len(contents_list),
                filenames,
            )

            if not contents_list or not filenames:
                logger.debug("Upload was cancelled or no files were provided.")

                return FilePickerResult(
                    uploaded_fcs_path_store=None,
                    alert_children="Upload canceled.",
                    alert_color="danger",
                    alert_is_open=True,
                ).to_tuple()

            services.validate_upload_payload(
                contents_list=contents_list,
                filenames=filenames,
            )

            saved_paths = services.save_uploaded_files(
                upload_directory=self.upload_directory,
                contents_list=contents_list,
                filenames=filenames,
            )

            consistency_report = services.check_saved_files_consistency(
                saved_paths=saved_paths,
            )

            alert_children, alert_color, alert_is_open = services.build_success_alert_payload(
                saved_paths=saved_paths,
                consistency_report=consistency_report,
            )

            logger.debug(
                "Upload handling succeeded with saved_paths=%r alert_color=%r alert_is_open=%r",
                [
                    str(path)
                    for path in saved_paths
                ],
                alert_color,
                alert_is_open,
            )

            return FilePickerResult(
                uploaded_fcs_path_store=[
                    str(path)
                    for path in saved_paths
                ],
                alert_children=alert_children,
                alert_color=alert_color,
                alert_is_open=alert_is_open,
            ).to_tuple()