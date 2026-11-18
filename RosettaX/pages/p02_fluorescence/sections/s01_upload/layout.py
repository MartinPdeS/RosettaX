
import dash
import dash_bootstrap_components as dbc
from RosettaX.utils import ui_forms


def get_layout(section) -> dbc.Card:
    """
    Build the upload section layout.
    """
    card = section.layout_builder.get_layout()

    return card


def build_card_title(section) -> dash.html.Div:
    """
    Build the card title with compact hover help.
    """
    return ui_forms.build_title_with_info(
        title=f"{section.section_number}. {section.workflow_step.title}",
        tooltip_target_id=section.upload_tooltip_target_id,
        tooltip_id=section.upload_tooltip_id,
        tooltip_text=section.workflow_step.tooltip_text,
    )
