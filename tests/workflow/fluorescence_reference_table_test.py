"""Regression tests for workflow fluorescence reference table."""

# Run pytest before application imports so the suite loads its own dependency setup.
if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))


from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.workflow.table.fluorescence import (
    CUSTOM_FLUORESCENCE_REFERENCE_PRESET_NAME,
    GENERIC_FLUORESCENCE_REFERENCE_PRESET_NAME,
    ROSETTA_MIX_FLUORESCENCE_REFERENCE_PRESET_NAME,
    SUMMER_SCHOOL_APOGEE_APC_FLUORESCENCE_REFERENCE_PRESET_NAME,
    SUMMER_SCHOOL_CYTEK_FITC_FLUORESCENCE_REFERENCE_PRESET_NAME,
    FluorescenceReferenceTable,
    build_fluorescence_reference_preset_options,
)


class Test_FluorescenceReferencePresets:
    """Regression checks for fluorescence reference presets."""

    def test_build_rows_from_named_preset_populates_calibrated_intensity_column(self):
        """Check build rows from named preset populates calibrated intensity column."""
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
        """Check build rows from named preset preserves measured intensity column."""
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

    def test_build_rows_from_shorter_preset_preserves_overflow_measured_intensity_rows(self):
        """Check build rows from shorter preset preserves overflow measured intensity rows."""
        rows = FluorescenceReferenceTable.build_rows_from_preset_name(
            preset_name=GENERIC_FLUORESCENCE_REFERENCE_PRESET_NAME,
            current_rows=[
                {
                    FluorescenceReferenceTable.column_calibrated_intensity: "500",
                    FluorescenceReferenceTable.column_measured_intensity: "12.3",
                },
                {
                    FluorescenceReferenceTable.column_calibrated_intensity: "5000",
                    FluorescenceReferenceTable.column_measured_intensity: "78.9",
                },
                {
                    FluorescenceReferenceTable.column_calibrated_intensity: "50000",
                    FluorescenceReferenceTable.column_measured_intensity: "456.7",
                },
                {
                    FluorescenceReferenceTable.column_calibrated_intensity: "500000",
                    FluorescenceReferenceTable.column_measured_intensity: "999.1",
                },
                {
                    FluorescenceReferenceTable.column_calibrated_intensity: "5e+06",
                    FluorescenceReferenceTable.column_measured_intensity: "321.0",
                },
            ],
        )

        assert len(rows) == 5
        assert rows[4][FluorescenceReferenceTable.column_calibrated_intensity] == ""
        assert rows[4][FluorescenceReferenceTable.column_measured_intensity] == "321.0"

    def test_resolve_matching_preset_name_returns_custom_for_manual_values(self):
        """Check resolve matching preset name returns custom for manual values."""
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
        """Check resolve runtime preset name matches known MESF values."""
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

    def test_build_rows_from_summer_school_apogee_apc_preset_uses_expected_mesf_values(self):
        """Check build rows from summer school apogee apc preset uses expected MESF values."""
        rows = FluorescenceReferenceTable.build_rows_from_preset_name(
            preset_name=SUMMER_SCHOOL_APOGEE_APC_FLUORESCENCE_REFERENCE_PRESET_NAME,
        )

        assert [
            row[FluorescenceReferenceTable.column_calibrated_intensity]
            for row in rows
        ] == [
            "1084",
            "4068",
            "15785",
            "51397",
            "166228",
        ]

    def test_resolve_runtime_preset_name_matches_summer_school_cytek_fitc_values(self):
        """Check resolve runtime preset name matches summer school cytek fitc values."""
        runtime_config = RuntimeConfig.from_dict(
            {
                "calibration": {
                    "mesf_values": [2417, 8043, 27055, 91014, 303940, 943000],
                }
            }
        )

        assert (
            FluorescenceReferenceTable.resolve_runtime_preset_name(
                runtime_config=runtime_config,
            )
            == SUMMER_SCHOOL_CYTEK_FITC_FLUORESCENCE_REFERENCE_PRESET_NAME
        )

    def test_preset_options_include_summer_school_entries(self):
        """Check preset options include summer school entries."""
        option_values = [
            option["value"]
            for option in build_fluorescence_reference_preset_options()
        ]

        assert SUMMER_SCHOOL_APOGEE_APC_FLUORESCENCE_REFERENCE_PRESET_NAME in option_values
        assert SUMMER_SCHOOL_CYTEK_FITC_FLUORESCENCE_REFERENCE_PRESET_NAME in option_values
