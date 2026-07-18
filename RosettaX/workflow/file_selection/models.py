"""Typed state models for uploaded-file batches."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class UploadedFile:
    """One uploaded file and the metadata needed by page controls."""

    path: str
    filename: str
    column_names: tuple[str, ...] = ()
    number_of_events: int | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UploadedFile":
        path = str(data.get("path") or data.get("uploaded_fcs_path") or "").strip()
        filename = str(
            data.get("filename")
            or data.get("uploaded_filename")
            or Path(path).name
        )
        return cls(
            path=path,
            filename=filename,
            column_names=tuple(str(name) for name in data.get("column_names") or ()),
            number_of_events=data.get("number_of_events"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "filename": self.filename,
            "column_names": list(self.column_names),
            "number_of_events": self.number_of_events,
        }


@dataclass(frozen=True)
class UploadedFileBatch:
    """A compatible batch of uploaded files with shared channel metadata."""

    files: tuple[UploadedFile, ...]
    reference_column_names: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "UploadedFileBatch":
        if not isinstance(data, dict):
            return cls(files=())

        raw_files = data.get("files") or []
        files = tuple(
            UploadedFile.from_dict(item)
            for item in raw_files
            if isinstance(item, dict)
        )
        reference_columns = data.get("reference_column_names")
        if reference_columns is None:
            reference_columns = data.get("column_names") or data.get("available_channels") or ()

        return cls(
            files=files,
            reference_column_names=tuple(str(name) for name in reference_columns),
        )

    @classmethod
    def from_value(cls, value: Any) -> "UploadedFileBatch":
        """Normalize typed, serialized, and legacy path-list state."""
        if isinstance(value, cls):
            return value
        if isinstance(value, dict):
            return cls.from_dict(value)
        if isinstance(value, list):
            return cls(
                files=tuple(
                    UploadedFile(path=str(path), filename=Path(str(path)).name)
                    for path in value
                    if str(path).strip()
                )
            )
        return cls(files=())

    def to_dict(self) -> dict[str, Any]:
        return {
            "files": [file.to_dict() for file in self.files],
            "reference_column_names": list(self.reference_column_names),
            "number_of_files": len(self.files),
        }
