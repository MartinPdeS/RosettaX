# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any, Optional

from RosettaX.utils import casting
from RosettaX.utils.runtime_config import RuntimeConfig

from . import services as table_services


CUSTOM_FLUORESCENCE_REFERENCE_PRESET_NAME = "Custom"
GENERIC_FLUORESCENCE_REFERENCE_PRESET_NAME = "Generic"
ROSETTA_MIX_FLUORESCENCE_REFERENCE_PRESET_NAME = "Rosetta Mix"
RAINBOW_SIX_FLUORESCENCE_REFERENCE_PRESET_NAME = "Rainbow 6"
BROAD_EIGHT_FLUORESCENCE_REFERENCE_PRESET_NAME = "Broad 8"


@dataclass(frozen=True)
class FluorescenceReferencePreset:
    """
    Preset MESF values for fluorescence calibration standards.
    """

    name: str
    mesf_values: list[float]
    description: str = ""


def build_fluorescence_reference_presets() -> dict[str, FluorescenceReferencePreset]:
    """
    Build built-in fluorescence reference presets.
    """
    return {
        GENERIC_FLUORESCENCE_REFERENCE_PRESET_NAME: FluorescenceReferencePreset(
            name=GENERIC_FLUORESCENCE_REFERENCE_PRESET_NAME,
            mesf_values=[1.0e3, 1.0e4, 1.0e5, 1.0e6],
            description="Generic four-point MESF ladder.",
        ),
        ROSETTA_MIX_FLUORESCENCE_REFERENCE_PRESET_NAME: FluorescenceReferencePreset(
            name=ROSETTA_MIX_FLUORESCENCE_REFERENCE_PRESET_NAME,
            mesf_values=[5.0e2, 5.0e3, 5.0e4, 5.0e5, 5.0e6, 5.0e7],
            description="Rosetta Mix fluorescence ladder.",
        ),
        RAINBOW_SIX_FLUORESCENCE_REFERENCE_PRESET_NAME: FluorescenceReferencePreset(
            name=RAINBOW_SIX_FLUORESCENCE_REFERENCE_PRESET_NAME,
            mesf_values=[2.0e2, 2.0e3, 2.0e4, 2.0e5, 2.0e6, 2.0e7],
            description="Six-population rainbow-style MESF ladder.",
        ),
        BROAD_EIGHT_FLUORESCENCE_REFERENCE_PRESET_NAME: FluorescenceReferencePreset(
            name=BROAD_EIGHT_FLUORESCENCE_REFERENCE_PRESET_NAME,
            mesf_values=[1.0e2, 5.0e2, 2.0e3, 1.0e4, 5.0e4, 2.0e5, 1.0e6, 5.0e6],
            description="Broad eight-population MESF ladder.",
        ),
    }


def build_fluorescence_reference_preset_options() -> list[dict[str, str]]:
    """
    Build dropdown options for fluorescence reference presets.
    """
    options = [
        {
            "label": CUSTOM_FLUORESCENCE_REFERENCE_PRESET_NAME,
            "value": CUSTOM_FLUORESCENCE_REFERENCE_PRESET_NAME,
        }
    ]

    options.extend(
        {
            "label": preset.name,
            "value": preset.name,
        }
        for preset in build_fluorescence_reference_presets().values()
    )

    return options


def get_fluorescence_reference_preset(
    preset_name: Any,
) -> Optional[FluorescenceReferencePreset]:
    """
    Resolve one built-in fluorescence reference preset by name.
    """
    preset_name_string = str(preset_name or "").strip()

    return build_fluorescence_reference_presets().get(
        preset_name_string,
    )


class FluorescenceReferenceTable:
    """
    Workflow helpers for the fluorescence calibration reference table.
    """

    column_calibrated_intensity = "col1"
    column_measured_intensity = "col2"

    columns: list[dict[str, Any]] = [
        {
            "name": "Intensity [a.u.]",
            "id": column_measured_intensity,
            "editable": True,
        },
        {
            "name": "Intensity [standard units]",
            "id": column_calibrated_intensity,
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
    def build_rows_from_preset_name(
        cls,
        *,
        preset_name: Any,
        current_rows: Optional[list[dict[str, Any]]] = None,
    ) -> list[dict[str, Any]]:
        """
        Build fluorescence calibration rows from a selected preset.
        """
        preset_name_string = str(
            preset_name or CUSTOM_FLUORESCENCE_REFERENCE_PRESET_NAME,
        ).strip()

        if preset_name_string == CUSTOM_FLUORESCENCE_REFERENCE_PRESET_NAME:
            return cls.normalize_rows(
                rows=current_rows,
            )

        preset = get_fluorescence_reference_preset(
            preset_name_string,
        )

        if preset is None:
            return cls.normalize_rows(
                rows=current_rows,
            )

        preset_rows = cls.build_rows_from_mesf_values(
            preset.mesf_values,
        )

        normalized_current_rows = cls.normalize_rows(
            rows=current_rows,
        )

        if not normalized_current_rows:
            return preset_rows

        merged_rows: list[dict[str, Any]] = []

        for row_index, preset_row in enumerate(preset_rows):
            merged_row = dict(preset_row)

            if row_index < len(normalized_current_rows):
                merged_row[cls.column_measured_intensity] = str(
                    normalized_current_rows[row_index].get(
                        cls.column_measured_intensity,
                        "",
                    )
                    or ""
                ).strip()

            merged_rows.append(merged_row)

        for row_index in range(len(preset_rows), len(normalized_current_rows)):
            measured_intensity = str(
                normalized_current_rows[row_index].get(
                    cls.column_measured_intensity,
                    "",
                )
                or ""
            ).strip()

            if not measured_intensity:
                continue

            merged_rows.append(
                {
                    cls.column_calibrated_intensity: "",
                    cls.column_measured_intensity: measured_intensity,
                }
            )

        return merged_rows

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
    def resolve_matching_preset_name(
        cls,
        *,
        rows: Optional[list[dict[str, Any]]],
    ) -> str:
        """
        Resolve the selected preset name from the table calibrated-intensity column.
        """
        normalized_rows = cls.normalize_rows(
            rows=rows,
        )

        calibrated_values = cls.parse_mesf_values(
            [
                row.get(cls.column_calibrated_intensity, "")
                for row in normalized_rows
                if isinstance(row, dict)
            ]
        )

        if not calibrated_values:
            return CUSTOM_FLUORESCENCE_REFERENCE_PRESET_NAME

        for preset in build_fluorescence_reference_presets().values():
            preset_values = cls.parse_mesf_values(
                preset.mesf_values,
            )

            if calibrated_values == preset_values:
                return preset.name

        return CUSTOM_FLUORESCENCE_REFERENCE_PRESET_NAME

    @classmethod
    def resolve_runtime_preset_name(
        cls,
        *,
        runtime_config: RuntimeConfig,
    ) -> str:
        """
        Resolve the fluorescence preset that matches the runtime MESF values.
        """
        return cls.resolve_matching_preset_name(
            rows=cls.build_rows_from_runtime_config(
                runtime_config=runtime_config,
            ),
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