# -*- coding: utf-8 -*-

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, ctx, html, no_update

from RosettaX.pages.p07_documentation.components import (
    build_documentation_card,
    build_documentation_container,
    build_documentation_hero,
    build_documentation_link_chip,
)
from RosettaX.workflow.detector.loader import load_detector_configuration_preset_catalog


PAGE_NAME = "documentation-supported-cytometers"

FIGURE_ENTRIES_BY_BRAND: dict[str, list[tuple[str, str]]] = {
    "Agilent": [
        ("/assets/detector_figures/agilent_novocyte_fsc.png", "NovoCyte FSC"),
        ("/assets/detector_figures/agilent_novocyte_ssc.png", "NovoCyte SSC"),
    ],
    "Apogee": [
        ("/assets/detector_figures/apogee_a60_forward.png", "A60-Micro Forward"),
        ("/assets/detector_figures/apogee_a60_side.png", "A60-Micro Side"),
    ],
    "BD Biosciences": [
        ("/assets/detector_figures/bd_facscanto2_fsc.png", "FACSCanto II FSC"),
        ("/assets/detector_figures/bd_facscanto2_ssc.png", "FACSCanto II SSC"),
    ],
    "Beckman Coulter Life Sciences": [
        ("/assets/detector_figures/beckman_cyttofelx_flourescence.png", "CytoFLEX Fluorescence"),
        ("/assets/detector_figures/beckman_cyttofelx_ssc.png", "CytoFLEX SSC"),
    ],
    "Cytek Biosciences": [
        ("/assets/detector_figures/cytek_aurora_fsc.png", "Aurora FSC"),
        ("/assets/detector_figures/cytek_aurora_ssc.png", "Aurora SSC"),
    ],
    "nanoFCM": [
        ("/assets/detector_figures/nanofcm_nanoanalyzer_fsc.png", "NanoAnalyzer FSC"),
        ("/assets/detector_figures/nanofcm_nanoanalyzer_ssc.png", "NanoAnalyzer SSC"),
    ],
    "Sony Biosciences": [
        ("/assets/detector_figures/sony_id7000_fsc.png", "ID7000 FSC"),
        ("/assets/detector_figures/sony_id7000_ssc.png", "ID7000 SSC"),
    ],
    "Thermo Fisher Scientific": [
        ("/assets/detector_figures/thermofisher_attune_fsc.png", "Attune NxT FSC"),
        ("/assets/detector_figures/thermofisher_attune_ssc.png", "Attune NxT SSC"),
    ],
}


def _build_figure_button_id(brand_name: str, figure_label: str) -> str:
    cleaned_value = "".join(
        character.lower() if character.isalnum() else "-"
        for character in f"{brand_name}-{figure_label}"
    )
    while "--" in cleaned_value:
        cleaned_value = cleaned_value.replace("--", "-")
    return f"{PAGE_NAME}-figure-open-{cleaned_value.strip('-')}"


FIGURE_BUTTON_MAP: dict[str, tuple[str, str, str]] = {
    _build_figure_button_id(brand_name, figure_label): (brand_name, figure_src, figure_label)
    for brand_name, entries in FIGURE_ENTRIES_BY_BRAND.items()
    for figure_src, figure_label in entries
}

FIGURE_MODAL_ID = f"{PAGE_NAME}-figure-modal"
FIGURE_MODAL_IMAGE_ID = f"{PAGE_NAME}-figure-modal-image"
FIGURE_MODAL_TITLE_ID = f"{PAGE_NAME}-figure-modal-title"
FIGURE_MODAL_CLOSE_ID = f"{PAGE_NAME}-figure-modal-close"


class SupportedCytometersDocumentationPage:
    """
    Detailed documentation for supported cytometer presets.
    """

    def __init__(self) -> None:
        self.page_name = PAGE_NAME
        self.contact_email = "martin.poinsinet.de.sivry@gmail.com"

    def _id(self, name: str) -> str:
        return f"{self.page_name}-{name}"

    def layout(self, **_kwargs) -> dbc.Container:
        return build_documentation_container(
            [
                build_documentation_hero(
                    hero_id=self._id("hero"),
                    title="Supported Flow Cytometers",
                    description=(
                        "This page documents the detector preset catalog used by RosettaX for scattering workflows. "
                        "It explains what “support” means in practice, what assumptions each preset family carries, "
                        "and what information is needed to add a new cytometer family responsibly."
                    ),
                ),
                html.Div(style={"height": "18px"}),
                build_documentation_card(
                    title="Related pages",
                    subtitle="The documentation hub ties detector support back to the broader calibration model.",
                    body=[
                        html.Div(
                            [
                                build_documentation_link_chip(
                                    label="Back to documentation hub",
                                    href="/documentation",
                                ),
                                build_documentation_link_chip(
                                    label="Peak scripts",
                                    href="/documentation/peak-scripts",
                                ),
                                build_documentation_link_chip(
                                    label="Regression models",
                                    href="/documentation/regression-models",
                                ),
                            ],
                            style={
                                "display": "flex",
                                "flexWrap": "wrap",
                                "gap": "10px",
                            },
                        ),
                    ],
                    min_height="unset",
                ),
                html.Div(style={"height": "18px"}),
                dbc.Row(
                    [
                        dbc.Col(self._catalog_card(), lg=7),
                        dbc.Col(self._support_meaning_card(), lg=5),
                    ],
                    className="g-3",
                ),
                html.Div(style={"height": "18px"}),
                dbc.Row(
                    [
                        dbc.Col(self._selection_guidance_card(), lg=6),
                        dbc.Col(self._review_checklist_card(), lg=6),
                    ],
                    className="g-3",
                ),
                html.Div(style={"height": "18px"}),
                self._request_support_card(),
                self._figure_preview_modal(),
            ]
        )

    def _catalog_card(self) -> dbc.Card:
        catalog = load_detector_configuration_preset_catalog()
        grouped_rows: dict[str, list[str]] = {}

        for item in catalog:
            if item["brand"] == "Custom":
                continue
            grouped_rows.setdefault(item["brand"], []).append(item["label"])

        table = dbc.Table(
            [
                html.Thead(
                    html.Tr(
                        [
                            html.Th("Brand", style={"width": "22%"}),
                            html.Th("Supported models / detector presets", style={"width": "36%"}),
                            html.Th("Detector geometry figures"),
                        ]
                    )
                ),
                html.Tbody(
                    [
                        html.Tr(
                            [
                                html.Td(brand_name, style={"fontWeight": "700"}),
                                html.Td(", ".join(model_labels), style={"opacity": 0.84}),
                                html.Td(self._build_brand_figure_cell(brand_name)),
                            ]
                        )
                        for brand_name, model_labels in grouped_rows.items()
                    ]
                ),
            ],
            bordered=False,
            hover=False,
            responsive=True,
            size="sm",
            style={"marginBottom": "0px"},
        )

        return build_documentation_card(
            title="Packaged detector preset catalog",
            subtitle="These are the preset groups RosettaX can currently recognize or use as documented scattering geometries.",
            body=[
                html.Div(
                    f"RosettaX currently ships {len(catalog)} packaged detector presets across {len(grouped_rows)} brand groups.",
                    style={"marginBottom": "10px"},
                ),
                table,
            ],
        )

    def _build_brand_figure_cell(self, brand_name: str) -> html.Div:
        figure_entries = FIGURE_ENTRIES_BY_BRAND.get(brand_name, [])

        if not figure_entries:
            return html.Div(
                "Placeholder: detector figures not added yet.",
                style={
                    "fontStyle": "italic",
                    "opacity": 0.72,
                },
            )

        return html.Div(
            [
                dbc.Button(
                    [
                        html.Img(
                            src=figure_src,
                            alt=f"{brand_name} {figure_label} detector geometry figure",
                            style={
                                "width": "100%",
                                "height": "auto",
                                "borderRadius": "8px",
                                "border": "1px solid rgba(0, 0, 0, 0.14)",
                                "display": "block",
                            },
                        ),
                        html.Div(
                            figure_label,
                            style={
                                "fontSize": "0.74rem",
                                "opacity": 0.78,
                                "marginTop": "4px",
                                "textAlign": "center",
                            },
                        ),
                    ],
                    id=_build_figure_button_id(brand_name, figure_label),
                    style={
                        "width": "128px",
                        "padding": "0px",
                        "border": "0px",
                        "background": "transparent",
                    },
                    n_clicks=0,
                )
                for figure_src, figure_label in figure_entries
            ],
            style={
                "display": "flex",
                "gap": "8px",
                "flexWrap": "wrap",
            },
        )

    def _figure_preview_modal(self) -> dbc.Modal:
        return dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Detector geometry preview", id=FIGURE_MODAL_TITLE_ID)),
                dbc.ModalBody(
                    html.Img(
                        id=FIGURE_MODAL_IMAGE_ID,
                        src="",
                        alt="Detector geometry preview",
                        style={
                            "width": "100%",
                            "height": "auto",
                            "borderRadius": "8px",
                            "border": "1px solid rgba(0, 0, 0, 0.14)",
                            "display": "block",
                        },
                    )
                ),
                dbc.ModalFooter(
                    dbc.Button(
                        "Close",
                        id=FIGURE_MODAL_CLOSE_ID,
                        className="ms-auto",
                        n_clicks=0,
                    )
                ),
            ],
            id=FIGURE_MODAL_ID,
            is_open=False,
            size="xl",
            centered=True,
            scrollable=True,
        )

    def _support_meaning_card(self) -> dbc.Card:
        return build_documentation_card(
            title="What support means",
            subtitle="A supported cytometer is not a promise that every vendor option has been fully reverse engineered.",
            body=[
                html.Div(
                    "In RosettaX, support means there is a documented detector preset family that can be selected, reviewed, and reused consistently. That preset combines an instrument alias strategy with an explicit scattering geometry assumption.",
                ),
                html.Div(
                    "The point is reproducibility. Two users should be able to see the same preset label and know which geometry assumptions were used when the scattering calibration was fit.",
                ),
                html.Div(
                    "If your instrument has an unusual filter train or detector layout, the closest packaged preset may still be a useful starting point, but it should not be treated as a claim of exact vendor equivalence.",
                ),
            ],
        )

    def _request_support_card(self) -> dbc.Card:
        return build_documentation_card(
            title="How to request a new cytometer family",
            subtitle="Good support requests contain enough evidence to justify a reusable preset rather than a one-off workaround.",
            body=[
                html.Div("The most helpful starting point is one representative FCS file whose metadata contains the instrument name exactly as exported by the cytometer software."),
                html.Div("It also helps to include the scatter-channel labels you want RosettaX to recognize and any public optical notes that justify the detector geometry you expect to use."),
                dbc.Alert(
                    [
                        "Support contact: ",
                        html.A(
                            self.contact_email,
                            href=f"mailto:{self.contact_email}",
                            style={"textDecoration": "none"},
                        ),
                    ],
                    color="secondary",
                    style={
                        "marginBottom": "0px",
                        "borderRadius": "10px",
                    },
                ),
            ],
            min_height="unset",
        )

    def _selection_guidance_card(self) -> dbc.Card:
        return build_documentation_card(
            title="How to choose a detector preset",
            subtitle="Use model family, channel semantics, and fit behavior together rather than relying on instrument name alone.",
            body=[
                html.Div("Start with the preset family whose brand and model labels match the FCS metadata closest."),
                html.Div("Confirm the selected channel behaves like the expected detector type (forward, side, fluorescence-like) for that preset."),
                html.Div("If multiple presets appear plausible, compare calibration fit consistency across the same standard table before deciding."),
                html.Div("Treat preset selection as a modeling choice to be recorded, not a hidden implementation detail."),
            ],
            min_height="unset",
        )

    def _review_checklist_card(self) -> dbc.Card:
        return build_documentation_card(
            title="Preset review checklist",
            subtitle="Use this checklist when you onboard a new cytometer configuration to avoid silent drift.",
            body=[
                html.Div("Check channel aliases and auto-detect behavior against at least one representative FCS file."),
                html.Div("Regenerate detector geometry figures and verify they match the intended collection orientation."),
                html.Div("Run a known calibration standard and compare slope stability with expected instrument behavior."),
                html.Div("Capture limitations explicitly if one preset is only valid for specific lasers or channels."),
            ],
            min_height="unset",
        )


_page = SupportedCytometersDocumentationPage()
layout = _page.layout


dash.register_page(
    __name__,
    path="/documentation/supported-cytometers",
    name="Supported Cytometers Documentation",
    layout=layout,
)


@callback(
    Output(FIGURE_MODAL_ID, "is_open"),
    Output(FIGURE_MODAL_IMAGE_ID, "src"),
    Output(FIGURE_MODAL_IMAGE_ID, "alt"),
    Output(FIGURE_MODAL_TITLE_ID, "children"),
    [Input(button_id, "n_clicks") for button_id in FIGURE_BUTTON_MAP] + [Input(FIGURE_MODAL_CLOSE_ID, "n_clicks")],
    State(FIGURE_MODAL_ID, "is_open"),
    prevent_initial_call=True,
)
def _toggle_figure_preview_modal(*callback_args):
    triggered_id = ctx.triggered_id

    if triggered_id == FIGURE_MODAL_CLOSE_ID:
        return False, no_update, no_update, no_update

    if triggered_id in FIGURE_BUTTON_MAP:
        brand_name, figure_src, figure_label = FIGURE_BUTTON_MAP[triggered_id]
        return (
            True,
            figure_src,
            f"{brand_name} {figure_label} detector geometry preview",
            f"{brand_name} - {figure_label}",
        )

    return no_update, no_update, no_update, no_update
