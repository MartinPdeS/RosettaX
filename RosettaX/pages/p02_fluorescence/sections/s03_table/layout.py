# -*- coding: utf-8 -*-

import dash
import dash_bootstrap_components as dbc

from RosettaX.utils import styling, ui_forms
from RosettaX.workflow.table.fluorescence import (
    FluorescenceReferenceTable,
    build_fluorescence_reference_preset_options,
)


def get_layout(section) -> dbc.Card:
    """
    Build the fluorescence reference table layout.
    """
    card = section.layout_builder.get_layout()
    body = card.children[1]
    body.children = [
        build_preset_controls(section),
        dash.html.Div(
            style={
                "height": "14px",
            },
        ),
        *list(body.children),
    ]

    return ui_forms.apply_workflow_section_card_style(
        card=card,
        color_name=section.card_color,
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


def build_preset_controls(section) -> dash.html.Div:
    """
    Build fluorescence reference preset controls displayed above the table.
    """
    return ui_forms.build_inline_row(
        label="Reference preset:",
        control=dash.html.Div(
            [
                ui_forms.persistent_dropdown(
                    id=section.ids.bead_table_preset_dropdown,
                    options=build_fluorescence_reference_preset_options(),
                    value=section.default_reference_preset_name,
                    clearable=False,
                    searchable=False,
                    style={
                        "width": "320px",
                    },
                ),
                ui_forms.build_info_badge(
                    tooltip_target_id=section.reference_table_preset_tooltip_target_id,
                ),
                dbc.Tooltip(
                    (
                        "Select a built-in fluorescence bead ladder to populate the "
                        "calibrated-intensity column. Choose Custom to keep manual MESF edits."
                    ),
                    id=section.reference_table_preset_tooltip_id,
                    target=section.reference_table_preset_tooltip_target_id,
                    placement="right",
                ),
            ],
            style={
                "display": "flex",
                "alignItems": "center",
                "overflow": "visible",
            },
        ),
        margin_top=False,
        row_style_overrides={
            "overflow": "visible",
        },
        control_wrapper_style_overrides={
            "overflow": "visible",
        },
    )
