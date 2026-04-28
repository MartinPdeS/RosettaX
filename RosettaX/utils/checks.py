# -*- coding: utf-8 -*-

import logging
from pathlib import Path
from typing import Any, Optional

from RosettaX.utils.fcs_metadata import FCSMetadata
from RosettaX.utils.reader import FCSFile


logger = logging.getLogger(__name__)


class FCSMultiFileConsistencyChecker:
    """
    Check consistency across multiple FCS files.

    Responsibilities
    ----------------
    - Normalize input file paths.
    - Read FCS metadata once per file.
    - Compare column names against the first reference file.
    - Compare FCS versions against the first reference file.
    - Compare detector voltages against the first reference file.
    - Return JSON safe reports for Dash callbacks.
    """

    def __init__(self, file_paths: list[str]) -> None:
        self.file_paths = self._normalize_file_paths(file_paths=file_paths)
        self._metadata_by_file_path: dict[str, FCSMetadata] = {}

        logger.debug(
            "Initialized FCSMultiFileConsistencyChecker with file_paths=%r",
            self.file_paths,
        )

    @staticmethod
    def _normalize_file_paths(file_paths: list[str]) -> list[str]:
        normalized_file_paths = [
            str(Path(file_path).expanduser())
            for file_path in file_paths
            if str(file_path).strip()
        ]

        logger.debug(
            "Normalized FCS file paths. input_count=%r, normalized_count=%r",
            len(file_paths),
            len(normalized_file_paths),
        )

        return normalized_file_paths

    @staticmethod
    def _build_empty_column_name_consistency_report() -> dict[str, Any]:
        return {
            "are_all_files_consistent": True,
            "reference_file_path": None,
            "reference_column_names": [],
            "invalid_file_paths": [],
            "mismatch_details": [],
        }

    @staticmethod
    def _build_empty_version_consistency_report() -> dict[str, Any]:
        return {
            "are_all_files_consistent": True,
            "reference_file_path": None,
            "reference_fcs_version": None,
            "invalid_file_paths": [],
            "mismatch_details": [],
        }

    @staticmethod
    def _build_empty_detector_voltage_consistency_report() -> dict[str, Any]:
        return {
            "are_all_files_consistent": True,
            "reference_file_path": None,
            "reference_detector_voltages": {},
            "invalid_file_paths": [],
            "mismatch_details": [],
        }

    @classmethod
    def build_empty_consistency_report(cls) -> dict[str, Any]:
        column_name_consistency_report = cls._build_empty_column_name_consistency_report()
        version_consistency_report = cls._build_empty_version_consistency_report()
        detector_voltage_consistency_report = cls._build_empty_detector_voltage_consistency_report()

        return {
            "are_all_files_consistent": True,
            "reference_file_path": None,
            "reference_column_names": [],
            "reference_fcs_version": None,
            "reference_detector_voltages": {},
            "invalid_file_paths": [],
            "mismatch_details": [],
            "column_name_consistency": column_name_consistency_report,
            "version_consistency": version_consistency_report,
            "detector_voltage_consistency": detector_voltage_consistency_report,
        }

    def get_file_metadata(self, file_path: str) -> FCSMetadata:
        normalized_file_path = str(Path(file_path).expanduser())

        if normalized_file_path in self._metadata_by_file_path:
            logger.debug(
                "Using cached FCS metadata for file_path=%r",
                normalized_file_path,
            )

            return self._metadata_by_file_path[normalized_file_path]

        logger.debug(
            "Reading FCS metadata for file_path=%r",
            normalized_file_path,
        )

        try:
            with FCSFile(normalized_file_path, writable=False) as fcs_file:
                file_metadata = fcs_file.get_metadata()
        except Exception:
            logger.exception(
                "Failed to read FCS metadata for file_path=%r",
                normalized_file_path,
            )
            raise

        self._metadata_by_file_path[normalized_file_path] = file_metadata

        logger.debug(
            "Read FCS metadata for file_path=%r, summary=%r",
            normalized_file_path,
            file_metadata.debug_summary(),
        )

        return file_metadata

    def check_column_name_consistency(self) -> dict[str, Any]:
        logger.debug(
            "Checking FCS column name consistency for file_count=%r",
            len(self.file_paths),
        )

        if not self.file_paths:
            return self._build_empty_column_name_consistency_report()

        reference_file_path = self.file_paths[0]

        try:
            reference_file_metadata = self.get_file_metadata(reference_file_path)
        except Exception as exc:
            logger.error(
                "Could not read reference FCS columns for file_path=%r",
                reference_file_path,
                exc_info=True,
            )

            return {
                "are_all_files_consistent": False,
                "reference_file_path": reference_file_path,
                "reference_column_names": [],
                "invalid_file_paths": [reference_file_path],
                "mismatch_details": [
                    f"{Path(reference_file_path).name}: could not read columns "
                    f"({type(exc).__name__}: {exc})"
                ],
            }

        reference_column_name_tuple = tuple(reference_file_metadata.column_names)

        invalid_file_paths: list[str] = []
        mismatch_details: list[str] = []

        for current_file_path in self.file_paths[1:]:
            try:
                current_file_metadata = self.get_file_metadata(current_file_path)
            except Exception as exc:
                invalid_file_paths.append(current_file_path)
                mismatch_details.append(
                    f"{Path(current_file_path).name}: could not read columns "
                    f"({type(exc).__name__}: {exc})"
                )

                logger.error(
                    "Could not read FCS columns for file_path=%r",
                    current_file_path,
                    exc_info=True,
                )

                continue

            current_column_name_tuple = tuple(current_file_metadata.column_names)

            if current_column_name_tuple != reference_column_name_tuple:
                invalid_file_paths.append(current_file_path)
                mismatch_details.append(
                    f"{Path(current_file_path).name}: columns do not match "
                    f"{Path(reference_file_path).name}"
                )

                logger.warning(
                    "FCS column mismatch. reference_file_path=%r, current_file_path=%r, "
                    "reference_columns=%r, current_columns=%r",
                    reference_file_path,
                    current_file_path,
                    list(reference_column_name_tuple),
                    list(current_column_name_tuple),
                )

        report = {
            "are_all_files_consistent": len(invalid_file_paths) == 0,
            "reference_file_path": reference_file_path,
            "reference_column_names": list(reference_file_metadata.column_names),
            "invalid_file_paths": invalid_file_paths,
            "mismatch_details": mismatch_details,
        }

        logger.debug(
            "Finished FCS column name consistency check. report=%r",
            report,
        )

        return report

    def check_version_consistency(self) -> dict[str, Any]:
        logger.debug(
            "Checking FCS version consistency for file_count=%r",
            len(self.file_paths),
        )

        if not self.file_paths:
            return self._build_empty_version_consistency_report()

        reference_file_path = self.file_paths[0]

        try:
            reference_file_metadata = self.get_file_metadata(reference_file_path)
        except Exception as exc:
            logger.error(
                "Could not read reference FCS version for file_path=%r",
                reference_file_path,
                exc_info=True,
            )

            return {
                "are_all_files_consistent": False,
                "reference_file_path": reference_file_path,
                "reference_fcs_version": None,
                "invalid_file_paths": [reference_file_path],
                "mismatch_details": [
                    f"{Path(reference_file_path).name}: could not read FCS version "
                    f"({type(exc).__name__}: {exc})"
                ],
            }

        invalid_file_paths: list[str] = []
        mismatch_details: list[str] = []

        for current_file_path in self.file_paths[1:]:
            try:
                current_file_metadata = self.get_file_metadata(current_file_path)
            except Exception as exc:
                invalid_file_paths.append(current_file_path)
                mismatch_details.append(
                    f"{Path(current_file_path).name}: could not read FCS version "
                    f"({type(exc).__name__}: {exc})"
                )

                logger.error(
                    "Could not read FCS version for file_path=%r",
                    current_file_path,
                    exc_info=True,
                )

                continue

            if current_file_metadata.fcs_version != reference_file_metadata.fcs_version:
                invalid_file_paths.append(current_file_path)
                mismatch_details.append(
                    f"{Path(current_file_path).name}: FCS version does not match "
                    f"{Path(reference_file_path).name} "
                    f"({current_file_metadata.fcs_version} != "
                    f"{reference_file_metadata.fcs_version})"
                )

                logger.warning(
                    "FCS version mismatch. reference_file_path=%r, current_file_path=%r, "
                    "reference_version=%r, current_version=%r",
                    reference_file_path,
                    current_file_path,
                    reference_file_metadata.fcs_version,
                    current_file_metadata.fcs_version,
                )

        report = {
            "are_all_files_consistent": len(invalid_file_paths) == 0,
            "reference_file_path": reference_file_path,
            "reference_fcs_version": reference_file_metadata.fcs_version,
            "invalid_file_paths": invalid_file_paths,
            "mismatch_details": mismatch_details,
        }

        logger.debug(
            "Finished FCS version consistency check. report=%r",
            report,
        )

        return report

    def check_detector_voltage_consistency(self) -> dict[str, Any]:
        logger.debug(
            "Checking FCS detector voltage consistency for file_count=%r",
            len(self.file_paths),
        )

        if not self.file_paths:
            return self._build_empty_detector_voltage_consistency_report()

        reference_file_path = self.file_paths[0]

        try:
            reference_file_metadata = self.get_file_metadata(reference_file_path)
        except Exception as exc:
            logger.error(
                "Could not read reference FCS detector voltages for file_path=%r",
                reference_file_path,
                exc_info=True,
            )

            return {
                "are_all_files_consistent": False,
                "reference_file_path": reference_file_path,
                "reference_detector_voltages": {},
                "invalid_file_paths": [reference_file_path],
                "mismatch_details": [
                    f"{Path(reference_file_path).name}: could not read detector voltages "
                    f"({type(exc).__name__}: {exc})"
                ],
            }

        invalid_file_paths: list[str] = []
        mismatch_details: list[str] = []

        for current_file_path in self.file_paths[1:]:
            try:
                current_file_metadata = self.get_file_metadata(current_file_path)
            except Exception as exc:
                invalid_file_paths.append(current_file_path)
                mismatch_details.append(
                    f"{Path(current_file_path).name}: could not read detector voltages "
                    f"({type(exc).__name__}: {exc})"
                )

                logger.error(
                    "Could not read FCS detector voltages for file_path=%r",
                    current_file_path,
                    exc_info=True,
                )

                continue

            if current_file_metadata.detector_voltages != reference_file_metadata.detector_voltages:
                invalid_file_paths.append(current_file_path)

                voltage_mismatch_details = self._build_detector_voltage_mismatch_details(
                    reference_file_path=reference_file_path,
                    current_file_path=current_file_path,
                    reference_detector_voltages=reference_file_metadata.detector_voltages,
                    current_detector_voltages=current_file_metadata.detector_voltages,
                )

                mismatch_details.extend(voltage_mismatch_details)

                logger.warning(
                    "FCS detector voltage mismatch. reference_file_path=%r, current_file_path=%r, "
                    "reference_detector_voltages=%r, current_detector_voltages=%r",
                    reference_file_path,
                    current_file_path,
                    reference_file_metadata.detector_voltages,
                    current_file_metadata.detector_voltages,
                )

        report = {
            "are_all_files_consistent": len(invalid_file_paths) == 0,
            "reference_file_path": reference_file_path,
            "reference_detector_voltages": reference_file_metadata.detector_voltages,
            "invalid_file_paths": invalid_file_paths,
            "mismatch_details": mismatch_details,
        }

        logger.debug(
            "Finished FCS detector voltage consistency check. report=%r",
            report,
        )

        return report

    @staticmethod
    def _build_detector_voltage_mismatch_details(
        reference_file_path: str,
        current_file_path: str,
        reference_detector_voltages: dict[str, Optional[float]],
        current_detector_voltages: dict[str, Optional[float]],
    ) -> list[str]:
        mismatch_details: list[str] = []

        all_detector_names = sorted(
            set(reference_detector_voltages.keys())
            | set(current_detector_voltages.keys())
        )

        for detector_name in all_detector_names:
            reference_voltage = reference_detector_voltages.get(detector_name)
            current_voltage = current_detector_voltages.get(detector_name)

            if current_voltage == reference_voltage:
                continue

            mismatch_details.append(
                f"{Path(current_file_path).name}: detector voltage for "
                f"{detector_name} does not match {Path(reference_file_path).name} "
                f"({current_voltage} != {reference_voltage})"
            )

        return mismatch_details

    def check_multifiles_consistency(self) -> dict[str, Any]:
        logger.debug(
            "Checking complete FCS multi file consistency for file_paths=%r",
            self.file_paths,
        )

        if not self.file_paths:
            return self.build_empty_consistency_report()

        column_name_consistency_report = self.check_column_name_consistency()
        version_consistency_report = self.check_version_consistency()
        detector_voltage_consistency_report = self.check_detector_voltage_consistency()

        combined_invalid_file_paths = sorted(
            set(
                column_name_consistency_report["invalid_file_paths"]
                + version_consistency_report["invalid_file_paths"]
                + detector_voltage_consistency_report["invalid_file_paths"]
            )
        )

        combined_mismatch_details = (
            list(column_name_consistency_report["mismatch_details"])
            + list(version_consistency_report["mismatch_details"])
            + list(detector_voltage_consistency_report["mismatch_details"])
        )

        report = {
            "are_all_files_consistent": (
                column_name_consistency_report["are_all_files_consistent"]
                and version_consistency_report["are_all_files_consistent"]
                and detector_voltage_consistency_report["are_all_files_consistent"]
            ),
            "reference_file_path": column_name_consistency_report["reference_file_path"],
            "reference_column_names": column_name_consistency_report["reference_column_names"],
            "reference_fcs_version": version_consistency_report["reference_fcs_version"],
            "reference_detector_voltages": detector_voltage_consistency_report[
                "reference_detector_voltages"
            ],
            "invalid_file_paths": combined_invalid_file_paths,
            "mismatch_details": combined_mismatch_details,
            "column_name_consistency": column_name_consistency_report,
            "version_consistency": version_consistency_report,
            "detector_voltage_consistency": detector_voltage_consistency_report,
        }

        logger.debug(
            "Finished complete FCS multi file consistency check. report=%r",
            report,
        )

        return report
