
import dash
import dash_bootstrap_components as dbc
from RosettaX.utils import ui_forms


def get_layout(section) -> dbc.Card:
    """
    Build the fluorescence peak section layout.
    """
    card = section.layout_builder.get_layout()

    return card


def build_section_title(section) -> dash.html.Div:
    """
    Build the section title with compact hover help.
    """
    return ui_forms.build_title_with_info(
        title=f"{section.section_number}. {section.workflow_step.title}",
        tooltip_target_id=section.section_tooltip_target_id,
        tooltip_id=section.section_tooltip_id,
        tooltip_text=section.workflow_step.tooltip_text,
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
