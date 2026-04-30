# -*- coding: utf-8 -*-

import dash
import dash_bootstrap_components as dbc

from RosettaX.utils import styling
from RosettaX.utils import ui_forms


def get_layout(section) -> dbc.Card:
    """
    Build the fluorescence peak section layout.
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


def build_section_title(section) -> dash.html.Div:
    """
    Build the section title with compact hover help.
    """
    return ui_forms.build_title_with_info(
        title=f"{section.section_number}. Fluorescence peak detection",
        tooltip_target_id=section.section_tooltip_target_id,
        tooltip_id=section.section_tooltip_id,
        tooltip_text=(
            "Use this section to detect fluorescence bead population peaks "
            "from the calibration FCS file. These measured peak positions are "
            "written into the fluorescence calibration table and paired with "
            "the known MESF values."
        ),
    )


def build_graph_title(section) -> dash.html.Div:
    """
    Build the graph title with compact hover help.
    """
    return ui_forms.build_title_with_info(
        title=f"{section.section_number}. Fluorescence peak detection graph",
        tooltip_target_id=section.graph_tooltip_target_id,
        tooltip_id=section.graph_tooltip_id,
        tooltip_text=(
            "This graph previews the selected fluorescence signal and overlays "
            "the detected or manually selected peak positions. Use it to verify "
            "that the retained peaks correspond to the expected calibration bead "
            "populations."
        ),
    )
