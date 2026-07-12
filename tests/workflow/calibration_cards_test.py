# -*- coding: utf-8 -*-

import dash_bootstrap_components as dbc

from RosettaX.workflow import calibration_cards


class Test_CalibrationCards:
    def test_missing_profile_preference_keeps_cards_expanded(self) -> None:
        assert calibration_cards.profile_collapses_calibration_cards({}) is False

    def test_profile_can_collapse_cards(self) -> None:
        assert calibration_cards.profile_collapses_calibration_cards(
            {"ui": {"collapse_calibration_cards": True}}
        ) is True

    def test_settings_profile_path_migrates_to_runtime_preference(self) -> None:
        assert calibration_cards.profile_collapses_calibration_cards(
            {"misc": {"ui": {"collapse_calibration_cards": True}}}
        ) is True

    def test_click_toggles_current_card_state(self) -> None:
        is_open, label = calibration_cards.resolve_card_toggle(
            triggered_id={"type": calibration_cards.TOGGLE_ID_TYPE},
            is_open=False,
            runtime_config_data={"ui": {"collapse_calibration_cards": True}},
        )

        assert is_open is True
        assert label == "Hide"

    def test_profile_load_resets_card_state(self) -> None:
        is_open, label = calibration_cards.resolve_card_toggle(
            triggered_id="runtime-config-store",
            is_open=True,
            runtime_config_data={"ui": {"collapse_calibration_cards": True}},
        )

        assert is_open is False
        assert label == "Show"

    def test_card_body_is_wrapped_in_profile_aware_collapse(self) -> None:
        card = dbc.Card([dbc.CardHeader("Section"), dbc.CardBody("Body")])

        result = calibration_cards.make_collapsible_section_card(
            card,
            page_name="test-page",
            section_key="1",
            initially_collapsed=True,
        )

        assert isinstance(result.children[1], dbc.Collapse)
        assert result.children[1].kwargs["is_open"] is False
        assert result.children[1].id == {
            "type": calibration_cards.COLLAPSE_ID_TYPE,
            "page": "test-page",
            "section": "1",
        }
        assert result.children[0].children.id == {
            "type": calibration_cards.TOGGLE_ID_TYPE,
            "page": "test-page",
            "section": "1",
        }
        assert result.children[0].children.style["cursor"] == "pointer"
