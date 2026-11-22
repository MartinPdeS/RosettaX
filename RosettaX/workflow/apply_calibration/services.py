
import numpy as np
from . import io
from .fluorescence import FluorescenceCalibration, apply_legacy_calibration_to_series
from .payload import CalibrationPayload
from .scattering import (
    ScatteringTargetModelParameters,
    apply_scattering_calibration_to_dataframe,
    build_scattering_output_columns,
)
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CalibrationApplication:
    """
    One calibration application mapped to its source channel.
    """

    selected_calibration: str
    calibration_payload: dict[str, Any]
    scattering_target_model_parameters: ScatteringTargetModelParameters | None = None


@dataclass(frozen=True)
class ApplyCalibrationRequest:
    """
    Request for applying one or more calibrations to one or more FCS files.
    """

    uploaded_fcs_paths: list[str]
    export_columns: list[str]
    calibrations: list[CalibrationApplication] = field(default_factory=list)


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

    if not request.calibrations:
        raise ValueError("At least one calibration file must be selected.")

    input_source_channels: list[str] = []
    output_channels: list[str] = []
    calibration_descriptions: list[str] = []
    warnings: list[str] = []
    source_channels_seen: set[str] = set()
    unresolved_calibration_applications: list[tuple[CalibrationApplication, CalibrationPayload]] = []

    for calibration_application in request.calibrations:
        if not calibration_application.selected_calibration:
            raise ValueError("A calibration file must be selected.")

        if (
            not isinstance(calibration_application.calibration_payload, dict)
            or not calibration_application.calibration_payload
        ):
            raise ValueError("Uploaded calibration payload is missing.")

        calibration = CalibrationPayload.from_value(value=calibration_application.calibration_payload)
        if (
            calibration.calibration_type == "scattering"
            and calibration.version is None
            and calibration.saved_payload.get("version") not in (None, "")
        ):
            raise ValueError("Scattering calibration version must be an integer.")

        source_channel = calibration.source_channel

        if not source_channel:
            raise ValueError('Calibration payload is missing "source_channel".')

        if source_channel in source_channels_seen:
            raise ValueError(
                f'More than one calibration targets source channel "{source_channel}".'
            )

        source_channels_seen.add(
            source_channel,
        )
        input_source_channels.append(
            source_channel,
        )

        unresolved_calibration_applications.append((calibration_application, calibration))

    input_export_columns = io.build_input_export_columns(
        source_channels=input_source_channels,
        export_columns=request.export_columns,
    )

    transformer_factories: list[Callable[[str], Callable[[Any], Any]]] = []
    reserved_output_names = set(input_export_columns)

    for calibration_application, calibration in unresolved_calibration_applications:
        source_channel = calibration.source_channel
        if calibration.is_scattering_v2:
            if calibration_application.scattering_target_model_parameters is None:
                raise ValueError(
                    "Scattering target model parameters are required for scattering calibration."
                )

            default_output_columns = build_scattering_output_columns(
                source_channel=source_channel,
            )
            resolved_output_channels = [
                resolve_unique_output_channel_name(
                    preferred_name=calibration.output_channel_name or default_output_columns.mie_equivalent_diameter_nm,
                    reserved_names=reserved_output_names.union(
                        {
                            default_output_columns.estimated_coupling,
                        },
                    ),
                ),
            ]
        else:
            resolved_output_channels = [
                resolve_unique_output_channel_name(
                    preferred_name=calibration.output_channel_name or source_channel,
                    reserved_names=reserved_output_names,
                ),
            ]

        for output_channel in resolved_output_channels:
            reserved_output_names.add(output_channel)

            if output_channel not in output_channels:
                output_channels.append(
                    output_channel,
                )

        calibration_descriptions.append(
            f'{calibration_application.selected_calibration} -> "{", ".join(resolved_output_channels)}"'
        )
        transformer_factories.append(
            _build_calibration_transformer_factory(
                application=calibration_application,
                source_channel=source_channel,
                is_scattering=calibration.is_scattering_v2,
                output_channels=resolved_output_channels,
                calibration_payload=calibration,
                warnings=warnings,
            )
        )

    dataframe_transformer_factory = _combine_transformer_factories(transformer_factories=transformer_factories)

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
        selected_calibrations=calibration_descriptions,
        source_channels=input_source_channels,
        file_count=len(
            request.uploaded_fcs_paths,
        ),
        output_channels=output_channels,
        warnings=warnings,
    )

    return ApplyCalibrationFilesResult(
        payload_bytes=payload_bytes,
        download_filename=download_filename,
        source_channel=", ".join(input_source_channels),
        output_channels=output_channels,
        file_count=len(
            request.uploaded_fcs_paths,
        ),
        warnings=warnings,
        status=status,
    )


def build_multi_calibration_dataframe_transformer_factory(
    *,
    calibration_applications: list[tuple[CalibrationApplication, str, bool, list[str]]],
    warnings: list[str],
):
    """Build one dataframe transformer factory that applies calibrations in sequence."""
    return _combine_transformer_factories(
        transformer_factories=[
            _build_calibration_transformer_factory(
                application=application, source_channel=source_channel, is_scattering=is_scattering,
                output_channels=output_channels, calibration_payload=application.calibration_payload,
                warnings=warnings,
            )
            for application, source_channel, is_scattering, output_channels in calibration_applications
        ],
    )


def _build_calibration_transformer_factory(
    *,
    application: CalibrationApplication,
    source_channel: str,
    is_scattering: bool,
    output_channels: list[str],
    calibration_payload: dict[str, Any] | CalibrationPayload,
    warnings: list[str],
) -> Callable[[str], Callable[[Any], Any]]:
    """Build the per-file transformer for one calibration and its output names."""
    if is_scattering:
        return build_scattering_dataframe_transformer_factory(
            source_channel=source_channel, output_channel_names=output_channels,
            calibration_payload=calibration_payload,
            target_model_parameters=application.scattering_target_model_parameters,
        )

    if isinstance(calibration_payload, CalibrationPayload):
        calibration_payload = FluorescenceCalibration.from_payload(payload=calibration_payload.saved_payload)

    return build_legacy_dataframe_transformer_factory(
        source_channel=source_channel, output_channel_name=output_channels[0],
        calibration_payload=calibration_payload, warnings=warnings,
    )


def _combine_transformer_factories(
    *, transformer_factories: list[Callable[[str], Callable[[Any], Any]]],
) -> Callable[[str], Callable[[Any], Any]]:
    """Create one per-file transformer by composing the calibration transforms."""
    def dataframe_transformer_factory(uploaded_fcs_path: str):
        individual_transformers = [factory(uploaded_fcs_path) for factory in transformer_factories]

        def dataframe_transformer(
            dataframe: Any,
        ) -> Any:
            output_dataframe = dataframe

            for transformer in individual_transformers:
                output_dataframe = transformer(
                    output_dataframe,
                )

            return output_dataframe

        return dataframe_transformer

    return dataframe_transformer_factory


def build_scattering_dataframe_transformer_factory(
    *,
    source_channel: str,
    output_channel_names: list[str],
    calibration_payload: dict[str, Any] | CalibrationPayload,
    target_model_parameters: ScatteringTargetModelParameters,
):
    """
    Build a per-file dataframe transformer factory for scattering calibration.

    Returns a callable that accepts an FCS file path and itself returns a
    dataframe transformer function suitable for use with
    :func:`~RosettaX.workflow.apply_calibration.io.build_exported_fcs_bytes`.

    Parameters
    ----------
    source_channel : str
        Detector column to calibrate.
    calibration_payload : dict[str, Any] or CalibrationPayload
        Saved calibration data or its normalized representation for this run.
    target_model_parameters : ScatteringTargetModelParameters
        Target Mie model parameters for the scattering conversion.

    Returns
    -------
    Callable[[str], Callable[[Any], Any]]
        A factory function ``f(uploaded_fcs_path) -> transformer``.
    """

    def dataframe_transformer_factory(
        uploaded_fcs_path: str,
    ):
        """
        Return a dataframe transformer bound to *uploaded_fcs_path*.

        Parameters
        ----------
        uploaded_fcs_path : str
            Path to the FCS file being processed.

        Returns
        -------
        Callable[[Any], Any]
            Transformer that applies scattering calibration to a DataFrame.
        """
        def dataframe_transformer(
            dataframe: Any,
        ) -> Any:
            """
            Apply scattering calibration to *dataframe* and return the result.

            Parameters
            ----------
            dataframe : Any
                Pandas DataFrame loaded from the FCS file.

            Returns
            -------
            Any
                Transformed DataFrame with calibrated scattering columns.
            """
            result = apply_scattering_calibration_to_dataframe(
                dataframe=dataframe,
                source_channel=source_channel,
                output_channel_names=output_channel_names,
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
    output_channel_name: str,
    calibration_payload: dict[str, Any] | FluorescenceCalibration,
    warnings: list[str] | None = None,
):
    """
    Build a per-file dataframe transformer factory for legacy fluorescence calibration.

    Returns a callable that accepts an FCS file path and itself returns a
    dataframe transformer applying the power-law fluorescence calibration.

    Parameters
    ----------
    source_channel : str
        Detector column to calibrate.
    calibration_payload : dict[str, Any] or FluorescenceCalibration
        Saved calibration data or the parsed fluorescence transformation.

    Returns
    -------
    Callable[[str], Callable[[Any], Any]]
        A factory function ``f(uploaded_fcs_path) -> transformer``.
    """

    def dataframe_transformer_factory(
        _uploaded_fcs_path: str,
    ):
        """
        Return a dataframe transformer (ignores the file path argument).

        Parameters
        ----------
        _uploaded_fcs_path : str
            Unused FCS file path (accepted for interface compatibility).

        Returns
        -------
        Callable[[Any], Any]
            Transformer that applies fluorescence calibration to a DataFrame.
        """
        def dataframe_transformer(
            dataframe: Any,
        ) -> Any:
            """
            Apply legacy fluorescence calibration to *dataframe*.

            Parameters
            ----------
            dataframe : Any
                Pandas DataFrame loaded from the FCS file.

            Returns
            -------
            Any
                Deep copy of *dataframe* with the source channel values
                replaced by calibrated intensities.
            """
            output_dataframe = dataframe.copy(
                deep=True,
            )

            values = output_dataframe[source_channel].to_numpy(
                copy=True,
            )

            output_dataframe[output_channel_name] = apply_legacy_calibration_to_series(
                values=np.asarray(
                    values,
                    dtype=float,
                ),
                calibration_payload=calibration_payload,
                warning_messages=warnings,
                source_channel=source_channel,
            )

            attach_detector_metadata_override(
                dataframe=output_dataframe,
                column_name=output_channel_name,
                detector_metadata={
                    "S": build_applied_output_long_name(
                        source_channel=source_channel,
                    ),
                },
            )

            return output_dataframe

        return dataframe_transformer

    return dataframe_transformer_factory


def resolve_source_channel(
    calibration_payload: dict[str, Any],
) -> str:
    """
    Resolve the canonical source channel name from a calibration payload.

    Checks the top-level ``"source_channel"`` key first.  If absent or empty,
    falls back to ``payload["instrument_response"]["measured_channel"]`` for
    legacy scattering calibration payloads.

    Parameters
    ----------
    calibration_payload : dict[str, Any]
        Loaded calibration JSON payload.

    Returns
    -------
    str
        Source channel name, or an empty string when not found.
    """
    return CalibrationPayload.from_value(value=calibration_payload).source_channel


def resolve_requested_output_channel_name(
    calibration_payload: dict[str, Any],
    *,
    default: str,
) -> str:
    """
    Resolve the preferred applied output channel short name from a calibration payload.
    """
    preferred_name = CalibrationPayload.from_value(value=calibration_payload).output_channel_name
    return preferred_name or str(default).strip()


def resolve_unique_output_channel_name(
    *,
    preferred_name: str,
    reserved_names: set[str],
) -> str:
    """
    Ensure an applied output channel name is unique among exported columns.
    """
    base_name = str(preferred_name or "").strip() or "Calibrated channel"
    candidate_name = base_name
    suffix = 2

    while candidate_name in reserved_names:
        candidate_name = f"{base_name} {suffix}"
        suffix += 1

    return candidate_name


def build_applied_output_long_name(
    *,
    source_channel: str,
) -> str:
    """
    Build the FCS long-name metadata for a calibrated output parameter.
    """
    return f"RosettaX based on {str(source_channel).strip()}"


def attach_detector_metadata_override(
    *,
    dataframe: Any,
    column_name: str,
    detector_metadata: dict[str, Any],
) -> None:
    """
    Attach detector metadata overrides consumed by the FCS builder.
    """
    attrs = getattr(dataframe, "attrs", {})

    existing_overrides = attrs.get(
        "fcs_detector_metadata_overrides",
        {},
    )

    normalized_overrides = (
        {
            str(name): dict(metadata)
            for name, metadata in existing_overrides.items()
            if isinstance(metadata, dict)
        }
        if isinstance(existing_overrides, dict)
        else {}
    )

    current_override = normalized_overrides.get(
        str(column_name),
        {},
    )
    current_override.update(
        {
            str(key): value
            for key, value in detector_metadata.items()
        }
    )
    normalized_overrides[str(column_name)] = current_override
    attrs["fcs_detector_metadata_overrides"] = normalized_overrides


def build_success_message(
    *,
    selected_calibrations: list[str],
    source_channels: list[str],
    file_count: int,
    output_channels: list[str],
    warnings: list[str],
) -> str:
    """
    Build a compact success message for the apply-calibration action.

    Parameters
    ----------
    selected_calibrations : list[str]
        Human-readable descriptions of the calibrations that were applied.
    source_channels : list[str]
        Detector columns that were calibrated.
    file_count : int
        Number of FCS files that were processed.
    output_channels : list[str]
        Names of the exported output columns.

    Returns
    -------
    str
        Human-readable success message for display in the UI.
    """
    output_channel_text = ", ".join(
        [
            f'"{output_channel}"'
            for output_channel in output_channels
        ]
    )

    source_channel_text = ", ".join(
        [
            f'"{source_channel}"'
            for source_channel in source_channels
        ]
    )

    calibration_text = "; ".join(selected_calibrations)

    status_message = (
        f"Applied calibration(s) {calibration_text} to source channel(s) "
        f"{source_channel_text} for {file_count} file(s). Exported column(s): "
        f"{output_channel_text}."
    )

    if warnings:
        warning_text = " ".join(
            str(warning).strip()
            for warning in warnings
            if str(warning).strip()
        )

        if warning_text:
            status_message = f"{status_message} Warning: {warning_text}"

    return status_message
