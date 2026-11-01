"""FCS DATA and TEXT serialization helpers."""

import logging
import numpy as np
import pandas as pd
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class FCSBuilder:
    dataframe: pd.DataFrame
    keywords: dict[str, Any]
    detectors: dict[int, dict[str, Any]]
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

    def _event_dtype_and_names(self) -> tuple[np.dtype, list[str]]:
        datatype = str(self.keywords.get("$DATATYPE", "F")).strip().upper()
        endian_prefix = self._endian_prefix()
        number_of_parameters = int(self.keywords["$PAR"])

        fields: list[tuple[str, np.dtype]] = []
        names: list[str] = []

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
        flat: dict[str, Any] = dict(self.keywords)
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

        ordered: list[str] = []

        for key in preferred:
            if key in flat and key not in ordered:
                ordered.append(key)

        for key in sorted(flat.keys()):
            if key not in ordered:
                ordered.append(key)

        parts: list[str] = []

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

        if (
            self.dataframe.shape[0] != expected_events
            or self.dataframe.shape[1] != expected_parameters
        ):
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
        version = (
            self.fcs_version
            if self.fcs_version in {"FCS2.0", "FCS3.0", "FCS3.1"}
            else "FCS3.1"
        )

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
