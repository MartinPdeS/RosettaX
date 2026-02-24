# -*- coding: utf-8 -*-

import mmap
import os
import re
import weakref
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple, List

import numpy as np
import pandas as pd


@dataclass
class FCSFile:
    """
    FCS reader exposing DATA as either:
      - dataframe_view: zero copy DataFrame backed by an mmap buffer (borrowed view)
      - dataframe_copy(): independent DataFrame (owned copy)

    Lifetime rule (strict):
      If you access dataframe_view (or any Series / NumPy view derived from it),
      you must ensure those objects are gone before close() or leaving a `with` block.

    This class therefore enforces close correctness: if exported buffers still exist,
    close raises RuntimeError with instructions.
    """

    file_path: str
    writable: bool = False

    header: Dict[str, Any] = field(init=False)
    text: Dict[str, Any] = field(init=False)
    delimiter: str = field(init=False)

    _file_handle: Any = field(init=False, default=None, repr=False)
    _mmap: Optional[mmap.mmap] = field(init=False, default=None, repr=False)
    _records: Optional[np.ndarray] = field(init=False, default=None, repr=False)
    _dataframe_view: Optional[pd.DataFrame] = field(init=False, default=None, repr=False)
    _finalizer: Any = field(init=False, default=None, repr=False)

    def __post_init__(self) -> None:
        self.file_path = str(self.file_path)
        self._validate_file()
        self.header = self._read_header()
        self.text, self.delimiter = self._read_text()
        self._open_mmap()

        # Safety net: do not rely on __del__, but try to prevent FD leaks if user forgets.
        self._finalizer = weakref.finalize(self, type(self)._best_effort_close, self)

    def __enter__(self) -> "FCSDataFrameFile":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        # Enforce correctness. If caller leaked view objects, raise.
        self.close()

    # ----------------------------
    # Public API
    # ----------------------------

    @property
    def dataframe_view(self) -> pd.DataFrame:
        """
        Zero copy DataFrame backed by mmap. Borrowed view.
        Only valid while the file is open and must not outlive the instance.
        """
        if self._dataframe_view is not None:
            return self._dataframe_view

        self._ensure_records_loaded()

        if self._records is None:
            raise RuntimeError("Internal error: records not loaded.")

        column_names = self._column_names()
        num_parameters = int(self.text["Keywords"]["$PAR"])

        columns: Dict[str, np.ndarray] = {}
        for parameter_index in range(1, num_parameters + 1):
            columns[column_names[parameter_index - 1]] = self._records[f"parameter_{parameter_index}"]

        dataframe = pd.DataFrame(columns, copy=False)

        dataframe.attrs["fcs_header"] = dict(self.header)
        dataframe.attrs["fcs_keywords"] = dict(self.text["Keywords"])
        dataframe.attrs["fcs_detectors"] = {k: dict(v) for k, v in self.text["Detectors"].items()}
        dataframe.attrs["fcs_delimiter"] = self.delimiter

        self._dataframe_view = dataframe
        return dataframe

    def dataframe_copy(self, *, deep: bool = True) -> pd.DataFrame:
        """
        Independent DataFrame that can outlive the file.
        This necessarily copies the DATA segment.
        """
        view = self.dataframe_view
        if deep:
            return view.copy(deep=True)
        return view.copy()

    def close(self) -> None:
        """
        Close mmap and file handle.

        Raises
        ------
        RuntimeError
            If there are still exported buffers referencing the mmap.
        """
        # Drop internal references first. This helps when only internal objects keep the export alive.
        self._dataframe_view = None
        self._records = None

        mmap_obj = self._mmap
        file_handle = self._file_handle

        self._mmap = None
        self._file_handle = None

        if mmap_obj is not None:
            try:
                mmap_obj.close()
            except BufferError as exc:
                # Put back, because close failed. This prevents half-closed state.
                self._mmap = mmap_obj
                self._file_handle = file_handle
                raise RuntimeError(
                    "Cannot close FCSDataFrameFile: there are still live NumPy or pandas views "
                    "referencing the underlying mmap buffer. "
                    "Delete the DataFrame returned by dataframe_view and any derived Series or arrays "
                    "(for example `del df_view`, `del series`, `del array`), then call close() again. "
                    "If you need data after closing, use dataframe_copy()."
                ) from exc

        if file_handle is not None:
            file_handle.close()

    # ----------------------------
    # Parsing helpers (kept inside class, not ad hoc globals)
    # ----------------------------

    def _validate_file(self) -> None:
        if not os.path.isfile(self.file_path):
            raise FileNotFoundError(f'"{os.path.basename(self.file_path)}" does not exist.')
        if os.path.getsize(self.file_path) < 257:
            raise FileNotFoundError(
                f'"{os.path.basename(self.file_path)}" is not a valid FCS file because it is too small.'
            )

    def _read_header(self) -> Dict[str, Any]:
        with open(self.file_path, "rb") as handle:
            header_bytes = handle.read(256)

        try:
            fcs_version = header_bytes[:6].decode("ascii")
        except UnicodeDecodeError as exc:
            raise FileNotFoundError(
                f'"{os.path.basename(self.file_path)}" is not a valid FCS file because the version cannot be decoded.'
            ) from exc

        if fcs_version not in {"FCS2.0", "FCS3.0", "FCS3.1"}:
            raise FileNotFoundError(
                f'"{os.path.basename(self.file_path)}" is not a valid FCS file because the version is invalid.'
            )

        try:
            text_start = int(header_bytes[10:18].strip() or b"0")
            text_end = int(header_bytes[18:26].strip() or b"0")
            data_start = int(header_bytes[26:34].strip() or b"0")
            data_end = int(header_bytes[34:42].strip() or b"0")
        except ValueError as exc:
            raise FileNotFoundError(
                f'"{os.path.basename(self.file_path)}" is not a valid FCS file because header offsets are invalid.'
            ) from exc

        return {
            "FCS version": fcs_version,
            "Text start": text_start,
            "Text end": text_end,
            "Data start": data_start,
            "Data end": data_end,
        }

    @staticmethod
    def _split_text_payload(payload: str, delimiter: str) -> List[str]:
        """
        Split TEXT payload (without leading delimiter), respecting FCS escaping:
        delimiter inside a token is escaped by doubling it.
        """
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
        text_start = int(self.header["Text start"])
        text_end = int(self.header["Text end"])

        if text_end <= text_start:
            raise FileNotFoundError(
                f'"{os.path.basename(self.file_path)}" is not a valid FCS file because TEXT bounds are invalid.'
            )

        length = text_end - text_start + 1
        with open(self.file_path, "rb") as handle:
            handle.seek(text_start)
            raw = handle.read(length)

        try:
            text_section = raw.decode("ascii", errors="strict")
        except UnicodeDecodeError as exc:
            raise FileNotFoundError(
                f'"{os.path.basename(self.file_path)}" is not a valid FCS file because TEXT cannot be decoded.'
            ) from exc

        if not text_section:
            raise FileNotFoundError(
                f'"{os.path.basename(self.file_path)}" is not a valid FCS file because TEXT is empty.'
            )

        delimiter = text_section[0]
        payload = text_section[1:]

        items = self._split_text_payload(payload, delimiter)

        # Trailing delimiter => trailing empty token(s). Drop them to keep alignment.
        while items and items[-1] == "":
            items.pop()

        if len(items) < 2:
            raise FileNotFoundError(
                f'"{os.path.basename(self.file_path)}" is not a valid FCS file because TEXT is malformed.'
            )

        if len(items) % 2 == 1:
            items = items[:-1]

        keywords: Dict[str, Any] = {}
        for index in range(0, len(items), 2):
            key = items[index].strip()
            value = items[index + 1].strip()

            if value.lstrip("-").isdigit():
                keywords[key] = int(value)
            else:
                keywords[key] = value

        parsed: Dict[str, Any] = {"Keywords": keywords, "Detectors": {}}
        self._group_detectors(parsed)

        return parsed, delimiter

    def _group_detectors(self, parsed_text: Dict[str, Any]) -> None:
        keywords = parsed_text["Keywords"]
        detectors: Dict[int, Dict[str, Any]] = {}

        if "$PAR" not in keywords:
            raise FileNotFoundError(
                f'"{os.path.basename(self.file_path)}" is not a valid FCS file because $PAR is missing.'
            )

        num_parameters = int(keywords["$PAR"])
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

        for parameter_index in range(1, num_parameters + 1):
            detectors.setdefault(parameter_index, {})

        parsed_text["Detectors"] = detectors

    def _open_mmap(self) -> None:
        mode = "r+b" if self.writable else "rb"
        self._file_handle = open(self.file_path, mode)
        access = mmap.ACCESS_WRITE if self.writable else mmap.ACCESS_READ
        self._mmap = mmap.mmap(self._file_handle.fileno(), 0, access=access)

    @staticmethod
    def _endian_prefix(byteord: str) -> str:
        byteord = str(byteord).strip()
        if byteord == "1,2,3,4":
            return "<"
        if byteord == "4,3,2,1":
            return ">"
        raise ValueError(f'Unsupported $BYTEORD "{byteord}".')

    @staticmethod
    def _dtype_for_parameter(datatype: str, bits: int, endian_prefix: str) -> np.dtype:
        datatype = str(datatype).strip().upper()
        bits = int(bits)

        if bits % 8 != 0:
            raise ValueError(f"$PnB must be byte aligned, got {bits} bits.")

        nbytes = bits // 8

        if datatype == "I":
            if nbytes == 1:
                return np.dtype(endian_prefix + "u1")
            if nbytes == 2:
                return np.dtype(endian_prefix + "u2")
            if nbytes == 4:
                return np.dtype(endian_prefix + "u4")
            if nbytes == 8:
                return np.dtype(endian_prefix + "u8")
            raise ValueError(f"Unsupported integer width: {bits} bits")

        if datatype == "F":
            if bits != 32:
                raise ValueError("For $DATATYPE=F, expected $PnB=32.")
            return np.dtype(endian_prefix + "f4")

        if datatype == "D":
            if bits != 64:
                raise ValueError("For $DATATYPE=D, expected $PnB=64.")
            return np.dtype(endian_prefix + "f8")

        raise ValueError(f'Unsupported $DATATYPE "{datatype}".')

    def _event_dtype(self) -> np.dtype:
        keywords = self.text["Keywords"]
        detectors = self.text["Detectors"]

        if str(keywords.get("$MODE", "L")).strip().upper() != "L":
            raise ValueError('Only $MODE="L" is supported.')

        num_parameters = int(keywords["$PAR"])
        datatype = str(keywords["$DATATYPE"]).strip().upper()
        endian_prefix = self._endian_prefix(str(keywords.get("$BYTEORD", "1,2,3,4")))

        fields: List[Tuple[str, np.dtype]] = []
        for parameter_index in range(1, num_parameters + 1):
            detector = detectors.get(parameter_index, {})
            bits = int(detector.get("B", keywords.get(f"$P{parameter_index}B", 32)))
            dt = self._dtype_for_parameter(datatype, bits, endian_prefix)
            fields.append((f"parameter_{parameter_index}", dt))

        return np.dtype(fields)

    def _column_names(self) -> List[str]:
        detectors = self.text["Detectors"]
        num_parameters = int(self.text["Keywords"]["$PAR"])
        names: List[str] = []
        for parameter_index in range(1, num_parameters + 1):
            names.append(str(detectors.get(parameter_index, {}).get("N", f"P{parameter_index}")))
        return names

    def _resolve_data_bounds(self, expected_bytes: int) -> Tuple[int, int]:
        """
        Choose between header offsets and TEXT offsets using expected size validation.
        """
        keywords = self.text["Keywords"]
        file_size = os.path.getsize(self.file_path)

        candidates: List[Tuple[int, int, str]] = []

        header_start = int(self.header.get("Data start", 0))
        header_end = int(self.header.get("Data end", 0))
        if header_start > 0 and header_end > 0:
            candidates.append((header_start, header_end, "header"))

        if "$BEGINDATA" in keywords and "$ENDDATA" in keywords:
            candidates.append((int(keywords["$BEGINDATA"]), int(keywords["$ENDDATA"]), "text"))

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

        for start, end, _src in candidates:
            ns, ne = normalize(start, end)
            if is_valid(ns, ne):
                return ns, ne

        name = os.path.basename(self.file_path)
        raise FileNotFoundError(
            f'"{name}" is not a valid FCS file because DATA bounds are invalid or too small for expected payload.'
        )

    def _ensure_records_loaded(self) -> None:
        if self._records is not None:
            return
        if self._mmap is None:
            raise RuntimeError("File is closed.")

        keywords = self.text["Keywords"]
        num_events = int(keywords["$TOT"])

        event_dtype = self._event_dtype()
        bytes_per_event = event_dtype.itemsize
        expected_bytes = num_events * bytes_per_event

        data_start, data_end = self._resolve_data_bounds(expected_bytes=expected_bytes)

        # Use exactly expected_bytes (ignore any extra trailing bytes in DATA segment)
        mv = memoryview(self._mmap)[data_start : data_start + expected_bytes]
        self._records = np.frombuffer(mv, dtype=event_dtype, count=num_events)

    @staticmethod
    def _best_effort_close(instance: "FCSDataFrameFile") -> None:
        """
        Finalizer fallback: do not raise. Try to close if possible.
        """
        try:
            instance._dataframe_view = None
            instance._records = None
            if instance._mmap is not None:
                try:
                    instance._mmap.close()
                except BufferError:
                    # Cannot safely close, leave it to OS at process exit.
                    pass
                instance._mmap = None
            if instance._file_handle is not None:
                try:
                    instance._file_handle.close()
                except Exception:
                    pass
                instance._file_handle = None
        except Exception:
            pass

    # ----------------------------
    # Writing support (round trip)
    # ----------------------------

    @classmethod
    def builder_from_dataframe(
        cls,
        dataframe: pd.DataFrame,
        *,
        template: Optional["FCSDataFrameFile"] = None,
        force_float32: bool = True,
    ) -> "FCSBuilder":
        if template is not None:
            keywords = dict(template.text["Keywords"])
            detectors = {k: dict(v) for k, v in template.text["Detectors"].items()}
            delimiter = template.delimiter
            version = str(template.header.get("FCS version", "FCS3.1"))
        else:
            keywords = {"$MODE": "L", "$BYTEORD": "1,2,3,4", "$DATATYPE": "F"}
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
        raise ValueError(f'Unsupported $BYTEORD "{byteord}".')

    def _dtype_for_parameter(self, datatype: str, bits: int, endian_prefix: str) -> np.dtype:
        datatype = str(datatype).strip().upper()
        bits = int(bits)

        if bits % 8 != 0:
            raise ValueError(f"$PnB must be byte aligned, got {bits} bits.")

        nbytes = bits // 8

        if datatype == "I":
            if nbytes == 1:
                return np.dtype(endian_prefix + "u1")
            if nbytes == 2:
                return np.dtype(endian_prefix + "u2")
            if nbytes == 4:
                return np.dtype(endian_prefix + "u4")
            if nbytes == 8:
                return np.dtype(endian_prefix + "u8")
            raise ValueError(f"Unsupported integer width: {bits} bits")

        if datatype == "F":
            if bits != 32:
                raise ValueError("For $DATATYPE=F, expected $PnB=32.")
            return np.dtype(endian_prefix + "f4")

        if datatype == "D":
            if bits != 64:
                raise ValueError("For $DATATYPE=D, expected $PnB=64.")
            return np.dtype(endian_prefix + "f8")

        raise ValueError(f'Unsupported $DATATYPE "{datatype}".')

    def _event_dtype_and_names(self) -> Tuple[np.dtype, List[str]]:
        datatype = str(self.keywords.get("$DATATYPE", "F")).strip().upper()
        endian_prefix = self._endian_prefix()
        num_parameters = int(self.keywords["$PAR"])

        fields: List[Tuple[str, np.dtype]] = []
        names: List[str] = []
        for parameter_index in range(1, num_parameters + 1):
            detector = self.detectors[parameter_index]
            name = str(detector.get("N", f"P{parameter_index}"))
            bits = int(detector.get("B", 32))
            dt = self._dtype_for_parameter(datatype, bits, endian_prefix)
            fields.append((f"parameter_{parameter_index}", dt))
            names.append(name)

        return np.dtype(fields), names

    def _escape_token(self, token: Any) -> str:
        token_str = str(token)

        # Empty tokens create "//" in TEXT which is ambiguous with the escape sequence for a literal delimiter.
        # Encode empties as a single space. The reader strips values, so it round trips back to "".
        if token_str == "":
            token_str = " "

        return token_str.replace(self.delimiter, self.delimiter + self.delimiter)

    def _build_text_segment(self) -> bytes:
        flat: Dict[str, Any] = dict(self.keywords)
        num_parameters = int(flat["$PAR"])

        for parameter_index in range(1, num_parameters + 1):
            detector = self.detectors[parameter_index]
            for suffix, value in detector.items():
                flat[f"$P{parameter_index}{suffix}"] = value

        # Stable, readable ordering; semantics do not depend on order.
        preferred = ["$TOT", "$PAR", "$DATATYPE", "$BYTEORD", "$MODE", "$BEGINDATA", "$ENDDATA"]
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

        if self.dataframe.shape[0] != expected_events or self.dataframe.shape[1] != expected_parameters:
            raise ValueError("DataFrame shape does not match $TOT and $PAR.")

        records = np.empty(expected_events, dtype=event_dtype)
        for parameter_index, column_name in enumerate(column_names, start=1):
            column_values = self.dataframe[column_name].to_numpy(copy=False)
            records[f"parameter_{parameter_index}"] = column_values.astype(
                event_dtype[f"parameter_{parameter_index}"], copy=False
            )

        return records.tobytes(order="C")

    def build_bytes(self) -> bytes:
        version = self.fcs_version if self.fcs_version in {"FCS2.0", "FCS3.0", "FCS3.1"} else "FCS3.1"

        data_bytes = self._build_data_bytes()

        # First pass TEXT without begin/end, then compute offsets, then final TEXT.
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

        return bytes(header) + text_bytes + data_bytes

    def write(self, path: str) -> None:
        payload = self.build_bytes()
        with open(str(path), "wb") as handle:
            handle.write(payload)