# -*- coding: utf-8 -*-

from RosettaX.workflow.save.callbacks import save_button_should_be_disabled


class Test_SaveButtonVisibility:
    def test_save_button_should_be_disabled_for_empty_name(self) -> None:
        assert save_button_should_be_disabled("") is True
        assert save_button_should_be_disabled("   ") is True
        assert save_button_should_be_disabled(None) is True

    def test_save_button_should_be_enabled_for_non_empty_name(self) -> None:
        assert save_button_should_be_disabled("my_calibration") is False

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
            )
            is False
        )
