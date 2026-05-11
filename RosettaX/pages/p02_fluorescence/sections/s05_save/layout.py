# -*- coding: utf-8 -*-

import dash_bootstrap_components as dbc

from RosettaX.utils import styling
from RosettaX.utils import ui_forms


def get_layout(section) -> dbc.Card:
    """
    Create the fluorescence save section layout.
    """
    card = section.layout_builder.get_layout()

    return ui_forms.apply_workflow_section_card_style(
        card=card,
        color_name=section.card_color,
        header_font_weight="750",
        header_font_size="1.02rem",
    )
