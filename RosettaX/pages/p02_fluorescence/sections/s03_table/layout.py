# -*- coding: utf-8 -*-

import dash
import dash_bootstrap_components as dbc

from RosettaX.utils import styling
from RosettaX.utils import ui_forms
from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.workflow.table.fluorescence import FluorescenceReferenceTable


def get_layout(section) -> dbc.Card:
    """
    Build the fluorescence reference table layout.
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
        title=f"{section.section_number}. Calibration reference table",
        tooltip_target_id=section.reference_table_tooltip_target_id,
        tooltip_id=section.reference_table_tooltip_id,
        tooltip_text=(
            "Enter the known MESF values for the fluorescence calibration "
            "beads and use the fluorescence peak detection section to fill "
            "the measured peak positions. This table is the source of truth "
            "for the fluorescence calibration fit."
        ),
    )


def build_default_bead_rows() -> list[dict[str, str]]:
    """
    Build initial table rows from the default runtime profile.
    """
    runtime_config = RuntimeConfig.from_default_profile()

    return FluorescenceReferenceTable.build_rows_from_runtime_config(
        runtime_config=runtime_config,
    )
