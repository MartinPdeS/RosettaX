import dash
import dash_bootstrap_components as dbc
import json
import re
from dash import dcc, html
from RosettaX.pages.p07_documentation.components import (
    build_documentation_card,
    build_documentation_container,
    build_documentation_guide_header,
)
from RosettaX.workflow.detector.catalog import load_instrument_catalog
from RosettaX.workflow.detector.loader import (
    load_detector_configuration_presets,
)
from RosettaX.workflow.scattering import ModelConfiguration
from RosettaX.workflow.validation_recordings import supported_cytometers

PAGE_NAME = "documentation-supported-cytometers"

SUPPORTED_CYTOMETERS = supported_cytometers()

CATALOG_PATH = "/documentation/supported-cytometers"
def model_slug(*, brand: str, model: str) -> str:
    """Return the stable URL segment for a supported instrument."""
    manufacturer = {"Beckman Coulter": "beckman-coulter", "Miltenyi Biotec": "miltenyi"}.get(brand, brand)
    return re.sub(r"[^a-z0-9]+", "-", f"{manufacturer}-{model}".lower()).strip("-")


MODEL_DETAILS = {
    model_slug(brand=brand, model=model): (brand, model)
    for brand, models in SUPPORTED_CYTOMETERS.items()
    for model in models
}


def build_model_detail_page(*, model: str = "", **_kwargs) -> dbc.Container:
    """Show the Rosetta channels and any packaged detector geometry."""
    back_link = html.A("Supported cytometers", href=CATALOG_PATH)
    if model not in MODEL_DETAILS:
        return build_documentation_container([html.H2("Detector model unavailable"), back_link])

    brand, display_name = MODEL_DETAILS[model]
    preset_model = {"A60 Micro": "A60-Micro Standard", "A50 Micro": "A50-Micro Standard", "MicroPLUS": "MicroPLUS Standard"}.get(
        display_name, display_name,
    )
    instruments = load_instrument_catalog()["instruments"]
    instrument = next((entry for entry in instruments.values() if entry.get("model") == preset_model), {})
    channels = instrument.get("rosetta_channels", {})
    if not channels:
        channels = {
            "FACSymphony A5": {"scattering": ["SSC-H"], "green_fluorescence": ["BB515-H"]},
            "Northern Lights": {"scattering": ["SSC-H"], "green_fluorescence": ["B2-H"]},
        }.get(display_name, {})
    detector_cards = []
    for preset_name, preset in load_detector_configuration_presets().items():
        if preset["instrument"] != preset_model:
            continue
        figure = ModelConfiguration.build_optical_configuration_preview_figure(
            detector_numerical_aperture=preset["detector_numerical_aperture"],
            detector_cache_numerical_aperture=preset.get("detector_cache_numerical_aperture", 0),
            blocker_bar_numerical_aperture=preset.get("blocker_bar_numerical_aperture", 0),
            medium_refractive_index=1.333,
            detector_phi_angle_degree=preset.get("detector_phi_angle_degree", 0),
            detector_gamma_angle_degree=preset.get("detector_gamma_angle_degree", 0),
            detector_sampling=preset["detector_sampling"],
            detector_configuration_preset=preset_name,
        )
        preset_settings = {key: value for key, value in preset.items() if key != "description"}
        preset_json = json.dumps(preset_settings, indent=2, sort_keys=True)
        detector_cards.append(html.Section(
            [
                html.H2(preset_name, className="h5 mb-2"),
                dbc.Row([
                    dbc.Col(dcc.Graph(
                        figure=figure,
                        config={"responsive": True, "displaylogo": False},
                        style={"height": "380px"},
                    ), lg=8),
                    dbc.Col([
                        html.Pre(
                            preset_json,
                            className="small overflow-auto mb-0 p-3 border rounded",
                            style={"height": "340px", "whiteSpace": "pre-wrap", "overflowWrap": "anywhere"},
                        ),
                    ], lg=4),
                ], className="g-3 align-items-center"),
            ],
            className="border rounded p-3",
        ))
    return build_documentation_container(
        [
            build_documentation_guide_header(
                hero_id=f"{PAGE_NAME}-{model}",
                title=f"{brand} {display_name}",
                description="Rosetta channels and detector geometry.",
                related=[("Supported cytometers", CATALOG_PATH)],
            ),
            html.Div([
                build_documentation_card(
                    title="Rosetta detector channels",
                    subtitle="Channel names used by Rosetta for this model.",
                    body=[html.Dl([
                        html.Dt("Scattering"), html.Dd(", ".join(channels.get("scattering") or []) or "Select from the FCS file"),
                        html.Dt("Green fluorescence"), html.Dd(", ".join(channels.get("green_fluorescence") or []) or "Select from the FCS file"),
                    ], className="mb-0")],
                    min_height="unset",
                ),
                html.Div(detector_cards, className="d-grid gap-3", style={"gridAutoRows": "1fr"}) if detector_cards else None,
                *([] if detector_cards else [dbc.Alert(
                    "A 3D preview is available when RosettaX has a dedicated geometry preset for the model. "
                    "This model has a validation recording but no packaged geometry preset.",
                    color="secondary", className="mb-0",
                )]),
            ], className="d-grid gap-3 mt-3"),
        ],
        class_name="rosettax-docs-guide",
    )


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
                build_documentation_guide_header(
                    hero_id=self._id("hero"),
                    title="Supported Flow Cytometers",
                    description="See which instruments have FCS recordings in the Rosetta validation suite and browse packaged detector presets.",
                    related=[
                        ("Peak scripts", "/documentation/peak-scripts"),
                        ("Regression models", "/documentation/regression-models"),
                    ],
                ),
                self._supported_cytometers_card(),
                html.Div(style={"height": "18px"}),
                dbc.Row(
                    [
                        dbc.Col(self._selection_guidance_card(), lg=6),
                        dbc.Col(self._support_meaning_card(), lg=6),
                    ],
                    className="g-3",
                ),
                html.Div(style={"height": "18px"}),
                dbc.Row(
                    [
                        dbc.Col(self._review_checklist_card(), lg=6),
                        dbc.Col(self._request_support_card(), lg=6),
                    ],
                    className="g-3",
                ),
            ],
            class_name="rosettax-docs-guide",
        )

    def _supported_cytometers_card(self) -> dbc.Card:
        """List instrument models represented in cross-device Rosetta validation."""
        return build_documentation_card(
            title="Supported cytometers",
            subtitle="Each model has a recording in the Rosetta validation suite. Some recordings exercise warning paths when the data cannot support sizing.",
            body=[dbc.Table(
                [
                    html.Thead(html.Tr([html.Th("Manufacturer"), html.Th("Model"), html.Th("3D geometry")])),
                    html.Tbody([
                        html.Tr([
                            html.Td(brand),
                            html.Td(html.A(model, href=f"{CATALOG_PATH}/{model_slug(brand=brand, model=model)}")),
                            html.Td("Available" if model in {"A60 Micro", "FACSLyric", "FACSymphony A1", "Aurora"} else "—"),
                        ])
                        for brand, models in SUPPORTED_CYTOMETERS.items()
                        for model in models
                    ]),
                ],
                responsive=True, hover=True, className="rosettax-docs-table mb-0",
            )],
        )

    def _support_meaning_card(self) -> dbc.Card:
        return build_documentation_card(
            title="What support means",
            subtitle="A supported cytometer is not a promise that every vendor option has been fully reverse engineered.",
            body=[
                html.Div(
                    "The supported list reflects the models represented in the cross-device FCS validation suite. A dedicated detector geometry preset is available for some models.",
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
    path=CATALOG_PATH,
    name="Supported Cytometers Documentation",
    layout=layout,
)


dash.register_page(
    f"{__name__}.detector_model",
    path_template=f"{CATALOG_PATH}/<model>",
    name="Cytometer detector geometry",
    layout=build_model_detail_page,
)
