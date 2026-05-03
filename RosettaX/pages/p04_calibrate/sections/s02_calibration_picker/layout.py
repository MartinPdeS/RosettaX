# -*- coding: utf-8 -*-

import logging
from typing import Any, Optional

import dash
import dash_bootstrap_components as dbc

from RosettaX.utils import styling
from RosettaX.utils import ui_forms
from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.workflow.apply_calibration.scattering import (
    CUSTOM_PRESET_NAME,
    build_scattering_target_model_preset_options,
)
from RosettaX.workflow.scattering.model import ScatteringModelConfiguration
from RosettaX.workflow.plotting import scatter2d

from . import services


logger = logging.getLogger(__name__)


class CalibrationPickerLayout:
    """
    Layout builder for the calibration picker section.
    """

    model_configuration = ScatteringModelConfiguration

    def __init__(
        self,
        *,
        page: Any,
        section_number: int,
        card_color: str = "green",
        secondary_card_color: str = "gray",
    ) -> None:
        self.page = page
        self.section_number = section_number
        self.card_color = card_color
        self.secondary_card_color = secondary_card_color

        self.header_tooltip_target_id = (
            f"{self.page.ids.CalibrationPicker.dropdown}-section-info-target"
        )
        self.header_tooltip_id = (
            f"{self.page.ids.CalibrationPicker.dropdown}-section-info-tooltip"
        )

        self.target_model_tooltip_target_id = (
            f"{self.page.ids.CalibrationPicker.target_mie_model}-section-info-target"
        )
        self.target_model_tooltip_id = (
            f"{self.page.ids.CalibrationPicker.target_mie_model}-section-info-tooltip"
        )

        self.target_graph_tooltip_target_id = (
            f"{self.page.ids.CalibrationPicker.target_mie_relation_graph}-info-target"
        )
        self.target_graph_tooltip_id = (
            f"{self.page.ids.CalibrationPicker.target_mie_relation_graph}-info-tooltip"
        )

    def build_layout(self) -> dbc.Card:
        """
        Build the calibration picker layout.
        """
        logger.debug("Building CalibrationPicker layout.")

        return dbc.Card(
            [
                self._build_header(),
                self._build_body(),
            ],
            style=ui_forms.build_workflow_section_card_style(
                color_name=self.card_color,
            ),
        )

    def _build_header(self) -> dbc.CardHeader:
        """
        Build the section header.
        """
        return ui_forms.build_card_header_with_info(
            title=f"{self.section_number}. Select calibration",
            tooltip_target_id=self.header_tooltip_target_id,
            tooltip_id=self.header_tooltip_id,
            tooltip_text=(
                "Select a saved fluorescence or scattering calibration. "
                "Fluorescence calibrations can be applied directly. Scattering "
                "calibrations also require a target particle model for diameter "
                "conversion."
            ),
            subtitle="Choose the calibration file that will be applied to the uploaded FCS data.",
            color_name=self.card_color,
        )

    def _build_body(self) -> dbc.CardBody:
        """
        Build the section body.
        """
        return dbc.CardBody(
            [
                self._build_picker_panel(),
                dash.html.Div(
                    style={
                        "height": "18px",
                    },
                ),
                self._build_scattering_target_model_section(),
            ],
            style=ui_forms.build_workflow_section_body_style(),
        )

    def _build_picker_panel(self) -> dbc.Card:
        """
        Build the selected calibration picker panel.
        """
        return dbc.Card(
            dbc.CardBody(
                [
                    dash.html.Div(
                        [
                            dash.html.Div(
                                [
                                    dash.html.Div(
                                        "Calibration file",
                                        style={
                                            "fontWeight": "700",
                                            "fontSize": "1rem",
                                        },
                                    ),
                                    dash.html.Div(
                                        (
                                            "Pick one saved calibration JSON file. "
                                            "The list is built from the fluorescence "
                                            "and scattering calibration folders."
                                        ),
                                        style=ui_forms.build_workflow_section_subtitle_style(
                                            font_size="0.9rem",
                                            opacity=0.72,
                                            margin_top_px=2,
                                        ),
                                    ),
                                ],
                                style={
                                    "flex": "1 1 280px",
                                },
                            ),
                            self._build_picker_row(),
                        ],
                        style={
                            "display": "flex",
                            "alignItems": "center",
                            "justifyContent": "space-between",
                            "gap": "18px",
                            "flexWrap": "wrap",
                            "overflow": "visible",
                        },
                    ),
                ],
                style={
                    "padding": "14px 16px",
                    "overflow": "visible",
                },
            ),
            style=ui_forms.build_workflow_panel_style(
                color_name=self.card_color,
                background=styling.build_rgba(
                    self.card_color,
                    0.04,
                ),
            ),
        )

    def _build_picker_row(self) -> dash.html.Div:
        """
        Build the calibration dropdown and refresh row.
        """
        return dash.html.Div(
            [
                dash.html.Div(
                    ui_forms.persistent_dropdown(
                        id=self.page.ids.CalibrationPicker.dropdown,
                        options=[],
                        value=None,
                        clearable=False,
                        searchable=True,
                        style={
                            "width": "100%",
                        },
                    ),
                    style={
                        "flex": "1 1 420px",
                        "minWidth": "320px",
                        "position": "relative",
                        "zIndex": 20,
                    },
                ),
                dbc.Button(
                    "Refresh",
                    id=self.page.ids.CalibrationPicker.refresh_button,
                    color="secondary",
                    outline=True,
                ),
            ],
            style={
                "display": "flex",
                "alignItems": "center",
                "gap": "10px",
                "flex": "1.25 1 520px",
                "minWidth": "360px",
                "overflow": "visible",
            },
        )

    def _build_scattering_target_model_section(self) -> dash.html.Div:
        """
        Build target particle model controls shown for scattering calibration.
        """
        return dash.html.Div(
            [
                dbc.Card(
                    [
                        dbc.CardHeader(
                            [
                                ui_forms.build_title_with_info(
                                    title="Target particle model",
                                    tooltip_target_id=self.target_model_tooltip_target_id,
                                    tooltip_id=self.target_model_tooltip_id,
                                    tooltip_text=(
                                        "The selected scattering calibration provides the "
                                        "instrument response. These parameters define the "
                                        "target particle model used to convert calibrated "
                                        "optical coupling into equivalent diameter."
                                    ),
                                    title_style_overrides={
                                        "fontSize": "1rem",
                                    },
                                ),
                                dash.html.Div(
                                    (
                                        "Configure the target Mie model used for scattering "
                                        "diameter inversion."
                                    ),
                                    style=ui_forms.build_workflow_section_subtitle_style(
                                        font_size="0.84rem",
                                        opacity=0.72,
                                    ),
                                ),
                            ],
                            style=ui_forms.build_workflow_subpanel_header_style(
                                color_name=self.card_color,
                            ),
                        ),
                        dbc.CardBody(
                            [
                                dash.html.Div(
                                    [
                                        self._build_target_model_controls_panel(),
                                        self._build_target_mie_relation_preview_panel(),
                                    ],
                                    style={
                                        "display": "flex",
                                        "gap": "18px",
                                        "alignItems": "stretch",
                                        "width": "100%",
                                        "flexWrap": "wrap",
                                        "overflow": "visible",
                                    },
                                ),
                            ],
                            style=ui_forms.build_workflow_panel_body_style(
                                style_overrides={
                                    "padding": "16px",
                                },
                            ),
                        ),
                    ],
                    style=ui_forms.build_workflow_subpanel_card_style(
                        color_name=self.card_color,
                    ),
                ),
            ],
            id=self.page.ids.CalibrationPicker.scattering_target_model_container,
            style=services.build_scattering_target_model_container_style(
                is_visible=False,
            ),
        )

    def _build_target_model_controls_panel(self) -> dbc.Card:
        """
        Build the target model form controls panel.
        """
        return dbc.Card(
            [
                dbc.CardHeader(
                    [
                        dash.html.Div(
                            "Model parameters",
                            style={
                                "fontWeight": "700",
                                "fontSize": "0.98rem",
                            },
                        ),
                        dash.html.Div(
                            "Preset, particle type, refractive indices, and model specific diameter range.",
                            style=ui_forms.build_workflow_section_subtitle_style(
                                font_size="0.84rem",
                                opacity=0.72,
                            ),
                        ),
                    ],
                    style=ui_forms.build_workflow_subpanel_header_style(
                        color_name=self.secondary_card_color,
                    ),
                ),
                dbc.CardBody(
                    [
                        ui_forms.build_inline_row(
                            label="Preset:",
                            control=ui_forms.persistent_dropdown(
                                id=self.page.ids.CalibrationPicker.target_model_preset,
                                options=build_scattering_target_model_preset_options(),
                                value=CUSTOM_PRESET_NAME,
                                clearable=False,
                                searchable=False,
                                style={
                                    "width": "220px",
                                },
                            ),
                            label_width_px=230,
                            margin_top=False,
                        ),
                        ui_forms.build_inline_row(
                            label="Particle type:",
                            control=ui_forms.persistent_dropdown(
                                id=self.page.ids.CalibrationPicker.target_mie_model,
                                options=self.model_configuration.mie_model_options,
                                value="Solid Sphere",
                                clearable=False,
                                searchable=False,
                                style={
                                    "width": "220px",
                                },
                            ),
                            label_width_px=230,
                            margin_top=True,
                        ),
                        self._build_numeric_input_row(
                            label="Medium refractive index:",
                            component_id=self.page.ids.CalibrationPicker.target_medium_refractive_index,
                            value=1.333,
                            min_value=1.0,
                            max_value=2.5,
                            step=0.001,
                        ),
                        self._build_solid_sphere_parameters(),
                        self._build_core_shell_parameters(),
                    ],
                    style=ui_forms.build_workflow_panel_body_style(
                        style_overrides={
                            "padding": "14px",
                        },
                    ),
                ),
            ],
            style={
                **ui_forms.build_workflow_subpanel_card_style(
                    color_name=self.secondary_card_color,
                ),
                "flex": "1 1 460px",
                "minWidth": "420px",
            },
        )

    def _build_solid_sphere_parameters(self) -> dash.html.Div:
        """
        Build solid sphere target parameter controls.
        """
        return dash.html.Div(
            [
                self._build_numeric_input_row(
                    label="Particle refractive index:",
                    component_id=self.page.ids.CalibrationPicker.target_particle_refractive_index,
                    value=1.39,
                    min_value=1.0,
                    max_value=2.5,
                    step=0.001,
                ),
                self._build_numeric_input_row(
                    label="Particle diameter min [nm]:",
                    component_id=self.page.ids.CalibrationPicker.target_solid_sphere_diameter_min_nm,
                    value=30,
                    min_value=1,
                    step=1,
                ),
                self._build_numeric_input_row(
                    label="Particle diameter max [nm]:",
                    component_id=self.page.ids.CalibrationPicker.target_solid_sphere_diameter_max_nm,
                    value=1000,
                    min_value=1,
                    step=1,
                ),
                self._build_numeric_input_row(
                    label="Particle diameter points:",
                    component_id=self.page.ids.CalibrationPicker.target_solid_sphere_diameter_count,
                    value=500,
                    min_value=2,
                    step=1,
                ),
            ],
            id=self.page.ids.CalibrationPicker.target_solid_sphere_parameter_container,
            style=services.build_target_parameter_container_style(
                is_visible=True,
            ),
        )

    def _build_core_shell_parameters(self) -> dash.html.Div:
        """
        Build core shell target parameter controls.
        """
        return dash.html.Div(
            [
                self._build_numeric_input_row(
                    label="Core refractive index:",
                    component_id=self.page.ids.CalibrationPicker.target_core_refractive_index,
                    value=1.37,
                    min_value=1.0,
                    max_value=2.5,
                    step=0.001,
                ),
                self._build_numeric_input_row(
                    label="Shell refractive index:",
                    component_id=self.page.ids.CalibrationPicker.target_shell_refractive_index,
                    value=1.46,
                    min_value=1.0,
                    max_value=2.5,
                    step=0.001,
                ),
                self._build_numeric_input_row(
                    label="Shell thickness [nm]:",
                    component_id=self.page.ids.CalibrationPicker.target_shell_thickness_nm,
                    value=5,
                    min_value=0,
                    step=1,
                ),
                self._build_numeric_input_row(
                    label="Core diameter min [nm]:",
                    component_id=self.page.ids.CalibrationPicker.target_core_shell_core_diameter_min_nm,
                    value=30,
                    min_value=1,
                    step=1,
                ),
                self._build_numeric_input_row(
                    label="Core diameter max [nm]:",
                    component_id=self.page.ids.CalibrationPicker.target_core_shell_core_diameter_max_nm,
                    value=1000,
                    min_value=1,
                    step=1,
                ),
                self._build_numeric_input_row(
                    label="Core diameter points:",
                    component_id=self.page.ids.CalibrationPicker.target_core_shell_core_diameter_count,
                    value=500,
                    min_value=2,
                    step=1,
                ),
            ],
            id=self.page.ids.CalibrationPicker.target_core_shell_parameter_container,
            style=services.build_target_parameter_container_style(
                is_visible=False,
            ),
        )

    def _build_target_mie_relation_preview_panel(self) -> dbc.Card:
        """
        Build the target Mie relation preview panel.
        """
        return dbc.Card(
            [
                dbc.CardHeader(
                    [
                        ui_forms.build_title_with_info(
                            title="Target Mie relation preview",
                            tooltip_target_id=self.target_graph_tooltip_target_id,
                            tooltip_id=self.target_graph_tooltip_id,
                            tooltip_text=(
                                "This preview shows the target Mie relation used for "
                                "diameter inversion. If the full relation is not monotonic, "
                                "RosettaX automatically selects the largest monotonic branch."
                            ),
                            title_style_overrides={
                                "fontSize": "0.98rem",
                            },
                        ),
                        dash.html.Div(
                            "Full relation and selected monotonic branch when needed.",
                            style=ui_forms.build_workflow_section_subtitle_style(
                                font_size="0.84rem",
                                opacity=0.72,
                            ),
                        ),
                    ],
                    style=ui_forms.build_workflow_subpanel_header_style(
                        color_name=self.secondary_card_color,
                    ),
                ),
                dbc.CardBody(
                    [
                        dbc.Alert(
                            "Target Mie relation status will appear here.",
                            id=self.page.ids.CalibrationPicker.target_mie_relation_status,
                            color="secondary",
                            style={
                                "marginBottom": "10px",
                            },
                        ),
                        scatter2d.Scatter2DGraph.build_component(
                            component_ids=scatter2d.Scatter2DGraphIds(
                                graph=self.page.ids.CalibrationPicker.target_mie_relation_graph,
                                axis_scale_toggle=self.page.ids.CalibrationPicker.target_mie_relation_axis_scale_toggle,
                            ),
                            figure=services.build_empty_target_mie_relation_figure(),
                            x_log_enabled=self._get_default_target_mie_relation_xscale() == "log",
                            y_log_enabled=self._get_default_target_mie_relation_yscale() == "log",
                            graph_style={
                                "height": "320px",
                                "width": "100%",
                            },
                        ),
                    ],
                    style=ui_forms.build_workflow_panel_body_style(
                        style_overrides={
                            "padding": "14px",
                        },
                    ),
                ),
            ],
            style={
                **ui_forms.build_workflow_subpanel_card_style(
                    color_name=self.secondary_card_color,
                ),
                "flex": "1.25 1 560px",
                "minWidth": "440px",
            },
        )

    def _build_numeric_input_row(
        self,
        *,
        label: str,
        component_id: str,
        value: Any,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        step: Optional[float] = None,
    ) -> dash.html.Div:
        """
        Build one labeled numeric input row.
        """
        return ui_forms.build_inline_row(
            label=label,
            control=ui_forms.persistent_input(
                id=component_id,
                type="number",
                value=value,
                min=min_value,
                max=max_value,
                step=step,
                debounce=True,
                style={
                    "width": "180px",
                },
            ),
            label_width_px=230,
            margin_top=True,
        )

    @staticmethod
    def _get_default_target_mie_relation_xscale() -> str:
        """
        Return the default x axis scale for the target Mie relation preview.
        """
        runtime_config = RuntimeConfig.from_default_profile()

        return services.normalize_axis_scale(
            runtime_config.get_str(
                "calibration.target_mie_relation_xscale",
                default="linear",
            ),
            default="linear",
        )

    @staticmethod
    def _get_default_target_mie_relation_yscale() -> str:
        """
        Return the default y axis scale for the target Mie relation preview.
        """
        runtime_config = RuntimeConfig.from_default_profile()

        return services.normalize_axis_scale(
            runtime_config.get_str(
                "calibration.target_mie_relation_yscale",
                default="log",
            ),
            default="log",
        )