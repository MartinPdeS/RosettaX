# -*- coding: utf-8 -*-

import dash_bootstrap_components as dbc

from RosettaX.utils import ui_forms


def get_layout(section) -> dbc.Card:
    """
    Create the fluorescence save section layout.
    """
    card = section.layout_builder.get_layout()

    return card
