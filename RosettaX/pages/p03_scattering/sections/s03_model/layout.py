from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

import dash
import dash_bootstrap_components as dbc

from RosettaX.utils import styling, ui_forms

from . import services

if TYPE_CHECKING:
    from .main import Model

logger = logging.getLogger(__name__)

FIELD_LABEL_STYLE_OVERRIDES = {
    "fontSize": styling.get_typography_token("subtitle_size", "0.86rem"),
    "fontWeight": styling.get_typography_token("label_weight", "500"),
    "letterSpacing": "0.006em",
    "opacity": 0.9,
}
SECTION_TITLE_STYLE_OVERRIDES = {
    "fontSize": "1.14rem",
    "fontWeight": "780",
    "letterSpacing": "-0.01em",
}


def get_layout(section: Model) -> dbc.Card:
    """
    Build the scattering parameter layout.
    """
    logger.debug("Building Parameters layout.")

    return dbc.Card(
        [
            build_header(section),
            build_collapse(section),
        ],
    )


def build_header(section: Model) -> dbc.CardHeader:
    """
    Build section header.
    """
    return ui_forms.build_card_header_with_info(
        title=f"{section.section_number}. Set optical configuration",
        tooltip_target_id=section.section_tooltip_target_id,
        tooltip_id=section.section_tooltip_id,
        tooltip_text=(
            "These controls define the illumination, detector geometry, and "
            "angular sampling used to compute the calibration standard coupling "
            "values."
        ),
        color_name=section.card_color,
        title_style_overrides=SECTION_TITLE_STYLE_OVERRIDES,
    )


def build_collapse(section: Model) -> dbc.Collapse:
    """
    Build collapsible parameter body.
    """
    return dbc.Collapse(
        build_body(section),
        id=section.ids.collapse_example,
        is_open=True,
    )


def build_body(section: Model) -> dbc.CardBody:
    """
    Build parameter body.
    """
    return dbc.CardBody(
        [
            dash.html.Div(
                [
                    build_optical_configuration_controls(section),
                    build_optical_configuration_visualization(section),
                ],
                style={
                    "display": "flex",
                    "gap": "28px",
                    "alignItems": "flex-start",
                    "width": "100%",
                    "flexWrap": "wrap",
                    "overflow": "visible",
                },
            ),
        ],
        style=ui_forms.build_workflow_section_body_style(),
    )


def build_optical_configuration_controls(section: Model) -> dash.html.Div:
    """
    Build optical configuration controls.
    """
    return dash.html.Div(
        [
            dash.html.Div(
                [
                    dbc.Button(
                        "Auto-detect",
                        id=section.ids.detector_configuration_auto_detect_button,
                        n_clicks=0,
                        color="secondary",
                        outline=True,
                        size="sm",
                        style={
                            "whiteSpace": "nowrap",
                            "flexShrink": 0,
                        },
                    ),
                    dbc.Alert(
                        "",
                        id=section.ids.detector_configuration_auto_detect_status,
                        color="info",
                        is_open=False,
                        style={
                            "marginLeft": "12px",
                            "marginBottom": "0px",
                            "borderRadius": "10px",
                            "padding": "6px 12px",
                            "fontSize": "0.85rem",
                            "display": "inline-block",
                        },
                    ),
                ],
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "marginBottom": styling.get_spacing_token("xs"),
                },
            ),
            ui_forms.build_inline_row(
                label="Detector preset:",
                control=dash.html.Div(
                    [
                        dash.dcc.Dropdown(
                            id=section.ids.detector_configuration_brand,
                            options=[
                                {
                                    "label": "No preset",
                                    "value": "",
                                },
                                *section.model_configuration.build_detector_preset_brand_options(),
                            ],
                            value="",
                            placeholder="Select brand",
                            clearable=False,
                            searchable=False,
                            persistence=True,
                            persistence_type="session",
                            style={
                                "width": "220px",
                            },
                        ),
                        dash.dcc.Dropdown(
                            id=section.ids.detector_configuration_model,
                            options=[],
                            value=None,
                            placeholder="Select model",
                            clearable=True,
                            searchable=False,
                            disabled=True,
                            persistence=True,
                            persistence_type="session",
                            style={
                                "width": "220px",
                                "marginLeft": "10px",
                            },
                        ),
                        dash.dcc.Dropdown(
                            id=section.ids.detector_configuration_type,
                            options=[],
                            value=None,
                            placeholder="Select detector type",
                            clearable=True,
                            searchable=False,
                            disabled=True,
                            persistence=True,
                            persistence_type="session",
                            style={
                                "width": "220px",
                                "marginLeft": "10px",
                            },
                        ),
                        dash.dcc.Dropdown(
                            id=section.ids.detector_configuration_preset,
                            options=[
                                {
                                    "label": "No preset",
                                    "value": "",
                                },
                                *section.model_configuration.build_detector_preset_options(),
                            ],
                            value="",
                            clearable=True,
                            searchable=False,
                            persistence=True,
                            persistence_type="session",
                            style={
                                "display": "none",
                            },
                        ),
                        dbc.Tooltip(
                            (
                                "Choose a detector brand first, then one model, then one "
                                "detector type (for example FSC or SSC) to load a predefined "
                                "collection geometry. "
                                "Leave the brand on No preset to keep the detector unconfigured, "
                                "select Custom to edit a Generic detector manually, or click "
                                "Auto-detect above to try matching the uploaded FCS "
                                "metadata to a known preset."
                            ),
                            id=section.detector_preset_tooltip_id,
                            target=section.detector_preset_tooltip_target_id,
                            placement="right",
                        ),
                        ui_forms.build_info_badge(
                            tooltip_target_id=section.detector_preset_tooltip_target_id,
                        ),
                    ],
                    style={
                        "display": "flex",
                        "alignItems": "center",
                        "overflow": "visible",
                    },
                ),
                label_width_px=170,
                margin_top=True,
                margin_top_px=8,
                label_style_overrides=FIELD_LABEL_STYLE_OVERRIDES,
                row_style_overrides={
                    "overflow": "visible",
                },
                control_wrapper_style_overrides={
                    "overflow": "visible",
                },
            ),
            dbc.Accordion(
                [
                    dbc.AccordionItem(
                        dash.html.Div(
                            [
                                build_numeric_input_row(
                                    section,
                                    label="Wavelength (nm):",
                                    component_id=section.ids.wavelength_nm,
                                    placeholder="Wavelength (nm)",
                                    value=section.default_values.wavelength_nm,
                                    min_value=1,
                                    step=1,
                                    input_mode="numeric",
                                    width_px=220,
                                ),
                                build_numeric_input_row(
                                    section,
                                    label="Detector NA:",
                                    component_id=section.ids.detector_numerical_aperture,
                                    placeholder="Detector NA",
                                    value=section.default_values.detector_numerical_aperture,
                                    min_value=0.0,
                                    max_value=1.5,
                                    step=0.001,
                                    width_px=220,
                                ),
                                build_numeric_input_row(
                                    section,
                                    label="Detector cache NA:",
                                    component_id=section.ids.detector_cache_numerical_aperture,
                                    placeholder="Detector cache NA",
                                    value=section.default_values.detector_cache_numerical_aperture,
                                    min_value=0.0,
                                    max_value=section.default_values.detector_numerical_aperture,
                                    step=0.001,
                                    width_px=220,
                                ),
                                build_numeric_input_row(
                                    section,
                                    label="Blocker bar NA:",
                                    component_id=section.ids.blocker_bar_numerical_aperture,
                                    placeholder="Blocker bar NA",
                                    value=section.default_values.blocker_bar_numerical_aperture,
                                    min_value=0.0,
                                    max_value=1.5,
                                    step=0.001,
                                    width_px=220,
                                ),
                                build_numeric_input_row(
                                    section,
                                    label="Detector sampling:",
                                    component_id=section.ids.detector_sampling,
                                    placeholder="Detector sampling",
                                    value=section.default_values.detector_sampling,
                                    min_value=1,
                                    step=1,
                                    input_mode="numeric",
                                    width_px=220,
                                ),
                                build_numeric_input_row(
                                    section,
                                    label="Detector phi angle (deg):",
                                    component_id=section.ids.detector_phi_angle_degree,
                                    placeholder="Detector phi angle",
                                    value=section.default_values.detector_phi_angle_degree,
                                    min_value=-360.0,
                                    max_value=360.0,
                                    step=0.1,
                                    width_px=220,
                                ),
                                build_numeric_input_row(
                                    section,
                                    label="Detector gamma angle (deg):",
                                    component_id=section.ids.detector_gamma_angle_degree,
                                    placeholder="Detector gamma angle",
                                    value=section.default_values.detector_gamma_angle_degree,
                                    min_value=-360.0,
                                    max_value=360.0,
                                    step=0.1,
                                    width_px=220,
                                ),
                                ui_forms.build_inline_row(
                                    label="Detector angular weighting:",
                                    control=dash.html.Div(
                                        [
                                            dash.dcc.Textarea(
                                                id=section.ids.detector_angular_weighting_json,
                                                value="",
                                                persistence=True,
                                                persistence_type="session",
                                                style={
                                                    "width": "520px",
                                                    "height": "120px",
                                                    "fontFamily": "SFMono-Regular, Menlo, Monaco, Consolas, monospace",
                                                    "fontSize": "0.84rem",
                                                },
                                                placeholder=(
                                                    "{\n"
                                                    '  "mode": "split-separation-angle",\n'
                                                    '  "metric": "local-top-bottom",\n'
                                                    '  "keep": "positive",\n'
                                                    '  "separation_angle_degree": 20.0\n'
                                                    "}"
                                                ),
                                            ),
                                            dbc.FormText(
                                                "Optional JSON object using the detector_angular_weighting schema from detector definition files.",
                                                style={
                                                    "maxWidth": "520px",
                                                },
                                            ),
                                        ],
                                        style={
                                            "display": "flex",
                                            "flexDirection": "column",
                                            "gap": "6px",
                                        },
                                    ),
                                    margin_top_px=8,
                                    label_style_overrides=FIELD_LABEL_STYLE_OVERRIDES,
                                    row_style_overrides={
                                        "overflow": "visible",
                                        "alignItems": "flex-start",
                                    },
                                    control_wrapper_style_overrides={
                                        "overflow": "visible",
                                    },
                                ),
                                dbc.Alert(
                                    "",
                                    id=section.ids.detector_angular_weighting_alert,
                                    color="warning",
                                    is_open=False,
                                    style={
                                        "marginTop": "4px",
                                        "marginBottom": "0px",
                                        "borderRadius": "10px",
                                        "padding": "8px 12px",
                                        "fontSize": "0.9rem",
                                    },
                                ),
                            ],
                            id=section.ids.detector_configuration_custom_values_container,
                            style=services.build_parameter_group_style(
                                is_visible=False,
                            ),
                        ),
                        title="Advanced optical and detector settings",
                    ),
                ],
                start_collapsed=True,
                always_open=True,
                style={"marginTop": "8px"},
            ),
            dbc.Alert(
                "",
                id=section.ids.detector_numerical_aperture_warning,
                color="warning",
                is_open=False,
                style={
                    "marginTop": "12px",
                    "marginBottom": "0px",
                    "borderRadius": "10px",
                    "padding": "8px 12px",
                    "fontSize": "0.9rem",
                },
            ),
        ],
        style={
            "flex": "1 1 520px",
            "minWidth": "480px",
            "display": "flex",
            "flexDirection": "column",
            "gap": styling.get_spacing_token("xs"),
            "overflow": "visible",
        },
    )


def build_optical_configuration_visualization(section: Model) -> dbc.Card:
    """
    Build optical configuration preview graph.
    """
    return dbc.Card(
        [
            dbc.CardHeader(
                ui_forms.build_title_with_info(
                    title="Optical preview",
                    tooltip_target_id=section.optical_preview_tooltip_target_id,
                    tooltip_id=section.optical_preview_tooltip_id,
                    tooltip_text=(
                        "This preview visualizes the detector collection region "
                        "and blocker bar geometry from the current optical "
                        "configuration. It is only a geometric preview, not the "
                        "final Mie coupling curve."
                    ),
                    title_style_overrides={
                        "fontSize": "1.02rem",
                        "fontWeight": "700",
                    },
                ),
                style={
                    "background": "rgba(128, 128, 128, 0.08)",
                    "borderBottom": "1px solid rgba(128, 128, 128, 0.18)",
                    "padding": "10px 14px",
                    "borderTopLeftRadius": "10px",
                    "borderTopRightRadius": "10px",
                },
            ),
            dbc.CardBody(
                [
                    dash.dcc.Store(
                        id=section.ids.optical_configuration_preview_signature_store,
                        storage_type="memory",
                    ),
                    dash.dcc.Graph(
                        id=section.ids.optical_configuration_preview,
                        # The callback builds the preview from the active controls.
                        figure={"data": [], "layout": {}},
                        style={
                            **styling.PLOTLY_GRAPH_STYLE,
                            "height": "30vh",
                        },
                        config={
                            **styling.PLOTLY_GRAPH_CONFIG,
                            "modeBarButtonsToRemove": [
                                *styling.PLOTLY_GRAPH_CONFIG.get(
                                    "modeBarButtonsToRemove", []
                                ),
                                "pan3d",
                            ],
                        },
                        className="optical-configuration-preview-graph",
                    ),
                ],
                style={
                    "padding": "0px",
                },
            ),
        ],
        style={
            "flex": "0 1 430px",
            "minWidth": "340px",
            "borderRadius": "10px",
            "overflow": "visible",
        },
    )


def build_particle_configuration_panel(section: Model) -> dbc.Card:
    """
    Build the particle configuration subpanel.
    """
    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    ui_forms.build_title_with_info(
                        title="Particle configuration",
                        tooltip_target_id=section.particle_configuration_tooltip_target_id,
                        tooltip_id=section.particle_configuration_tooltip_id,
                        tooltip_text=(
                            "These controls define the particle model and refractive "
                            "indices used to compute the modeled optical coupling of "
                            "the calibration standard."
                        ),
                        subtitle="Particle model and refractive index parameters.",
                        title_style_overrides={
                            "fontSize": "1rem",
                        },
                    ),
                ],
                style=ui_forms.build_workflow_subpanel_header_style(
                    color_name=section.card_color,
                ),
            ),
            dbc.CardBody(
                build_particle_configuration_section(section),
                style=ui_forms.build_workflow_panel_body_style(),
            ),
        ],
        style=ui_forms.build_workflow_subpanel_card_style(
            color_name=section.card_color,
        ),
    )


def build_particle_configuration_section(section: Model) -> dash.html.Div:
    """
    Build particle configuration section.
    """
    return dash.html.Div(
        [
            ui_forms.build_inline_row(
                label="Scatterer preset:",
                control=dash.html.Div(
                    [
                        dash.dcc.Dropdown(
                            id=section.ids.scatterer_preset,
                            options=section.model_configuration.build_scatterer_preset_options(),
                            value="",
                            clearable=False,
                            searchable=False,
                            persistence=True,
                            persistence_type="session",
                            style={
                                "width": "320px",
                            },
                        ),
                        ui_forms.build_info_badge(
                            tooltip_target_id=section.scatterer_preset_tooltip_target_id,
                        ),
                        dbc.Tooltip(
                            (
                                "Use a scatterer preset to load a predefined bead set and "
                                "matching refractive index defaults for calibration setup."
                            ),
                            id=section.scatterer_preset_tooltip_id,
                            target=section.scatterer_preset_tooltip_target_id,
                            placement="right",
                        ),
                    ],
                    style={
                        "display": "flex",
                        "alignItems": "center",
                        "overflow": "visible",
                    },
                ),
                margin_top=False,
                row_style_overrides={
                    "overflow": "visible",
                },
                control_wrapper_style_overrides={
                    "overflow": "visible",
                },
            ),
            dash.html.Div(
                [
                    ui_forms.build_inline_row(
                        label="Particle type:",
                        control=dash.dcc.Dropdown(
                            id=section.ids.mie_model,
                            options=section.model_configuration.mie_model_options,
                            value=section.default_values.mie_model,
                            clearable=False,
                            searchable=False,
                            persistence=True,
                            persistence_type="session",
                            style={
                                "width": "220px",
                            },
                        ),
                        margin_top=False,
                        row_style_overrides={
                            "overflow": "visible",
                        },
                        control_wrapper_style_overrides={
                            "overflow": "visible",
                        },
                    ),
                    refractive_index_picker(
                        section,
                        label="Medium refractive index:",
                        preset_id=section.ids.medium_refractive_index_source,
                        value_id=section.ids.medium_refractive_index_custom,
                        default_value=section.default_values.medium_refractive_index,
                        preset_options=section.model_configuration.medium_refractive_index_presets,
                    ),
                    dash.html.Div(
                        build_solid_sphere_parameters_block(section),
                        id=section.ids.solid_sphere_container,
                        style=services.build_parameter_group_style(
                            is_visible=True,
                        ),
                    ),
                    dash.html.Div(
                        build_core_shell_parameters_block(section),
                        id=section.ids.core_shell_container,
                        style=services.build_parameter_group_style(
                            is_visible=False,
                        ),
                    ),
                ],
                id=section.ids.particle_configuration_custom_values_container,
                style=services.build_parameter_group_style(
                    is_visible=False,
                ),
            ),
        ],
        style={
            "display": "flex",
            "flexDirection": "column",
            "gap": styling.get_spacing_token("xs"),
            "overflow": "visible",
        },
    )


def build_solid_sphere_parameters_block(section: Model) -> list[Any]:
    """
    Build solid sphere parameter controls.
    """
    return [
        refractive_index_picker(
            section,
            label="Particle refractive index:",
            preset_id=section.ids.particle_refractive_index_source,
            value_id=section.ids.particle_refractive_index_custom,
            default_value=section.default_values.particle_refractive_index,
            preset_options=section.model_configuration.particle_refractive_index_presets,
        ),
    ]


def build_core_shell_parameters_block(section: Model) -> list[Any]:
    """
    Build core shell parameter controls.
    """
    return [
        refractive_index_picker(
            section,
            label="Core refractive index:",
            preset_id=section.ids.core_refractive_index_source,
            value_id=section.ids.core_refractive_index_custom,
            default_value=section.default_values.core_refractive_index,
            preset_options=section.model_configuration.core_refractive_index_presets,
        ),
        refractive_index_picker(
            section,
            label="Shell refractive index:",
            preset_id=section.ids.shell_refractive_index_source,
            value_id=section.ids.shell_refractive_index_custom,
            default_value=section.default_values.shell_refractive_index,
            preset_options=section.model_configuration.shell_refractive_index_presets,
        ),
    ]


def build_numeric_input_row(
    section: Model,
    *,
    label: str,
    component_id: str,
    placeholder: str,
    value: Any,
    min_value: float | None = None,
    max_value: float | None = None,
    step: float | None = None,
    input_mode: str = "decimal",
    width_px: int = 220,
) -> dash.html.Div:
    """
    Build a labeled numeric input row.
    """
    return ui_forms.build_inline_row(
        label=label,
        control=dash.dcc.Input(
            id=component_id,
            type="text",
            placeholder=placeholder,
            value=value,
            inputMode=input_mode,
            debounce=True,
            persistence=True,
            persistence_type="session",
            style={
                "width": f"{width_px}px",
            },
        ),
        margin_top_px=8,
        label_style_overrides=FIELD_LABEL_STYLE_OVERRIDES,
        row_style_overrides={
            "overflow": "visible",
        },
        control_wrapper_style_overrides={
            "overflow": "visible",
        },
    )


def refractive_index_picker(
    section: Model,
    *,
    label: str,
    preset_id: str,
    value_id: str,
    default_value: float,
    preset_options: Sequence[dict],
    preset_placeholder_label: str = "Select preset",
) -> dash.html.Div:
    """
    Build refractive index preset and custom value controls.
    """
    preset_dropdown = dash.dcc.Dropdown(
        id=preset_id,
        options=list(preset_options),
        value=None,
        placeholder=preset_placeholder_label,
        clearable=True,
        searchable=False,
        persistence=True,
        persistence_type="session",
        style={
            "width": "220px",
            "marginRight": "10px",
        },
    )

    numeric_input = dash.dcc.Input(
        id=value_id,
        type="number",
        value=default_value,
        min=1.0,
        max=2.5,
        step=0.001,
        debounce=True,
        persistence=True,
        persistence_type="session",
        style={
            "width": "160px",
        },
    )

    return ui_forms.build_inline_row(
        label=label,
        control=dash.html.Div(
            [
                preset_dropdown,
                numeric_input,
            ],
            style={
                "display": "flex",
                "alignItems": "center",
                "overflow": "visible",
            },
        ),
        margin_top_px=8,
        label_style_overrides=FIELD_LABEL_STYLE_OVERRIDES,
        row_style_overrides={
            "overflow": "visible",
        },
        control_wrapper_style_overrides={
            "overflow": "visible",
        },
    )
