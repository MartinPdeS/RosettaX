# -*- coding: utf-8 -*-

import base64
import json

import pytest

from RosettaX.workflow.cross_calibration import services


def _build_fluorescence_record() -> dict:
    return {
        "schema": "rosettax_calibration_v1",
        "payload": {
            "calibration_type": "fluorescence",
            "source_channel": "FITC-A",
            "reference_points": [
                {"measured_value": 100.0, "reference_value": 500.0},
                {"measured_value": 200.0, "reference_value": 5_000.0},
                {"measured_value": 300.0, "reference_value": 50_000.0},
                {"measured_value": 400.0, "reference_value": 500_000.0},
                {"measured_value": 500.0, "reference_value": 5_000_000.0},
            ],
            "payload": {
                "y_definition": "Intensity [calibrated units]",
            },
        },
    }


def _build_scattering_record() -> dict:
    return {
        "schema": "rosettax_calibration_v1",
        "payload": {
            "calibration_type": "scattering",
            "source_channel": "SSC-A",
            "reference_table": [
                {"measured_peak_position": 100.0, "expected_coupling": 1.0},
                {"measured_peak_position": 200.0, "expected_coupling": 2.0},
            ],
        },
    }


def _build_dash_upload_contents(payload: dict) -> str:
    raw_bytes = json.dumps(payload).encode("utf-8")
    return "data:application/json;base64," + base64.b64encode(raw_bytes).decode("ascii")


class Test_CrossCalibrationServices:
    def test_build_cross_calibration_uirevision_changes_with_result_identity(self) -> None:
        first_revision = services.build_cross_calibration_uirevision(
            {
                "primary_file_name": "primary_a.json",
                "secondary_file_name": "secondary.json",
                "calibration_type": "fluorescence",
                "source_channel": "FITC-A",
                "point_count": 5,
            }
        )

        second_revision = services.build_cross_calibration_uirevision(
            {
                "primary_file_name": "primary_b.json",
                "secondary_file_name": "secondary.json",
                "calibration_type": "fluorescence",
                "source_channel": "FITC-A",
                "point_count": 5,
            }
        )

        assert first_revision != second_revision

    def test_build_upload_prompt_text_does_not_mention_file_size(self) -> None:
        prompt_text = services.build_upload_prompt_text("primary reference")

        assert "Maximum file size" not in prompt_text
        assert prompt_text == "Select primary reference calibration JSON"

    def test_parse_uploaded_calibration_rejects_unsupported_schema(self) -> None:
        invalid_record = {
            "schema": "unsupported",
            "payload": {
                "calibration_type": "fluorescence",
            },
        }

        with pytest.raises(ValueError, match="schema is unsupported"):
            services.parse_uploaded_calibration(
                contents=_build_dash_upload_contents(invalid_record),
                filename="invalid.json",
            )

    def test_build_cross_calibration_result_builds_primary_to_secondary_transfer_relation(
        self,
    ) -> None:
        primary_record = _build_fluorescence_record()
        secondary_record = _build_fluorescence_record()
        secondary_record["payload"]["reference_points"] = [
            {
                "measured_value": point["measured_value"] * 0.5,
                "reference_value": point["reference_value"],
            }
            for point in secondary_record["payload"]["reference_points"]
        ]

        primary_summary = services.build_calibration_summary(
            filename="primary.json",
            calibration_payload=primary_record["payload"],
        )
        secondary_summary = services.build_calibration_summary(
            filename="secondary.json",
            calibration_payload=secondary_record["payload"],
        )

        result = services.build_cross_calibration_result(
            primary_summary=primary_summary,
            secondary_summary=secondary_summary,
        )

        assert result.point_count == 5
        assert result.calibration_type == "fluorescence"
        assert result.x_quantity == "secondary_measured_value"
        assert "Secondary routine-bead peak" in result.x_axis_label
        assert "Primary calibrated scale" in result.y_axis_label
        assert result.r_squared >= 0.0
        assert len(result.points) == 5
        assert result.warnings == []
        assert result.points[0].bead_index == 1
        assert result.points[0].primary_reference_value == 500.0
        assert result.points[0].secondary_measured_value is not None

    def test_build_cross_calibration_result_rejects_mismatched_types(self) -> None:
        fluorescence_record = _build_fluorescence_record()
        scattering_record = _build_scattering_record()

        primary_summary = services.build_calibration_summary(
            filename="primary.json",
            calibration_payload=fluorescence_record["payload"],
        )
        secondary_summary = services.build_calibration_summary(
            filename="secondary.json",
            calibration_payload=scattering_record["payload"],
        )

        with pytest.raises(ValueError, match="must be of the same type"):
            services.build_cross_calibration_result(
                primary_summary=primary_summary,
                secondary_summary=secondary_summary,
            )

    def test_build_export_payload_wraps_result_with_cross_schema(self) -> None:
        result = {
            "point_count": 3,
            "r_squared": 0.998,
            "warnings": [],
            "points": [],
        }

        payload = services.build_export_payload(
            result=result,
            export_name="apogee_fitc_cross",
        )

        assert payload["schema"] == "rosettax_cross_calibration_v1"
        assert payload["name"] == "apogee_fitc_cross"
        assert payload["payload"]["calibration_type"] == "cross"
        assert payload["payload"]["transfer_role"] == "primary_to_secondary"
        assert payload["payload"]["name"] == "apogee_fitc_cross"

    def test_build_result_figure_sets_stable_uirevision(self) -> None:
        result = {
            "primary_file_name": "primary.json",
            "secondary_file_name": "secondary.json",
            "calibration_type": "fluorescence",
            "source_channel": "FITC-A",
            "x_axis_label": "Secondary routine-bead peak on FITC-A [a.u.]",
            "y_axis_label": "Primary calibrated scale: MESF",
            "slope": 1.1,
            "intercept": 0.2,
            "point_count": 2,
            "points": [
                {"bead_index": 1, "x_value": 100.0, "y_value": 500.0},
                {"bead_index": 2, "x_value": 500.0, "y_value": 2000.0},
            ],
        }

        figure = services.build_result_figure(
            result=result,
        )

        assert isinstance(figure.layout.uirevision, str)
        assert "primary.json" in figure.layout.uirevision
