# -*- coding: utf-8 -*-

from typing import Any

import dash
import dash_bootstrap_components as dbc

from RosettaX.utils import ui_forms
from RosettaX.utils.runtime_config import RuntimeConfig


TOGGLE_ID_TYPE = "calibration-card-toggle"
COLLAPSE_ID_TYPE = "calibration-card-collapse"
TOGGLE_LABEL_ID_TYPE = "calibration-card-toggle-label"


def _component_id(*, id_type: str, page_name: str, section_key: str) -> dict[str, str]:
    return {
        "type": id_type,
        "page": page_name,
        "section": section_key,
    }


def profile_collapses_calibration_cards(runtime_config_data: Any = None) -> bool:
    """Return the active profile's calibration-card initial state."""
    runtime_config = RuntimeConfig.from_dict(
        runtime_config_data if isinstance(runtime_config_data, dict) else None
    )
    return runtime_config.get_bool("ui.collapse_calibration_cards", default=False)


def collapse_label(*, is_open: bool) -> str:
    """Build the compact action label shown in a workflow card header."""
    return "Hide" if is_open else "Show"


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
    """Build a section and collapse numbered workflow cards."""
    layout = section.get_layout()
    section_number = getattr(section, "section_number", None)
    if section_number is None or not isinstance(layout, dbc.Card):
        return layout

    return make_profile_aware_collapsible_card(
        layout,
        page_name=page_name,
        section_key=str(section_number),
    )


def make_profile_aware_collapsible_card(
    card: dbc.Card,
    *,
    page_name: str,
    section_key: str,
) -> dbc.Card:
    """Apply the bundled default profile's initial state to a workflow card."""
    return make_collapsible_section_card(
        card,
        page_name=page_name,
        section_key=section_key,
        initially_collapsed=profile_collapses_calibration_cards(
            RuntimeConfig.from_default_profile().to_dict()
        ),
    )


def resolve_card_toggle(
    *,
    triggered_id: Any,
    is_open: Any,
    runtime_config_data: Any,
) -> tuple[bool, str]:
    """Resolve a click toggle or reset the card from a newly loaded profile."""
    if isinstance(triggered_id, dict) and triggered_id.get("type") == TOGGLE_ID_TYPE:
        next_is_open = not bool(is_open)
    else:
        next_is_open = not profile_collapses_calibration_cards(runtime_config_data)
    return next_is_open, collapse_label(is_open=next_is_open)
