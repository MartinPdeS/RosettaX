# -*- coding: utf-8 -*-

from RosettaX.workflow.save.callbacks import save_button_should_be_disabled


class Test_SaveButtonVisibility:
    def test_save_button_should_be_disabled_for_empty_name(self) -> None:
        assert save_button_should_be_disabled("") is True
        assert save_button_should_be_disabled("   ") is True
        assert save_button_should_be_disabled(None) is True

    def test_save_button_should_be_enabled_for_non_empty_name(self) -> None:
        assert save_button_should_be_disabled("my_calibration") is False
