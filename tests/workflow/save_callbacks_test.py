# -*- coding: utf-8 -*-

import json
import logging

import dash

from RosettaX.workflow.save.callbacks import (
    _build_save_review_summary,
    save_button_should_be_disabled,
)
from RosettaX.workflow.save.models import SaveConfig
from RosettaX.workflow.save.services import run_save_workflow


class Test_SaveButtonVisibility:
    def test_save_button_should_be_disabled_for_empty_name(self) -> None:
        assert save_button_should_be_disabled("") is True
        assert save_button_should_be_disabled("   ") is True
        assert save_button_should_be_disabled(None) is True

    def test_save_button_should_be_enabled_for_non_empty_name(self) -> None:
        assert (
            save_button_should_be_disabled(
                "my_calibration",
                "FITC (MESF)",
                require_output_channel_name=True,
                calibration_payload={"fit": {"slope": 1.2}},
                review_acknowledgment=["reviewed"],
            )
            is False
        )

    def test_save_button_should_require_output_channel_name_when_configured(self) -> None:
        assert (
            save_button_should_be_disabled(
                "my_calibration",
                "",
                require_output_channel_name=True,
            )
            is True
        )
        assert (
            save_button_should_be_disabled(
                "my_calibration",
                "FITC (MESF)",
                require_output_channel_name=True,
                calibration_payload={"fit": {"slope": 1.2}},
                review_acknowledgment=["reviewed"],
            )
            is False
        )


class Test_SaveWorkflowContract:
    def test_save_workflow_wraps_payload_without_mutating_source(self) -> None:
        source_payload = {
            "source_channel": "FITC-A",
            "fit": {"slope": 1.2, "intercept": 0.3},
        }

        result = run_save_workflow(
            file_name=" Fluorescence reference ",
            output_channel_name="FITC (MESF)",
            calibration_payload=source_payload,
            config=SaveConfig(calibration_kind="fluorescence"),
            logger=logging.getLogger(__name__),
        )

        assert result.save_out == 'Prepared calibration download "Fluorescence_reference.json".'
        assert source_payload == {
            "source_channel": "FITC-A",
            "fit": {"slope": 1.2, "intercept": 0.3},
        }
        assert result.download_data["filename"] == "Fluorescence_reference.json"

        record = json.loads(result.download_data["content"])
        assert record["schema"] == "rosettax_calibration_v1"
        assert record["kind"] == "fluorescence"
        assert record["payload"] == {
            **source_payload,
            "applied_output_channel_name": "FITC (MESF)",
        }

    def test_save_workflow_does_not_produce_download_for_invalid_payload(self) -> None:
        result = run_save_workflow(
            file_name="example",
            output_channel_name=None,
            calibration_payload=None,
            config=SaveConfig(calibration_kind="fluorescence"),
            logger=logging.getLogger(__name__),
        )

        assert result.save_out == "Create a calibration before saving."
        assert result.download_data is dash.no_update

    def test_save_button_requires_calibration_and_review_acknowledgment(self) -> None:
        assert (
            save_button_should_be_disabled(
                "example",
                "FITC (MESF)",
                require_output_channel_name=True,
                calibration_payload={"fit": {"slope": 1.2}},
                review_acknowledgment=[],
            )
            is True
        )
        assert (
            save_button_should_be_disabled(
                "example",
                "FITC (MESF)",
                require_output_channel_name=True,
                calibration_payload=None,
                review_acknowledgment=["reviewed"],
            )
            is True
        )

    def test_save_review_summary_identifies_required_inputs(self) -> None:
        summary = _build_save_review_summary(
            file_name="",
            output_channel_name="",
            calibration_payload=None,
            config=SaveConfig(
                calibration_kind="fluorescence",
                require_output_channel_name=True,
            ),
        )

        assert summary.color == "warning"
        assert summary.children[0].children == "Needs attention"
        assert "Create a calibration" in summary.children[1].children
