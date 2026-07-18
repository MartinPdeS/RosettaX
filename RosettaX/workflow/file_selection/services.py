"""File-selection behavior shared by multi-file workflows."""

from typing import Any

from .models import UploadedFile, UploadedFileBatch


def resolve_batch(value: UploadedFileBatch | dict[str, Any] | list[Any] | None) -> UploadedFileBatch:
    """Normalize serialized or typed batch state."""
    if isinstance(value, UploadedFileBatch):
        return value
    return UploadedFileBatch.from_value(value)


def build_file_options(
    value: UploadedFileBatch | dict[str, Any] | list[Any] | None,
) -> list[dict[str, str]]:
    """Build dropdown options for the files in an uploaded batch."""
    batch = resolve_batch(value)
    return [
        {"label": file.filename, "value": file.path}
        for file in batch.files
        if file.path
    ]


def resolve_selected_file(
    value: UploadedFileBatch | dict[str, Any] | list[Any] | None,
    *,
    current_path: Any = None,
) -> UploadedFile | None:
    """Keep the current selection when valid, otherwise select the first file."""
    batch = resolve_batch(value)
    current_path_string = str(current_path or "").strip()
    if current_path_string:
        for file in batch.files:
            if file.path == current_path_string:
                return file
    return batch.files[0] if batch.files else None


def build_channel_options(column_names: list[Any] | tuple[Any, ...]) -> list[dict[str, str]]:
    """Build dropdown options from compatible FCS channel names."""
    return [
        {"label": str(name), "value": str(name)}
        for name in column_names
        if str(name).strip()
    ]


def resolve_selected_channel(
    column_names: list[Any] | tuple[Any, ...],
    *,
    current_value: Any = None,
    fallback_index: int = 0,
) -> str | None:
    """Keep a valid channel selection or choose a bounded fallback."""
    names = [str(name) for name in column_names if str(name).strip()]
    current = str(current_value or "").strip()
    if current in names:
        return current
    if not names:
        return None
    index = min(max(int(fallback_index), 0), len(names) - 1)
    return names[index]
