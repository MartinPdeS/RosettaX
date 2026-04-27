# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any, Optional

import numpy as np

from . import io

from .fluorescence import apply_legacy_calibration_to_series

from .scattering import (
    ScatteringTargetModelParameters,
    apply_scattering_calibration_to_dataframe,
    build_scattering_output_columns,
    calibration_is_scattering_v2
)

@dataclass(frozen=True)
class ApplyCalibrationRequest:
    """
    Request for applying one calibration to one or more FCS files.
    """

    uploaded_fcs_paths: list[str]
    selected_calibration: str
    export_columns: list[str]
    scattering_target_model_parameters: Optional[ScatteringTargetModelParameters] = None


@dataclass(frozen=True)
class ApplyCalibrationFilesResult:
    """
    Result of applying calibration to one or more FCS files.
    """

    payload_bytes: bytes
    download_filename: str
    source_channel: str
    output_channels: list[str]
    file_count: int
    warnings: list[str]
    status: str


def apply_calibration_to_fcs_files(
    *,
    request: ApplyCalibrationRequest,
) -> ApplyCalibrationFilesResult:
    """
    Apply a selected calibration to one or more FCS files and return export bytes.
    """
    if not request.uploaded_fcs_paths:
        raise ValueError("At least one uploaded FCS file is required.")

    if not request.selected_calibration:
        raise ValueError("A calibration file must be selected.")

    calibration_file_path = io.resolve_calibration_file_path(
        request.selected_calibration,
    )

    calibration_payload = io.load_calibration_payload(
        calibration_file_path,
    )

    source_channel = resolve_source_channel(
        calibration_payload,
    )

    if not source_channel:
        raise ValueError('Calibration payload is missing "source_channel".')

    input_export_columns = io.build_input_export_columns(
        source_channel=source_channel,
        export_columns=request.export_columns,
    )

    if calibration_is_scattering_v2(
        calibration_payload,
    ):
        if request.scattering_target_model_parameters is None:
            raise ValueError(
                "Scattering target model parameters are required for scattering calibration."
            )

        output_channels = build_scattering_output_columns(
            source_channel=source_channel,
        ).as_list()

        dataframe_transformer_factory = build_scattering_dataframe_transformer_factory(
            source_channel=source_channel,
            calibration_payload=calibration_payload,
            target_model_parameters=request.scattering_target_model_parameters,
        )

    else:
        output_channels = [
            source_channel,
        ]

        dataframe_transformer_factory = build_legacy_dataframe_transformer_factory(
            source_channel=source_channel,
            calibration_payload=calibration_payload,
        )

    if len(request.uploaded_fcs_paths) == 1:
        uploaded_fcs_path = request.uploaded_fcs_paths[0]

        payload_bytes = io.build_exported_fcs_bytes(
            uploaded_fcs_path=uploaded_fcs_path,
            input_export_columns=input_export_columns,
            dataframe_transformer=dataframe_transformer_factory(
                uploaded_fcs_path,
            ),
        )

        download_filename = io.build_export_filename(
            uploaded_fcs_path=uploaded_fcs_path,
            output_channels=output_channels,
        )

    else:
        payload_bytes = io.build_zip_of_exported_fcs_files(
            uploaded_fcs_paths=request.uploaded_fcs_paths,
            input_export_columns=input_export_columns,
            output_channels=output_channels,
            dataframe_transformer_factory=dataframe_transformer_factory,
        )

        download_filename = io.build_zip_filename(
            output_channels=output_channels,
            file_count=len(
                request.uploaded_fcs_paths,
            ),
        )

    status = build_success_message(
        selected_calibration=request.selected_calibration,
        source_channel=source_channel,
        file_count=len(
            request.uploaded_fcs_paths,
        ),
        output_channels=output_channels,
    )

    return ApplyCalibrationFilesResult(
        payload_bytes=payload_bytes,
        download_filename=download_filename,
        source_channel=source_channel,
        output_channels=output_channels,
        file_count=len(
            request.uploaded_fcs_paths,
        ),
        warnings=[],
        status=status,
    )


def build_scattering_dataframe_transformer_factory(
    *,
    source_channel: str,
    calibration_payload: dict[str, Any],
    target_model_parameters: ScatteringTargetModelParameters,
):
    """
    Build a dataframe transformer factory for scattering calibration.
    """

    def dataframe_transformer_factory(
        uploaded_fcs_path: str,
    ):
        def dataframe_transformer(
            dataframe: Any,
        ) -> Any:
            result = apply_scattering_calibration_to_dataframe(
                dataframe=dataframe,
                source_channel=source_channel,
                calibration_payload=calibration_payload,
                target_model_parameters=target_model_parameters,
                metadata={
                    "uploaded_fcs_path": str(
                        uploaded_fcs_path,
                    ),
                    "source_channel": source_channel,
                },
            )

            return result.dataframe

        return dataframe_transformer

    return dataframe_transformer_factory


def build_legacy_dataframe_transformer_factory(
    *,
    source_channel: str,
    calibration_payload: dict[str, Any],
):
    """
    Build a dataframe transformer factory for legacy fluorescence calibration.
    """

    def dataframe_transformer_factory(
        _uploaded_fcs_path: str,
    ):
        def dataframe_transformer(
            dataframe: Any,
        ) -> Any:
            output_dataframe = dataframe.copy(
                deep=True,
            )

            values = output_dataframe[source_channel].to_numpy(
                copy=True,
            )

            output_dataframe[source_channel] = apply_legacy_calibration_to_series(
                values=np.asarray(
                    values,
                    dtype=float,
                ),
                calibration_payload=calibration_payload,
            )

            return output_dataframe

        return dataframe_transformer

    return dataframe_transformer_factory


def resolve_source_channel(
    calibration_payload: dict[str, Any],
) -> str:
    """
    Resolve the canonical source channel from a calibration payload.
    """
    if not isinstance(calibration_payload, dict):
        return ""

    source_channel = str(
        calibration_payload.get(
            "source_channel",
            "",
        )
    ).strip()

    if source_channel:
        return source_channel

    instrument_response = calibration_payload.get(
        "instrument_response",
    )

    if isinstance(instrument_response, dict):
        measured_channel = str(
            instrument_response.get(
                "measured_channel",
                "",
            )
        ).strip()

        if measured_channel:
            return measured_channel

    return ""


def build_success_message(
    *,
    selected_calibration: Any,
    source_channel: str,
    file_count: int,
    output_channels: list[str],
) -> str:
    """
    Build a compact success message.
    """
    output_channel_text = ", ".join(
        [
            f'"{output_channel}"'
            for output_channel in output_channels
        ]
    )

    return (
        f'Applied calibration "{selected_calibration}" to source channel '
        f'"{source_channel}" for {file_count} file(s). Exported column(s): '
        f"{output_channel_text}."
    )