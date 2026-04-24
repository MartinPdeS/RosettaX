# -*- coding: utf-8 -*-

import base64
import logging
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from RosettaX.pages.fluorescence.backend import BackEnd
from RosettaX.utils import service
from RosettaX.utils.runtime_config import RuntimeConfig


@dataclass(frozen=True)
class UploadState:
    uploaded_fcs_path: Any
    uploaded_filename: Any
    scattering_detector_options: list[dict[str, Any]]
    scattering_detector_value: Any
    fluorescence_detector_options: list[dict[str, Any]]
    fluorescence_detector_value: Any
    runtime_config_data: dict[str, Any]

    def to_tuple(self) -> tuple[Any, Any, Any, Any, Any, Any, Any]:
        return (
            self.uploaded_fcs_path,
            self.uploaded_filename,
            self.scattering_detector_options,
            self.scattering_detector_value,
            self.fluorescence_detector_options,
            self.fluorescence_detector_value,
            self.runtime_config_data,
        )


def clean_optional_string(value: Any) -> Optional[str]:
    if value is None:
        return None

    cleaned_value = str(value).strip()

    if not cleaned_value:
        return None

    if cleaned_value.lower() == "none":
        return None

    return cleaned_value


def build_loaded_filename_text(stored_filename: Any) -> str:
    cleaned_filename = clean_optional_string(stored_filename)

    if not cleaned_filename:
        return ""

    return f"Loaded file: {cleaned_filename}"


def write_upload_to_tempfile(
    *,
    contents: str,
    filename: str,
) -> str:
    """
    Decode Dash upload contents and write them to a temporary file.

    The uploaded suffix is preserved so FCS readers that rely on file extension
    continue to behave normally.
    """
    try:
        _, encoded_content = contents.split(",", 1)
    except ValueError as exception:
        raise ValueError("Upload contents must contain a base64 payload.") from exception

    raw_bytes = base64.b64decode(encoded_content)

    file_suffix = Path(filename).suffix or ".bin"
    temporary_directory = Path(tempfile.gettempdir()) / "rosettax_uploads"
    temporary_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=file_suffix,
        dir=temporary_directory,
    ) as temporary_file:
        temporary_file.write(raw_bytes)
        temporary_file_path = Path(temporary_file.name)

    return str(temporary_file_path)


def pick_dropdown_value(
    *,
    preferred_value: Optional[str],
    current_value: Optional[str],
    options: list[dict[str, Any]],
) -> Optional[str]:
    allowed_values = {
        str(option.get("value"))
        for option in options
        if "value" in option
    }

    if preferred_value is not None and preferred_value in allowed_values:
        return preferred_value

    if current_value is not None and current_value in allowed_values:
        return current_value

    if options:
        return str(options[0].get("value"))

    return None


def build_empty_upload_state(
    *,
    runtime_config: RuntimeConfig,
    uploaded_fcs_path: Any = None,
    uploaded_filename: Any = "",
) -> UploadState:
    return UploadState(
        uploaded_fcs_path=uploaded_fcs_path,
        uploaded_filename=uploaded_filename,
        scattering_detector_options=[],
        scattering_detector_value=None,
        fluorescence_detector_options=[],
        fluorescence_detector_value=None,
        runtime_config_data=runtime_config.to_dict(),
    )


def resolve_selected_file(
    *,
    contents: Optional[str],
    stored_fcs_path: Optional[str],
    filename: Optional[str],
    stored_filename: Optional[str],
    logger: logging.Logger,
) -> tuple[Optional[str], str]:
    if contents and filename:
        selected_fcs_path = write_upload_to_tempfile(
            contents=contents,
            filename=filename,
        )
        display_filename = filename

        logger.debug(
            "Resolved uploaded file to temporary path selected_fcs_path=%r display_filename=%r",
            selected_fcs_path,
            display_filename,
        )
        return selected_fcs_path, display_filename

    if stored_fcs_path:
        selected_fcs_path = stored_fcs_path
        display_filename = stored_filename or Path(selected_fcs_path).name

        logger.debug(
            "Resolved stored file selected_fcs_path=%r display_filename=%r",
            selected_fcs_path,
            display_filename,
        )
        return selected_fcs_path, display_filename

    logger.debug("No uploaded or stored FCS file could be resolved.")
    return None, ""


def initialize_backend(
    *,
    page: Any,
    selected_fcs_path: str,
    logger: logging.Logger,
) -> bool:
    try:
        page.backend = BackEnd(
            selected_fcs_path,
        )
        logger.debug(
            "Initialized fluorescence backend for selected_fcs_path=%r",
            selected_fcs_path,
        )
        return True
    except Exception:
        logger.exception(
            "Failed to initialize fluorescence backend for selected_fcs_path=%r",
            selected_fcs_path,
        )
        page.backend = None
        return False


def extract_channel_options(
    *,
    selected_fcs_path: str,
    logger: logging.Logger,
):
    channels = service.build_channel_options_from_file(
        selected_fcs_path,
    )

    logger.debug(
        "Extracted channel options successfully for selected_fcs_path=%r",
        selected_fcs_path,
    )

    return channels


def resolve_detector_values(
    *,
    runtime_config: RuntimeConfig,
    channels: Any,
    current_scattering_detector_value: Optional[str],
    current_fluorescence_detector_value: Optional[str],
) -> tuple[list[dict[str, Any]], Any, list[dict[str, Any]], Any]:
    scattering_detector_options = list(channels.scatter_options or [])
    fluorescence_detector_options = list(channels.secondary_options or [])

    preferred_scattering_detector = clean_optional_string(
        runtime_config.get_path(
            "page_defaults.fluorescence.scattering_detector",
            default=None,
        )
    )
    preferred_fluorescence_detector = clean_optional_string(
        runtime_config.get_path(
            "page_defaults.fluorescence.fluorescence_detector",
            default=None,
        )
    )

    scattering_detector_value = pick_dropdown_value(
        preferred_value=preferred_scattering_detector,
        current_value=current_scattering_detector_value,
        options=scattering_detector_options,
    )

    if scattering_detector_value is None:
        scattering_detector_value = pick_dropdown_value(
            preferred_value=None,
            current_value=clean_optional_string(channels.scatter_value),
            options=scattering_detector_options,
        )

    fluorescence_detector_value = pick_dropdown_value(
        preferred_value=preferred_fluorescence_detector,
        current_value=current_fluorescence_detector_value,
        options=fluorescence_detector_options,
    )

    if fluorescence_detector_value is None:
        fluorescence_detector_value = pick_dropdown_value(
            preferred_value=None,
            current_value=clean_optional_string(channels.fluorescence_value),
            options=fluorescence_detector_options,
        )

    return (
        scattering_detector_options,
        scattering_detector_value,
        fluorescence_detector_options,
        fluorescence_detector_value,
    )


def build_upload_state(
    *,
    page: Any,
    contents: Optional[str],
    stored_fcs_path: Optional[str],
    filename: Optional[str],
    stored_filename: Optional[str],
    current_scattering_detector_value: Optional[str],
    current_fluorescence_detector_value: Optional[str],
    runtime_config_data: Optional[dict[str, Any]],
    logger: logging.Logger,
) -> UploadState:
    runtime_config = RuntimeConfig.from_dict(
        runtime_config_data,
    )

    try:
        selected_fcs_path, display_filename = resolve_selected_file(
            contents=contents,
            stored_fcs_path=stored_fcs_path,
            filename=filename,
            stored_filename=stored_filename,
            logger=logger,
        )
    except Exception:
        logger.exception(
            "Failed while resolving selected file with filename=%r stored_fcs_path=%r",
            filename,
            stored_fcs_path,
        )
        page.backend = None
        return build_empty_upload_state(
            runtime_config=runtime_config,
        )

    if not selected_fcs_path:
        page.backend = None
        return build_empty_upload_state(
            runtime_config=runtime_config,
        )

    if not initialize_backend(
        page=page,
        selected_fcs_path=selected_fcs_path,
        logger=logger,
    ):
        return build_empty_upload_state(
            runtime_config=runtime_config,
            uploaded_fcs_path=selected_fcs_path,
            uploaded_filename=display_filename,
        )

    try:
        channels = extract_channel_options(
            selected_fcs_path=selected_fcs_path,
            logger=logger,
        )
    except Exception:
        logger.exception(
            "Failed to extract channel options from selected_fcs_path=%r",
            selected_fcs_path,
        )
        return build_empty_upload_state(
            runtime_config=runtime_config,
            uploaded_fcs_path=selected_fcs_path,
            uploaded_filename=display_filename,
        )

    runtime_config.update_paths(
        **{
            "files.fluorescence_fcs_file_path": selected_fcs_path,
        }
    )

    (
        scattering_detector_options,
        scattering_detector_value,
        fluorescence_detector_options,
        fluorescence_detector_value,
    ) = resolve_detector_values(
        runtime_config=runtime_config,
        channels=channels,
        current_scattering_detector_value=current_scattering_detector_value,
        current_fluorescence_detector_value=current_fluorescence_detector_value,
    )

    logger.debug(
        "Built upload state with uploaded_fcs_path=%r uploaded_filename=%r "
        "scattering_detector_value=%r fluorescence_detector_value=%r",
        selected_fcs_path,
        display_filename,
        scattering_detector_value,
        fluorescence_detector_value,
    )

    return UploadState(
        uploaded_fcs_path=selected_fcs_path,
        uploaded_filename=display_filename,
        scattering_detector_options=scattering_detector_options,
        scattering_detector_value=scattering_detector_value,
        fluorescence_detector_options=fluorescence_detector_options,
        fluorescence_detector_value=fluorescence_detector_value,
        runtime_config_data=runtime_config.to_dict(),
    )