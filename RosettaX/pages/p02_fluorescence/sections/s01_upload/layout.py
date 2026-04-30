# -*- coding: utf-8 -*-

import dash
import dash_bootstrap_components as dbc

from RosettaX.utils import styling
from RosettaX.utils import ui_forms


def get_layout(section) -> dbc.Card:
    """
    Build the upload section layout.
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


def build_card_title(section) -> dash.html.Div:
    """
    Build the card title with compact hover help.
    """
    return ui_forms.build_title_with_info(
        title=f"{section.section_number}. Upload calibration FCS file",
        tooltip_target_id=section.upload_tooltip_target_id,
        tooltip_id=section.upload_tooltip_id,
        tooltip_text=(
            "Upload an FCS file measured from fluorescence calibration "
            "beads with known MESF values. RosettaX uses the bead peak "
            "positions and the known MESF references to build the "
            "fluorescence calibration."
        ),
    )
