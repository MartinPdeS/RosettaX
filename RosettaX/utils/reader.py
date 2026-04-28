# -*- coding: utf-8 -*-

import logging
import mmap
import os
import re
import weakref
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, List

import numpy as np
import pandas as pd

from RosettaX.utils.fcs_metadata import FCSMetadata


logger = logging.getLogger(__name__)


@dataclass
class FCSFile:
    """
    Safe FCS reader.

    Design choice
    -------------
    This reader never exposes zero copy pandas or NumPy views backed by the mmap
    buffer. All public data accessors return owned copies so the file can always
    be closed safely.

    Recommended usage
    -----------------
    with FCSFile(path) as fcs:
        names = fcs.get_column_names()
        x = fcs.column_copy("FSC-A", dtype=float, n=200_000)
    """

    file_path: str | Path
    writable: bool = False

    header: Dict[str, Any] = field(init=False)
    text: Dict[str, Any] = field(init=False)
    delimiter: str = field(init=False)
    metadata: FCSMetadata = field(init=False)

    _file_handle: Any = field(init=False, default=None, repr=False)
    _mmap: Optional[mmap.mmap] = field(init=False, default=None, repr=False)
    _records: Optional[np.ndarray] = field(init=False, default=None, repr=False)
    _finalizer: Any = field(init=False, default=None, repr=False)

    def __post_init__(self) -> None:
        self.file_path = str(self.file_path)

        logger.debug(
            "Initializing FCSFile with file_path=%r, writable=%r",
            self.file_path,
            self.writable,
        )

        self._validate_file()

        self.header = self._read_header()
        self.text, self.delimiter = self._read_text()

        self.metadata = FCSMetadata(
            file_path=self.file_path,
            header=self.header,
            text=self.text,
            delimiter=self.delimiter,
        )

        logger.debug(
            "Parsed FCS metadata: %r",
            self.metadata.debug_summary(),
        )

        self._open_mmap()

        self._finalizer = weakref.finalize(
            self,
            type(self)._best_effort_close,
            self,
        )

    def __enter__(self) -> "FCSFile":
        logger.debug("Entering FCSFile context for file_path=%r", self.file_path)

        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc is not None:
            logger.debug(
                "Exiting FCSFile context with exception for file_path=%r, exception_type=%r, exception=%r",
                self.file_path,
                exc_type,
                exc,
            )
        else:
            logger.debug(
                "Exiting FCSFile context cleanly for file_path=%r",
                self.file_path,
            )

        self.close()

    def get_column_names(self) -> list[str]:
        return self.metadata.column_names

    def get_metadata(self) -> FCSMetadata:
        return self.metadata

    def get_detector_voltages(self) -> dict[str, Optional[float]]:
        return self.metadata.detector_voltages

    def column_copy(
        self,
        column_name: str,
        *,
        dtype: Any = float,
        n: int | None = None,
        start: int = 0,
    ) -> np.ndarray:
        """
        Return an owned NumPy array for one column.

        This always copies, so it is safe to use after the file closes.
        """
        logger.debug(
            "Copying FCS column for file_path=%r, column_name=%r, dtype=%r, n=%r, start=%r",
            self.file_path,
            column_name,
            dtype,
            n,
            start,
        )

        self._ensure_records_loaded()

        if self._records is None:
            message = "Internal error: records not loaded."
            logger.error(
                "%s file_path=%r",
                message,
                self.file_path,
            )
            raise RuntimeError(message)

        column_name = str(column_name)
        column_index = self._column_index_from_name(column_name)

        raw = self._records[f"parameter_{column_index}"]

        if dtype is None:
            owned = np.asarray(raw).copy()
        else:
            owned = np.asarray(raw, dtype=dtype).copy()

        if start:
            owned = owned[int(start) :]

        if n is not None:
            owned = owned[: int(n)]

        logger.debug(
            "Copied FCS column for file_path=%r, column_name=%r, result_shape=%r, result_dtype=%r",
            self.file_path,
            column_name,
            owned.shape,
            owned.dtype,
        )

        return owned

    def columns_copy(
        self,
        column_names: list[str],
        *,
        dtype: Any = float,
        n: int | None = None,
        start: int = 0,
    ) -> dict[str, np.ndarray]:
        """
        Return owned NumPy arrays for multiple columns.
        """
        logger.debug(
            "Copying FCS columns for file_path=%r, column_names=%r, dtype=%r, n=%r, start=%r",
            self.file_path,
            column_names,
            dtype,
            n,
            start,
        )

        result: dict[str, np.ndarray] = {}

        for name in list(column_names):
            result[str(name)] = self.column_copy(
                str(name),
                dtype=dtype,
                n=n,
                start=start,
            )

        return result

    def dataframe_copy(
        self,
        *,
        columns: list[str] | None = None,
        dtype: Any = float,
        n: int | None = None,
        start: int = 0,
        deep: bool = True,
    ) -> pd.DataFrame:
        """
        Return an owned DataFrame that can outlive the file.

        deep is kept for API compatibility, but this method always returns owned data.
        """
        if columns is None:
            columns = self.metadata.column_names

        logger.debug(
            "Copying FCS dataframe for file_path=%r, columns=%r, dtype=%r, n=%r, start=%r, deep=%r",
            self.file_path,
            columns,
            dtype,
            n,
            start,
            deep,
        )

        arrays = self.columns_copy(
            list(columns),
            dtype=dtype,
            n=n,
            start=start,
        )

        dataframe = pd.DataFrame(arrays, copy=False)

        for attribute_name, attribute_value in self.metadata.to_dataframe_attrs().items():
            dataframe.attrs[attribute_name] = attribute_value

        logger.debug(
            "Copied FCS dataframe for file_path=%r, shape=%r, columns=%r",
            self.file_path,
            dataframe.shape,
            list(dataframe.columns),
        )

        if deep:
            return dataframe.copy(deep=True)

        return dataframe

    def close(self) -> None:
        """
        Close mmap and file handle.

        Always safe because we never export mmap backed views.
        """
        logger.debug("Closing FCSFile for file_path=%r", self.file_path)

        mmap_obj = self._mmap
        file_handle = self._file_handle

        self._records = None
        self._mmap = None
        self._file_handle = None

        if mmap_obj is not None:
            try:
                mmap_obj.close()
            except Exception as exc:
                logger.warning(
                    "Failed to close mmap for file_path=%r: %s: %s",
                    self.file_path,
                    type(exc).__name__,
                    exc,
                )

        if file_handle is not None:
            try:
                file_handle.close()
            except Exception as exc:
                logger.warning(
                    "Failed to close file handle for file_path=%r: %s: %s",
                    self.file_path,
                    type(exc).__name__,
                    exc,
                )

    def _raise_file_error(
        self,
        message: str,
        *,
        exception: Exception | None = None,
    ) -> None:
        full_message = f'"{os.path.basename(self.file_path)}" {message}'

        if exception is None:
            logger.error(
                "Invalid FCS file: file_path=%r, reason=%s",
                self.file_path,
                full_message,
            )
            raise FileNotFoundError(full_message)

        logger.error(
            "Invalid FCS file: file_path=%r, reason=%s, exception_type=%s, exception=%s",
            self.file_path,
            full_message,
            type(exception).__name__,
            exception,
        )
        raise FileNotFoundError(full_message) from exception

    def _validate_file(self) -> None:
        logger.debug("Validating FCS file_path=%r", self.file_path)

        if not os.path.isfile(self.file_path):
            self._raise_file_error("does not exist.")

        file_size = os.path.getsize(self.file_path)

        if file_size < 257:
            self._raise_file_error(
                "is not a valid FCS file because it is too small."
            )

        logger.debug(
            "Validated FCS file_path=%r, file_size=%r bytes",
            self.file_path,
            file_size,
        )

    def _read_header(self) -> Dict[str, Any]:
        logger.debug("Reading FCS HEADER for file_path=%r", self.file_path)

        with open(self.file_path, "rb") as handle:
            header_bytes = handle.read(256)

        try:
            fcs_version = header_bytes[:6].decode("ascii")
        except UnicodeDecodeError as exc:
            self._raise_file_error(
                "is not a valid FCS file because the version cannot be decoded.",
                exception=exc,
            )

        if fcs_version not in {"FCS2.0", "FCS3.0", "FCS3.1"}:
            self._raise_file_error(
                "is not a valid FCS file because the version is invalid."
            )

        try:
            text_start = int(header_bytes[10:18].strip() or b"0")
            text_end = int(header_bytes[18:26].strip() or b"0")
            data_start = int(header_bytes[26:34].strip() or b"0")
            data_end = int(header_bytes[34:42].strip() or b"0")
        except ValueError as exc:
            self._raise_file_error(
                "is not a valid FCS file because header offsets are invalid.",
                exception=exc,
            )

        header = {
            "FCS version": fcs_version,
            "Text start": text_start,
            "Text end": text_end,
            "Data start": data_start,
            "Data end": data_end,
        }

        logger.debug(
            "Read FCS HEADER for file_path=%r, header=%r",
            self.file_path,
            header,
        )

        return header

    @staticmethod
    def _split_text_payload(payload: str, delimiter: str) -> List[str]:
        tokens: List[str] = []
        token_chars: List[str] = []

        index = 0

        while index < len(payload):
            ch = payload[index]

            if ch == delimiter:
                if index + 1 < len(payload) and payload[index + 1] == delimiter:
                    token_chars.append(delimiter)
                    index += 2
                    continue

                tokens.append("".join(token_chars))
                token_chars = []
                index += 1
                continue

            token_chars.append(ch)
            index += 1

        if token_chars:
            tokens.append("".join(token_chars))

        return tokens

    def _read_text(self) -> Tuple[Dict[str, Any], str]:
        logger.debug("Reading FCS TEXT for file_path=%r", self.file_path)

        text_start = int(self.header["Text start"])
        text_end = int(self.header["Text end"])

        if text_end <= text_start:
            self._raise_file_error(
                "is not a valid FCS file because TEXT bounds are invalid."
            )

        length = text_end - text_start + 1

        with open(self.file_path, "rb") as handle:
            handle.seek(text_start)
            raw = handle.read(length)

        try:
            text_section = raw.decode("ascii", errors="strict")
        except UnicodeDecodeError as exc:
            self._raise_file_error(
                "is not a valid FCS file because TEXT cannot be decoded.",
                exception=exc,
            )

        if not text_section:
            self._raise_file_error(
                "is not a valid FCS file because TEXT is empty."
            )

        delimiter = text_section[0]
        payload = text_section[1:]

        items = self._split_text_payload(payload, delimiter)

        while items and items[-1] == "":
            items.pop()

        if len(items) < 2:
            self._raise_file_error(
                "is not a valid FCS file because TEXT is malformed."
            )

        if len(items) % 2 == 1:
            logger.warning(
                "FCS TEXT contains an odd number of tokens. Dropping the last token for file_path=%r",
                self.file_path,
            )
            items = items[:-1]

        keywords: Dict[str, Any] = {}

        for index in range(0, len(items), 2):
            key = items[index].strip()
            value = items[index + 1].strip()

            if value.lstrip("-").isdigit():
                keywords[key] = int(value)
            else:
                keywords[key] = value

        parsed: Dict[str, Any] = {
            "Keywords": keywords,
            "Detectors": {},
        }

        self._group_detectors(parsed)

        logger.debug(
            "Read FCS TEXT for file_path=%r, delimiter=%r, number_of_keywords=%r, number_of_detectors=%r",
            self.file_path,
            delimiter,
            len(parsed["Keywords"]),
            len(parsed["Detectors"]),
        )

        return parsed, delimiter

    def _group_detectors(self, parsed_text: Dict[str, Any]) -> None:
        logger.debug("Grouping FCS detector keywords for file_path=%r", self.file_path)

        keywords = parsed_text["Keywords"]
        detectors: Dict[int, Dict[str, Any]] = {}

        if "$PAR" not in keywords:
            self._raise_file_error(
                "is not a valid FCS file because $PAR is missing."
            )

        number_of_parameters = int(keywords["$PAR"])
        parameter_pattern = re.compile(r"^\$P(\d+)([A-Z]+)$")

        keys_to_remove: List[str] = []

        for key, value in keywords.items():
            match = parameter_pattern.match(str(key))

            if match is None:
                continue

            parameter_index = int(match.group(1))
            suffix = match.group(2)

            detectors.setdefault(parameter_index, {})[suffix] = value
            keys_to_remove.append(key)

        for key in keys_to_remove:
            keywords.pop(key, None)

        for parameter_index in range(1, number_of_parameters + 1):
            detectors.setdefault(parameter_index, {})

        parsed_text["Detectors"] = detectors

        logger.debug(
            "Grouped FCS detectors for file_path=%r, number_of_parameters=%r, detector_indices=%r",
            self.file_path,
            number_of_parameters,
            sorted(detectors.keys()),
        )

    def _open_mmap(self) -> None:
        logger.debug(
            "Opening mmap for file_path=%r, writable=%r",
            self.file_path,
            self.writable,
        )

        mode = "r+b" if self.writable else "rb"
        access = mmap.ACCESS_WRITE if self.writable else mmap.ACCESS_READ

        try:
            self._file_handle = open(self.file_path, mode)
            self._mmap = mmap.mmap(
                self._file_handle.fileno(),
                0,
                access=access,
            )
        except Exception:
            logger.exception(
                "Failed to open mmap for file_path=%r, writable=%r",
                self.file_path,
                self.writable,
            )
            raise

        logger.debug("Opened mmap for file_path=%r", self.file_path)

    @staticmethod
    def _endian_prefix(byteord: str) -> str:
        byteord = str(byteord).strip()

        if byteord == "1,2,3,4":
            return "<"

        if byteord == "4,3,2,1":
            return ">"

        logger.error("Unsupported FCS $BYTEORD=%r", byteord)
        raise ValueError(f'Unsupported $BYTEORD "{byteord}".')

    @staticmethod
    def _dtype_for_parameter(datatype: str, bits: int, endian_prefix: str) -> np.dtype:
        datatype = str(datatype).strip().upper()
        bits = int(bits)

        if bits % 8 != 0:
            logger.error(
                "Invalid FCS parameter bit width. datatype=%r, bits=%r",
                datatype,
                bits,
            )
            raise ValueError(f"$PnB must be byte aligned, got {bits} bits.")

        number_of_bytes = bits // 8

        if datatype == "I":
            if number_of_bytes == 1:
                return np.dtype(endian_prefix + "u1")
            if number_of_bytes == 2:
                return np.dtype(endian_prefix + "u2")
            if number_of_bytes == 4:
                return np.dtype(endian_prefix + "u4")
            if number_of_bytes == 8:
                return np.dtype(endian_prefix + "u8")

            logger.error(
                "Unsupported FCS integer width. datatype=%r, bits=%r",
                datatype,
                bits,
            )
            raise ValueError(f"Unsupported integer width: {bits} bits")

        if datatype == "F":
            if bits != 32:
                logger.error(
                    "Invalid FCS float width for $DATATYPE=F. bits=%r",
                    bits,
                )
                raise ValueError("For $DATATYPE=F, expected $PnB=32.")

            return np.dtype(endian_prefix + "f4")

        if datatype == "D":
            if bits != 64:
                logger.error(
                    "Invalid FCS float width for $DATATYPE=D. bits=%r",
                    bits,
                )
                raise ValueError("For $DATATYPE=D, expected $PnB=64.")

            return np.dtype(endian_prefix + "f8")

        logger.error("Unsupported FCS $DATATYPE=%r", datatype)
        raise ValueError(f'Unsupported $DATATYPE "{datatype}".')

    def _event_dtype(self) -> np.dtype:
        keywords = self.text["Keywords"]
        detectors = self.text["Detectors"]

        mode = str(keywords.get("$MODE", "L")).strip().upper()

        if mode != "L":
            logger.error(
                "Unsupported FCS $MODE for file_path=%r, mode=%r",
                self.file_path,
                mode,
            )
            raise ValueError('Only $MODE="L" is supported.')

        number_of_parameters = int(keywords["$PAR"])
        datatype = str(keywords["$DATATYPE"]).strip().upper()
        endian_prefix = self._endian_prefix(str(keywords.get("$BYTEORD", "1,2,3,4")))

        fields: List[Tuple[str, np.dtype]] = []

        for parameter_index in range(1, number_of_parameters + 1):
            detector = detectors.get(parameter_index, {})
            bits = int(detector.get("B", keywords.get(f"$P{parameter_index}B", 32)))
            data_type = self._dtype_for_parameter(datatype, bits, endian_prefix)

            fields.append(
                (
                    f"parameter_{parameter_index}",
                    data_type,
                )
            )

        event_dtype = np.dtype(fields)

        logger.debug(
            "Built FCS event dtype for file_path=%r, dtype=%r, itemsize=%r",
            self.file_path,
            event_dtype,
            event_dtype.itemsize,
        )

        return event_dtype

    def _column_names(self) -> List[str]:
        return self.metadata.column_names

    def _column_index_from_name(self, column_name: str) -> int:
        column_names = self._column_names()

        try:
            index_zero_based = column_names.index(column_name)
        except ValueError as exc:
            logger.error(
                "FCS column not found for file_path=%r, column_name=%r, available_columns=%r",
                self.file_path,
                column_name,
                column_names,
            )
            raise KeyError(f'Column "{column_name}" not found.') from exc

        return index_zero_based + 1

    def _resolve_data_bounds(self, expected_bytes: int) -> Tuple[int, int]:
        keywords = self.text["Keywords"]
        file_size = os.path.getsize(self.file_path)

        logger.debug(
            "Resolving FCS DATA bounds for file_path=%r, expected_bytes=%r, file_size=%r",
            self.file_path,
            expected_bytes,
            file_size,
        )

        candidates: List[Tuple[int, int, str]] = []

        header_start = int(self.header.get("Data start", 0))
        header_end = int(self.header.get("Data end", 0))

        if header_start > 0 and header_end > 0:
            candidates.append(
                (
                    header_start,
                    header_end,
                    "header",
                )
            )

        if "$BEGINDATA" in keywords and "$ENDDATA" in keywords:
            candidates.append(
                (
                    int(keywords["$BEGINDATA"]),
                    int(keywords["$ENDDATA"]),
                    "text",
                )
            )

        def normalize(start: int, end: int) -> Tuple[int, int]:
            start = int(start)
            end = int(end)

            if end == file_size:
                end = file_size - 1

            return start, end

        def is_valid(start: int, end: int) -> bool:
            if start < 0 or end < 0:
                return False

            if start >= file_size:
                return False

            if end >= file_size:
                return False

            if end < start:
                return False

            segment_bytes = end - start + 1

            return segment_bytes >= expected_bytes

        for start, end, source_name in candidates:
            normalized_start, normalized_end = normalize(start, end)

            logger.debug(
                "Checking FCS DATA bounds candidate for file_path=%r, source=%r, start=%r, end=%r, normalized_start=%r, normalized_end=%r",
                self.file_path,
                source_name,
                start,
                end,
                normalized_start,
                normalized_end,
            )

            if is_valid(normalized_start, normalized_end):
                logger.debug(
                    "Resolved FCS DATA bounds for file_path=%r, source=%r, data_start=%r, data_end=%r",
                    self.file_path,
                    source_name,
                    normalized_start,
                    normalized_end,
                )

                return normalized_start, normalized_end

        logger.error(
            "Failed to resolve FCS DATA bounds for file_path=%r, expected_bytes=%r, candidates=%r",
            self.file_path,
            expected_bytes,
            candidates,
        )

        self._raise_file_error(
            "is not a valid FCS file because DATA bounds are invalid or too small for expected payload."
        )

    def _ensure_records_loaded(self) -> None:
        if self._records is not None:
            return

        if self._mmap is None:
            logger.error(
                "Cannot load FCS records because file is closed. file_path=%r",
                self.file_path,
            )
            raise RuntimeError("File is closed.")

        keywords = self.text["Keywords"]
        number_of_events = int(keywords["$TOT"])

        event_dtype = self._event_dtype()
        bytes_per_event = event_dtype.itemsize
        expected_bytes = number_of_events * bytes_per_event

        data_start, data_end = self._resolve_data_bounds(
            expected_bytes=expected_bytes,
        )

        logger.debug(
            "Loading FCS records for file_path=%r, number_of_events=%r, bytes_per_event=%r, expected_bytes=%r, data_start=%r, data_end=%r",
            self.file_path,
            number_of_events,
            bytes_per_event,
            expected_bytes,
            data_start,
            data_end,
        )

        memory_view = memoryview(self._mmap)[data_start : data_start + expected_bytes]
        self._records = np.frombuffer(
            memory_view,
            dtype=event_dtype,
            count=number_of_events,
        )

        logger.debug(
            "Loaded FCS records for file_path=%r, records_shape=%r, records_dtype=%r",
            self.file_path,
            self._records.shape,
            self._records.dtype,
        )

    @staticmethod
    def _best_effort_close(instance: "FCSFile") -> None:
        try:
            if instance._mmap is not None:
                try:
                    instance._mmap.close()
                except Exception:
                    logger.debug(
                        "Best effort close failed while closing mmap for file_path=%r",
                        instance.file_path,
                        exc_info=True,
                    )

                instance._mmap = None

            if instance._file_handle is not None:
                try:
                    instance._file_handle.close()
                except Exception:
                    logger.debug(
                        "Best effort close failed while closing file handle for file_path=%r",
                        instance.file_path,
                        exc_info=True,
                    )

                instance._file_handle = None

            instance._records = None

        except Exception:
            logger.debug(
                "Best effort close failed for file_path=%r",
                getattr(instance, "file_path", None),
                exc_info=True,
            )

    @classmethod
    def builder_from_dataframe(
        cls,
        dataframe: pd.DataFrame,
        *,
        template: Optional["FCSFile"] = None,
        force_float32: bool = True,
    ) -> "FCSBuilder":
        logger.debug(
            "Creating FCSBuilder from dataframe, dataframe_shape=%r, template_file_path=%r, force_float32=%r",
            dataframe.shape,
            getattr(template, "file_path", None),
            force_float32,
        )

        if template is not None:
            keywords = dict(template.text["Keywords"])
            detectors = {
                parameter_index: dict(detector)
                for parameter_index, detector in template.text["Detectors"].items()
            }
            delimiter = template.delimiter
            version = str(template.header.get("FCS version", "FCS3.1"))
        else:
            keywords = {
                "$MODE": "L",
                "$BYTEORD": "1,2,3,4",
                "$DATATYPE": "F",
            }
            detectors = {}
            delimiter = "|"
            version = "FCS3.1"

        keywords["$MODE"] = "L"
        keywords["$TOT"] = int(dataframe.shape[0])
        keywords["$PAR"] = int(dataframe.shape[1])

        if force_float32:
            keywords["$DATATYPE"] = "F"

        rebuilt_detectors: Dict[int, Dict[str, Any]] = {}

        for parameter_index, column_name in enumerate(list(dataframe.columns), start=1):
            detector = dict(detectors.get(parameter_index, {}))
            detector["N"] = str(column_name)

            if force_float32:
                detector["B"] = 32

            if "R" not in detector:
                values = dataframe[column_name].to_numpy(copy=False)

                if np.issubdtype(values.dtype, np.floating):
                    finite = values[np.isfinite(values)]
                    detector["R"] = float(max(1.0, float(np.max(finite)))) if finite.size else 1.0
                else:
                    detector["R"] = float(max(1, int(np.max(values)))) if values.size else 1.0

            rebuilt_detectors[parameter_index] = detector

        return FCSBuilder(
            dataframe=dataframe,
            keywords=keywords,
            detectors=rebuilt_detectors,
            delimiter=delimiter,
            fcs_version=version,
        )


@dataclass
class FCSBuilder:
    dataframe: pd.DataFrame
    keywords: Dict[str, Any]
    detectors: Dict[int, Dict[str, Any]]
    delimiter: str = "|"
    fcs_version: str = "FCS3.1"

    def _endian_prefix(self) -> str:
        byteord = str(self.keywords.get("$BYTEORD", "1,2,3,4")).strip()

        if byteord == "1,2,3,4":
            return "<"

        if byteord == "4,3,2,1":
            return ">"

        logger.error("Unsupported FCSBuilder $BYTEORD=%r", byteord)
        raise ValueError(f'Unsupported $BYTEORD "{byteord}".')

    def _dtype_for_parameter(
        self,
        datatype: str,
        bits: int,
        endian_prefix: str,
    ) -> np.dtype:
        datatype = str(datatype).strip().upper()
        bits = int(bits)

        if bits % 8 != 0:
            logger.error(
                "Invalid FCSBuilder parameter bit width. datatype=%r, bits=%r",
                datatype,
                bits,
            )
            raise ValueError(f"$PnB must be byte aligned, got {bits} bits.")

        number_of_bytes = bits // 8

        if datatype == "I":
            if number_of_bytes == 1:
                return np.dtype(endian_prefix + "u1")
            if number_of_bytes == 2:
                return np.dtype(endian_prefix + "u2")
            if number_of_bytes == 4:
                return np.dtype(endian_prefix + "u4")
            if number_of_bytes == 8:
                return np.dtype(endian_prefix + "u8")

            logger.error(
                "Unsupported FCSBuilder integer width. datatype=%r, bits=%r",
                datatype,
                bits,
            )
            raise ValueError(f"Unsupported integer width: {bits} bits")

        if datatype == "F":
            if bits != 32:
                logger.error(
                    "Invalid FCSBuilder float width for $DATATYPE=F. bits=%r",
                    bits,
                )
                raise ValueError("For $DATATYPE=F, expected $PnB=32.")

            return np.dtype(endian_prefix + "f4")

        if datatype == "D":
            if bits != 64:
                logger.error(
                    "Invalid FCSBuilder float width for $DATATYPE=D. bits=%r",
                    bits,
                )
                raise ValueError("For $DATATYPE=D, expected $PnB=64.")

            return np.dtype(endian_prefix + "f8")

        logger.error("Unsupported FCSBuilder $DATATYPE=%r", datatype)
        raise ValueError(f'Unsupported $DATATYPE "{datatype}".')

    def _event_dtype_and_names(self) -> Tuple[np.dtype, List[str]]:
        datatype = str(self.keywords.get("$DATATYPE", "F")).strip().upper()
        endian_prefix = self._endian_prefix()
        number_of_parameters = int(self.keywords["$PAR"])

        fields: List[Tuple[str, np.dtype]] = []
        names: List[str] = []

        for parameter_index in range(1, number_of_parameters + 1):
            detector = self.detectors[parameter_index]
            name = str(detector.get("N", f"P{parameter_index}"))
            bits = int(detector.get("B", 32))
            data_type = self._dtype_for_parameter(
                datatype,
                bits,
                endian_prefix,
            )

            fields.append(
                (
                    f"parameter_{parameter_index}",
                    data_type,
                )
            )
            names.append(name)

        event_dtype = np.dtype(fields)

        logger.debug(
            "Built FCSBuilder event dtype, dtype=%r, column_names=%r",
            event_dtype,
            names,
        )

        return event_dtype, names

    def _escape_token(self, token: Any) -> str:
        token_string = str(token)

        if token_string == "":
            token_string = " "

        return token_string.replace(
            self.delimiter,
            self.delimiter + self.delimiter,
        )

    def _build_text_segment(self) -> bytes:
        flat: Dict[str, Any] = dict(self.keywords)
        number_of_parameters = int(flat["$PAR"])

        for parameter_index in range(1, number_of_parameters + 1):
            detector = self.detectors[parameter_index]

            for suffix, value in detector.items():
                flat[f"$P{parameter_index}{suffix}"] = value

        preferred = [
            "$TOT",
            "$PAR",
            "$DATATYPE",
            "$BYTEORD",
            "$MODE",
            "$BEGINDATA",
            "$ENDDATA",
        ]

        ordered: List[str] = []

        for key in preferred:
            if key in flat and key not in ordered:
                ordered.append(key)

        for key in sorted(flat.keys()):
            if key not in ordered:
                ordered.append(key)

        parts: List[str] = []

        for key in ordered:
            parts.append(self._escape_token(key))
            parts.append(self._escape_token(flat[key]))

        text = self.delimiter + self.delimiter.join(parts) + self.delimiter

        return text.encode("ascii", errors="strict")

    def _build_data_bytes(self) -> bytes:
        event_dtype, column_names = self._event_dtype_and_names()

        expected_events = int(self.keywords["$TOT"])
        expected_parameters = int(self.keywords["$PAR"])

        logger.debug(
            "Building FCS DATA bytes, dataframe_shape=%r, expected_events=%r, expected_parameters=%r",
            self.dataframe.shape,
            expected_events,
            expected_parameters,
        )

        if self.dataframe.shape[0] != expected_events or self.dataframe.shape[1] != expected_parameters:
            logger.error(
                "DataFrame shape does not match FCS metadata. dataframe_shape=%r, expected_events=%r, expected_parameters=%r",
                self.dataframe.shape,
                expected_events,
                expected_parameters,
            )
            raise ValueError("DataFrame shape does not match $TOT and $PAR.")

        records = np.empty(expected_events, dtype=event_dtype)

        for parameter_index, column_name in enumerate(column_names, start=1):
            column_values = self.dataframe[column_name].to_numpy(copy=False)

            records[f"parameter_{parameter_index}"] = column_values.astype(
                event_dtype[f"parameter_{parameter_index}"],
                copy=False,
            )

        data_bytes = records.tobytes(order="C")

        logger.debug(
            "Built FCS DATA bytes, number_of_bytes=%r",
            len(data_bytes),
        )

        return data_bytes

    def build_bytes(self) -> bytes:
        version = self.fcs_version if self.fcs_version in {"FCS2.0", "FCS3.0", "FCS3.1"} else "FCS3.1"

        logger.debug(
            "Building FCS bytes, requested_version=%r, effective_version=%r",
            self.fcs_version,
            version,
        )

        data_bytes = self._build_data_bytes()

        text_bytes = self._build_text_segment()

        text_start = 256
        text_end = text_start + len(text_bytes) - 1
        data_start = text_end + 1
        data_end = data_start + len(data_bytes) - 1

        self.keywords["$BEGINDATA"] = int(data_start)
        self.keywords["$ENDDATA"] = int(data_end)

        text_bytes = self._build_text_segment()
        text_end = text_start + len(text_bytes) - 1
        data_start = text_end + 1
        data_end = data_start + len(data_bytes) - 1

        self.keywords["$BEGINDATA"] = int(data_start)
        self.keywords["$ENDDATA"] = int(data_end)

        text_bytes = self._build_text_segment()
        text_end = text_start + len(text_bytes) - 1
        data_start = text_end + 1
        data_end = data_start + len(data_bytes) - 1

        header = bytearray(b" " * 256)
        header[:6] = version.encode("ascii")

        def put_int(start: int, end: int, value: int) -> None:
            width = end - start
            header[start:end] = str(int(value)).rjust(width).encode("ascii")

        put_int(10, 18, text_start)
        put_int(18, 26, text_end)
        put_int(26, 34, data_start)
        put_int(34, 42, data_end)

        payload = bytes(header) + text_bytes + data_bytes

        logger.debug(
            "Built FCS payload, text_start=%r, text_end=%r, data_start=%r, data_end=%r, total_bytes=%r",
            text_start,
            text_end,
            data_start,
            data_end,
            len(payload),
        )

        return payload

    def write(self, path: str | Path) -> None:
        resolved_path = Path(path).expanduser()

        logger.debug(
            "Writing FCS file to path=%r",
            str(resolved_path),
        )

        payload = self.build_bytes()

        try:
            with open(str(resolved_path), "wb") as handle:
                handle.write(payload)
        except Exception:
            logger.exception(
                "Failed to write FCS file to path=%r",
                str(resolved_path),
            )
            raise

        logger.debug(
            "Wrote FCS file to path=%r, number_of_bytes=%r",
            str(resolved_path),
            len(payload),
        )