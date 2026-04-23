# -*- coding: utf-8 -*-

import dash_bootstrap_components as dbc

from RosettaX.utils import ui_forms


class Header:
    def __init__(self, page) -> None:
        self.page = page

    def get_layout(self) -> dbc.Card:
        return dbc.Card(
            dbc.CardBody(
                [
                    ui_forms.build_section_intro(
                        title="Apply calibration",
                        title_component="H2",
                        description=(
                            "Use this page when you already have a saved calibration and want to apply it "
                            "to one or more FCS files. Select the calibration payload, upload the target "
                            "files, choose the relevant detector mapping, and export calibrated outputs."
                        ),
                    )
                ]
            ),
            id=self.page.ids.Header.container,
        )

    def register_callbacks(self) -> None:
        pass