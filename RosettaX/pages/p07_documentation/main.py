# -*- coding: utf-8 -*-

import dash
import dash_bootstrap_components as dbc
from dash import html

from RosettaX.utils import ui_forms
from RosettaX.workflow.detector.loader import load_detector_configuration_preset_catalog


class DocumentationPage:
    """
    Under-the-hood documentation for RosettaX.

    This page explains how RosettaX models fluorescence and scattering
    calibrations, what is written into calibration files, and which checks are
    enforced before calibrated exports are produced.
    """

    def __init__(self) -> None:
        self.page_name = "documentation"
        self.reference_docs_url = "https://martinpdes.github.io/RosettaX/docs/latest/index.html"
        self.github_url = "https://github.com/MartinPdeS/RosettaX"

    def _id(self, name: str) -> str:
        return f"{self.page_name}-{name}"

    def layout(self, **_kwargs) -> dbc.Container:
        return dbc.Container(
            [
                self._hero_section(),
                html.Div(style={"height": "18px"}),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                self._table_of_contents_card(),
                                html.Div(style={"height": "18px"}),
                                self._resource_card(),
                            ],
                            lg=3,
                        ),
                        dbc.Col(
                            [
                                self._section_wrapper(
                                    section_id=self._id("system-model"),
                                    child=self._system_model_row(),
                                ),
                                html.Div(style={"height": "18px"}),
                                self._section_wrapper(
                                    section_id=self._id("supported-cytometers"),
                                    child=self._supported_cytometers_card(),
                                ),
                                html.Div(style={"height": "18px"}),
                                self._section_wrapper(
                                    section_id=self._id("refractive-index"),
                                    child=self._refractive_index_card(),
                                ),
                                html.Div(style={"height": "18px"}),
                                self._section_wrapper(
                                    section_id=self._id("regression-models"),
                                    child=self._regression_row(),
                                ),
                                html.Div(style={"height": "18px"}),
                                self._section_wrapper(
                                    section_id=self._id("calibration-files"),
                                    child=self._calibration_files_row(),
                                ),
                                html.Div(style={"height": "18px"}),
                                self._section_wrapper(
                                    section_id=self._id("apply-checks"),
                                    child=self._apply_checks_card(),
                                ),
                                html.Div(style={"height": "18px"}),
                                self._section_wrapper(
                                    section_id=self._id("reports"),
                                    child=self._reports_card(),
                                ),
                            ],
                            lg=9,
                        ),
                    ],
                    className="g-3",
                ),
            ],
            fluid=True,
            style={
                "paddingTop": "12px",
                "paddingBottom": "40px",
            },
        )

    def _hero_section(self) -> dbc.Card:
        card = dbc.Card(
            dbc.CardBody(
                [
                    html.Div(
                        "Documentation",
                        id=self._id("hero"),
                        style={
                            "fontWeight": "800",
                            "fontSize": "2.45rem",
                            "lineHeight": "1.05",
                            "marginBottom": "10px",
                        },
                    ),
                    html.Div(
                        (
                            "This page is the technical reference for what RosettaX is doing under the hood: "
                            "how refractive indices are resolved, which regression models are fitted, what is "
                            "saved into calibration JSON files, and which checks guard the apply workflow."
                        ),
                        style={
                            "fontSize": "1.05rem",
                            "opacity": 0.84,
                            "maxWidth": "980px",
                            "marginBottom": "0px",
                        },
                    ),
                ],
                style={"padding": "26px"},
            )
        )

        return ui_forms.apply_workflow_section_card_style(
            card=card,
            header_font_weight="750",
            header_font_size="1.02rem",
        )

    def _table_of_contents_card(self) -> dbc.Card:
        card = dbc.Card(
            [
                dbc.CardHeader(
                    [
                        html.Div(
                            "On this page",
                            style={"fontWeight": "750", "fontSize": "1.02rem"},
                        ),
                        html.Div(
                            "Jump to the part of the implementation you want to inspect.",
                            style={"fontSize": "0.86rem", "opacity": 0.76, "marginTop": "3px"},
                        ),
                    ]
                ),
                dbc.CardBody(
                    [
                        self._toc_link("System model", f"#{self._id('system-model')}"),
                        self._toc_link("Supported cytometers", f"#{self._id('supported-cytometers')}"),
                        self._toc_link("Material refractive index", f"#{self._id('refractive-index')}"),
                        self._toc_link("Regression models", f"#{self._id('regression-models')}"),
                        self._toc_link("Calibration files", f"#{self._id('calibration-files')}"),
                        self._toc_link("Apply checks", f"#{self._id('apply-checks')}"),
                        self._toc_link("Reports and provenance", f"#{self._id('reports')}"),
                    ],
                    style={"padding": "16px", "display": "flex", "flexDirection": "column", "gap": "10px"},
                ),
            ],
            style={"position": "sticky", "top": "12px"},
        )

        return ui_forms.apply_workflow_section_card_style(
            card=card,
            header_font_weight="750",
            header_font_size="1.02rem",
        )

    def _toc_link(self, label: str, href: str) -> html.A:
        return html.A(
            label,
            href=href,
            style={
                "textDecoration": "none",
                "fontWeight": "600",
                "padding": "10px 12px",
                "borderRadius": "10px",
                "border": "1px solid rgba(13, 110, 253, 0.14)",
                "background": "rgba(13, 110, 253, 0.04)",
                "display": "block",
            },
        )

    def _resource_card(self) -> dbc.Card:
        card = dbc.Card(
            [
                dbc.CardHeader(
                    [
                        html.Div(
                            "More resources",
                            style={"fontWeight": "750", "fontSize": "1.02rem"},
                        ),
                        html.Div(
                            "Use Documentation for internals. Use Help for getting started and debugging.",
                            style={"fontSize": "0.86rem", "opacity": 0.76, "marginTop": "3px"},
                        ),
                    ]
                ),
                dbc.CardBody(
                    [
                        dbc.Button(
                            "Open reference documentation",
                            href=self.reference_docs_url,
                            target="_blank",
                            rel="noopener noreferrer",
                            color="primary",
                            style={"width": "100%", "marginBottom": "10px"},
                        ),
                        dbc.Button(
                            "View source on GitHub",
                            href=self.github_url,
                            target="_blank",
                            rel="noopener noreferrer",
                            color="secondary",
                            outline=True,
                            style={"width": "100%"},
                        ),
                    ],
                    style={"padding": "16px"},
                ),
            ]
        )

        return ui_forms.apply_workflow_section_card_style(
            card=card,
            header_font_weight="750",
            header_font_size="1.02rem",
        )

    def _system_model_row(self) -> dbc.Row:
        return dbc.Row(
            [
                dbc.Col(self._fcs_system_card(), lg=6),
                dbc.Col(self._scattering_optics_card(), lg=6),
            ],
            className="g-3",
        )

    def _fcs_system_card(self) -> dbc.Card:
        return self._content_card(
            title="What kind of system RosettaX assumes",
            subtitle="RosettaX analyzes exported FCS data. It does not control the cytometer.",
            body=[
                html.Div(
                    "RosettaX assumes a standard event table exported from a flow cytometer, where each row is one event and each selected channel is an already processed instrument observable rather than a raw optical power trace.",
                ),
                html.Div(
                    "For fluorescence, the software works with one selected detector column plus optional gating context. For scattering, it treats the selected detector column as the measured instrument response that must be mapped to modeled optical coupling.",
                ),
                html.Div(
                    "The application therefore sits after acquisition: it inspects histograms and tables, fits calibration relations, serializes calibration records, and later re-applies those records to other FCS files.",
                ),
            ],
        )

    def _scattering_optics_card(self) -> dbc.Card:
        return self._content_card(
            title="Scattering optical model",
            subtitle="The scattering workflow uses a single-wavelength source plus photodiode-style collection geometry.",
            body=[
                html.Div(
                    "The scattering backend builds a Gaussian illumination source and a photodiode detector model through PyMieSim. The configurable optical terms are wavelength, detector NA, cache NA, blocker-bar NA, detector phi offset, detector gamma offset, and detector sampling.",
                ),
                html.Div(
                    "Internally, the modeled source defaults to optical power = 1.0 W, source numerical aperture = 0.1, and polarization angle = 0 degrees. Detector presets can inject angular weights and effective geometry corrections before coupling is computed.",
                ),
                html.Div(
                    "That means RosettaX is calibrating a measured scatter channel against a modeled collection geometry, not against raw Mie intensity integrated over an unspecified instrument.",
                ),
            ],
        )

    def _refractive_index_card(self) -> dbc.Card:
        return self._content_card(
            title="Material refractive index resolution",
            subtitle="Material presets are converted to numeric refractive indices at the selected wavelength.",
            body=[
                html.Div(
                    "When you choose a material such as water, PBS, polystyrene, silica, PMMA, lipid, or phospholipid, RosettaX resolves the refractive index from the packaged Sellmeier bank in RosettaX/assets/sellmeier_equations.json.",
                ),
                html.Pre(
                    "n^2 = a + sum(B_i * lambda^2 / (lambda^2 - C_i))\nwith lambda converted from nm to um before evaluation.",
                    style=self._pre_style(),
                ),
                html.Div(
                    "If the preset is a plain number, RosettaX uses that number directly. If a material source is empty or cannot be resolved, the workflow falls back to the numeric value already present in the input box.",
                ),
                html.Div(
                    "This matters in scattering because wavelength changes can update both medium and particle refractive indices before the Mie relation or calibration-standard model is computed.",
                ),
            ],
        )

    def _supported_cytometers_card(self) -> dbc.Card:
        grouped_rows: dict[str, list[str]] = {}

        for item in load_detector_configuration_preset_catalog():
            grouped_rows.setdefault(item["brand"], []).append(item["label"])

        table = dbc.Table(
            [
                html.Thead(
                    html.Tr(
                        [
                            html.Th("Brand", style={"width": "28%"}),
                            html.Th("Supported models / detector presets"),
                        ]
                    )
                ),
                html.Tbody(
                    [
                        html.Tr(
                            [
                                html.Td(brand_name, style={"fontWeight": "700"}),
                                html.Td(
                                    ", ".join(model_labels),
                                    style={"opacity": 0.84},
                                ),
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
            style={"marginBottom": "12px"},
        )

        return self._content_card(
            title="Supported cytometers and detector presets",
            subtitle="RosettaX currently ships these detector-preset groups for scattering modeling and auto-detect support.",
            body=[
                html.Div(
                    "The support list reflects the packaged detector preset bank. These presets encode modeled detector geometry, not a guarantee that every channel on every instrument configuration is already covered.",
                ),
                table,
                dbc.Alert(
                    "If your company would like RosettaX to support another cytometer, contact the maintainer with an example FCS file, the detector or channel naming you want recognized, and any public optical-geometry documentation that should inform the preset.",
                    color="secondary",
                    style={
                        "marginBottom": "0px",
                        "borderRadius": "10px",
                    },
                ),
            ],
        )

    def _regression_row(self) -> dbc.Row:
        return dbc.Row(
            [
                dbc.Col(self._fluorescence_regression_card(), lg=6),
                dbc.Col(self._scattering_regression_card(), lg=6),
            ],
            className="g-3",
        )

    def _fluorescence_regression_card(self) -> dbc.Card:
        return self._content_card(
            title="Fluorescence regression",
            subtitle="Fluorescence calibration is fitted as a log-log linear relation, equivalent to a power law.",
            body=[
                html.Pre(
                    "log10(y) = slope * log10(x) + intercept\ny = (10**intercept) * x**slope",
                    style=self._pre_style(),
                ),
                html.Div(
                    "Before fitting, RosettaX removes non-finite points and any pair where either the measured intensity or calibrated reference value is not strictly positive. The fit itself uses numpy.polyfit on the log10-transformed axes.",
                ),
                html.Div(
                    "The saved fluorescence payload keeps slope, intercept, prefactor, R², point count, source channel, optional gating channel and threshold, and the explicit reference-point table used for the fit.",
                ),
            ],
        )

    def _scattering_regression_card(self) -> dbc.Card:
        return self._content_card(
            title="Scattering regression",
            subtitle="Scattering calibration fits measured peak position to modeled optical coupling with a linear instrument-response model.",
            body=[
                html.Pre(
                    "theoretical_coupling = slope * measured_peak + intercept",
                    style=self._pre_style(),
                ),
                html.Div(
                    "RosettaX first computes modeled coupling for the calibration-standard particles from the selected Mie model and optical parameters. It then fits a linear response from measured peak positions to those coupling values. The default behavior fixes the intercept to zero.",
                ),
                html.Div(
                    "Only finite calibration pairs are used. For zero-intercept fits, RosettaX also requires non-zero measured peaks so the denominator stays valid. The saved calibration stores slope, intercept, R², whether zero-intercept was enforced, the reference table, and the full calibration-standard Mie relation.",
                ),
            ],
        )

    def _calibration_files_row(self) -> dbc.Row:
        return dbc.Row(
            [
                dbc.Col(self._calibration_record_card(), lg=6),
                dbc.Col(self._payload_details_card(), lg=6),
            ],
            className="g-3",
        )

    def _calibration_record_card(self) -> dbc.Card:
        return self._content_card(
            title="Calibration file wrapper",
            subtitle="Every saved calibration is wrapped in the same outer record.",
            body=[
                html.Pre(
                    '{\n  "schema": "rosettax_calibration_v1",\n  "kind": "fluorescence" | "scattering",\n  "created_at": "...",\n  "name": "...",\n  "payload": { ... }\n}',
                    style=self._pre_style(),
                ),
                html.Div(
                    "The outer wrapper is created by the shared save workflow. The inner payload differs by calibration type and is what the apply workflow actually interprets later.",
                ),
            ],
        )

    def _payload_details_card(self) -> dbc.Card:
        return self._content_card(
            title="What the inner payload contains",
            subtitle="Fluorescence and scattering payloads preserve different kinds of evidence.",
            body=[
                html.Div(
                    "Fluorescence payloads store fit_model, fit_metrics, parameters, reference_points, source_channel, optional gating metadata, and a legacy-compatible payload block used during apply.",
                ),
                html.Div(
                    "Scattering payloads store instrument_response, calibration_standard_mie_relation, reference_table, source_channel, output_quantity, version, and metadata describing the optical assumptions and standard table context.",
                ),
                html.Div(
                    "In both cases, the goal is the same: another user should be able to inspect the JSON and understand what was fitted without reopening the original session.",
                ),
            ],
        )

    def _apply_checks_card(self) -> dbc.Card:
        return self._content_card(
            title="Checks performed while applying a calibration",
            subtitle="Apply is not a blind export step. It validates both the request and the target model before producing output.",
            body=[
                html.Div(
                    "At the request level, RosettaX requires at least one uploaded FCS file, a selected calibration, and a non-empty calibration payload. It also resolves the source channel from the payload and fails if that channel is missing.",
                ),
                html.Div(
                    "If the calibration is scattering, target model parameters are mandatory. Diameter grids must be positive and ordered correctly, refractive indices must be finite and physically valid, and the requested source channel must exist in each input dataframe.",
                ),
                html.Div(
                    "For scattering diameter inversion, RosettaX checks whether the target Mie relation is strictly monotonic over the full requested range. If it is not, the apply workflow automatically selects the largest monotonic branch and records a warning so the export remains auditable.",
                ),
                html.Div(
                    "Export columns are normalized before writing output, and warnings collected during the apply run are surfaced again in the PDF report and result payload.",
                ),
            ],
        )

    def _reports_card(self) -> dbc.Card:
        return self._content_card(
            title="Reports and provenance",
            subtitle="The PDF report documents one apply/export run. It complements the calibration JSON instead of replacing it.",
            body=[
                html.Div(
                    "The apply report records the selected calibration, uploaded FCS paths, chosen export columns, output channels, warnings, and a sanitized snapshot of the saved calibration payload so the run can still be interpreted later.",
                ),
                html.Div(
                    "When the export artifact is a ZIP archive, the PDF is embedded into that bundle alongside the calibrated FCS files. This keeps the artifact and its provenance together instead of relying on a separate note or screenshot.",
                ),
                html.Div(
                    "Use the JSON to answer what the calibration is. Use the PDF to answer what happened during this particular apply run.",
                ),
            ],
        )

    def _pre_style(self) -> dict[str, str]:
        return {
            "marginBottom": "10px",
            "padding": "12px 14px",
            "borderRadius": "10px",
            "border": "1px solid rgba(13, 110, 253, 0.16)",
            "background": "rgba(13, 110, 253, 0.04)",
            "fontSize": "0.9rem",
            "lineHeight": "1.45",
            "whiteSpace": "pre-wrap",
        }

    def _content_card(self, *, title: str, subtitle: str, body: list[html.Div | html.Pre]) -> dbc.Card:
        card = dbc.Card(
            [
                dbc.CardHeader(
                    [
                        html.Div(title, style={"fontWeight": "750", "fontSize": "1.02rem"}),
                        html.Div(subtitle, style={"fontSize": "0.86rem", "opacity": 0.76, "marginTop": "3px"}),
                    ]
                ),
                dbc.CardBody(
                    body,
                    style={"padding": "16px"},
                ),
            ],
            style={"height": "100%"},
        )

        return ui_forms.apply_workflow_section_card_style(
            card=card,
            header_font_weight="750",
            header_font_size="1.02rem",
        )

    def _section_wrapper(self, *, section_id: str, child: html.Div) -> html.Div:
        return html.Div(child, id=section_id)


_page = DocumentationPage()
layout = _page.layout


dash.register_page(
    __name__,
    path="/documentation",
    name="Documentation",
    order=5,
    layout=layout,
)