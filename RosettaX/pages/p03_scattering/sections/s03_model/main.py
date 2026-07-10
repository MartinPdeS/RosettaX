# -*- coding: utf-8 -*-

import json
import logging
from typing import Any, Optional, Sequence

import dash
import dash_bootstrap_components as dbc
import numpy as np

from RosettaX.utils import styling, ui_forms, RuntimeConfig, casting
from RosettaX.workflow.peak.core import detectors as peak_detectors
from RosettaX.workflow import detector, scattering
from RosettaX.workflow.scattering.calibration_services import (
    DEFAULT_SOURCE_POLARIZATION_ANGLE_DEGREE,
)
from . import optical_preview


logger = logging.getLogger(__name__)


DETECTOR_NUMERICAL_APERTURE_EPSILON = 1e-6
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


class Model:
    """
    Scattering parameter section.

    Responsibilities
    ----------------
    - Render optical configuration controls.
    - Render particle configuration controls.
    - Render detector preset controls.
    - Render the optical configuration preview.
    - Synchronize parameter controls from the runtime configuration store.

    Ownership
    ---------
    This section owns only the visual parameter inputs.

    The reusable scattering model logic lives in
    RosettaX.workflow.scattering.model.
    """

    model_configuration = scattering.ModelConfiguration

    def __init__(
        self,
        page: Any,
        section_number: int,
        card_color: str = "blue",
    ) -> None:
        self.page = page
        self.ids = page.ids.Parameters
        self.section_number = section_number
        self.card_color = card_color
        self.default_values = self.model_configuration.build_default_profile_defaults()

        self.section_tooltip_target_id = f"{self.ids.mie_model}-section-info-target"
        self.section_tooltip_id = f"{self.ids.mie_model}-section-info-tooltip"

        self.particle_configuration_tooltip_target_id = f"{self.ids.mie_model}-particle-info-target"
        self.particle_configuration_tooltip_id = f"{self.ids.mie_model}-particle-info-tooltip"

        self.scatterer_preset_tooltip_target_id = f"{self.ids.scatterer_preset}-info-target"
        self.scatterer_preset_tooltip_id = f"{self.ids.scatterer_preset}-info-tooltip"

        self.detector_preset_tooltip_target_id = f"{self.ids.detector_configuration_preset}-info-target"
        self.detector_preset_tooltip_id = f"{self.ids.detector_configuration_preset}-info-tooltip"

        self.optical_preview_tooltip_target_id = f"{self.ids.optical_configuration_preview}-info-target"
        self.optical_preview_tooltip_id = f"{self.ids.optical_configuration_preview}-info-tooltip"

        logger.debug(
            "Initialized Parameters section with page=%r",
            page,
        )

    def get_layout(self) -> dbc.Card:
        """
        Build the scattering parameter layout.
        """
        logger.debug("Building Parameters layout.")

        return dbc.Card(
            [
                self._build_header(),
                self._build_collapse(),
            ],
            style=ui_forms.build_workflow_section_card_style(
                color_name=self.card_color,
            ),
        )

    def _build_header(self) -> dbc.CardHeader:
        """
        Build section header.
        """
        return ui_forms.build_card_header_with_info(
            title=f"{self.section_number}. Set optical configuration",
            tooltip_target_id=self.section_tooltip_target_id,
            tooltip_id=self.section_tooltip_id,
            tooltip_text=(
                "These controls define the illumination, detector geometry, and "
                "angular sampling used to compute the calibration standard coupling "
                "values."
            ),
            subtitle=(
                "Configure the illumination, detector geometry, and angular sampling "
                "used for scattering calibration."
            ),
            color_name=self.card_color,
            title_style_overrides=SECTION_TITLE_STYLE_OVERRIDES,
        )

    def _build_collapse(self) -> dbc.Collapse:
        """
        Build collapsible parameter body.
        """
        return dbc.Collapse(
            self._build_body(),
            id=self.ids.collapse_example,
            is_open=True,
        )

    def _build_body(self) -> dbc.CardBody:
        """
        Build parameter body.
        """
        return dbc.CardBody(
            [
                dash.html.Div(
                    [
                        self._build_optical_configuration_controls(),
                        self._build_optical_configuration_visualization(),
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

    def _build_optical_configuration_controls(self) -> dash.html.Div:
        """
        Build optical configuration controls.
        """
        return dash.html.Div(
            [
                dash.html.Div(
                    [
                        dbc.Button(
                            "Auto-detect",
                            id=self.ids.detector_configuration_auto_detect_button,
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
                            id=self.ids.detector_configuration_auto_detect_status,
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
                                id=self.ids.detector_configuration_brand,
                                options=[
                                    {
                                        "label": "No preset",
                                        "value": "",
                                    },
                                    *self.model_configuration.build_detector_preset_brand_options(),
                                ],
                                value="",
                                placeholder="Select brand",
                                clearable=False,
                                searchable=False,
                                style={
                                    "width": "220px",
                                },
                            ),
                            dash.dcc.Dropdown(
                                id=self.ids.detector_configuration_model,
                                options=[],
                                value=None,
                                placeholder="Select model",
                                clearable=True,
                                searchable=False,
                                disabled=True,
                                style={
                                    "width": "220px",
                                    "marginLeft": "10px",
                                },
                            ),
                            dash.dcc.Dropdown(
                                id=self.ids.detector_configuration_type,
                                options=[],
                                value=None,
                                placeholder="Select detector type",
                                clearable=True,
                                searchable=False,
                                disabled=True,
                                style={
                                    "width": "220px",
                                    "marginLeft": "10px",
                                },
                            ),
                            dash.dcc.Dropdown(
                                id=self.ids.detector_configuration_preset,
                                options=[
                                    {
                                        "label": "No preset",
                                        "value": "",
                                    },
                                    *self.model_configuration.build_detector_preset_options(),
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
                                id=self.detector_preset_tooltip_id,
                                target=self.detector_preset_tooltip_target_id,
                                placement="right",
                            ),
                            ui_forms.build_info_badge(
                                tooltip_target_id=self.detector_preset_tooltip_target_id,
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
                dash.html.Div(
                    [
                        self._build_numeric_input_row(
                            label="Wavelength (nm):",
                            component_id=self.ids.wavelength_nm,
                            placeholder="Wavelength (nm)",
                            value=self.default_values.wavelength_nm,
                            min_value=1,
                            step=1,
                            input_mode="numeric",
                            width_px=220,
                        ),
                        self._build_numeric_input_row(
                            label="Detector NA:",
                            component_id=self.ids.detector_numerical_aperture,
                            placeholder="Detector NA",
                            value=self.default_values.detector_numerical_aperture,
                            min_value=0.0,
                            max_value=1.5,
                            step=0.001,
                            width_px=220,
                        ),
                        self._build_numeric_input_row(
                            label="Detector cache NA:",
                            component_id=self.ids.detector_cache_numerical_aperture,
                            placeholder="Detector cache NA",
                            value=self.default_values.detector_cache_numerical_aperture,
                            min_value=0.0,
                            max_value=self.default_values.detector_numerical_aperture,
                            step=0.001,
                            width_px=220,
                        ),
                        self._build_numeric_input_row(
                            label="Blocker bar NA:",
                            component_id=self.ids.blocker_bar_numerical_aperture,
                            placeholder="Blocker bar NA",
                            value=self.default_values.blocker_bar_numerical_aperture,
                            min_value=0.0,
                            max_value=1.5,
                            step=0.001,
                            width_px=220,
                        ),
                        self._build_numeric_input_row(
                            label="Detector sampling:",
                            component_id=self.ids.detector_sampling,
                            placeholder="Detector sampling",
                            value=self.default_values.detector_sampling,
                            min_value=1,
                            step=1,
                            input_mode="numeric",
                            width_px=220,
                        ),
                        self._build_numeric_input_row(
                            label="Detector phi angle (deg):",
                            component_id=self.ids.detector_phi_angle_degree,
                            placeholder="Detector phi angle",
                            value=self.default_values.detector_phi_angle_degree,
                            min_value=-360.0,
                            max_value=360.0,
                            step=0.1,
                            width_px=220,
                        ),
                        self._build_numeric_input_row(
                            label="Detector gamma angle (deg):",
                            component_id=self.ids.detector_gamma_angle_degree,
                            placeholder="Detector gamma angle",
                            value=self.default_values.detector_gamma_angle_degree,
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
                                        id=self.ids.detector_angular_weighting_json,
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
                                            '{\n'
                                            '  "mode": "split-separation-angle",\n'
                                            '  "metric": "local-top-bottom",\n'
                                            '  "keep": "positive",\n'
                                            '  "separation_angle_degree": 20.0\n'
                                            '}'
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
                            id=self.ids.detector_angular_weighting_alert,
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
                    id=self.ids.detector_configuration_custom_values_container,
                    style=self._build_detector_configuration_custom_values_style(
                        is_visible=False,
                    ),
                ),
                dbc.Alert(
                    "",
                    id=self.ids.detector_numerical_aperture_warning,
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

    def _build_optical_configuration_visualization(self) -> dbc.Card:
        """
        Build optical configuration preview graph.
        """
        return dbc.Card(
            [
                dbc.CardHeader(
                    ui_forms.build_title_with_info(
                        title="Optical preview",
                        tooltip_target_id=self.optical_preview_tooltip_target_id,
                        tooltip_id=self.optical_preview_tooltip_id,
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
                        dash.dcc.Graph(
                            id=self.ids.optical_configuration_preview,
                            figure=self.model_configuration.build_optical_configuration_preview_figure(
                                detector_numerical_aperture=self.default_values.detector_numerical_aperture,
                                detector_cache_numerical_aperture=self.default_values.detector_cache_numerical_aperture,
                                blocker_bar_numerical_aperture=self.default_values.blocker_bar_numerical_aperture,
                                medium_refractive_index=self.default_values.medium_refractive_index,
                                detector_phi_angle_degree=self.default_values.detector_phi_angle_degree,
                                detector_gamma_angle_degree=self.default_values.detector_gamma_angle_degree,
                                polarization_angle_degree=DEFAULT_SOURCE_POLARIZATION_ANGLE_DEGREE,
                                detector_sampling=self.default_values.detector_sampling,
                                detector_configuration_preset=self.model_configuration.custom_detector_preset_name,
                            ),
                            style={
                                **styling.PLOTLY_GRAPH_STYLE,
                                "height": "30vh",
                            },
                            config={
                                **styling.PLOTLY_GRAPH_CONFIG,
                                "modeBarButtonsToRemove": [
                                    *styling.PLOTLY_GRAPH_CONFIG.get("modeBarButtonsToRemove", []),
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

    def _build_particle_configuration_panel(self) -> dbc.Card:
        """
        Build the particle configuration subpanel.
        """
        return dbc.Card(
            [
                dbc.CardHeader(
                    [
                        ui_forms.build_title_with_info(
                            title="Particle configuration",
                            tooltip_target_id=self.particle_configuration_tooltip_target_id,
                            tooltip_id=self.particle_configuration_tooltip_id,
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
                        color_name=self.card_color,
                    ),
                ),
                dbc.CardBody(
                    self._build_particle_configuration_section(),
                    style=ui_forms.build_workflow_panel_body_style(),
                ),
            ],
            style=ui_forms.build_workflow_subpanel_card_style(
                color_name=self.card_color,
            ),
        )

    def _build_particle_configuration_section(self) -> dash.html.Div:
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
                                id=self.ids.scatterer_preset,
                                options=self.model_configuration.build_scatterer_preset_options(),
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
                                tooltip_target_id=self.scatterer_preset_tooltip_target_id,
                            ),
                            dbc.Tooltip(
                                (
                                        "Use a scatterer preset to load a predefined bead set and "
                                        "matching refractive index defaults for calibration setup."
                                ),
                                id=self.scatterer_preset_tooltip_id,
                                target=self.scatterer_preset_tooltip_target_id,
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
                                id=self.ids.mie_model,
                                options=self.model_configuration.mie_model_options,
                                value=self.default_values.mie_model,
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
                        self._refractive_index_picker(
                            label="Medium refractive index:",
                            preset_id=self.ids.medium_refractive_index_source,
                            value_id=self.ids.medium_refractive_index_custom,
                            default_value=self.default_values.medium_refractive_index,
                            preset_options=self.model_configuration.medium_refractive_index_presets,
                        ),
                        dash.html.Div(
                            self._build_solid_sphere_parameters_block(),
                            id=self.ids.solid_sphere_container,
                            style=self._build_parameter_group_style(
                                is_visible=True,
                            ),
                        ),
                        dash.html.Div(
                            self._build_core_shell_parameters_block(),
                            id=self.ids.core_shell_container,
                            style=self._build_parameter_group_style(
                                is_visible=False,
                            ),
                        ),
                    ],
                    id=self.ids.particle_configuration_custom_values_container,
                    style=self._build_preset_configuration_container_style(
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

    def _build_parameter_group_style(
        self,
        *,
        is_visible: bool,
    ) -> dict[str, str]:
        """
        Build a consistent layout style for model-specific parameter groups.
        """
        return {
            "display": "flex" if is_visible else "none",
            "flexDirection": "column",
            "gap": styling.get_spacing_token("xs"),
            "overflow": "visible",
        }

    @staticmethod
    def _build_detector_configuration_custom_values_style(
        *,
        is_visible: bool,
    ) -> dict[str, str]:
        return {
            "display": "flex" if is_visible else "none",
            "flexDirection": "column",
            "gap": styling.get_spacing_token("xs"),
            "overflow": "visible",
        }

    @staticmethod
    def _build_preset_configuration_container_style(
        *,
        is_visible: bool,
    ) -> dict[str, str]:
        return {
            "display": "flex" if is_visible else "none",
            "flexDirection": "column",
            "gap": styling.get_spacing_token("xs"),
            "overflow": "visible",
        }

    @staticmethod
    def _resolve_show_preset_configuration(
        runtime_config_data: Any,
    ) -> bool:
        runtime_config = RuntimeConfig.from_dict(
            runtime_config_data if isinstance(runtime_config_data, dict) else None
        )

        return runtime_config.get_bool(
            "ui.show_preset_configuration",
            default=False,
        )

    def _should_show_detector_preset_configuration(
        self,
        *,
        preset_name: Any,
        show_preset_configuration: bool,
    ) -> bool:
        normalized_preset_name = str(preset_name or "").strip()

        if (
            normalized_preset_name
            == self.model_configuration.custom_detector_preset_name
        ):
            return True

        return bool(show_preset_configuration and normalized_preset_name)

    def _should_show_scatterer_preset_configuration(
        self,
        *,
        preset_name: Any,
        show_preset_configuration: bool,
    ) -> bool:
        normalized_preset_name = str(preset_name or "").strip()

        if (
            normalized_preset_name
            == self.model_configuration.custom_scatterer_preset_name
        ):
            return True

        return bool(show_preset_configuration and normalized_preset_name)

    def _build_solid_sphere_parameters_block(self) -> list[Any]:
        """
        Build solid sphere parameter controls.
        """
        return [
            self._refractive_index_picker(
                label="Particle refractive index:",
                preset_id=self.ids.particle_refractive_index_source,
                value_id=self.ids.particle_refractive_index_custom,
                default_value=self.default_values.particle_refractive_index,
                preset_options=self.model_configuration.particle_refractive_index_presets,
            ),
        ]

    def _build_core_shell_parameters_block(self) -> list[Any]:
        """
        Build core shell parameter controls.
        """
        return [
            self._refractive_index_picker(
                label="Core refractive index:",
                preset_id=self.ids.core_refractive_index_source,
                value_id=self.ids.core_refractive_index_custom,
                default_value=self.default_values.core_refractive_index,
                preset_options=self.model_configuration.core_refractive_index_presets,
            ),
            self._refractive_index_picker(
                label="Shell refractive index:",
                preset_id=self.ids.shell_refractive_index_source,
                value_id=self.ids.shell_refractive_index_custom,
                default_value=self.default_values.shell_refractive_index,
                preset_options=self.model_configuration.shell_refractive_index_presets,
            ),
        ]

    def _build_numeric_input_row(
        self,
        *,
        label: str,
        component_id: str,
        placeholder: str,
        value: Any,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        step: Optional[float] = None,
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

    def _refractive_index_picker(
        self,
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

    @staticmethod
    def _clamp_detector_cache_numerical_aperture(
        detector_numerical_aperture: Any,
        detector_cache_numerical_aperture: Any,
    ) -> Any:
        """
        Keep detector cache numerical aperture within the detector aperture.
        """
        resolved_detector_numerical_aperture = casting.as_optional_float(
            detector_numerical_aperture
        )
        resolved_detector_cache_numerical_aperture = casting.as_optional_float(
            detector_cache_numerical_aperture
        )

        if resolved_detector_numerical_aperture is None:
            return detector_cache_numerical_aperture

        if resolved_detector_cache_numerical_aperture is None:
            return detector_cache_numerical_aperture

        strict_upper_bound = max(
            0.0,
            resolved_detector_numerical_aperture - DETECTOR_NUMERICAL_APERTURE_EPSILON,
        )

        if resolved_detector_cache_numerical_aperture < resolved_detector_numerical_aperture:
            return detector_cache_numerical_aperture

        logger.debug(
            "Clamping detector cache numerical aperture from %r to strict upper bound %r below detector numerical aperture %r.",
            detector_cache_numerical_aperture,
            strict_upper_bound,
            detector_numerical_aperture,
        )

        return strict_upper_bound

    @staticmethod
    def _resolve_selected_peak_detector_channel(
        *,
        selected_peak_process_name: Any,
        detector_dropdown_ids: list[dict[str, Any]],
        detector_dropdown_values: list[Any],
    ) -> Any:
        """
        Resolve the peak detector channel currently driving scattering calibration.
        """
        channel_values = peak_detectors.resolve_detector_channels_for_process(
            detector_dropdown_ids=detector_dropdown_ids,
            detector_dropdown_values=detector_dropdown_values,
            process_name=selected_peak_process_name,
        )

        for channel_name in ("primary", "scattering", "scattering_axis", "x_axis", "x"):
            resolved_channel = channel_values.get(channel_name)

            if resolved_channel:
                return resolved_channel

        return None

    def register_callbacks(self) -> None:
        """
        Register parameter callbacks.
        """
        logger.debug("Registering Parameters callbacks.")

        self._register_visibility_callbacks()
        self._register_scatterer_preset_callbacks()
        self._register_refractive_index_callbacks()
        self._register_detector_configuration_callbacks()
        self._register_detector_numerical_aperture_warning_callback()
        self._register_optical_configuration_preview_callback()
        self._register_runtime_sync_callbacks()

    def _register_runtime_sync_callbacks(self) -> None:
        """
        Register runtime configuration synchronization callback.
        """

        @dash.callback(
            dash.Output(self.ids.detector_configuration_preset, "value"),
            dash.Output(self.ids.scatterer_preset, "value"),
            dash.Output(self.ids.mie_model, "value"),
            dash.Output(self.ids.medium_refractive_index_custom, "value"),
            dash.Output(self.ids.particle_refractive_index_custom, "value"),
            dash.Output(self.ids.core_refractive_index_custom, "value"),
            dash.Output(self.ids.shell_refractive_index_custom, "value"),
            dash.Output(self.ids.wavelength_nm, "value"),
            dash.Output(self.ids.detector_numerical_aperture, "value"),
            dash.Output(self.ids.detector_cache_numerical_aperture, "value"),
            dash.Output(self.ids.blocker_bar_numerical_aperture, "value"),
            dash.Output(self.ids.detector_sampling, "value"),
            dash.Output(self.ids.detector_phi_angle_degree, "value"),
            dash.Output(self.ids.detector_gamma_angle_degree, "value"),
            dash.Input("runtime-config-store", "data"),
            prevent_initial_call=False,
        )
        def sync_parameters_from_runtime_config(
            runtime_config_data: Any,
        ) -> tuple[Any, ...]:
            logger.debug(
                "sync_parameters_from_runtime_config called with runtime_config_data=%r",
                runtime_config_data,
            )

            runtime_config = RuntimeConfig.from_dict(
                runtime_config_data if isinstance(runtime_config_data, dict) else None
            )

            resolved_values = self.model_configuration.build_defaults_from_runtime_config(
                runtime_config_data,
            ).to_callback_values()

            detector_preset = self.model_configuration.resolve_runtime_detector_preset(
                runtime_config.get_str(
                    "optics.detector_configuration_preset",
                    default="",
                ),
            )

            resolved_detector_values = (
                self.model_configuration.resolve_detector_configuration_values(
                    preset_name=detector_preset,
                    current_detector_numerical_aperture=resolved_values[6],
                    current_detector_cache_numerical_aperture=resolved_values[7],
                    current_blocker_bar_numerical_aperture=resolved_values[8],
                    current_detector_sampling=resolved_values[9],
                    current_detector_phi_angle_degree=resolved_values[10],
                    current_detector_gamma_angle_degree=resolved_values[11],
                )
            )

            resolved_wavelength_nm = self.model_configuration.resolve_detector_preset_wavelength_nm(
                preset_name=detector_preset,
                current_wavelength_nm=resolved_values[5],
            )

            resolved_values = (
                *resolved_values[:6],
                *resolved_detector_values,
            )

            resolved_values = (
                *resolved_values[:5],
                resolved_wavelength_nm,
                *resolved_values[6:],
            )

            scatterer_preset = self.model_configuration.resolve_runtime_scatterer_preset(
                runtime_config.get_str(
                    "particle_model.scatterer_preset",
                    default="",
                )
            )

            if self.model_configuration.scatterer_preset_disables_manual_controls(
                preset_name=scatterer_preset,
            ):
                (
                    resolved_mie_model,
                    _medium_ri_source,
                    resolved_medium_refractive_index,
                    _particle_ri_source,
                    resolved_particle_refractive_index,
                    _core_ri_source,
                    resolved_core_refractive_index,
                    _shell_ri_source,
                    resolved_shell_refractive_index,
                ) = self.model_configuration.resolve_scatterer_preset_values(
                    preset_name=scatterer_preset,
                    current_mie_model=resolved_values[0],
                    current_medium_refractive_index_source=None,
                    current_medium_refractive_index=resolved_values[1],
                    current_particle_refractive_index_source=None,
                    current_particle_refractive_index=resolved_values[2],
                    current_core_refractive_index_source=None,
                    current_core_refractive_index=resolved_values[3],
                    current_shell_refractive_index_source=None,
                    current_shell_refractive_index=resolved_values[4],
                    wavelength_nm=resolved_values[5],
                )

                resolved_values = (
                    resolved_mie_model,
                    resolved_medium_refractive_index,
                    resolved_particle_refractive_index,
                    resolved_core_refractive_index,
                    resolved_shell_refractive_index,
                    *resolved_values[5:],
                )

            resolved_values = (
                *resolved_values[:7],
                self._clamp_detector_cache_numerical_aperture(
                    resolved_values[6],
                    resolved_values[7],
                ),
                *resolved_values[8:],
            )

            logger.debug(
                "sync_parameters_from_runtime_config returning detector_preset=%r resolved_values=%r",
                detector_preset,
                resolved_values,
            )

            return (
                detector_preset or "",
                scatterer_preset,
                *resolved_values,
            )

    def _register_scatterer_preset_callbacks(self) -> None:
        """
        Register scatterer preset callbacks.
        """

        @dash.callback(
            dash.Output(self.ids.mie_model, "value", allow_duplicate=True),
            dash.Output(self.ids.medium_refractive_index_source, "value", allow_duplicate=True),
            dash.Output(self.ids.medium_refractive_index_custom, "value", allow_duplicate=True),
            dash.Output(self.ids.particle_refractive_index_source, "value", allow_duplicate=True),
            dash.Output(self.ids.particle_refractive_index_custom, "value", allow_duplicate=True),
            dash.Output(self.ids.core_refractive_index_source, "value", allow_duplicate=True),
            dash.Output(self.ids.core_refractive_index_custom, "value", allow_duplicate=True),
            dash.Output(self.ids.shell_refractive_index_source, "value", allow_duplicate=True),
            dash.Output(self.ids.shell_refractive_index_custom, "value", allow_duplicate=True),
            dash.Input(self.ids.scatterer_preset, "value"),
            dash.State(self.ids.mie_model, "value"),
            dash.State(self.ids.medium_refractive_index_source, "value"),
            dash.State(self.ids.medium_refractive_index_custom, "value"),
            dash.State(self.ids.particle_refractive_index_source, "value"),
            dash.State(self.ids.particle_refractive_index_custom, "value"),
            dash.State(self.ids.core_refractive_index_source, "value"),
            dash.State(self.ids.core_refractive_index_custom, "value"),
            dash.State(self.ids.shell_refractive_index_source, "value"),
            dash.State(self.ids.shell_refractive_index_custom, "value"),
            dash.State(self.ids.wavelength_nm, "value"),
            prevent_initial_call=True,
        )
        def apply_scatterer_preset(
            preset_name: Any,
            current_mie_model: Any,
            current_medium_refractive_index_source: Any,
            current_medium_refractive_index: Any,
            current_particle_refractive_index_source: Any,
            current_particle_refractive_index: Any,
            current_core_refractive_index_source: Any,
            current_core_refractive_index: Any,
            current_shell_refractive_index_source: Any,
            current_shell_refractive_index: Any,
            wavelength_nm: Any,
        ) -> tuple[Any, ...]:
            logger.debug(
                "apply_scatterer_preset called with triggered_id=%r preset_name=%r",
                dash.ctx.triggered_id,
                preset_name,
            )

            (
                resolved_mie_model,
                resolved_medium_refractive_index_source,
                resolved_medium_refractive_index,
                resolved_particle_refractive_index_source,
                resolved_particle_refractive_index,
                resolved_core_refractive_index_source,
                resolved_core_refractive_index,
                resolved_shell_refractive_index_source,
                resolved_shell_refractive_index,
            ) = self.model_configuration.resolve_scatterer_preset_values(
                preset_name=preset_name,
                current_mie_model=current_mie_model,
                current_medium_refractive_index_source=current_medium_refractive_index_source,
                current_medium_refractive_index=current_medium_refractive_index,
                current_particle_refractive_index_source=current_particle_refractive_index_source,
                current_particle_refractive_index=current_particle_refractive_index,
                current_core_refractive_index_source=current_core_refractive_index_source,
                current_core_refractive_index=current_core_refractive_index,
                current_shell_refractive_index_source=current_shell_refractive_index_source,
                current_shell_refractive_index=current_shell_refractive_index,
                wavelength_nm=wavelength_nm,
            )

            return (
                resolved_mie_model,
                resolved_medium_refractive_index_source,
                resolved_medium_refractive_index,
                resolved_particle_refractive_index_source,
                resolved_particle_refractive_index,
                resolved_core_refractive_index_source,
                resolved_core_refractive_index,
                resolved_shell_refractive_index_source,
                resolved_shell_refractive_index,
            )

        @dash.callback(
            dash.Output(self.ids.mie_model, "disabled"),
            dash.Output(self.ids.medium_refractive_index_source, "disabled"),
            dash.Output(self.ids.medium_refractive_index_custom, "disabled"),
            dash.Output(self.ids.particle_refractive_index_source, "disabled"),
            dash.Output(self.ids.particle_refractive_index_custom, "disabled"),
            dash.Output(self.ids.core_refractive_index_source, "disabled"),
            dash.Output(self.ids.core_refractive_index_custom, "disabled"),
            dash.Output(self.ids.shell_refractive_index_source, "disabled"),
            dash.Output(self.ids.shell_refractive_index_custom, "disabled"),
            dash.Input(self.ids.scatterer_preset, "value"),
            prevent_initial_call=False,
        )
        def sync_scatterer_preset_disabled_state(
            preset_name: Any,
        ) -> tuple[bool, ...]:
            is_locked = self.model_configuration.scatterer_preset_disables_manual_controls(
                preset_name=preset_name,
            )

            return (
                is_locked,
                is_locked,
                is_locked,
                is_locked,
                is_locked,
                is_locked,
                is_locked,
                is_locked,
                is_locked,
            )

    def _register_visibility_callbacks(self) -> None:
        """
        Register particle model visibility callbacks.
        """

        @dash.callback(
            dash.Output(
                self.ids.particle_configuration_custom_values_container,
                "style",
            ),
            dash.Output(self.ids.solid_sphere_container, "style"),
            dash.Output(self.ids.core_shell_container, "style"),
            dash.Input("runtime-config-store", "data"),
            dash.Input(self.ids.mie_model, "value"),
            dash.Input(self.ids.scatterer_preset, "value"),
            prevent_initial_call=False,
        )
        def toggle_parameter_blocks(
            runtime_config_data: Any,
            mie_model_value: Optional[str],
            scatterer_preset: Any,
        ) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
            resolved_mie_model = self.model_configuration.resolve_mie_model(
                mie_model_value,
            )
            show_preset_configuration = self._resolve_show_preset_configuration(
                runtime_config_data,
            )

            resolved_styles = (
                self._build_preset_configuration_container_style(
                    is_visible=self._should_show_scatterer_preset_configuration(
                        preset_name=scatterer_preset,
                        show_preset_configuration=show_preset_configuration,
                    ),
                ),
                self._build_parameter_group_style(
                    is_visible=resolved_mie_model != "Core/Shell Sphere",
                ),
                self._build_parameter_group_style(
                    is_visible=resolved_mie_model == "Core/Shell Sphere",
                ),
            )

            logger.debug(
                "toggle_parameter_blocks called with mie_model_value=%r scatterer_preset=%r show_preset_configuration=%r styles=%r",
                mie_model_value,
                scatterer_preset,
                show_preset_configuration,
                resolved_styles,
            )

            return resolved_styles

    def _register_refractive_index_callbacks(self) -> None:
        """
        Register refractive index preset callbacks.
        """

        @dash.callback(
            dash.Output(
                self.ids.medium_refractive_index_custom,
                "value",
                allow_duplicate=True,
            ),
            dash.Input(self.ids.medium_refractive_index_source, "value"),
            dash.Input(self.ids.wavelength_nm, "value"),
            dash.State(self.ids.medium_refractive_index_custom, "value"),
            prevent_initial_call=True,
        )
        def apply_medium_preset(
            preset_value: Any,
            wavelength_nm: Any,
            current_value: Any,
        ) -> Any:
            return self.model_configuration.apply_refractive_index_preset(
                preset_value=preset_value,
                wavelength_nm=wavelength_nm,
                current_value=current_value,
            )

        @dash.callback(
            dash.Output(
                self.ids.particle_refractive_index_custom,
                "value",
                allow_duplicate=True,
            ),
            dash.Input(self.ids.particle_refractive_index_source, "value"),
            dash.Input(self.ids.wavelength_nm, "value"),
            dash.State(self.ids.particle_refractive_index_custom, "value"),
            prevent_initial_call=True,
        )
        def apply_particle_preset(
            preset_value: Any,
            wavelength_nm: Any,
            current_value: Any,
        ) -> Any:
            return self.model_configuration.apply_refractive_index_preset(
                preset_value=preset_value,
                wavelength_nm=wavelength_nm,
                current_value=current_value,
            )

        @dash.callback(
            dash.Output(
                self.ids.core_refractive_index_custom,
                "value",
                allow_duplicate=True,
            ),
            dash.Input(self.ids.core_refractive_index_source, "value"),
            dash.Input(self.ids.wavelength_nm, "value"),
            dash.State(self.ids.core_refractive_index_custom, "value"),
            prevent_initial_call=True,
        )
        def apply_core_preset(
            preset_value: Any,
            wavelength_nm: Any,
            current_value: Any,
        ) -> Any:
            return self.model_configuration.apply_refractive_index_preset(
                preset_value=preset_value,
                wavelength_nm=wavelength_nm,
                current_value=current_value,
            )

        @dash.callback(
            dash.Output(
                self.ids.shell_refractive_index_custom,
                "value",
                allow_duplicate=True,
            ),
            dash.Input(self.ids.shell_refractive_index_source, "value"),
            dash.Input(self.ids.wavelength_nm, "value"),
            dash.State(self.ids.shell_refractive_index_custom, "value"),
            prevent_initial_call=True,
        )
        def apply_shell_preset(
            preset_value: Any,
            wavelength_nm: Any,
            current_value: Any,
        ) -> Any:
            return self.model_configuration.apply_refractive_index_preset(
                preset_value=preset_value,
                wavelength_nm=wavelength_nm,
                current_value=current_value,
            )

    def _register_detector_configuration_callbacks(self) -> None:
        """
        Register detector configuration callbacks.
        """

        @dash.callback(
            dash.Output(self.ids.detector_configuration_brand, "value"),
            dash.Input(self.ids.detector_configuration_preset, "value"),
            dash.State(self.ids.detector_configuration_brand, "value"),
            prevent_initial_call=False,
        )
        def sync_detector_configuration_brand_from_preset(
            preset_name: Any,
            current_brand: Any,
        ) -> str:
            resolved_brand = self.model_configuration.resolve_detector_preset_brand(
                preset_name,
            )

            if resolved_brand:
                return resolved_brand

            return str(current_brand or "").strip()

        @dash.callback(
            dash.Output(self.ids.detector_configuration_model, "options"),
            dash.Output(self.ids.detector_configuration_model, "value"),
            dash.Output(self.ids.detector_configuration_model, "disabled"),
            dash.Input(self.ids.detector_configuration_brand, "value"),
            dash.State(self.ids.detector_configuration_preset, "value"),
            dash.State(self.ids.detector_configuration_model, "value"),
            prevent_initial_call=False,
        )
        def sync_detector_configuration_models_for_brand(
            brand_name: Any,
            current_preset_name: Any,
            current_model_name: Any,
        ) -> tuple[list[dict[str, Any]], Any, bool]:
            resolved_options = self.model_configuration.build_detector_preset_model_options(
                brand_name,
            )

            if not resolved_options:
                return [], None, True

            option_values = {
                option["value"]
                for option in resolved_options
            }
            resolved_model_from_preset = self.model_configuration.resolve_detector_preset_model(
                current_preset_name,
            )

            if resolved_model_from_preset in option_values:
                resolved_value = resolved_model_from_preset
            elif current_model_name in option_values:
                resolved_value = current_model_name
            elif len(resolved_options) == 1:
                resolved_value = resolved_options[0]["value"]
            else:
                resolved_value = None

            return resolved_options, resolved_value, False

        @dash.callback(
            dash.Output(self.ids.detector_configuration_type, "options"),
            dash.Output(self.ids.detector_configuration_type, "value"),
            dash.Output(self.ids.detector_configuration_type, "disabled"),
            dash.Input(self.ids.detector_configuration_model, "value"),
            dash.State(self.ids.detector_configuration_brand, "value"),
            dash.State(self.ids.detector_configuration_preset, "value"),
            dash.State(self.ids.detector_configuration_type, "value"),
            prevent_initial_call=False,
        )
        def sync_detector_configuration_types_for_model(
            model_name: Any,
            brand_name: Any,
            current_preset_name: Any,
            current_type_name: Any,
        ) -> tuple[list[dict[str, Any]], Any, bool]:
            resolved_options = self.model_configuration.build_detector_preset_type_options(
                brand=brand_name,
                model=model_name,
            )

            if not resolved_options:
                return [], None, True

            option_values = {
                option["value"]
                for option in resolved_options
            }

            if current_preset_name in option_values:
                resolved_value = current_preset_name
            elif current_type_name in option_values:
                resolved_value = current_type_name
            elif len(resolved_options) == 1:
                resolved_value = resolved_options[0]["value"]
            else:
                resolved_value = None

            return resolved_options, resolved_value, False

        @dash.callback(
            dash.Output(
                self.ids.detector_configuration_preset,
                "value",
                allow_duplicate=True,
            ),
            dash.Input(self.ids.detector_configuration_type, "value"),
            prevent_initial_call=True,
        )
        def sync_detector_configuration_preset_from_model(
            type_value: Any,
        ) -> Any:
            return type_value or ""

        @dash.callback(
            dash.Output(
                self.ids.detector_configuration_preset,
                "value",
                allow_duplicate=True,
            ),
            dash.Output(
                self.ids.wavelength_nm,
                "value",
                allow_duplicate=True,
            ),
            dash.Output(self.ids.detector_configuration_auto_detect_status, "children"),
            dash.Output(self.ids.detector_configuration_auto_detect_status, "color"),
            dash.Output(self.ids.detector_configuration_auto_detect_status, "is_open"),
            dash.Input(self.ids.detector_configuration_auto_detect_button, "n_clicks"),
            dash.State("runtime-config-store", "data"),
            dash.State(self.page.ids.Scattering.process_dropdown, "value"),
            dash.State(
                self.page.ids.Scattering.process_detector_dropdown_pattern(),
                "id",
            ),
            dash.State(
                self.page.ids.Scattering.process_detector_dropdown_pattern(),
                "value",
            ),
            dash.State(self.ids.wavelength_nm, "value"),
            prevent_initial_call=True,
        )
        def auto_detect_detector_configuration_preset(
            n_clicks: Any,
            runtime_config_data: Any,
            selected_peak_process_name: Any,
            detector_dropdown_ids: list[dict[str, Any]],
            detector_dropdown_values: list[Any],
            current_wavelength_nm: Any,
        ) -> tuple[Any, Any, str, str, bool]:
            if not n_clicks:
                return dash.no_update, dash.no_update, "", "info", False

            runtime_config = RuntimeConfig.from_dict(
                runtime_config_data if isinstance(runtime_config_data, dict) else None
            )
            uploaded_fcs_path = runtime_config.get_str(
                "files.scattering_fcs_file_path",
                default="",
            )

            if not str(uploaded_fcs_path or "").strip():
                return (
                    dash.no_update,
                    dash.no_update,
                    "Upload a scattering FCS file before running detector auto-detect.",
                    "warning",
                    True,
                )

            selected_detector_channel = self._resolve_selected_peak_detector_channel(
                selected_peak_process_name=selected_peak_process_name,
                detector_dropdown_ids=detector_dropdown_ids,
                detector_dropdown_values=detector_dropdown_values,
            )

            if not str(selected_detector_channel or "").strip():
                return (
                    dash.no_update,
                    dash.no_update,
                    "Select the peak detector channel before running detector auto-detect.",
                    "warning",
                    True,
                )

            detected_preset = self.model_configuration.detect_detector_preset_from_uploaded_fcs(
                uploaded_fcs_path=uploaded_fcs_path,
                selected_detector_channel=selected_detector_channel,
            )

            if not detected_preset:
                filled_fields: list[str] = []
                missing_fields: list[str] = ["detector preset", "wavelength"]

                status_text = (
                    "Auto-detect could only fill some fields. "
                    f"Filled: {', '.join(filled_fields) if filled_fields else 'none'}. "
                    f"Missing: {', '.join(missing_fields)}. "
                    f"Selected peak detector channel: {selected_detector_channel}."
                )

                return (
                    dash.no_update,
                    dash.no_update,
                    status_text,
                    "warning",
                    True,
                )

            detected_wavelength_nm = self.model_configuration.resolve_detector_preset_wavelength_nm(
                preset_name=detected_preset,
                current_wavelength_nm=current_wavelength_nm,
            )

            wavelength_status_text = ""

            if detected_wavelength_nm is not None:
                wavelength_status_text = f" Wavelength: {detected_wavelength_nm} nm."

            filled_fields = [f"detector preset={detected_preset}"]
            missing_fields: list[str] = []

            if detected_wavelength_nm is not None:
                filled_fields.append(f"wavelength={detected_wavelength_nm} nm")
            else:
                missing_fields.append("wavelength")

            return (
                detected_preset,
                detected_wavelength_nm if detected_wavelength_nm is not None else current_wavelength_nm,
                (
                    "Auto-detect completed. "
                    f"Filled: {', '.join(filled_fields)}. "
                    f"Missing: {', '.join(missing_fields) if missing_fields else 'none'}. "
                    f"Selected peak detector channel: {selected_detector_channel}."
                    f"{wavelength_status_text}"
                ),
                "info",
                True,
            )

        @dash.callback(
            dash.Output(
                self.ids.detector_configuration_custom_values_container,
                "style",
            ),
            dash.Input("runtime-config-store", "data"),
            dash.Input(self.ids.detector_configuration_preset, "value"),
            prevent_initial_call=False,
        )
        def toggle_detector_configuration_custom_values(
            runtime_config_data: Any,
            preset_name: Any,
        ) -> dict[str, str]:
            logger.debug(
                "toggle_detector_configuration_custom_values called with preset_name=%r",
                preset_name,
            )

            show_preset_configuration = self._resolve_show_preset_configuration(
                runtime_config_data,
            )

            return self._build_detector_configuration_custom_values_style(
                is_visible=self._should_show_detector_preset_configuration(
                    preset_name=preset_name,
                    show_preset_configuration=show_preset_configuration,
                ),
            )

        @dash.callback(
            dash.Output(self.ids.wavelength_nm, "disabled"),
            dash.Output(self.ids.detector_numerical_aperture, "disabled"),
            dash.Output(self.ids.detector_cache_numerical_aperture, "disabled"),
            dash.Output(self.ids.blocker_bar_numerical_aperture, "disabled"),
            dash.Output(self.ids.detector_sampling, "disabled"),
            dash.Output(self.ids.detector_phi_angle_degree, "disabled"),
            dash.Output(self.ids.detector_gamma_angle_degree, "disabled"),
            dash.Output(self.ids.detector_angular_weighting_json, "disabled"),
            dash.Input(self.ids.detector_configuration_preset, "value"),
            prevent_initial_call=False,
        )
        def sync_detector_preset_disabled_state(
            preset_name: Any,
        ) -> tuple[bool, ...]:
            normalized_preset_name = str(preset_name or "").strip()
            is_locked = (
                normalized_preset_name
                != self.model_configuration.custom_detector_preset_name
            )

            return (
                is_locked,
                is_locked,
                is_locked,
                is_locked,
                is_locked,
                is_locked,
                is_locked,
                is_locked,
            )

        @dash.callback(
            dash.Output(
                self.ids.wavelength_nm,
                "value",
                allow_duplicate=True,
            ),
            dash.Output(
                self.ids.detector_numerical_aperture,
                "value",
                allow_duplicate=True,
            ),
            dash.Output(
                self.ids.detector_cache_numerical_aperture,
                "value",
                allow_duplicate=True,
            ),
            dash.Output(
                self.ids.blocker_bar_numerical_aperture,
                "value",
                allow_duplicate=True,
            ),
            dash.Output(
                self.ids.detector_sampling,
                "value",
                allow_duplicate=True,
            ),
            dash.Output(
                self.ids.detector_phi_angle_degree,
                "value",
                allow_duplicate=True,
            ),
            dash.Output(
                self.ids.detector_gamma_angle_degree,
                "value",
                allow_duplicate=True,
            ),
            dash.Input(self.ids.detector_configuration_preset, "value"),
            dash.State(self.ids.wavelength_nm, "value"),
            dash.State(self.ids.detector_numerical_aperture, "value"),
            dash.State(self.ids.detector_cache_numerical_aperture, "value"),
            dash.State(self.ids.blocker_bar_numerical_aperture, "value"),
            dash.State(self.ids.detector_sampling, "value"),
            dash.State(self.ids.detector_phi_angle_degree, "value"),
            dash.State(self.ids.detector_gamma_angle_degree, "value"),
            prevent_initial_call=True,
        )
        def apply_detector_configuration_preset(
            preset_name: Any,
            current_wavelength_nm: Any,
            current_detector_numerical_aperture: Any,
            current_detector_cache_numerical_aperture: Any,
            current_blocker_bar_numerical_aperture: Any,
            current_detector_sampling: Any,
            current_detector_phi_angle_degree: Any,
            current_detector_gamma_angle_degree: Any,
        ) -> tuple[Any, Any, Any, Any, Any, Any, Any]:
            logger.debug(
                "apply_detector_configuration_preset called with preset_name=%r",
                preset_name,
            )

            resolved_values = self.model_configuration.resolve_detector_configuration_values(
                preset_name=preset_name,
                current_detector_numerical_aperture=current_detector_numerical_aperture,
                current_detector_cache_numerical_aperture=current_detector_cache_numerical_aperture,
                current_blocker_bar_numerical_aperture=current_blocker_bar_numerical_aperture,
                current_detector_sampling=current_detector_sampling,
                current_detector_phi_angle_degree=current_detector_phi_angle_degree,
                current_detector_gamma_angle_degree=current_detector_gamma_angle_degree,
            )

            resolved_wavelength_nm = self.model_configuration.resolve_detector_preset_wavelength_nm(
                preset_name=preset_name,
                current_wavelength_nm=current_wavelength_nm,
            )

            logger.debug(
                "apply_detector_configuration_preset returning resolved_values=%r",
                resolved_values,
            )

            resolved_values = (
                resolved_values[0],
                self._clamp_detector_cache_numerical_aperture(
                    resolved_values[0],
                    resolved_values[1],
                ),
                *resolved_values[2:],
            )

            return (
                resolved_wavelength_nm,
                *resolved_values,
            )

        @dash.callback(
            dash.Output(
                self.ids.detector_cache_numerical_aperture,
                "max",
            ),
            dash.Input(self.ids.detector_numerical_aperture, "value"),
            prevent_initial_call=False,
        )
        def sync_detector_cache_numerical_aperture_max(
            detector_numerical_aperture: Any,
        ) -> Any:
            resolved_detector_numerical_aperture = casting.as_optional_float(
                detector_numerical_aperture
            )

            resolved_cache_max = None

            if resolved_detector_numerical_aperture is not None:
                resolved_cache_max = max(
                    0.0,
                    resolved_detector_numerical_aperture
                    - DETECTOR_NUMERICAL_APERTURE_EPSILON,
                )

            logger.debug(
                "sync_detector_cache_numerical_aperture_max called with detector_numerical_aperture=%r resolved_max=%r",
                detector_numerical_aperture,
                resolved_cache_max,
            )

            return resolved_cache_max

        @dash.callback(
            dash.Output(
                self.ids.detector_cache_numerical_aperture,
                "value",
                allow_duplicate=True,
            ),
            dash.Input(self.ids.detector_numerical_aperture, "value"),
            dash.State(self.ids.detector_cache_numerical_aperture, "value"),
            prevent_initial_call=True,
        )
        def clamp_detector_cache_numerical_aperture_after_detector_change(
            detector_numerical_aperture: Any,
            detector_cache_numerical_aperture: Any,
        ) -> Any:
            resolved_detector_cache_numerical_aperture = (
                self._clamp_detector_cache_numerical_aperture(
                    detector_numerical_aperture,
                    detector_cache_numerical_aperture,
                )
            )

            if resolved_detector_cache_numerical_aperture == detector_cache_numerical_aperture:
                return dash.no_update

            return resolved_detector_cache_numerical_aperture

    def _register_detector_numerical_aperture_warning_callback(self) -> None:
        """
        Register a warning callback when detector NA exceeds the medium index.
        """

        @dash.callback(
            dash.Output(self.ids.detector_numerical_aperture_warning, "children"),
            dash.Output(self.ids.detector_numerical_aperture_warning, "is_open"),
            dash.Input(self.ids.detector_numerical_aperture, "value"),
            dash.Input(self.ids.medium_refractive_index_custom, "value"),
            prevent_initial_call=False,
        )
        def update_detector_numerical_aperture_warning(
            detector_numerical_aperture: Any,
            medium_refractive_index: Any,
        ) -> tuple[str, bool]:
            resolved_detector_numerical_aperture = casting.as_optional_float(
                detector_numerical_aperture,
            )
            resolved_medium_refractive_index = casting.as_optional_float(
                medium_refractive_index,
            )

            if (
                resolved_detector_numerical_aperture is None
                or resolved_medium_refractive_index is None
                or resolved_detector_numerical_aperture <= resolved_medium_refractive_index
            ):
                return "", False

            warning_message = (
                f"Detector NA ({resolved_detector_numerical_aperture:.3f}) exceeds the medium refractive index "
                f"({resolved_medium_refractive_index:.3f}). Physically, NA should satisfy NA <= n_medium."
            )

            logger.debug(
                "update_detector_numerical_aperture_warning opening alert with detector_numerical_aperture=%r medium_refractive_index=%r",
                resolved_detector_numerical_aperture,
                resolved_medium_refractive_index,
            )

            return warning_message, True

    def _register_optical_configuration_preview_callback(self) -> None:
        """
        Register optical configuration preview callback.
        """

        @dash.callback(
            dash.Output(
                self.ids.optical_configuration_preview,
                "figure",
            ),
            dash.Input(self.ids.detector_numerical_aperture, "value"),
            dash.Input(self.ids.detector_cache_numerical_aperture, "value"),
            dash.Input(self.ids.blocker_bar_numerical_aperture, "value"),
            dash.Input(self.ids.medium_refractive_index_custom, "value"),
            dash.Input(self.ids.detector_phi_angle_degree, "value"),
            dash.Input(self.ids.detector_gamma_angle_degree, "value"),
            dash.Input(self.ids.detector_sampling, "value"),
            dash.Input(self.ids.detector_configuration_preset, "value"),
            dash.Input(self.ids.detector_angular_weighting_json, "value"),
            dash.State(self.ids.optical_configuration_preview, "relayoutData"),
            prevent_initial_call=False,
        )
        def update_optical_configuration_preview(
            detector_numerical_aperture: Any,
            detector_cache_numerical_aperture: Any,
            blocker_bar_numerical_aperture: Any,
            medium_refractive_index: Any,
            detector_phi_angle_degree: Any,
            detector_gamma_angle_degree: Any,
            detector_sampling: Any,
            detector_configuration_preset: Any,
            detector_angular_weighting_json: Any,
            relayout_data: Any,
        ):
            logger.debug(
                "update_optical_configuration_preview called with "
                "detector_numerical_aperture=%r detector_cache_numerical_aperture=%r "
                "blocker_bar_numerical_aperture=%r "
                "medium_refractive_index=%r detector_phi_angle_degree=%r "
                "detector_gamma_angle_degree=%r detector_sampling=%r "
                "detector_configuration_preset=%r relayout_data=%r",
                detector_numerical_aperture,
                detector_cache_numerical_aperture,
                blocker_bar_numerical_aperture,
                medium_refractive_index,
                detector_phi_angle_degree,
                detector_gamma_angle_degree,
                detector_sampling,
                detector_configuration_preset,
                detector_angular_weighting_json,
                relayout_data,
            )

            return self.model_configuration.build_optical_configuration_preview_figure(
                detector_numerical_aperture=detector_numerical_aperture,
                detector_cache_numerical_aperture=detector_cache_numerical_aperture,
                blocker_bar_numerical_aperture=blocker_bar_numerical_aperture,
                medium_refractive_index=medium_refractive_index,
                detector_phi_angle_degree=detector_phi_angle_degree,
                detector_gamma_angle_degree=detector_gamma_angle_degree,
                polarization_angle_degree=DEFAULT_SOURCE_POLARIZATION_ANGLE_DEGREE,
                detector_sampling=detector_sampling,
                detector_configuration_preset=detector_configuration_preset,
                detector_angular_weighting_json=detector_angular_weighting_json,
                camera=optical_preview.resolve_locked_camera_from_relayout_data(
                    relayout_data=relayout_data,
                ),
            )

        @dash.callback(
            dash.Output(self.ids.detector_angular_weighting_alert, "children"),
            dash.Output(self.ids.detector_angular_weighting_alert, "is_open"),
            dash.Output(self.ids.detector_angular_weighting_alert, "color"),
            dash.Input(self.ids.detector_angular_weighting_json, "value"),
            dash.Input(self.ids.detector_configuration_preset, "value"),
            dash.Input(self.ids.detector_numerical_aperture, "value"),
            dash.Input(self.ids.detector_cache_numerical_aperture, "value"),
            dash.Input(self.ids.blocker_bar_numerical_aperture, "value"),
            dash.Input(self.ids.medium_refractive_index_custom, "value"),
            dash.Input(self.ids.detector_phi_angle_degree, "value"),
            dash.Input(self.ids.detector_gamma_angle_degree, "value"),
            dash.Input(self.ids.detector_sampling, "value"),
            prevent_initial_call=False,
        )
        def validate_detector_angular_weighting_json(
            detector_angular_weighting_json: Any,
            detector_configuration_preset: Any,
            detector_numerical_aperture: Any,
            detector_cache_numerical_aperture: Any,
            blocker_bar_numerical_aperture: Any,
            medium_refractive_index: Any,
            detector_phi_angle_degree: Any,
            detector_gamma_angle_degree: Any,
            detector_sampling: Any,
        ) -> tuple[str, bool, str]:
            if (
                str(detector_configuration_preset or "").strip()
                != self.model_configuration.custom_detector_preset_name
            ):
                return "", False, "warning"

            if detector_angular_weighting_json in (None, ""):
                return "", False, "warning"

            try:
                parsed_payload = json.loads(str(detector_angular_weighting_json))
            except json.JSONDecodeError as exc:
                return f"Invalid detector angular weighting JSON: {exc.msg}.", True, "warning"

            if not isinstance(parsed_payload, dict):
                return "Detector angular weighting JSON must define an object.", True, "warning"

            try:
                detector_angular_weights = detector.resolve_detector_angular_weights(
                    preset_name=detector_configuration_preset,
                    detector_sampling=detector_sampling,
                    current_detector_numerical_aperture=detector_numerical_aperture,
                    current_detector_cache_numerical_aperture=detector_cache_numerical_aperture,
                    current_blocker_bar_numerical_aperture=blocker_bar_numerical_aperture,
                    current_detector_phi_angle_degree=detector_phi_angle_degree,
                    current_detector_gamma_angle_degree=detector_gamma_angle_degree,
                    current_medium_refractive_index=medium_refractive_index,
                    current_detector_angular_weighting=parsed_payload,
                )
            except Exception as exc:
                return f"Detector angular weighting is invalid: {exc}", True, "warning"

            if detector_angular_weights is None:
                return (
                    "Custom detector angular weighting is loaded, but no detector geometry is available to display yet.",
                    True,
                    "info",
                )

            weight_array = np.asarray(
                detector_angular_weights,
                dtype=np.complex128,
            ).reshape(-1)
            kept_count = int(
                np.count_nonzero(
                    weight_array != 0.0
                )
            )
            total_count = int(weight_array.size)
            kept_fraction = 0.0 if total_count == 0 else kept_count / total_count

            return (
                f"Custom detector angular weighting is active: keeping {kept_count}/{total_count} angular samples ({kept_fraction:.1%}).",
                True,
                "info",
            )
