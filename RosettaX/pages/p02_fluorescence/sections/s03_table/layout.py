import dash
from RosettaX.utils import ui_forms


def build_card_title(section) -> dash.html.Div:
    """
    Build the card title with compact hover help.
    """
    return ui_forms.build_title_with_info(
        title=f"{section.section_number}. {section.workflow_step.title}",
        tooltip_target_id=section.reference_table_tooltip_target_id,
        tooltip_id=section.reference_table_tooltip_id,
        tooltip_text=section.workflow_step.tooltip_text,
    )
