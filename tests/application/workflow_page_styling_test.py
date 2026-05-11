# -*- coding: utf-8 -*-

from types import SimpleNamespace

from RosettaX.pages.p02_fluorescence.sections.s00_header import (
    layout as fluorescence_header_layout,
)
from RosettaX.pages.p03_scattering.sections.s00_header import Header as ScatteringHeader
from RosettaX.utils import styling


class Test_WorkflowPageStyling:
    def test_workflow_page_color_scheme_uses_shared_sequence(self) -> None:
        assert styling.get_workflow_page_header_color() == "green"
        assert [
            styling.get_workflow_section_color(section_number)
            for section_number in range(1, 7)
        ] == [
            "yellow",
            "blue",
            "orange",
            "cyan",
            "purple",
            "gray",
        ]

    def test_fluorescence_header_uses_shared_header_card_and_step_colors(self) -> None:
        section = SimpleNamespace(
            card_color=styling.get_workflow_page_header_color(),
        )

        card = fluorescence_header_layout.get_layout(section)

        assert styling.build_rgba("green", 0.75) in card.style["borderLeft"]

        step_row = card.children.children[1]
        first_step_card = step_row.children[0].children
        second_step_card = step_row.children[1].children

        first_step_badge_style = first_step_card.children.children[0].style
        second_step_badge_style = second_step_card.children.children[0].style

        assert first_step_badge_style["backgroundColor"] == styling.build_rgba(
            "yellow",
            0.12,
        )
        assert second_step_badge_style["backgroundColor"] == styling.build_rgba(
            "blue",
            0.12,
        )

    def test_scattering_header_uses_shared_header_card_and_step_colors(self) -> None:
        header = ScatteringHeader(
            page=SimpleNamespace(),
            card_color=styling.get_workflow_page_header_color(),
        )

        card = header.get_layout()

        assert styling.build_rgba("green", 0.75) in card.style["borderLeft"]

        step_row = card.children.children[1]
        first_step_card = step_row.children[0].children
        fifth_step_card = step_row.children[4].children

        first_step_badge_style = first_step_card.children.children[0].style
        fifth_step_badge_style = fifth_step_card.children.children[0].style

        assert first_step_badge_style["backgroundColor"] == styling.build_rgba(
            "yellow",
            0.12,
        )
        assert fifth_step_badge_style["backgroundColor"] == styling.build_rgba(
            "purple",
            0.12,
        )
