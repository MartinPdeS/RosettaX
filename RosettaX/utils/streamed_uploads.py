# -*- coding: utf-8 -*-

import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO, Optional
from uuid import UUID, uuid4

from RosettaX.utils.upload_limits import format_upload_size, get_max_upload_bytes


STREAMED_UPLOAD_TOKEN_PREFIX = "rosettax-upload://"
STREAMED_UPLOAD_ERROR_PREFIX = "rosettax-upload-error://"
DEFAULT_STREAMED_UPLOAD_DIRECTORY = Path.home() / ".rosettax" / "uploads" / "staged"
DEFAULT_STREAM_CHUNK_BYTES = 1024 * 1024
ALLOWED_STREAMED_UPLOAD_EXTENSIONS = frozenset({".fcs", ".json"})


@dataclass(frozen=True)
class StreamedUpload:
    """One server-side upload referenced by an opaque browser token."""

    token: str
    file_path: Path
    filename: str
    size_bytes: int


def is_streamed_upload_token(value: Any) -> bool:
    """Return whether a callback value references a server-side upload."""
    return isinstance(value, str) and value.startswith(STREAMED_UPLOAD_TOKEN_PREFIX)


def build_streamed_upload_error_token(message: Any) -> str:
    """Build an error value that can travel through the existing Dash callback."""
    clean_message = str(message or "Upload failed.").strip() or "Upload failed."
    return f"{STREAMED_UPLOAD_ERROR_PREFIX}{clean_message}"


def raise_for_streamed_upload_error(value: Any) -> None:
    """Raise a user-facing error carried by the browser upload bridge."""
    if isinstance(value, str) and value.startswith(STREAMED_UPLOAD_ERROR_PREFIX):
        message = value.removeprefix(STREAMED_UPLOAD_ERROR_PREFIX).strip()
        raise ValueError(message or "Upload failed.")


def sanitize_streamed_upload_filename(filename: Any) -> str:
    """Normalize an uploaded filename without allowing path traversal."""
    filename_only = Path(str(filename or "").strip()).name
    safe_filename = re.sub(r"[^A-Za-z0-9._-]+", "_", filename_only).strip("._")

    if not safe_filename:
        raise ValueError("Uploaded file name is missing.")

    suffix = Path(safe_filename).suffix.lower()
    if suffix not in ALLOWED_STREAMED_UPLOAD_EXTENSIONS:
        allowed_text = ", ".join(sorted(ALLOWED_STREAMED_UPLOAD_EXTENSIONS))
        raise ValueError(
            f"Unsupported uploaded file type {suffix or '<none>'}. "
            f"Allowed file types: {allowed_text}."
        )

    return safe_filename


def stage_streamed_upload(
    *,
    stream: BinaryIO,
    filename: Any,
    content_length: Optional[int] = None,
    staging_directory: Path = DEFAULT_STREAMED_UPLOAD_DIRECTORY,
    max_upload_bytes: Optional[int] = None,
) -> StreamedUpload:
    """Stream one request body to disk without materializing it in memory."""
    resolved_max_upload_bytes = (
        get_max_upload_bytes() if max_upload_bytes is None else int(max_upload_bytes)
    )
    safe_filename = sanitize_streamed_upload_filename(filename)

    if content_length is not None and int(content_length) > resolved_max_upload_bytes:
        raise ValueError(
            "Upload exceeds the maximum supported size of "
            f"{format_upload_size(resolved_max_upload_bytes)}."
        )

    upload_identifier = uuid4().hex
    upload_directory = Path(staging_directory) / upload_identifier
    upload_directory.mkdir(parents=True, exist_ok=False)
    file_path = upload_directory / safe_filename
    size_bytes = 0

    try:
        with file_path.open("wb") as output_file:
            while True:
                chunk = stream.read(DEFAULT_STREAM_CHUNK_BYTES)
                if not chunk:
                    break

                size_bytes += len(chunk)
                if size_bytes > resolved_max_upload_bytes:
                    raise ValueError(
                        "Upload exceeds the maximum supported size of "
                        f"{format_upload_size(resolved_max_upload_bytes)}."
                    )

                output_file.write(chunk)

        if size_bytes == 0:
            raise ValueError("Uploaded file is empty.")

    except Exception:
        shutil.rmtree(upload_directory, ignore_errors=True)
        raise

    return StreamedUpload(
        token=f"{STREAMED_UPLOAD_TOKEN_PREFIX}{upload_identifier}",
        file_path=file_path,
        filename=safe_filename,
        size_bytes=size_bytes,
    )


def resolve_streamed_upload(
    token: Any,
    *,
    staging_directory: Path = DEFAULT_STREAMED_UPLOAD_DIRECTORY,
    max_upload_bytes: Optional[int] = None,
) -> StreamedUpload:
    """Resolve and validate an opaque upload token from a Dash callback."""
    raise_for_streamed_upload_error(token)

    if not is_streamed_upload_token(token):
        raise ValueError("Upload token is invalid.")

    token_identifier = str(token).removeprefix(STREAMED_UPLOAD_TOKEN_PREFIX)
    try:
        normalized_identifier = UUID(token_identifier).hex
    except (TypeError, ValueError, AttributeError) as error:
        raise ValueError("Upload token is invalid.") from error

    base_directory = Path(staging_directory).expanduser().resolve()
    upload_directory = (base_directory / normalized_identifier).resolve()
    if upload_directory.parent != base_directory or not upload_directory.is_dir():
        raise ValueError("Uploaded file is no longer available.")

    uploaded_files = [path for path in upload_directory.iterdir() if path.is_file()]
    if len(uploaded_files) != 1:
        raise ValueError("Uploaded file storage is invalid.")

    file_path = uploaded_files[0]
    resolved_file_path = file_path.resolve()
    if resolved_file_path.parent != upload_directory:
        raise ValueError("Uploaded file storage is invalid.")
    file_path = resolved_file_path
    safe_filename = sanitize_streamed_upload_filename(file_path.name)
    size_bytes = file_path.stat().st_size
    resolved_max_upload_bytes = (
        get_max_upload_bytes() if max_upload_bytes is None else int(max_upload_bytes)
    )
    if size_bytes > resolved_max_upload_bytes:
        raise ValueError(
            "Upload exceeds the maximum supported size of "
            f"{format_upload_size(resolved_max_upload_bytes)}."
        )

    return StreamedUpload(
        token=str(token),
        file_path=file_path,
        filename=safe_filename,
        size_bytes=size_bytes,
    )
