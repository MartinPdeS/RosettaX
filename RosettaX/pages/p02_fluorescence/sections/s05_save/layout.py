# -*- coding: utf-8 -*-

import dash_bootstrap_components as dbc

from RosettaX.utils import styling
from RosettaX.utils import ui_forms


def get_layout(section) -> dbc.Card:
    """
    Create the fluorescence save section layout.
    """
    card = section.layout_builder.get_layout()

    section_style = styling.build_workflow_section_legacy_style(
        section.card_color,
    )

    return ui_forms.apply_workflow_section_card_style(
        card=card,
        header_background=section_style["header_background"],
        header_border=section_style["header_border"],
        left_border=section_style["left_border"],
        header_font_weight="750",
        header_font_size="1.02rem",
    )
