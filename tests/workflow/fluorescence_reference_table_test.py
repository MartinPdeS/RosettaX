# -*- coding: utf-8 -*-

from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.workflow.table.fluorescence import (
    CUSTOM_FLUORESCENCE_REFERENCE_PRESET_NAME,
    GENERIC_FLUORESCENCE_REFERENCE_PRESET_NAME,
    ROSETTA_MIX_FLUORESCENCE_REFERENCE_PRESET_NAME,
    FluorescenceReferenceTable,
)


class Test_FluorescenceReferencePresets:
    def test_build_rows_from_named_preset_populates_calibrated_intensity_column(self):
        rows = FluorescenceReferenceTable.build_rows_from_preset_name(
            preset_name=ROSETTA_MIX_FLUORESCENCE_REFERENCE_PRESET_NAME,
        )

        assert [row[FluorescenceReferenceTable.column_calibrated_intensity] for row in rows] == [
            "500",
            "5000",
            "50000",
            "500000",
            "5e+06",
            "5e+07",
        ]
        assert all(
            row[FluorescenceReferenceTable.column_measured_intensity] == ""
            for row in rows
        )

    def test_build_rows_from_named_preset_preserves_measured_intensity_column(self):
        rows = FluorescenceReferenceTable.build_rows_from_preset_name(
            preset_name=ROSETTA_MIX_FLUORESCENCE_REFERENCE_PRESET_NAME,
            current_rows=[
                {
                    FluorescenceReferenceTable.column_calibrated_intensity: "1",
                    FluorescenceReferenceTable.column_measured_intensity: "12.3",
                },
                {
                    FluorescenceReferenceTable.column_calibrated_intensity: "2",
                    FluorescenceReferenceTable.column_measured_intensity: "78.9",
                },
                {
                    FluorescenceReferenceTable.column_calibrated_intensity: "3",
                    FluorescenceReferenceTable.column_measured_intensity: "456.7",
                },
            ],
        )

        assert [row[FluorescenceReferenceTable.column_calibrated_intensity] for row in rows[:3]] == [
            "500",
            "5000",
            "50000",
        ]
        assert [row[FluorescenceReferenceTable.column_measured_intensity] for row in rows[:3]] == [
            "12.3",
            "78.9",
            "456.7",
        ]

    def test_resolve_matching_preset_name_returns_custom_for_manual_values(self):
        rows = [
            {
                FluorescenceReferenceTable.column_calibrated_intensity: "123",
                FluorescenceReferenceTable.column_measured_intensity: "",
            },
            {
                FluorescenceReferenceTable.column_calibrated_intensity: "456",
                FluorescenceReferenceTable.column_measured_intensity: "",
            },
        ]

        assert (
            FluorescenceReferenceTable.resolve_matching_preset_name(rows=rows)
            == CUSTOM_FLUORESCENCE_REFERENCE_PRESET_NAME
        )

    def test_resolve_runtime_preset_name_matches_known_mesf_values(self):
        runtime_config = RuntimeConfig.from_dict(
            {
                "calibration": {
                    "mesf_values": [1.0e3, 1.0e4, 1.0e5, 1.0e6],
                }
            }
        )

        assert (
            FluorescenceReferenceTable.resolve_runtime_preset_name(
                runtime_config=runtime_config,
            )
            == GENERIC_FLUORESCENCE_REFERENCE_PRESET_NAME
        )