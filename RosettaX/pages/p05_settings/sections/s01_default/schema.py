# -*- coding: utf-8 -*-

import logging
from dataclasses import dataclass
from typing import Any, Optional

from RosettaX.workflow import scattering, apply_calibration, detector
from RosettaX.workflow.peak import registry as peak_registry
from RosettaX.workflow.table.fluorescence import (
    CUSTOM_FLUORESCENCE_REFERENCE_PRESET_NAME,
    build_fluorescence_reference_preset_options,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FieldDefinition:
    name: str
    section: str
    label: str
    component_kind: str
    value_kind: str
    runtime_path: str
    profile_path: str
    default: Any
    placeholder: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    step: Optional[float] = None
    options: Optional[list[dict[str, Any]]] = None
    group: Optional[str] = None


def build_peak_process_dropdown_options() -> list[dict[str, Any]]:
    """
    Build dropdown options for preferred peak process selection.

    Returns
    -------
    list[dict[str, Any]]
        Peak process dropdown options.
    """
    options = peak_registry.build_peak_process_options()

    if options:
        return options

    return [
        {
            "label": peak_registry.DEFAULT_PROCESS_NAME,
            "value": peak_registry.DEFAULT_PROCESS_NAME,
        }
    ]


PROFILE_SECTION_ORDER: list[tuple[str, str]] = [
    ("fluorescence", "Fluorescence"),
    ("scattering", "Scattering"),
    ("apply_calibration", "Apply calibration"),
    ("figure_style", "Figure style"),
    ("metadata", "Metadata"),
    ("misc", "Misc"),
]


PEAK_PROCESS_OPTIONS = build_peak_process_dropdown_options()
SCATTERING_PRESET_OPTIONS = scattering.build_scattering_calibration_scatterer_preset_options()
APPLY_TARGET_PRESET_OPTIONS = apply_calibration.scattering.build_scattering_target_model_preset_options()
DETECTOR_PRESET_OPTIONS = detector.build_detector_preset_options()
SETTINGS_DETECTOR_PRESET_OPTIONS = [
    {
        "label": "No default",
        "value": "",
    },
    *DETECTOR_PRESET_OPTIONS,
]
FLUORESCENCE_REFERENCE_PRESET_OPTIONS = build_fluorescence_reference_preset_options()


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


SCATTERING_DERIVED_OUTPUT_MODE_OPTIONS: list[dict[str, str]] = [
    {
        "label": "Coupling + diameter",
        "value": "both",
    },
    {
        "label": "Coupling only",
        "value": "estimated_coupling",
    },
    {
        "label": "Diameter only",
        "value": "mie_equivalent_diameter_nm",
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
        name="default_fluorescence_reference_preset",
        section="fluorescence",
        group="Calibration",
        label="Default fluorescence reference preset:",
        component_kind="dropdown",
        value_kind="fluorescence_reference_preset",
        runtime_path="calibration.mesf_values",
        profile_path="",
        default=CUSTOM_FLUORESCENCE_REFERENCE_PRESET_NAME,
        options=FLUORESCENCE_REFERENCE_PRESET_OPTIONS,
    ),
    FieldDefinition(
        name="mesf_values",
        section="fluorescence",
        group="Calibration",
        label="Custom MESF values:",
        component_kind="text",
        value_kind="float_list",
        runtime_path="calibration.mesf_values",
        profile_path="fluorescence.calibration.mesf_values",
        default=[],
    ),
    FieldDefinition(
        name="default_fluorescence_peak_process",
        section="fluorescence",
        group="Peak workflow",
        label="Default fluorescence peak process:",
        component_kind="dropdown",
        value_kind="choice",
        runtime_path="calibration.default_fluorescence_peak_process",
        profile_path="fluorescence.calibration.default_fluorescence_peak_process",
        default=peak_registry.DEFAULT_PROCESS_NAME,
        options=PEAK_PROCESS_OPTIONS,
    ),
    FieldDefinition(
        name="fluorescence_peak_table_sort_order",
        section="fluorescence",
        group="Peak workflow",
        label="Fluorescence peak table order:",
        component_kind="dropdown",
        value_kind="choice",
        runtime_path="fluorescence_calibration.peak_table_sort_order",
        profile_path="fluorescence.calibration.peak_table_sort_order",
        default="ascending",
        options=PEAK_TABLE_SORT_ORDER_OPTIONS,
    ),
    FieldDefinition(
        name="default_scatterer_preset",
        section="scattering",
        group="Calibration standard table",
        label="Default scatterer preset:",
        component_kind="dropdown",
        value_kind="choice",
        runtime_path="particle_model.scatterer_preset",
        profile_path="scattering.particle_model.scatterer_preset",
        default=scattering.CUSTOM_SCATTERER_PRESET_NAME,
        options=SCATTERING_PRESET_OPTIONS,
    ),
    FieldDefinition(
        name="detector_configuration_preset",
        section="scattering",
        group="Detector",
        label="Detector preset:",
        component_kind="dropdown",
        value_kind="choice",
        runtime_path="optics.detector_configuration_preset",
        profile_path="scattering.optics.detector_configuration_preset",
        default="",
        options=SETTINGS_DETECTOR_PRESET_OPTIONS,
    ),
    FieldDefinition(
        name="medium_refractive_index",
        section="scattering",
        group="Optics",
        label="Medium refractive index:",
        component_kind="number",
        value_kind="float",
        runtime_path="optics.medium_refractive_index",
        profile_path="scattering.optics.medium_refractive_index",
        default=1.334,
        min_value=0.001,
        max_value=2.5,
        step=0.001,
    ),
    FieldDefinition(
        name="detector_numerical_aperture",
        section="scattering",
        group="Detector",
        label="Detector numerical aperture:",
        component_kind="number",
        value_kind="float",
        runtime_path="optics.detector_numerical_aperture",
        profile_path="scattering.optics.detector_numerical_aperture",
        default=0.45,
        min_value=0.0,
        max_value=1.49,
        step=0.001,
    ),
    FieldDefinition(
        name="detector_cache_numerical_aperture",
        section="scattering",
        group="Detector",
        label="Detector cache NA:",
        component_kind="number",
        value_kind="float",
        runtime_path="optics.detector_cache_numerical_aperture",
        profile_path="scattering.optics.detector_cache_numerical_aperture",
        default=0.0,
        min_value=0.0,
        max_value=1.49,
        step=0.001,
    ),
    FieldDefinition(
        name="blocker_bar_numerical_aperture",
        section="scattering",
        group="Detector",
        label="Blocker bar NA:",
        component_kind="number",
        value_kind="float",
        runtime_path="optics.blocker_bar_numerical_aperture",
        profile_path="scattering.optics.blocker_bar_numerical_aperture",
        default=0.0,
        min_value=0.0,
        max_value=1.49,
        step=0.001,
    ),
    FieldDefinition(
        name="detector_sampling",
        section="scattering",
        group="Detector",
        label="Detector sampling:",
        component_kind="number",
        value_kind="int",
        runtime_path="optics.detector_sampling",
        profile_path="scattering.optics.detector_sampling",
        default=1000,
        min_value=1,
        step=1,
    ),
    FieldDefinition(
        name="detector_phi_angle_degree",
        section="scattering",
        group="Detector",
        label="Detector phi angle (deg):",
        component_kind="number",
        value_kind="float",
        runtime_path="optics.detector_phi_angle_degree",
        profile_path="scattering.optics.detector_phi_angle_degree",
        default=0.0,
        min_value=-360.0,
        max_value=360.0,
        step=0.1,
    ),
    FieldDefinition(
        name="detector_gamma_angle_degree",
        section="scattering",
        group="Detector",
        label="Detector gamma angle (deg):",
        component_kind="number",
        value_kind="float",
        runtime_path="optics.detector_gamma_angle_degree",
        profile_path="scattering.optics.detector_gamma_angle_degree",
        default=0.0,
        min_value=-360.0,
        max_value=360.0,
        step=0.1,
    ),
    FieldDefinition(
        name="core_refractive_index",
        section="scattering",
        group="Calibration standard table",
        label="Core refractive index:",
        component_kind="number",
        value_kind="float",
        runtime_path="particle_model.core_refractive_index",
        profile_path="scattering.particle_model.core_refractive_index",
        default=1.5,
        min_value=0.001,
        max_value=2.5,
        step=0.001,
    ),
    FieldDefinition(
        name="shell_refractive_index",
        section="scattering",
        group="Calibration standard table",
        label="Shell refractive index:",
        component_kind="number",
        value_kind="float",
        runtime_path="particle_model.shell_refractive_index",
        profile_path="scattering.particle_model.shell_refractive_index",
        default=1.5,
        min_value=0.001,
        max_value=2.5,
        step=0.001,
    ),
    FieldDefinition(
        name="particle_refractive_index",
        section="scattering",
        group="Calibration standard table",
        label="Particle refractive index:",
        component_kind="number",
        value_kind="float",
        runtime_path="particle_model.particle_refractive_index",
        profile_path="scattering.particle_model.particle_refractive_index",
        default=1.59,
        min_value=0.001,
        max_value=2.5,
        step=0.001,
    ),
    FieldDefinition(
        name="wavelength_nm",
        section="scattering",
        group="Optics",
        label="Wavelength (nm):",
        component_kind="number",
        value_kind="float",
        runtime_path="optics.wavelength_nm",
        profile_path="scattering.optics.wavelength_nm",
        default=488.0,
        min_value=1,
        step=1,
    ),
    FieldDefinition(
        name="shell_thickness_nm",
        section="scattering",
        group="Calibration standard table",
        label="Default shell thickness list (nm):",
        component_kind="text",
        value_kind="float_list",
        runtime_path="particle_model.shell_thickness_nm",
        profile_path="scattering.particle_model.shell_thickness_nm",
        default=[],
        placeholder="5, 10, 15",
    ),
    FieldDefinition(
        name="core_diameter_nm",
        section="scattering",
        group="Calibration standard table",
        label="Default core diameter list (nm):",
        component_kind="text",
        value_kind="float_list",
        runtime_path="particle_model.core_diameter_nm",
        profile_path="scattering.particle_model.core_diameter_nm",
        default=[],
        placeholder="80, 120, 160",
    ),
    FieldDefinition(
        name="particle_diameter_nm",
        section="scattering",
        group="Calibration standard table",
        label="Default particle diameter list (nm):",
        component_kind="text",
        value_kind="float_list",
        runtime_path="particle_model.particle_diameter_nm",
        profile_path="scattering.particle_model.particle_diameter_nm",
        default=[],
        placeholder="100, 200, 300",
    ),
    FieldDefinition(
        name="mie_model",
        section="scattering",
        group="Calibration standard table",
        label="Particle type:",
        component_kind="dropdown",
        value_kind="choice",
        runtime_path="particle_model.mie_model",
        profile_path="scattering.particle_model.mie_model",
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
        group="Peak workflow",
        label="Default scattering peak process:",
        component_kind="dropdown",
        value_kind="choice",
        runtime_path="scattering_calibration.default_peak_process",
        profile_path="scattering.calibration.default_peak_process",
        default=peak_registry.DEFAULT_PROCESS_NAME,
        options=PEAK_PROCESS_OPTIONS,
    ),
    FieldDefinition(
        name="scattering_peak_table_sort_order",
        section="scattering",
        group="Peak workflow",
        label="Scattering peak table order:",
        component_kind="dropdown",
        value_kind="choice",
        runtime_path="scattering_calibration.peak_table_sort_order",
        profile_path="scattering.calibration.peak_table_sort_order",
        default="ascending",
        options=PEAK_TABLE_SORT_ORDER_OPTIONS,
    ),
    FieldDefinition(
        name="default_apply_target_model_preset",
        section="apply_calibration",
        group="Target model",
        label="Default apply target preset:",
        component_kind="dropdown",
        value_kind="choice",
        runtime_path="calibration.target_model_preset",
        profile_path="apply_calibration.calibration.target_model_preset",
        default=apply_calibration.scattering.CUSTOM_PRESET_NAME,
        options=APPLY_TARGET_PRESET_OPTIONS,
    ),
    FieldDefinition(
        name="target_mie_relation_xscale",
        section="apply_calibration",
        group="Target model",
        label="Target Mie relation x scale:",
        component_kind="dropdown",
        value_kind="choice",
        runtime_path="calibration.target_mie_relation_xscale",
        profile_path="apply_calibration.calibration.target_mie_relation_xscale",
        default="linear",
        options=AXIS_SCALE_OPTIONS,
    ),
    FieldDefinition(
        name="target_mie_relation_yscale",
        section="apply_calibration",
        group="Target model",
        label="Target Mie relation y scale:",
        component_kind="dropdown",
        value_kind="choice",
        runtime_path="calibration.target_mie_relation_yscale",
        profile_path="apply_calibration.calibration.target_mie_relation_yscale",
        default="log",
        options=AXIS_SCALE_OPTIONS,
    ),
    FieldDefinition(
        name="histogram_xscale",
        section="apply_calibration",
        group="Peak graph defaults",
        label="Peak graph x scale:",
        component_kind="dropdown",
        value_kind="choice",
        runtime_path="calibration.histogram_xscale",
        profile_path="apply_calibration.calibration.histogram_xscale",
        default="linear",
        options=AXIS_SCALE_OPTIONS,
    ),
    FieldDefinition(
        name="histogram_yscale",
        section="apply_calibration",
        group="Peak graph defaults",
        label="Peak graph y scale:",
        component_kind="dropdown",
        value_kind="choice",
        runtime_path="calibration.histogram_yscale",
        profile_path="apply_calibration.calibration.histogram_yscale",
        default="log",
        options=AXIS_SCALE_OPTIONS,
    ),
    FieldDefinition(
        name="peak_graph_colormap_log",
        section="apply_calibration",
        group="Peak graph defaults",
        label="Peak graph color log by default:",
        component_kind="dropdown",
        value_kind="yes_no_bool",
        runtime_path="calibration.peak_graph_colormap_log",
        profile_path="apply_calibration.calibration.peak_graph_colormap_log",
        default=False,
        options=YES_NO_OPTIONS,
    ),
    FieldDefinition(
        name="max_events_for_analysis",
        section="apply_calibration",
        group="Export defaults",
        label="Max events for analysis:",
        component_kind="number",
        value_kind="int",
        runtime_path="calibration.max_events_for_analysis",
        profile_path="apply_calibration.calibration.max_events_for_analysis",
        default=10000,
        min_value=1,
        step=1,
    ),
    FieldDefinition(
        name="operator_name",
        section="metadata",
        group="Metadata",
        label="Operator name:",
        component_kind="text",
        value_kind="string",
        runtime_path="metadata.operator_name",
        profile_path="apply_calibration.metadata.operator_name",
        default="",
    ),
    FieldDefinition(
        name="instrument_name",
        section="metadata",
        group="Metadata",
        label="Instrument name:",
        component_kind="text",
        value_kind="string",
        runtime_path="metadata.instrument_name",
        profile_path="apply_calibration.metadata.instrument_name",
        default="",
    ),
    FieldDefinition(
        name="graph_height",
        section="figure_style",
        group="Figure style",
        label="Graph height:",
        component_kind="text",
        value_kind="string",
        runtime_path="visualization.graph_height",
        profile_path="apply_calibration.visualization.graph_height",
        default="850px",
        placeholder="850px, 70vh, calc(100vh - 260px)",
    ),
    FieldDefinition(
        name="default_marker_opacity",
        section="figure_style",
        group="Figure style",
        label="Default marker opacity:",
        component_kind="number",
        value_kind="float",
        runtime_path="visualization.default_marker_opacity",
        profile_path="apply_calibration.visualization.default_marker_opacity",
        default=0.72,
        min_value=0.0,
        max_value=1.0,
        step=0.01,
    ),
    FieldDefinition(
        name="default_marker_size",
        section="figure_style",
        group="Figure style",
        label="Default marker size:",
        component_kind="number",
        value_kind="float",
        runtime_path="visualization.default_marker_size",
        profile_path="apply_calibration.visualization.default_marker_size",
        default=8.0,
        min_value=1.0,
        step=0.5,
    ),
    FieldDefinition(
        name="n_bins",
        section="apply_calibration",
        group="Peak graph defaults",
        label="Number of bins for plots:",
        component_kind="number",
        value_kind="int",
        runtime_path="calibration.n_bins_for_plots",
        profile_path="apply_calibration.calibration.n_bins_for_plots",
        default=100,
        min_value=10,
        step=1,
    ),
    FieldDefinition(
        name="default_line_width",
        section="figure_style",
        group="Figure style",
        label="Default line width:",
        component_kind="number",
        value_kind="float",
        runtime_path="visualization.default_line_width",
        profile_path="apply_calibration.visualization.default_line_width",
        default=2.0,
        min_value=0.5,
        step=0.5,
    ),
    FieldDefinition(
        name="default_font_size",
        section="figure_style",
        group="Figure style",
        label="Default font size:",
        component_kind="number",
        value_kind="float",
        runtime_path="visualization.default_font_size",
        profile_path="apply_calibration.visualization.default_font_size",
        default=14.0,
        min_value=1,
        max_value=100,
        step=1,
        placeholder="e.g. 14",
    ),
    FieldDefinition(
        name="default_tick_size",
        section="figure_style",
        group="Figure style",
        label="Default tick size:",
        component_kind="number",
        value_kind="float",
        runtime_path="visualization.default_tick_size",
        profile_path="apply_calibration.visualization.default_tick_size",
        default=12.0,
        min_value=1,
        max_value=100,
        step=1,
        placeholder="e.g. 12",
    ),
    FieldDefinition(
        name="show_grid_by_default",
        section="figure_style",
        group="Figure style",
        label="Show grid by default:",
        component_kind="dropdown",
        value_kind="yes_no_bool",
        runtime_path="visualization.show_grid_by_default",
        profile_path="apply_calibration.visualization.show_grid_by_default",
        default=True,
        options=YES_NO_OPTIONS,
    ),
    FieldDefinition(
        name="fluorescence_fcs_file_path",
        section="fluorescence",
        group="Files",
        label="Default Fluorescence FCS file path:",
        component_kind="text",
        value_kind="string",
        runtime_path="files.fluorescence_fcs_file_path",
        profile_path="fluorescence.files.fcs_file_path",
        default="",
    ),
    FieldDefinition(
        name="scattering_fcs_file_path",
        section="scattering",
        group="Files",
        label="Default Scattering FCS file path:",
        component_kind="text",
        value_kind="string",
        runtime_path="files.scattering_fcs_file_path",
        profile_path="scattering.files.fcs_file_path",
        default="",
    ),
    FieldDefinition(
        name="theme_mode",
        section="misc",
        group="Interface",
        label="Theme mode:",
        component_kind="dropdown",
        value_kind="choice",
        runtime_path="ui.theme_mode",
        profile_path="misc.ui.theme_mode",
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
        section="misc",
        group="Interface",
        label="Show graphs:",
        component_kind="dropdown",
        value_kind="yes_no_bool",
        runtime_path="ui.show_graphs",
        profile_path="misc.ui.show_graphs",
        default=False,
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


def section_field_groups(
    section_key: str,
) -> list[tuple[str, list[str]]]:
    grouped_fields: list[tuple[str, list[str]]] = []
    field_names_by_group: dict[str, list[str]] = {}

    for field in FIELD_DEFINITIONS:
        if field.section != section_key:
            continue

        group_name = str(field.group or "General")

        if group_name not in field_names_by_group:
            field_names_by_group[group_name] = []
            grouped_fields.append((group_name, field_names_by_group[group_name]))

        field_names_by_group[group_name].append(field.name)

    return grouped_fields
