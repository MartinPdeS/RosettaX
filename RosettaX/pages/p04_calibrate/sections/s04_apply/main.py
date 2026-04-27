# -*- coding: utf-8 -*-

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional
import io
import json
import logging
import zipfile

import dash
import dash_bootstrap_components as dbc
import numpy as np
from dash import dcc

from RosettaX.utils import directories
from RosettaX.utils.reader import FCSFile


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ApplySectionResult:
    """
    Result container for the apply and export section callbacks.
    """

    status: Any = dash.no_update
    export_column_options: Any = dash.no_update
    export_column_values: Any = dash.no_update
    download_data: Any = dash.no_update

    def to_tuple(self) -> tuple:
        """
        Convert the result into callback output order.
        """
        return (
            self.status,
            self.export_column_options,
            self.export_column_values,
            self.download_data,
        )


class Apply:
    """
    Apply a saved calibration to uploaded FCS files and export calibrated files.

    The source channel is always read from the top level ``source_channel`` field
    of the calibration payload.

    For scattering version 2 calibrations, the source channel is preserved and
    the estimated optical coupling is written to a new derived output column.
    """

    def __init__(
        self,
        page: Any,
    ) -> None:
        self.page = page

    def get_layout(self) -> dbc.Card:
        """
        Build the apply and export layout.
        """
        return dbc.Card(
            [
                self._build_header(),
                self._build_body(),
            ]
        )

    def _build_header(self) -> dbc.CardHeader:
        """
        Build the section header.
        """
        return dbc.CardHeader(
            "3. Apply and export",
        )

    def _build_body(self) -> dbc.CardBody:
        """
        Build the section body.
        """
        return dbc.CardBody(
            [
                self._build_export_columns_section(),
                dash.html.Div(
                    style={
                        "height": "12px",
                    },
                ),
                self._build_action_button_row(),
                dash.html.Div(
                    style={
                        "height": "10px",
                    },
                ),
                self._build_status_alert(),
                dcc.Download(
                    id=self.page.ids.Export.download,
                ),
            ]
        )

    def _build_export_columns_section(self) -> dash.html.Div:
        """
        Build the extra export columns selector.
        """
        return dash.html.Div(
            [
                dash.html.Div(
                    "Additional columns to export",
                    style={
                        "marginBottom": "6px",
                    },
                ),
                dash.dcc.Dropdown(
                    id=self.page.ids.Export.export_columns_dropdown,
                    options=[],
                    value=[],
                    multi=True,
                    placeholder="Select extra columns to export",
                    clearable=True,
                ),
                dash.html.Div(
                    style={
                        "height": "6px",
                    },
                ),
                dash.html.Small(
                    (
                        "The calibration source channel will always be included. "
                        "These extra columns will be exported unchanged."
                    ),
                    style={
                        "opacity": 0.75,
                    },
                ),
            ]
        )

    def _build_action_button_row(self) -> dash.html.Div:
        """
        Build the apply and export action row.
        """
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
        """
        Build the status alert.
        """
        return dbc.Alert(
            "Status will appear here.",
            id=self.page.ids.Export.status,
            color="secondary",
            style={
                "marginBottom": "0px",
            },
        )

    def register_callbacks(self) -> None:
        """
        Register apply and export callbacks.
        """

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
                "populate_export_columns called with uploaded_fcs_path=%r "
                "current_export_columns=%r",
                uploaded_fcs_path,
                current_export_columns,
            )

            first_uploaded_fcs_path = self._resolve_first_uploaded_fcs_path(
                uploaded_fcs_path,
            )

            if not first_uploaded_fcs_path:
                logger.debug(
                    "No uploaded FCS path available. Returning empty export dropdown."
                )

                return ApplySectionResult(
                    export_column_options=[],
                    export_column_values=[],
                ).to_tuple()[1:3]

            try:
                with FCSFile(str(first_uploaded_fcs_path), writable=False) as fcs_file:
                    column_names = [
                        str(name)
                        for name in fcs_file.get_column_names()
                    ]

            except Exception:
                logger.exception(
                    "Failed to read column names from uploaded_fcs_path=%r",
                    first_uploaded_fcs_path,
                )

                return ApplySectionResult(
                    export_column_options=[],
                    export_column_values=[],
                ).to_tuple()[1:3]

            options = [
                {
                    "label": column_name,
                    "value": column_name,
                }
                for column_name in column_names
            ]

            allowed_values = {
                option["value"]
                for option in options
            }

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
            dash.State(self.page.ids.CalibrationPicker.dropdown, "value"),
            dash.State(self.page.ids.Export.export_columns_dropdown, "value"),
            prevent_initial_call=True,
        )
        def apply_and_export_calibration(
            n_clicks: int,
            uploaded_fcs_path: Any,
            selected_calibration: Any,
            export_columns: Any,
        ) -> tuple:
            logger.debug(
                "apply_and_export_calibration called with n_clicks=%r "
                "uploaded_fcs_path=%r selected_calibration=%r export_columns=%r",
                n_clicks,
                uploaded_fcs_path,
                selected_calibration,
                export_columns,
            )

            del n_clicks

            resolved_uploaded_fcs_paths = self._resolve_uploaded_fcs_paths(
                uploaded_fcs_path,
            )

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

            try:
                calibration_file_path = self._resolve_calibration_file_path(
                    selected_calibration,
                )

                calibration_payload = self._load_calibration_payload(
                    calibration_file_path,
                )

                source_channel = self._resolve_source_channel(
                    calibration_payload,
                )

                if not source_channel:
                    return (
                        'Calibration payload is missing "source_channel".',
                        dash.no_update,
                    )

                output_channel = self._resolve_output_channel(
                    source_channel=source_channel,
                    calibration_payload=calibration_payload,
                )

                resolved_export_columns = self._normalize_export_columns(
                    export_columns,
                )

                input_export_columns = self._build_input_export_columns(
                    source_channel=source_channel,
                    export_columns=resolved_export_columns,
                )

                if len(resolved_uploaded_fcs_paths) == 1:
                    single_uploaded_fcs_path = resolved_uploaded_fcs_paths[0]

                    exported_bytes = self._build_calibrated_file_bytes(
                        uploaded_fcs_path=single_uploaded_fcs_path,
                        source_channel=source_channel,
                        output_channel=output_channel,
                        input_export_columns=input_export_columns,
                        calibration_payload=calibration_payload,
                    )

                    download_filename = self._build_export_filename(
                        uploaded_fcs_path=single_uploaded_fcs_path,
                        output_channel=output_channel,
                    )

                    logger.debug(
                        "Single-file calibration export succeeded with "
                        "download_filename=%r input_export_columns=%r "
                        "source_channel=%r output_channel=%r",
                        download_filename,
                        input_export_columns,
                        source_channel,
                        output_channel,
                    )

                    return (
                        (
                            f'Applied calibration "{selected_calibration}" to source channel '
                            f'"{source_channel}" for 1 file and exported result column '
                            f'"{output_channel}".'
                        ),
                        dcc.send_bytes(
                            exported_bytes,
                            download_filename,
                        ),
                    )

                zip_bytes = self._build_zip_of_calibrated_files(
                    uploaded_fcs_paths=resolved_uploaded_fcs_paths,
                    source_channel=source_channel,
                    output_channel=output_channel,
                    input_export_columns=input_export_columns,
                    calibration_payload=calibration_payload,
                )

                zip_filename = self._build_zip_filename(
                    output_channel=output_channel,
                    file_count=len(resolved_uploaded_fcs_paths),
                )

            except Exception as exc:
                logger.exception(
                    "Failed to apply and export calibration for uploaded_fcs_path=%r "
                    "selected_calibration=%r",
                    uploaded_fcs_path,
                    selected_calibration,
                )

                return (
                    f"Failed to apply and export calibration: {type(exc).__name__}: {exc}",
                    dash.no_update,
                )

            logger.debug(
                "Multi-file calibration export succeeded with zip_filename=%r "
                "input_export_columns=%r file_count=%r source_channel=%r "
                "output_channel=%r",
                zip_filename,
                input_export_columns,
                len(resolved_uploaded_fcs_paths),
                source_channel,
                output_channel,
            )

            return (
                (
                    f'Applied calibration "{selected_calibration}" to source channel '
                    f'"{source_channel}" for {len(resolved_uploaded_fcs_paths)} files '
                    f'and exported result column "{output_channel}".'
                ),
                dcc.send_bytes(
                    zip_bytes,
                    zip_filename,
                ),
            )

    @staticmethod
    def _resolve_first_uploaded_fcs_path(
        uploaded_fcs_path: Any,
    ) -> Optional[str]:
        """
        Resolve the first uploaded FCS path.
        """
        resolved_uploaded_fcs_paths = Apply._resolve_uploaded_fcs_paths(
            uploaded_fcs_path,
        )

        if not resolved_uploaded_fcs_paths:
            return None

        return resolved_uploaded_fcs_paths[0]

    @staticmethod
    def _resolve_uploaded_fcs_paths(
        uploaded_fcs_path: Any,
    ) -> list[str]:
        """
        Normalize uploaded FCS path payload into a list of paths.
        """
        if uploaded_fcs_path is None:
            return []

        if isinstance(uploaded_fcs_path, list):
            return [
                str(path)
                for path in uploaded_fcs_path
                if str(path).strip()
            ]

        resolved_single_path = str(
            uploaded_fcs_path,
        ).strip()

        if not resolved_single_path:
            return []

        return [
            resolved_single_path,
        ]

    @staticmethod
    def _normalize_export_columns(
        export_columns: Any,
    ) -> list[str]:
        """
        Normalize extra export columns.
        """
        if not isinstance(export_columns, list):
            return []

        return [
            str(column)
            for column in export_columns
            if str(column).strip()
        ]

    @staticmethod
    def _build_input_export_columns(
        *,
        source_channel: str,
        export_columns: list[str],
    ) -> list[str]:
        """
        Build input columns required to read from the source FCS file.

        The source channel is always included. Additional export columns are
        copied unchanged.
        """
        final_columns = [
            str(
                source_channel,
            )
        ]

        for column_name in export_columns:
            column_name_string = str(
                column_name,
            )

            if column_name_string != source_channel:
                final_columns.append(
                    column_name_string,
                )

        return final_columns

    @staticmethod
    def _resolve_calibration_file_path(
        selected_calibration: Any,
    ) -> Path:
        """
        Resolve a calibration picker value into an on disk path.
        """
        selected_calibration_str = str(
            selected_calibration,
        ).strip()

        if not selected_calibration_str:
            raise ValueError("Selected calibration path is empty.")

        folder_name, file_name = selected_calibration_str.split(
            "/",
            1,
        )

        if folder_name == "fluorescence":
            return Path(
                directories.fluorescence_calibration,
            ) / file_name

        if folder_name == "scattering":
            return Path(
                directories.scattering_calibration,
            ) / file_name

        raise ValueError(
            f'Unsupported calibration folder "{folder_name}".'
        )

    @staticmethod
    def _load_calibration_payload(
        calibration_file_path: Path,
    ) -> dict[str, Any]:
        """
        Load a saved calibration payload from disk.
        """
        record = json.loads(
            calibration_file_path.read_text(
                encoding="utf-8",
            )
        )

        if not isinstance(record, dict):
            raise ValueError("Calibration file root record is invalid.")

        outer_payload = record.get(
            "payload",
        )

        if not isinstance(outer_payload, dict):
            raise ValueError('Calibration file is missing top-level "payload".')

        logger.debug(
            "Loaded calibration file=%r with top-level payload keys=%r",
            str(calibration_file_path),
            list(outer_payload.keys()),
        )

        return outer_payload

    @staticmethod
    def _resolve_source_channel(
        calibration_payload: dict[str, Any],
    ) -> str:
        """
        Resolve the canonical source channel from a calibration payload.

        All saved calibration payloads should expose source_channel at the top
        level.
        """
        if not isinstance(calibration_payload, dict):
            return ""

        return str(
            calibration_payload.get(
                "source_channel",
                "",
            )
        ).strip()

    @staticmethod
    def _resolve_output_channel(
        *,
        source_channel: str,
        calibration_payload: dict[str, Any],
    ) -> str:
        """
        Resolve the output column name written to the exported FCS file.

        Scattering version 2 calibrations produce estimated optical coupling and
        therefore write a new derived column. Legacy calibrations preserve the
        old behavior and overwrite the source channel.
        """
        calibration_type = str(
            calibration_payload.get(
                "calibration_type",
                "",
            )
        ).strip()

        calibration_version = int(
            calibration_payload.get(
                "version",
                0,
            )
            or 0
        )

        output_quantity = str(
            calibration_payload.get(
                "output_quantity",
                "",
            )
        ).strip()

        if calibration_type == "scattering" and calibration_version >= 2:
            suffix = output_quantity or "estimated_coupling"

            return f"{source_channel}_{suffix}"

        return source_channel

    @staticmethod
    def _apply_calibration_to_series(
        *,
        values: np.ndarray,
        calibration_payload: dict[str, Any],
    ) -> np.ndarray:
        """
        Apply a calibration payload to a one dimensional source channel array.

        Supported schemas:
        - scattering version 2 with instrument_response
        - legacy log model
        - legacy top level slope/intercept model
        - legacy top level scale/offset model
        """
        values_array = np.asarray(
            values,
            dtype=float,
        )

        if not isinstance(calibration_payload, dict):
            raise ValueError("Calibration payload must be a dictionary.")

        calibration_type = str(
            calibration_payload.get(
                "calibration_type",
                "",
            )
        ).strip()

        calibration_version = int(
            calibration_payload.get(
                "version",
                0,
            )
            or 0
        )

        if calibration_type == "scattering" and calibration_version >= 2:
            return Apply._apply_scattering_v2_calibration_to_series(
                values=values_array,
                calibration_payload=calibration_payload,
            )

        return Apply._apply_legacy_calibration_to_series(
            values=values_array,
            calibration_payload=calibration_payload,
        )

    @staticmethod
    def _apply_scattering_v2_calibration_to_series(
        *,
        values: np.ndarray,
        calibration_payload: dict[str, Any],
    ) -> np.ndarray:
        """
        Apply a scattering version 2 instrument response calibration.
        """
        instrument_response = calibration_payload.get(
            "instrument_response",
        )

        if not isinstance(instrument_response, dict):
            raise ValueError(
                'Scattering calibration payload is missing "instrument_response".'
            )

        slope_value = instrument_response.get(
            "slope",
        )

        intercept_value = instrument_response.get(
            "intercept",
            0.0,
        )

        if slope_value is None:
            raise ValueError(
                'Scattering calibration instrument_response is missing "slope".'
            )

        slope = float(
            slope_value,
        )

        intercept = float(
            intercept_value,
        )

        values_array = np.asarray(
            values,
            dtype=float,
        )

        return slope * values_array + intercept

    @staticmethod
    def _apply_legacy_calibration_to_series(
        *,
        values: np.ndarray,
        calibration_payload: dict[str, Any],
    ) -> np.ndarray:
        """
        Apply legacy fluorescence and simple linear calibration payloads.
        """
        values_array = np.asarray(
            values,
            dtype=float,
        )

        nested_parameters = calibration_payload.get(
            "parameters",
        )

        if not isinstance(nested_parameters, dict):
            nested_parameters = {}

        nested_payload = calibration_payload.get(
            "payload",
        )

        if not isinstance(nested_payload, dict):
            nested_payload = {}

        fit_model = str(
            calibration_payload.get(
                "fit_model",
                "",
            )
        ).strip()

        nested_model = str(
            nested_payload.get(
                "model",
                "",
            )
        ).strip()

        resolved_model = fit_model or nested_model

        if "log10(y)=slope*log10(x)+intercept" in resolved_model:
            slope_value = nested_parameters.get(
                "slope",
                nested_payload.get(
                    "slope",
                ),
            )

            intercept_value = nested_parameters.get(
                "intercept",
                nested_payload.get(
                    "intercept",
                ),
            )

            prefactor_value = nested_parameters.get(
                "prefactor",
                nested_payload.get(
                    "prefactor",
                ),
            )

            if slope_value is None or intercept_value is None:
                raise ValueError(
                    "Log calibration payload is missing slope or intercept."
                )

            slope = float(
                slope_value,
            )

            intercept = float(
                intercept_value,
            )

            prefactor = (
                float(
                    prefactor_value,
                )
                if prefactor_value is not None
                else float(
                    10 ** intercept,
                )
            )

            if np.any(values_array < 0):
                raise ValueError("Log calibration cannot be applied to negative values.")

            calibrated_values = np.zeros_like(
                values_array,
                dtype=float,
            )

            positive_mask = values_array > 0

            calibrated_values[positive_mask] = prefactor * np.power(
                values_array[positive_mask],
                slope,
            )

            calibrated_values[~positive_mask] = 0.0

            return calibrated_values

        top_level_slope = calibration_payload.get(
            "slope",
        )

        top_level_intercept = calibration_payload.get(
            "intercept",
        )

        if top_level_slope is not None and top_level_intercept is not None:
            slope = float(
                top_level_slope,
            )

            intercept = float(
                top_level_intercept,
            )

            return slope * values_array + intercept

        top_level_scale = calibration_payload.get(
            "scale",
        )

        if top_level_scale is not None:
            scale = float(
                top_level_scale,
            )

            offset = float(
                calibration_payload.get(
                    "offset",
                    0.0,
                )
            )

            return scale * values_array + offset

        raise ValueError(
            (
                "Unsupported calibration payload format. Expected scattering version 2 "
                'with "instrument_response", a log model, "slope"/"intercept", '
                'or "scale"/"offset".'
            )
        )

    def _build_calibrated_file_bytes(
        self,
        *,
        uploaded_fcs_path: str,
        source_channel: str,
        output_channel: str,
        input_export_columns: list[str],
        calibration_payload: dict[str, Any],
    ) -> bytes:
        """
        Build calibrated FCS bytes for one uploaded file.
        """
        with FCSFile(str(uploaded_fcs_path), writable=False) as input_fcs_file:
            export_dataframe = input_fcs_file.dataframe_copy(
                columns=input_export_columns,
                dtype=float,
                deep=True,
            )

            calibrated_values = self._apply_calibration_to_series(
                values=export_dataframe[source_channel].to_numpy(
                    copy=True,
                ),
                calibration_payload=calibration_payload,
            )

            export_dataframe[output_channel] = calibrated_values

            builder = FCSFile.builder_from_dataframe(
                export_dataframe,
                template=input_fcs_file,
                force_float32=True,
            )

            return builder.build_bytes()

    def _build_zip_of_calibrated_files(
        self,
        *,
        uploaded_fcs_paths: list[str],
        source_channel: str,
        output_channel: str,
        input_export_columns: list[str],
        calibration_payload: dict[str, Any],
    ) -> bytes:
        """
        Build a ZIP file containing calibrated FCS files.
        """
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(
            zip_buffer,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
        ) as zip_file:
            for uploaded_fcs_path in uploaded_fcs_paths:
                logger.debug(
                    "Processing uploaded_fcs_path=%r for batch calibration export",
                    uploaded_fcs_path,
                )

                exported_bytes = self._build_calibrated_file_bytes(
                    uploaded_fcs_path=uploaded_fcs_path,
                    source_channel=source_channel,
                    output_channel=output_channel,
                    input_export_columns=input_export_columns,
                    calibration_payload=calibration_payload,
                )

                member_filename = self._build_export_filename(
                    uploaded_fcs_path=uploaded_fcs_path,
                    output_channel=output_channel,
                )

                zip_file.writestr(
                    member_filename,
                    exported_bytes,
                )

        zip_buffer.seek(
            0,
        )

        return zip_buffer.getvalue()

    @staticmethod
    def _build_export_filename(
        *,
        uploaded_fcs_path: str,
        output_channel: str,
    ) -> str:
        """
        Build an exported FCS filename.
        """
        input_path = Path(
            str(
                uploaded_fcs_path,
            )
        )

        safe_output_channel = Apply._safe_filename_fragment(
            output_channel,
        )

        return f"{input_path.stem}_calibrated_{safe_output_channel}.fcs"

    @staticmethod
    def _build_zip_filename(
        *,
        output_channel: str,
        file_count: int,
    ) -> str:
        """
        Build an exported ZIP filename.
        """
        safe_output_channel = Apply._safe_filename_fragment(
            output_channel,
        )

        return f"calibrated_{file_count}_files_{safe_output_channel}.zip"

    @staticmethod
    def _safe_filename_fragment(
        value: Any,
    ) -> str:
        """
        Convert a string into a filename safe fragment.
        """
        return (
            str(
                value,
            )
            .replace("/", "_")
            .replace("\\", "_")
            .replace(" ", "_")
            .replace(":", "_")
        )