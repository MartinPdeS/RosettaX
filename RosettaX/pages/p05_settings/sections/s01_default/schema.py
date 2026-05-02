# -*- coding: utf-8 -*-

import logging
from dataclasses import dataclass
from typing import Any, Optional

from RosettaX.workflow.apply_calibration.scattering import (
    CUSTOM_PRESET_NAME,
    build_scattering_target_model_preset_options,
)
from RosettaX.workflow.model.scattering import (
    CUSTOM_SCATTERER_PRESET_NAME,
    build_scattering_calibration_scatterer_preset_options,
)
from RosettaX.workflow.peak import registry

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FieldDefinition:
    name: str
    section: str
    label: str
    component_kind: str
    value_kind: str
    runtime_path: str
    default: Any
    placeholder: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    step: Optional[float] = None
    options: Optional[list[dict[str, Any]]] = None


def build_peak_process_dropdown_options() -> list[dict[str, Any]]:
    """
    Build dropdown options for preferred peak process selection.

    Returns
    -------
    list[dict[str, Any]]
        Peak process dropdown options.
    """
    options = registry.build_peak_process_options()

    if options:
        return options

    return [
        {
            "label": registry.DEFAULT_PROCESS_NAME,
            "value": registry.DEFAULT_PROCESS_NAME,
        }
    ]


PROFILE_SECTION_ORDER: list[tuple[str, str]] = [
    ("miscellaneous", "Application and files"),
    ("calibration", "Shared workflow defaults"),
    ("fluorescence", "Fluorescence workflow"),
    ("scattering", "Scattering workflow"),
    ("visualization", "Visualization"),
]


PEAK_PROCESS_OPTIONS = build_peak_process_dropdown_options()
SCATTERING_PRESET_OPTIONS = build_scattering_calibration_scatterer_preset_options()
APPLY_TARGET_PRESET_OPTIONS = build_scattering_target_model_preset_options()


AXIS_SCALE_OPTIONS: list[dict[str, str]] = [
    {
        "label": "Linear",
        "value": "linear",
    },
    {
        "label": "Log",
        "value": "log",
    },
]


YES_NO_OPTIONS: list[dict[str, str]] = [
    {
        "label": "Yes",
        "value": "yes",
    },
    {
        "label": "No",
        "value": "no",
    },
]


PEAK_TABLE_SORT_ORDER_OPTIONS: list[dict[str, str]] = [
    {
        "label": "Small to large",
        "value": "ascending",
    },
    {
        "label": "Large to small",
        "value": "descending",
    },
]


FIELD_DEFINITIONS: list[FieldDefinition] = [
    FieldDefinition(
        name="mesf_values",
        section="fluorescence",
        label="MESF values:",
        component_kind="text",
        value_kind="float_list",
        runtime_path="calibration.mesf_values",
        default=[],
    ),
    FieldDefinition(
        name="peak_count",
        section="fluorescence",
        label="Peak count:",
        component_kind="number",
        value_kind="int",
        runtime_path="calibration.peak_count",
        default=6,
        min_value=1,
        max_value=10,
        step=1,
    ),
    FieldDefinition(
        name="default_fluorescence_peak_process",
        section="fluorescence",
        label="Default fluorescence peak process:",
        component_kind="dropdown",
        value_kind="choice",
        runtime_path="calibration.default_fluorescence_peak_process",
        default=registry.DEFAULT_PROCESS_NAME,
        options=PEAK_PROCESS_OPTIONS,
    ),
    FieldDefinition(
        name="fluorescence_peak_table_sort_order",
        section="fluorescence",
        label="Fluorescence peak table order:",
        component_kind="dropdown",
        value_kind="choice",
        runtime_path="fluorescence_calibration.peak_table_sort_order",
        default="ascending",
        options=PEAK_TABLE_SORT_ORDER_OPTIONS,
    ),
    FieldDefinition(
        name="default_scatterer_preset",
        section="scattering",
        label="Default scatterer preset:",
        component_kind="dropdown",
        value_kind="choice",
        runtime_path="particle_model.scatterer_preset",
        default=CUSTOM_SCATTERER_PRESET_NAME,
        options=SCATTERING_PRESET_OPTIONS,
    ),
    FieldDefinition(
        name="medium_refractive_index",
        section="scattering",
        label="Medium refractive index:",
        component_kind="number",
        value_kind="float",
        runtime_path="optics.medium_refractive_index",
        default=1.333,
        min_value=0.001,
        max_value=2.5,
        step=0.001,
    ),
    FieldDefinition(
        name="core_refractive_index",
        section="scattering",
        label="Core refractive index:",
        component_kind="number",
        value_kind="float",
        runtime_path="particle_model.core_refractive_index",
        default=1.45,
        min_value=0.001,
        max_value=2.5,
        step=0.001,
    ),
    FieldDefinition(
        name="shell_refractive_index",
        section="scattering",
        label="Shell refractive index:",
        component_kind="number",
        value_kind="float",
        runtime_path="particle_model.shell_refractive_index",
        default=1.40,
        min_value=0.001,
        max_value=2.5,
        step=0.001,
    ),
    FieldDefinition(
        name="particle_refractive_index",
        section="scattering",
        label="Particle refractive index:",
        component_kind="number",
        value_kind="float",
        runtime_path="particle_model.particle_refractive_index",
        default=1.45,
        min_value=0.001,
        max_value=2.5,
        step=0.001,
    ),
    FieldDefinition(
        name="wavelength_nm",
        section="scattering",
        label="Wavelength (nm):",
        component_kind="number",
        value_kind="float",
        runtime_path="optics.wavelength_nm",
        default=488.0,
        min_value=1,
        step=1,
    ),
    FieldDefinition(
        name="shell_thickness_nm",
        section="scattering",
        label="Default shell thickness list (nm):",
        component_kind="text",
        value_kind="float_list",
        runtime_path="particle_model.shell_thickness_nm",
        default=[],
        placeholder="5, 10, 15",
    ),
    FieldDefinition(
        name="core_diameter_nm",
        section="scattering",
        label="Default core diameter list (nm):",
        component_kind="text",
        value_kind="float_list",
        runtime_path="particle_model.core_diameter_nm",
        default=[],
        placeholder="80, 120, 160",
    ),
    FieldDefinition(
        name="particle_diameter_nm",
        section="scattering",
        label="Default particle diameter list (nm):",
        component_kind="text",
        value_kind="float_list",
        runtime_path="particle_model.particle_diameter_nm",
        default=[],
        placeholder="100, 200, 300",
    ),
    FieldDefinition(
        name="mie_model",
        section="scattering",
        label="Particle type:",
        component_kind="dropdown",
        value_kind="choice",
        runtime_path="particle_model.mie_model",
        default="Solid Sphere",
        options=[
            {
                "label": "Solid Sphere",
                "value": "Solid Sphere",
            },
            {
                "label": "Core/Shell Sphere",
                "value": "Core/Shell Sphere",
            },
        ],
    ),
    FieldDefinition(
        name="default_scattering_peak_process",
        section="scattering",
        label="Default scattering peak process:",
        component_kind="dropdown",
        value_kind="choice",
        runtime_path="scattering_calibration.default_peak_process",
        default=registry.DEFAULT_PROCESS_NAME,
        options=PEAK_PROCESS_OPTIONS,
    ),
    FieldDefinition(
        name="scattering_peak_table_sort_order",
        section="scattering",
        label="Scattering peak table order:",
        component_kind="dropdown",
        value_kind="choice",
        runtime_path="scattering_calibration.peak_table_sort_order",
        default="ascending",
        options=PEAK_TABLE_SORT_ORDER_OPTIONS,
    ),
    FieldDefinition(
        name="default_gating_channel",
        section="scattering",
        label="Default gating channel:",
        component_kind="text",
        value_kind="string",
        runtime_path="calibration.default_gating_channel",
        default="",
    ),
    FieldDefinition(
        name="default_gating_threshold",
        section="scattering",
        label="Default gating threshold:",
        component_kind="number",
        value_kind="float",
        runtime_path="calibration.default_gating_threshold",
        default=0.0,
        step=0.1,
    ),
    FieldDefinition(
        name="default_apply_target_model_preset",
        section="calibration",
        label="Default apply target preset:",
        component_kind="dropdown",
        value_kind="choice",
        runtime_path="calibration.target_model_preset",
        default=CUSTOM_PRESET_NAME,
        options=APPLY_TARGET_PRESET_OPTIONS,
    ),
    FieldDefinition(
        name="target_mie_relation_xscale",
        section="scattering",
        label="Target Mie relation x scale:",
        component_kind="dropdown",
        value_kind="choice",
        runtime_path="calibration.target_mie_relation_xscale",
        default="linear",
        options=AXIS_SCALE_OPTIONS,
    ),
    FieldDefinition(
        name="target_mie_relation_yscale",
        section="scattering",
        label="Target Mie relation y scale:",
        component_kind="dropdown",
        value_kind="choice",
        runtime_path="calibration.target_mie_relation_yscale",
        default="log",
        options=AXIS_SCALE_OPTIONS,
    ),
    FieldDefinition(
        name="histogram_xscale",
        section="calibration",
        label="Peak graph x scale:",
        component_kind="dropdown",
        value_kind="choice",
        runtime_path="calibration.histogram_xscale",
        default="linear",
        options=AXIS_SCALE_OPTIONS,
    ),
    FieldDefinition(
        name="histogram_yscale",
        section="calibration",
        label="Peak graph y scale:",
        component_kind="dropdown",
        value_kind="choice",
        runtime_path="calibration.histogram_yscale",
        default="log",
        options=AXIS_SCALE_OPTIONS,
    ),
    FieldDefinition(
        name="max_events_for_analysis",
        section="calibration",
        label="Max events for analysis:",
        component_kind="number",
        value_kind="int",
        runtime_path="calibration.max_events_for_analysis",
        default=100000,
        min_value=1,
        step=1,
    ),
    FieldDefinition(
        name="default_output_suffix",
        section="calibration",
        label="Default output suffix:",
        component_kind="text",
        value_kind="string",
        runtime_path="calibration.default_output_suffix",
        default="_calibrated",
    ),
    FieldDefinition(
        name="operator_name",
        section="calibration",
        label="Operator name:",
        component_kind="text",
        value_kind="string",
        runtime_path="metadata.operator_name",
        default="",
    ),
    FieldDefinition(
        name="instrument_name",
        section="calibration",
        label="Instrument name:",
        component_kind="text",
        value_kind="string",
        runtime_path="metadata.instrument_name",
        default="",
    ),
    FieldDefinition(
        name="graph_height",
        section="visualization",
        label="Graph height:",
        component_kind="text",
        value_kind="string",
        runtime_path="visualization.graph_height",
        default="850px",
        placeholder="850px, 70vh, calc(100vh - 260px)",
    ),
    FieldDefinition(
        name="default_marker_size",
        section="visualization",
        label="Default marker size:",
        component_kind="number",
        value_kind="float",
        runtime_path="visualization.default_marker_size",
        default=7.0,
        min_value=0.0,
        step=0.5,
    ),
    FieldDefinition(
        name="n_bins",
        section="visualization",
        label="Number of bins for plots:",
        component_kind="number",
        value_kind="int",
        runtime_path="calibration.n_bins_for_plots",
        default=256,
        min_value=1,
        step=1,
    ),
    FieldDefinition(
        name="show_calibration",
        section="visualization",
        label="Show calibration plot by default:",
        component_kind="dropdown",
        value_kind="yes_no_bool",
        runtime_path="calibration.show_calibration_plot_by_default",
        default=True,
        options=YES_NO_OPTIONS,
    ),
    FieldDefinition(
        name="default_line_width",
        section="visualization",
        label="Default line width:",
        component_kind="number",
        value_kind="float",
        runtime_path="visualization.default_line_width",
        default=2.0,
        min_value=0.5,
        step=0.5,
    ),
    FieldDefinition(
        name="default_font_size",
        section="visualization",
        label="Default font size:",
        component_kind="number",
        value_kind="float",
        runtime_path="visualization.default_font_size",
        default=14.0,
        min_value=1,
        max_value=100,
        step=1,
        placeholder="e.g. 14",
    ),
    FieldDefinition(
        name="default_tick_size",
        section="visualization",
        label="Default tick size:",
        component_kind="number",
        value_kind="float",
        runtime_path="visualization.default_tick_size",
        default=12.0,
        min_value=1,
        max_value=100,
        step=1,
        placeholder="e.g. 12",
    ),
    FieldDefinition(
        name="show_grid_by_default",
        section="visualization",
        label="Show grid by default:",
        component_kind="dropdown",
        value_kind="yes_no_bool",
        runtime_path="visualization.show_grid_by_default",
        default=True,
        options=YES_NO_OPTIONS,
    ),
    FieldDefinition(
        name="fluorescence_fcs_file_path",
        section="miscellaneous",
        label="Default Fluorescence FCS file path:",
        component_kind="text",
        value_kind="string",
        runtime_path="files.fluorescence_fcs_file_path",
        default="",
    ),
    FieldDefinition(
        name="scattering_fcs_file_path",
        section="miscellaneous",
        label="Default Scattering FCS file path:",
        component_kind="text",
        value_kind="string",
        runtime_path="files.scattering_fcs_file_path",
        default="",
    ),
    FieldDefinition(
        name="theme_mode",
        section="miscellaneous",
        label="Theme mode:",
        component_kind="dropdown",
        value_kind="choice",
        runtime_path="ui.theme_mode",
        default="dark",
        options=[
            {
                "label": "Dark",
                "value": "dark",
            },
            {
                "label": "Light",
                "value": "light",
            },
        ],
    ),
    FieldDefinition(
        name="show_graphs",
        section="miscellaneous",
        label="Show graphs:",
        component_kind="dropdown",
        value_kind="yes_no_bool",
        runtime_path="ui.show_graphs",
        default=True,
        options=YES_NO_OPTIONS,
    ),
]


FIELD_DEFINITION_BY_NAME: dict[str, FieldDefinition] = {
    field.name: field for field in FIELD_DEFINITIONS
}


def ordered_field_names() -> list[str]:
    return [field.name for field in FIELD_DEFINITIONS]


def section_field_names(
    section_key: str,
) -> list[str]:
    return [field.name for field in FIELD_DEFINITIONS if field.section == section_key]
