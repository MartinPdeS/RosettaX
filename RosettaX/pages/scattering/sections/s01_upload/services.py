# -*- coding: utf-8 -*-

import base64
import logging
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import dash

from RosettaX.pages.scattering.backend import BackEnd
from RosettaX.utils.runtime_config import RuntimeConfig


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UploadState:
    uploaded_fcs_path: Any = dash.no_update
    uploaded_filename: Any = dash.no_update
    runtime_config_data: Any = dash.no_update


def write_upload_to_tempfile(*, contents: str, filename: str) -> str:
    logger.debug(
        "write_upload_to_tempfile called with filename=%r contents_type=%s",
        filename,
        type(contents).__name__,
    )

    _, encoded_content = contents.split(",", 1)
    raw_bytes = base64.b64decode(encoded_content)

    file_suffix = Path(filename).suffix or ".bin"
    temporary_directory = Path(tempfile.gettempdir()) / "rosettax_uploads"
    temporary_directory.mkdir(parents=True, exist_ok=True)

    temporary_file_path = temporary_directory / f"{next(tempfile._get_candidate_names())}{file_suffix}"
    temporary_file_path.write_bytes(raw_bytes)

    logger.debug(
        "write_upload_to_tempfile wrote temporary_file_path=%r byte_count=%r",
        str(temporary_file_path),
        len(raw_bytes),
    )

    return str(temporary_file_path)


def build_upload_state(
    *,
    page: Any,
    contents: Optional[str],
    filename: Optional[str],
    runtime_config_data: Optional[dict[str, Any]],
) -> UploadState:
    logger.debug(
        "build_upload_state called with has_contents=%r filename=%r",
        bool(contents),
        filename,
    )

    runtime_config = RuntimeConfig.from_dict(runtime_config_data)

    if not contents or not filename:
        logger.debug("No upload payload provided. Returning empty UploadState.")
        return UploadState(
            uploaded_fcs_path=None,
            uploaded_filename=None,
            runtime_config_data=runtime_config.to_dict(),
        )

    try:
        uploaded_fcs_path = write_upload_to_tempfile(
            contents=contents,
            filename=filename,
        )

        runtime_config.update_paths(
            **{
                "files.scattering_fcs_file_path": uploaded_fcs_path,
            }
        )

        page.backend = BackEnd(
            fcs_file_path=uploaded_fcs_path,
        )

        logger.debug(
            "Created scattering backend for uploaded_fcs_path=%r",
            uploaded_fcs_path,
        )

        return UploadState(
            uploaded_fcs_path=uploaded_fcs_path,
            uploaded_filename=str(filename),
            runtime_config_data=runtime_config.to_dict(),
        )

    except Exception:
        logger.exception(
            "Failed to build upload state for filename=%r",
            filename,
        )
        page.backend = None

        return UploadState(
            uploaded_fcs_path=None,
            uploaded_filename=None,
            runtime_config_data=runtime_config.to_dict(),
        )