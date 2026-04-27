# -*- coding: utf-8 -*-

from typing import Any, Optional

from RosettaX.utils import casting
from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.workflow.table import services as table_services


class FluorescenceReferenceTable:
    """
    Workflow helpers for the fluorescence calibration reference table.
    """

    column_calibrated_intensity = "col1"
    column_measured_intensity = "col2"

    columns: list[dict[str, Any]] = [
        {
            "name": "Intensity [calibrated units]",
            "id": column_calibrated_intensity,
            "editable": True,
        },
        {
            "name": "Intensity [a.u.]",
            "id": column_measured_intensity,
            "editable": True,
        },
    ]

    user_data_column_ids = [
        column_calibrated_intensity,
        column_measured_intensity,
    ]

    @classmethod
    def build_default_rows(
        cls,
        *,
        row_count: int = 3,
    ) -> list[dict[str, str]]:
        """
        Build default empty fluorescence reference rows.
        """
        return table_services.build_empty_rows_from_column_ids(
            column_ids=cls.user_data_column_ids,
            row_count=row_count,
        )

    @classmethod
    def build_rows_from_runtime_config(
        cls,
        *,
        runtime_config: RuntimeConfig,
    ) -> list[dict[str, str]]:
        """
        Build fluorescence reference rows from runtime configuration.
        """
        mesf_values = runtime_config.get_path(
            "calibration.mesf_values",
            default=[],
        )

        return cls.build_rows_from_mesf_values(
            mesf_values,
        )

    @classmethod
    def build_rows_from_mesf_values(
        cls,
        mesf_values: Any,
    ) -> list[dict[str, str]]:
        """
        Build fluorescence calibration rows from MESF values.
        """
        parsed_values = cls.parse_mesf_values(
            mesf_values,
        )

        if not parsed_values:
            return cls.build_default_rows()

        return [
            {
                cls.column_calibrated_intensity: value,
                cls.column_measured_intensity: "",
            }
            for value in parsed_values
        ]

    @staticmethod
    def parse_mesf_values(
        mesf_values: Any,
    ) -> list[str]:
        """
        Parse MESF values into formatted strings.
        """
        if mesf_values is None:
            return []

        if isinstance(mesf_values, str):
            raw_parts = mesf_values.replace(";", ",").split(",")

        elif isinstance(mesf_values, (list, tuple)):
            raw_parts = list(mesf_values)

        else:
            raw_parts = [
                mesf_values,
            ]

        parsed_values: list[str] = []

        for raw_part in raw_parts:
            raw_value = str(raw_part).strip()

            if not raw_value:
                continue

            parsed_value = casting.as_float(
                raw_value,
            )

            if parsed_value is None:
                continue

            parsed_values.append(
                f"{float(parsed_value):.6g}"
            )

        return parsed_values

    @classmethod
    def normalize_rows(
        cls,
        *,
        rows: Optional[list[dict[str, Any]]],
    ) -> list[dict[str, Any]]:
        """
        Normalize fluorescence table rows.
        """
        return table_services.normalize_table_rows(
            rows=rows,
        )

    @classmethod
    def table_is_effectively_empty(
        cls,
        *,
        rows: Optional[list[dict[str, Any]]],
    ) -> bool:
        """
        Return whether the fluorescence table has no useful data.
        """
        return table_services.table_is_effectively_empty(
            rows=rows,
            user_data_column_ids=cls.user_data_column_ids,
        )

    @classmethod
    def should_rebuild_from_runtime_config(
        cls,
        *,
        profile_load_event_data: Any,
        current_rows: Optional[list[dict[str, Any]]],
    ) -> bool:
        """
        Decide whether runtime configuration should overwrite the table.
        """
        return table_services.should_rebuild_table_from_runtime_config(
            profile_load_was_requested=table_services.profile_load_was_requested(
                profile_load_event_data=profile_load_event_data,
            ),
            current_rows=cls.normalize_rows(
                rows=current_rows,
            ),
            user_data_column_ids=cls.user_data_column_ids,
        )

    @classmethod
    def add_empty_row(
        cls,
        *,
        rows: Optional[list[dict[str, Any]]],
    ) -> list[dict[str, Any]]:
        """
        Add one empty fluorescence table row.
        """
        return table_services.append_empty_row(
            rows=rows,
            empty_row={
                cls.column_calibrated_intensity: "",
                cls.column_measured_intensity: "",
            },
        )

    @classmethod
    def clear_measured_intensity(
        cls,
        *,
        rows: Optional[list[dict[str, Any]]],
    ) -> list[dict[str, Any]]:
        """
        Clear the measured intensity column.
        """
        return table_services.clear_columns(
            rows=rows,
            column_ids=[
                cls.column_measured_intensity,
            ],
        )

    @classmethod
    def clear_calibrated_intensity(
        cls,
        *,
        rows: Optional[list[dict[str, Any]]],
    ) -> list[dict[str, Any]]:
        """
        Clear the calibrated intensity column.
        """
        return table_services.clear_columns(
            rows=rows,
            column_ids=[
                cls.column_calibrated_intensity,
            ],
        )

    @classmethod
    def reset_rows(
        cls,
        *,
        row_count: int = 3,
    ) -> list[dict[str, str]]:
        """
        Reset the fluorescence reference table.
        """
        return cls.build_default_rows(
            row_count=row_count,
        )


COLUMN_CALIBRATED_INTENSITY = FluorescenceReferenceTable.column_calibrated_intensity
COLUMN_MEASURED_INTENSITY = FluorescenceReferenceTable.column_measured_intensity

fluorescence_table_columns = FluorescenceReferenceTable.columns
user_data_column_ids = FluorescenceReferenceTable.user_data_column_ids


def build_default_bead_rows(
    *,
    row_count: int = 3,
) -> list[dict[str, str]]:
    """
    Compatibility wrapper.
    """
    return FluorescenceReferenceTable.build_default_rows(
        row_count=row_count,
    )


def build_bead_rows_from_mesf_values(
    mesf_values: Any,
) -> list[dict[str, str]]:
    """
    Compatibility wrapper.
    """
    return FluorescenceReferenceTable.build_rows_from_mesf_values(
        mesf_values,
    )