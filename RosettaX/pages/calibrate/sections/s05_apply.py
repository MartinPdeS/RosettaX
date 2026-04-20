# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any, Optional
from pathlib import Path
import io
import json
import logging
import zipfile

import numpy as np
import dash
import dash_bootstrap_components as dbc
from dash import dcc

from RosettaX.utils.reader import FCSFile
from RosettaX.utils import directories

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ApplySectionResult:
    status: Any = dash.no_update
    export_column_options: Any = dash.no_update
    export_column_values: Any = dash.no_update
    download_data: Any = dash.no_update

    def to_tuple(self) -> tuple:
        return (
            self.status,
            self.export_column_options,
            self.export_column_values,
            self.download_data,
        )


class Apply:
    def __init__(self, page) -> None:
        self.page = page

    def get_layout(self) -> dbc.Card:
        return dbc.Card(
            [
                self._build_header(),
                self._build_body(),
            ]
        )

    def _build_header(self) -> dbc.CardHeader:
        return dbc.CardHeader("3. Apply and export")

    def _build_body(self) -> dbc.CardBody:
        return dbc.CardBody(
            [
                self._build_export_columns_section(),
                dash.html.Div(style={"height": "12px"}),
                self._build_action_button_row(),
                dash.html.Div(style={"height": "10px"}),
                self._build_status_alert(),
                dcc.Download(id=self.page.ids.Export.download),
            ]
        )

    def _build_export_columns_section(self) -> dash.html.Div:
        return dash.html.Div(
            [
                dash.html.Div(
                    "Additional columns to export",
                    style={"marginBottom": "6px"},
                ),
                dash.dcc.Dropdown(
                    id=self.page.ids.Export.export_columns_dropdown,
                    options=[],
                    value=[],
                    multi=True,
                    placeholder="Select extra columns to export",
                    clearable=True,
                ),
                dash.html.Div(style={"height": "6px"}),
                dash.html.Small(
                    "The calibrated target channel will always be included. "
                    "These extra columns will be exported unchanged.",
                    style={"opacity": 0.75},
                ),
            ]
        )

    def _build_action_button_row(self) -> dash.html.Div:
        return dash.html.Div(
            [
                dbc.Button(
                    "Apply & export",
                    id=self.page.ids.Export.apply_and_export_button,
                    n_clicks=0,
                    color="primary",
                ),
            ],
            style={
                "display": "flex",
                "alignItems": "center",
                "gap": "12px",
            },
        )

    def _build_status_alert(self) -> dbc.Alert:
        return dbc.Alert(
            "Status will appear here.",
            id=self.page.ids.Export.status,
            color="secondary",
            style={"marginBottom": "0px"},
        )

    def register_callbacks(self) -> None:
        @dash.callback(
            dash.Output(self.page.ids.Export.export_columns_dropdown, "options"),
            dash.Output(self.page.ids.Export.export_columns_dropdown, "value"),
            dash.Input(self.page.ids.Stores.uploaded_fcs_path_store, "data"),
            dash.State(self.page.ids.Export.export_columns_dropdown, "value"),
            prevent_initial_call=False,
        )
        def populate_export_columns(
            uploaded_fcs_path: Any,
            current_export_columns: Any,
        ) -> tuple:
            logger.debug(
                "populate_export_columns called with uploaded_fcs_path=%r current_export_columns=%r",
                uploaded_fcs_path,
                current_export_columns,
            )

            first_uploaded_fcs_path = self._resolve_first_uploaded_fcs_path(uploaded_fcs_path)

            if not first_uploaded_fcs_path:
                logger.debug("No uploaded FCS path available. Returning empty export dropdown.")
                return ApplySectionResult(
                    export_column_options=[],
                    export_column_values=[],
                ).to_tuple()[1:3]

            try:
                with FCSFile(str(first_uploaded_fcs_path), writable=False) as fcs_file:
                    column_names = [str(name) for name in fcs_file.get_column_names()]
            except Exception:
                logger.exception(
                    "Failed to read column names from uploaded_fcs_path=%r",
                    first_uploaded_fcs_path,
                )
                return ApplySectionResult(
                    export_column_options=[],
                    export_column_values=[],
                ).to_tuple()[1:3]

            options = [{"label": column_name, "value": column_name} for column_name in column_names]
            allowed_values = {option["value"] for option in options}

            if isinstance(current_export_columns, list):
                resolved_values = [
                    str(value)
                    for value in current_export_columns
                    if str(value) in allowed_values
                ]
            else:
                resolved_values = []

            logger.debug(
                "Resolved export columns dropdown with %r options and values=%r",
                len(options),
                resolved_values,
            )
            return options, resolved_values

        @dash.callback(
            dash.Output(self.page.ids.Export.status, "children"),
            dash.Output(self.page.ids.Export.download, "data"),
            dash.Input(self.page.ids.Export.apply_and_export_button, "n_clicks"),
            dash.State(self.page.ids.Stores.uploaded_fcs_path_store, "data"),
            dash.State(self.page.ids.Stores.selected_calibration_path_store, "data"),
            dash.State(self.page.ids.ChannelPicker.dropdown, "value"),
            dash.State(self.page.ids.Export.export_columns_dropdown, "value"),
            prevent_initial_call=True,
        )
        def apply_and_export_calibration(
            n_clicks: int,
            uploaded_fcs_path: Any,
            selected_calibration: Any,
            target_channel: Any,
            export_columns: Any,
        ) -> tuple:
            logger.debug(
                "apply_and_export_calibration called with n_clicks=%r uploaded_fcs_path=%r selected_calibration=%r target_channel=%r export_columns=%r",
                n_clicks,
                uploaded_fcs_path,
                selected_calibration,
                target_channel,
                export_columns,
            )
            del n_clicks

            resolved_uploaded_fcs_paths = self._resolve_uploaded_fcs_paths(uploaded_fcs_path)

            if not resolved_uploaded_fcs_paths:
                return (
                    "Upload at least one input FCS file first.",
                    dash.no_update,
                )

            if not selected_calibration:
                return (
                    "Select a calibration first.",
                    dash.no_update,
                )

            if not target_channel:
                return (
                    "Select a target channel first.",
                    dash.no_update,
                )

            resolved_export_columns = self._normalize_export_columns(export_columns)
            final_export_columns = self._build_final_export_columns(
                target_channel=target_channel,
                export_columns=resolved_export_columns,
            )

            try:
                calibration_file_path = self._resolve_calibration_file_path(selected_calibration)
                calibration_payload = self._load_calibration_payload(calibration_file_path)

                if len(resolved_uploaded_fcs_paths) == 1:
                    single_uploaded_fcs_path = resolved_uploaded_fcs_paths[0]

                    with FCSFile(str(single_uploaded_fcs_path), writable=False) as input_fcs_file:
                        export_dataframe = input_fcs_file.dataframe_copy(
                            columns=final_export_columns,
                            dtype=float,
                            deep=True,
                        )

                        calibrated_values = self._apply_calibration_to_series(
                            values=export_dataframe[str(target_channel)].to_numpy(copy=True),
                            calibration_payload=calibration_payload,
                        )
                        export_dataframe[str(target_channel)] = calibrated_values

                        builder = FCSFile.builder_from_dataframe(
                            export_dataframe,
                            template=input_fcs_file,
                            force_float32=True,
                        )
                        exported_bytes = builder.build_bytes()

                    download_filename = self._build_export_filename(
                        uploaded_fcs_path=single_uploaded_fcs_path,
                        target_channel=str(target_channel),
                    )

                    logger.debug(
                        "Single-file calibration export succeeded with download_filename=%r exported_columns=%r",
                        download_filename,
                        final_export_columns,
                    )

                    return (
                        (
                            f'Applied calibration "{selected_calibration}" to channel "{target_channel}" '
                            f'for 1 file and prepared export with columns: {", ".join(final_export_columns)}.'
                        ),
                        dcc.send_bytes(exported_bytes, download_filename),
                    )

                zip_bytes = self._build_zip_of_calibrated_files(
                    uploaded_fcs_paths=resolved_uploaded_fcs_paths,
                    target_channel=str(target_channel),
                    final_export_columns=final_export_columns,
                    calibration_payload=calibration_payload,
                )

                zip_filename = self._build_zip_filename(
                    target_channel=str(target_channel),
                    file_count=len(resolved_uploaded_fcs_paths),
                )

            except Exception as exc:
                logger.exception(
                    "Failed to apply and export calibration for uploaded_fcs_path=%r selected_calibration=%r target_channel=%r",
                    uploaded_fcs_path,
                    selected_calibration,
                    target_channel,
                )
                return (
                    f"Failed to apply and export calibration: {type(exc).__name__}: {exc}",
                    dash.no_update,
                )

            logger.debug(
                "Multi-file calibration export succeeded with zip_filename=%r exported_columns=%r file_count=%r",
                zip_filename,
                final_export_columns,
                len(resolved_uploaded_fcs_paths),
            )

            return (
                (
                    f'Applied calibration "{selected_calibration}" to channel "{target_channel}" '
                    f'for {len(resolved_uploaded_fcs_paths)} files and prepared a ZIP export with columns: '
                    f'{", ".join(final_export_columns)}.'
                ),
                dcc.send_bytes(zip_bytes, zip_filename),
            )

    @staticmethod
    def _resolve_first_uploaded_fcs_path(uploaded_fcs_path: Any) -> Optional[str]:
        resolved_uploaded_fcs_paths = Apply._resolve_uploaded_fcs_paths(uploaded_fcs_path)
        if not resolved_uploaded_fcs_paths:
            return None
        return resolved_uploaded_fcs_paths[0]

    @staticmethod
    def _resolve_uploaded_fcs_paths(uploaded_fcs_path: Any) -> list[str]:
        if uploaded_fcs_path is None:
            return []

        if isinstance(uploaded_fcs_path, list):
            return [str(path) for path in uploaded_fcs_path if str(path).strip()]

        resolved_single_path = str(uploaded_fcs_path).strip()
        if not resolved_single_path:
            return []

        return [resolved_single_path]

    @staticmethod
    def _normalize_export_columns(export_columns: Any) -> list[str]:
        if not isinstance(export_columns, list):
            return []

        return [str(column) for column in export_columns if str(column).strip()]

    @staticmethod
    def _build_final_export_columns(
        *,
        target_channel: Any,
        export_columns: list[str],
    ) -> list[str]:
        target_channel_str = str(target_channel)

        final_columns = [target_channel_str]
        for column_name in export_columns:
            if column_name != target_channel_str:
                final_columns.append(column_name)

        return final_columns

    @staticmethod
    def _resolve_calibration_file_path(selected_calibration: Any) -> Path:
        selected_calibration_str = str(selected_calibration).strip()
        if not selected_calibration_str:
            raise ValueError("Selected calibration path is empty.")

        folder_name, file_name = selected_calibration_str.split("/", 1)

        if folder_name == "fluorescence":
            return Path(directories.fluorescence_calibration_directory) / file_name

        if folder_name == "scattering":
            return Path(directories.scattering_calibration_directory) / file_name

        raise ValueError(f'Unsupported calibration folder "{folder_name}".')

    @staticmethod
    def _load_calibration_payload(calibration_file_path: Path) -> dict[str, Any]:
        record = json.loads(calibration_file_path.read_text(encoding="utf-8"))
        payload = record.get("payload")

        if not isinstance(payload, dict):
            raise ValueError("Calibration file payload is missing or invalid.")

        return payload

    @staticmethod
    def _apply_calibration_to_series(
        *,
        values: np.ndarray,
        calibration_payload: dict[str, Any],
    ) -> np.ndarray:
        if "slope" in calibration_payload:
            slope = float(calibration_payload["slope"])
            intercept = float(calibration_payload.get("intercept", 0.0))
            return slope * np.asarray(values, dtype=float) + intercept

        if "scale" in calibration_payload:
            scale = float(calibration_payload["scale"])
            offset = float(calibration_payload.get("offset", 0.0))
            return scale * np.asarray(values, dtype=float) + offset

        raise ValueError(
            'Unsupported calibration payload format. Expected "slope"/"intercept" or "scale"/"offset".'
        )

    def _build_zip_of_calibrated_files(
        self,
        *,
        uploaded_fcs_paths: list[str],
        target_channel: str,
        final_export_columns: list[str],
        calibration_payload: dict[str, Any],
    ) -> bytes:
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_file:
            for uploaded_fcs_path in uploaded_fcs_paths:
                logger.debug(
                    "Processing uploaded_fcs_path=%r for batch calibration export",
                    uploaded_fcs_path,
                )

                with FCSFile(str(uploaded_fcs_path), writable=False) as input_fcs_file:
                    export_dataframe = input_fcs_file.dataframe_copy(
                        columns=final_export_columns,
                        dtype=float,
                        deep=True,
                    )

                    calibrated_values = self._apply_calibration_to_series(
                        values=export_dataframe[target_channel].to_numpy(copy=True),
                        calibration_payload=calibration_payload,
                    )
                    export_dataframe[target_channel] = calibrated_values

                    builder = FCSFile.builder_from_dataframe(
                        export_dataframe,
                        template=input_fcs_file,
                        force_float32=True,
                    )
                    exported_bytes = builder.build_bytes()

                member_filename = self._build_export_filename(
                    uploaded_fcs_path=uploaded_fcs_path,
                    target_channel=target_channel,
                )
                zip_file.writestr(member_filename, exported_bytes)

        zip_buffer.seek(0)
        return zip_buffer.getvalue()

    @staticmethod
    def _build_export_filename(
        *,
        uploaded_fcs_path: str,
        target_channel: str,
    ) -> str:
        input_path = Path(str(uploaded_fcs_path))
        safe_target_channel = (
            str(target_channel)
            .replace("/", "_")
            .replace("\\", "_")
            .replace(" ", "_")
        )
        return f"{input_path.stem}_calibrated_{safe_target_channel}.fcs"

    @staticmethod
    def _build_zip_filename(
        *,
        target_channel: str,
        file_count: int,
    ) -> str:
        safe_target_channel = (
            str(target_channel)
            .replace("/", "_")
            .replace("\\", "_")
            .replace(" ", "_")
        )
        return f"calibrated_{file_count}_files_{safe_target_channel}.zip"