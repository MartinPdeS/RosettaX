# -*- coding: utf-8 -*-

import base64
import binascii
import logging
import re
from pathlib import Path
from typing import Any, Optional

from RosettaX.workflow.upload.models import UploadConfig
from RosettaX.workflow.upload.models import UploadState


DEFAULT_UPLOAD_DIRECTORY = Path.home() / ".rosettax" / "uploads"


def clean_optional_string(
    value: Any,
) -> Optional[str]:
    """
    Convert a value to a stripped string or None.
    """
    if value is None:
        return None

    clean_value = str(value).strip()

    if not clean_value:
        return None

    if clean_value.lower() == "none":
        return None

    return clean_value


def build_loaded_filename_text(
    filename: Optional[str],
) -> str:
    """
    Build the displayed uploaded filename text.
    """
    clean_filename = clean_optional_string(
        filename,
    )

    if clean_filename is None:
        return "No file loaded."

    return f"Loaded file: {clean_filename}"


def sanitize_filename(
    filename: Optional[str],
    *,
    fallback_filename: str = "uploaded_file.fcs",
) -> str:
    """
    Sanitize a filename before writing it to disk.
    """
    clean_filename = clean_optional_string(
        filename,
    )

    if clean_filename is None:
        return fallback_filename

    filename_only = Path(clean_filename).name

    safe_filename = re.sub(
        r"[^A-Za-z0-9._-]+",
        "_",
        filename_only,
    )

    safe_filename = safe_filename.strip(
        "._"
    )

    if not safe_filename:
        return fallback_filename

    return safe_filename


def decode_dash_upload_contents(
    contents: str,
) -> bytes:
    """
    Decode Dash upload contents.

    Dash upload payloads have the form:
        data:<mime>;base64,<payload>
    """
    if "," not in contents:
        raise ValueError(
            "Upload contents are malformed."
        )

    _metadata, encoded_payload = contents.split(
        ",",
        1,
    )

    try:
        return base64.b64decode(
            encoded_payload,
            validate=True,
        )
    except binascii.Error as error:
        raise ValueError(
            "Upload contents could not be decoded."
        ) from error


def resolve_upload_directory(
    config: UploadConfig,
) -> Path:
    """
    Resolve the upload directory for one upload workflow.
    """
    if config.upload_directory is not None:
        return Path(
            config.upload_directory,
        ).expanduser()

    return DEFAULT_UPLOAD_DIRECTORY


def save_uploaded_file(
    *,
    contents: str,
    filename: Optional[str],
    upload_directory: Path,
) -> Path:
    """
    Save one uploaded file and return its path.
    """
    upload_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    safe_filename = sanitize_filename(
        filename,
    )

    file_path = upload_directory / safe_filename

    file_bytes = decode_dash_upload_contents(
        contents,
    )

    file_path.write_bytes(
        file_bytes,
    )

    return file_path


def set_nested_dict_value(
    *,
    data: dict[str, Any],
    dotted_path: str,
    value: Any,
) -> dict[str, Any]:
    """
    Return a copy of data with one dotted path updated.

    Example
    -------
    files.fluorescence_fcs_file_path
    """
    next_data = dict(
        data or {}
    )

    path_parts = [
        part.strip()
        for part in dotted_path.split(".")
        if part.strip()
    ]

    if not path_parts:
        return next_data

    current_data = next_data

    for path_part in path_parts[:-1]:
        existing_value = current_data.get(
            path_part,
        )

        if not isinstance(existing_value, dict):
            existing_value = {}

        current_data[path_part] = dict(
            existing_value,
        )

        current_data = current_data[path_part]

    current_data[path_parts[-1]] = value

    return next_data


def build_upload_state(
    *,
    config: UploadConfig,
    contents: Optional[str],
    filename: Optional[str],
    stored_fcs_path: Optional[str],
    stored_filename: Optional[str],
    runtime_config_data: Optional[dict[str, Any]],
    logger: logging.Logger,
) -> UploadState:
    """
    Build the next upload state.

    If a new upload payload is present, it is saved to disk.
    Otherwise, the previous stored values are reused.
    """
    runtime_config_payload = (
        dict(runtime_config_data)
        if isinstance(runtime_config_data, dict)
        else {}
    )

    clean_contents = clean_optional_string(
        contents,
    )
    clean_filename = clean_optional_string(
        filename,
    )
    clean_stored_fcs_path = clean_optional_string(
        stored_fcs_path,
    )
    clean_stored_filename = clean_optional_string(
        stored_filename,
    )

    if clean_contents is None:
        logger.debug(
            "No new upload contents. Reusing stored_fcs_path=%r stored_filename=%r",
            clean_stored_fcs_path,
            clean_stored_filename,
        )

        next_runtime_config_payload = set_nested_dict_value(
            data=runtime_config_payload,
            dotted_path=config.runtime_config_output_path,
            value=clean_stored_fcs_path,
        )

        return UploadState(
            uploaded_fcs_path=clean_stored_fcs_path,
            uploaded_filename=clean_stored_filename,
            runtime_config_data=next_runtime_config_payload,
        )

    upload_directory = resolve_upload_directory(
        config,
    )

    saved_file_path = save_uploaded_file(
        contents=clean_contents,
        filename=clean_filename,
        upload_directory=upload_directory,
    )

    next_uploaded_filename = clean_filename or saved_file_path.name

    logger.debug(
        "Saved uploaded file to path=%r filename=%r",
        str(saved_file_path),
        next_uploaded_filename,
    )

    next_runtime_config_payload = set_nested_dict_value(
        data=runtime_config_payload,
        dotted_path=config.runtime_config_output_path,
        value=str(saved_file_path),
    )

    return UploadState(
        uploaded_fcs_path=str(saved_file_path),
        uploaded_filename=next_uploaded_filename,
        runtime_config_data=next_runtime_config_payload,
    )