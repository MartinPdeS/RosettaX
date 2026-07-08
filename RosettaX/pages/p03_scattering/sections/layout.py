# -*- coding: utf-8 -*-

import dash

from ..state import ScatteringPageState


def build_page_layout(page, sections) -> dash.html.Div:
    """
    Build the scattering page layout from the section instances.
    """
    return dash.html.Div(
        [
            dash.dcc.Store(
                id=page.ids.State.page_state_store,
                data=ScatteringPageState.empty().to_dict(),
                storage_type="session",
            ),
            dash.html.Div(
                [
                    section.get_layout()
                    for section in sections
                ],
                style={
                    "display": "flex",
                    "flexDirection": "column",
                    "gap": "18px",
                },
            ),
        ]
    )
