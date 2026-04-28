# -*- coding: utf-8 -*-

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FCSMetadata:
    """
    Parsed FCS metadata.

    This object stores the metadata extracted from the FCS HEADER and TEXT
    sections. It intentionally does not own the event data.

    Responsibilities
    ----------------
    - Store header fields.
    - Store parsed TEXT keywords.
    - Store grouped detector metadata.
    - Expose column names.
    - Expose FCS version.
    - Expose detector voltages.
    """

    file_path: str
    header: dict[str, Any]
    text: dict[str, Any]
    delimiter: str

    @property
    def file_name(self) -> str:
        return Path(self.file_path).name

    @property
    def keywords(self) -> dict[str, Any]:
        keywords = self.text.get("Keywords", {})

        if isinstance(keywords, dict):
            return keywords

        logger.warning(
            "FCS metadata keywords are malformed for file_path=%r",
            self.file_path,
        )

        return {}

    @property
    def detectors(self) -> dict[int, dict[str, Any]]:
        detectors = self.text.get("Detectors", {})

        if isinstance(detectors, dict):
            return detectors

        logger.warning(
            "FCS metadata detectors are malformed for file_path=%r",
            self.file_path,
        )

        return {}

    @property
    def fcs_version(self) -> Optional[str]:
        version_value = self.header.get("FCS version")

        if version_value is None:
            version_value = self.keywords.get("$VERSION")

        if version_value is None:
            return None

        return str(version_value)

    @property
    def column_names(self) -> list[str]:
        number_of_parameters = int(self.keywords["$PAR"])

        column_names: list[str] = []

        for parameter_index in range(1, number_of_parameters + 1):
            detector = self.detectors.get(parameter_index, {})
            column_name = detector.get("N", f"P{parameter_index}")
            column_names.append(str(column_name))

        return column_names

    @property
    def detector_voltages(self) -> dict[str, Optional[float]]:
        detector_voltages: dict[str, Optional[float]] = {}

        for parameter_index, column_name in enumerate(self.column_names, start=1):
            detector = self.detectors.get(parameter_index, {})
            voltage_value = detector.get("V")

            detector_voltages[column_name] = self._coerce_optional_float(
                value=voltage_value,
                detector_name=column_name,
            )

        return detector_voltages

    def to_dataframe_attrs(self) -> dict[str, Any]:
        """
        Return metadata in the format attached to pandas DataFrame attrs.
        """
        return {
            "fcs_header": dict(self.header),
            "fcs_keywords": dict(self.keywords),
            "fcs_detectors": {
                parameter_index: dict(detector)
                for parameter_index, detector in self.detectors.items()
            },
            "fcs_delimiter": self.delimiter,
            "fcs_version": self.fcs_version,
            "fcs_column_names": list(self.column_names),
            "fcs_detector_voltages": dict(self.detector_voltages),
        }

    def to_dict(self) -> dict[str, Any]:
        """
        Return a JSON friendly metadata dictionary.
        """
        return {
            "file_path": self.file_path,
            "file_name": self.file_name,
            "header": dict(self.header),
            "keywords": dict(self.keywords),
            "detectors": {
                str(parameter_index): dict(detector)
                for parameter_index, detector in self.detectors.items()
            },
            "delimiter": self.delimiter,
            "fcs_version": self.fcs_version,
            "column_names": list(self.column_names),
            "detector_voltages": dict(self.detector_voltages),
        }

    def debug_summary(self) -> dict[str, Any]:
        """
        Return a compact summary useful in logs.
        """
        return {
            "file_name": self.file_name,
            "fcs_version": self.fcs_version,
            "number_of_events": self.keywords.get("$TOT"),
            "number_of_parameters": self.keywords.get("$PAR"),
            "datatype": self.keywords.get("$DATATYPE"),
            "mode": self.keywords.get("$MODE"),
            "byte_order": self.keywords.get("$BYTEORD"),
            "column_names": list(self.column_names),
            "detector_voltages": dict(self.detector_voltages),
        }

    @staticmethod
    def _coerce_optional_float(
        value: Any,
        detector_name: str,
    ) -> Optional[float]:
        if value is None:
            return None

        value_string = str(value).strip()

        if not value_string:
            return None

        try:
            return float(value_string)
        except ValueError:
            logger.debug(
                "Could not convert detector voltage to float for detector_name=%r, value=%r",
                detector_name,
                value,
            )

            return None