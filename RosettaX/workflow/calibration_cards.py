# -*- coding: utf-8 -*-

from typing import Any

import dash
import dash_bootstrap_components as dbc

from RosettaX.utils import styling, ui_forms
from RosettaX.utils.runtime_config import RuntimeConfig


TOGGLE_ID_TYPE = "calibration-card-toggle"
COLLAPSE_ID_TYPE = "calibration-card-collapse"
TOGGLE_LABEL_ID_TYPE = "calibration-card-toggle-label"
WORKFLOW_STEP_CARD_ID_TYPE = "workflow-step-card"
FCS_TOOL_CARD_GAP = styling.get_spacing_token("lg")

CALIBRATION_WORKFLOW_SUBTITLES = {
    "fluorescent_calibration": {
        "1": "Load the bead measurement used to establish the fluorescence response.",
        "2": "Identify the fluorescence bead populations and record their measured peaks.",
        "3": "Pair the measured peaks with the known MESF reference values.",
        "4": "Fit the fluorescence response from the reference values and bead peaks.",
        "5": "Download the completed fluorescence calibration for later use.",
    },
    "scattering_calibration": {
        "1": "Load the bead measurement used to establish the scattering response.",
        "2": "Identify the scattering bead populations and record their measured peaks.",
        "3": "Configure the optical and detector model used for the calibration.",
        "4": "Define the calibration standard and calculate its modeled coupling.",
        "5": "Fit the instrument response from the measured and modeled bead values.",
        "6": "Download the completed scattering calibration for later use.",
    },
    "apply_calibration": {
        "1": "Choose the saved calibration files to apply to matching FCS channels.",
        "2": "Load the input FCS files that will receive the selected calibrations.",
        "3": "Generate and download calibrated FCS output files.",
    },
}


def _component_id(*, id_type: str, page_name: str, section_key: str) -> dict[str, str]:
    return {
        "type": id_type,
        "page": page_name,
        "section": section_key,
    }


def workflow_section_dom_id(*, page_name: str, section_key: str) -> str:
    """Return the DOM id used to navigate to a numbered workflow section."""
    return f"{page_name}-workflow-section-{section_key}"


def profile_collapses_calibration_cards(runtime_config_data: Any = None) -> bool:
    """Return the active profile's calibration-card initial state."""
    runtime_config = RuntimeConfig.from_dict(
        runtime_config_data if isinstance(runtime_config_data, dict) else None
    )
    return runtime_config.get_bool("ui.collapse_calibration_cards", default=False)


def collapse_label(*, is_open: bool) -> str:
    """Build the compact action label shown in a workflow card header."""
    return "Hide" if is_open else "Show"


def build_fcs_tool_card_stack(children: list[Any]) -> dash.html.Div:
    """Stack FCS tool cards with one consistent vertical gap."""
    return dash.html.Div(
        children,
        style={
            "display": "flex",
            "flexDirection": "column",
            "gap": FCS_TOOL_CARD_GAP,
        },
    )


def make_collapsible_section_card(
    card: dbc.Card,
    *,
    page_name: str,
    section_key: str,
    initially_collapsed: bool,
) -> dbc.Card:
    """Add a profile-aware collapse control to one workflow section card."""
    card_children = ui_forms.normalize_children(card.children)
    if len(card_children) < 2 or not isinstance(card_children[0], dbc.CardHeader):
        return card

    header = card_children[0]
    card.id = workflow_section_dom_id(
        page_name=page_name,
        section_key=section_key,
    )
    is_open = not initially_collapsed
    header_children = ui_forms.normalize_children(header.children)
    header.children = dash.html.Div(
        [
            dash.html.Div(
                header_children,
                style={
                    "flex": "1 1 auto",
                    "minWidth": "0",
                },
            ),
            dash.html.Span(
                collapse_label(is_open=is_open),
                id=_component_id(
                    id_type=TOGGLE_LABEL_ID_TYPE,
                    page_name=page_name,
                    section_key=section_key,
                ),
                style={
                    "fontWeight": "700",
                    "flex": "0 0 auto",
                },
            ),
        ],
        id=_component_id(
            id_type=TOGGLE_ID_TYPE,
            page_name=page_name,
            section_key=section_key,
        ),
        n_clicks=0,
        role="button",
        tabIndex=0,
        style={
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "space-between",
            "gap": "12px",
            "cursor": "pointer",
        },
    )
    card.children = [
        header,
        dbc.Collapse(
            card_children[1:],
            id=_component_id(
                id_type=COLLAPSE_ID_TYPE,
                page_name=page_name,
                section_key=section_key,
            ),
            is_open=is_open,
        ),
    ]
    return card


def build_collapsible_section_layout(section: Any, *, page_name: str) -> Any:
    """Build a numbered calibration section through the shared card helper."""
    layout = section.get_layout()
    section_number = getattr(section, "section_number", None)
    if section_number is None or not isinstance(layout, dbc.Card):
        return layout

    return build_calibration_workflow_section_card(
        card=layout,
        page_name=page_name,
        section_number=section_number,
        subtitle=CALIBRATION_WORKFLOW_SUBTITLES.get(page_name, {}).get(
            str(section_number)
        ),
        color_name=getattr(section, "card_color", None),
    )


def build_calibration_workflow_section_card(
    *,
    page_name: str,
    section_number: int,
    subtitle: str | None,
    card: dbc.Card | None = None,
    title: str | None = None,
    body_children: list[Any] | None = None,
    tooltip_text: str | None = None,
    tooltip_target_id: Any | None = None,
    tooltip_id: Any | None = None,
    color_name: str | None = None,
    style_overrides: dict[str, Any] | None = None,
) -> dbc.Card:
    """Build one collapsed, descriptive calibration workflow section card."""
    if card is None:
        if title is None or body_children is None:
            raise ValueError("title and body_children are required when card is omitted")
        from RosettaX.ui.workflow_cards import build_workflow_section_card

        card = build_workflow_section_card(
            section_number=section_number,
            title=title,
            subtitle=subtitle,
            body_children=body_children,
            tooltip_text=tooltip_text,
            tooltip_target_id=tooltip_target_id,
            tooltip_id=tooltip_id,
            color_name=color_name,
            style_overrides=style_overrides,
        )
    else:
        resolved_color_name = color_name or styling.get_workflow_section_color(
            section_number
        )
        ui_forms.apply_workflow_section_card_style(
            card,
            color_name=resolved_color_name,
        )
        _append_card_subtitle(card, subtitle)

    return make_profile_aware_collapsible_card(
        card,
        page_name=page_name,
        section_key=str(section_number),
    )


def _append_card_subtitle(card: dbc.Card, subtitle: str | None) -> None:
    """Add the shared visible subtitle to a legacy workflow card header."""
    if not subtitle:
        return

    card_children = ui_forms.normalize_children(card.children)
    if not card_children or not isinstance(card_children[0], dbc.CardHeader):
        return

    header = card_children[0]
    header.children = [
        *ui_forms.normalize_children(header.children),
        dash.html.Div(
            subtitle,
            style=ui_forms.build_workflow_section_subtitle_style(),
        ),
    ]


def make_profile_aware_collapsible_card(
    card: dbc.Card,
    *,
    page_name: str,
    section_key: str,
) -> dbc.Card:
    """Build a collapsed card until the browser's active profile is available."""
    return make_collapsible_section_card(
        card,
        page_name=page_name,
        section_key=section_key,
        initially_collapsed=True,
    )


def resolve_card_toggle(
    *,
    triggered_id: Any,
    is_open: Any,
    runtime_config_data: Any,
    toggle_clicks: Any = None,
    workflow_step_clicks: Any = None,
) -> tuple[bool, str] | None:
    """Resolve an explicit card action or an active-profile state update.

    Header workflow cards are rebuilt by progress callbacks. Their replacement
    ``n_clicks=0`` values must not be treated as an action, because the target
    section card remains mounted while the header card is recreated.
    """
    if isinstance(triggered_id, dict):
        trigger_type = triggered_id.get("type")

        if trigger_type == WORKFLOW_STEP_CARD_ID_TYPE:
            if not bool(workflow_step_clicks):
                return None
            next_is_open = True
        elif trigger_type == TOGGLE_ID_TYPE:
            if not bool(toggle_clicks):
                return None
            next_is_open = not bool(is_open)
        else:
            return None
    else:
        next_is_open = not profile_collapses_calibration_cards(runtime_config_data)
    return next_is_open, collapse_label(is_open=next_is_open)
