# -*- coding: utf-8 -*-

import json
import logging
from typing import Any, Optional

import dash_bootstrap_components as dbc
from dash import dcc, html

from .callbacks.shared import get_peak_processes
from .models import PeakConfig
from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.workflow.plotting.scatter2d import Scatter2DGraph
from RosettaX.workflow.plotting.scatter2d import Scatter2DGraphIds


logger = logging.getLogger(__name__)


class PeakLayout:
    """
    Reusable layout builder for fluorescence and scattering peak sections.

    Responsibilities
    ----------------
    - Build the peak workflow section card.
    - Build the process selector.
    - Build process specific controls.
    - Build detector dropdowns with optional process supplied labels.
    - Build process settings.
    - Build setting tooltips.
    - Build graph visibility controls.
    - Build shared 2D graph axis scale controls.
    - Build graph container.
    - Build workflow stores.
    """

    def __init__(
        self,
        *,
        ids: Any,
        config: PeakConfig,
    ) -> None:
        self.ids = ids
        self.config = config

    def get_layout(self) -> dbc.Card:
        """
        Build the complete peak section layout.
        """
        logger.debug(
            "Building peak layout with header_title=%r",
            self.config.header_title,
        )

        return dbc.Card(
            [
                self._build_header(),
                self._build_body(),
            ]
        )

    def _build_header(self) -> dbc.CardHeader:
        """
        Build the section header.
        """
        return dbc.CardHeader(
            self.config.header_title,
        )

    def _build_body(self) -> dbc.CardBody:
        """
        Build the section body.
        """
        return dbc.CardBody(
            [
                *self._build_state_stores(),
                *self._build_peak_workflow_layout(),
                self._build_script_status(),
            ]
        )

    def _build_state_stores(self) -> list[dcc.Store]:
        """
        Build the stores required by the peak workflow callbacks.
        """
        return [
            dcc.Store(
                id=self.ids.peak_lines_store,
                storage_type="session",
            ),
            dcc.Store(
                id=self.ids.hist_store,
                storage_type="session",
            ),
            dcc.Store(
                id=self.ids.source_channel_store,
                storage_type="session",
            ),
        ]

    def _build_peak_workflow_layout(self) -> list[Any]:
        """
        Build the complete reusable peak workflow layout.
        """
        processes = get_peak_processes()

        return [
            html.Div(
                [
                    self._build_peak_process_selector(
                        dropdown_id=self.ids.process_dropdown,
                        processes=processes,
                        label=self.config.process_dropdown_label,
                    ),
                    self._build_graph_toggle_control(
                        switch_id=self.ids.graph_toggle_switch,
                    ),
                ],
                style={
                    "display": "flex",
                    "alignItems": "end",
                    "gap": "16px",
                    "flexWrap": "wrap",
                },
            ),
            html.Div(
                self._build_peak_process_cards(
                    processes=processes,
                )
            ),
            html.H6(
                self.config.graph_title,
                style={
                    "marginTop": "18px",
                    "marginBottom": "8px",
                },
            ),
            self._build_graph_controls(
                container_id=self.ids.histogram_controls_container,
                nbins_control_container_id=self.ids.nbins_control_container,
                nbins_input_id=self.ids.nbins_input,
                number_of_bins=self._get_default_number_of_bins(),
            ),
            self._build_graph_container(
                container_id=self.ids.graph_toggle_container,
                graph_id=self.ids.graph_hist,
                axis_scale_toggle_id=self._get_axis_scale_toggle_id(),
            ),
        ]

    def _build_peak_process_selector(
        self,
        *,
        dropdown_id: str,
        processes: list[Any],
        value: Any = None,
        label: str = "Peak process",
    ) -> html.Div:
        """
        Build the peak process selector dropdown.
        """
        options = [
            {
                "label": self._get_process_label(
                    process=process,
                ),
                "value": self._get_process_name(
                    process=process,
                ),
            }
            for process in processes
        ]

        selected_value = value

        if selected_value is None and options:
            selected_value = options[0]["value"]

        return html.Div(
            [
                dbc.Label(
                    label,
                    html_for=dropdown_id,
                    style={
                        "marginBottom": "4px",
                        "fontSize": "0.85rem",
                    },
                ),
                dcc.Dropdown(
                    id=dropdown_id,
                    options=options,
                    value=selected_value,
                    clearable=False,
                    persistence=True,
                    persistence_type="session",
                ),
            ],
            style={
                "minWidth": "260px",
            },
        )

    def _build_peak_process_cards(
        self,
        *,
        processes: list[Any],
    ) -> list[dbc.Card]:
        """
        Build one process card per registered peak process.
        """
        return [
            self._build_peak_process_card(
                process=process,
            )
            for process in processes
        ]

    def _build_peak_process_card(
        self,
        *,
        process: Any,
    ) -> dbc.Card:
        """
        Build a single peak process card.
        """
        process_name = self._get_process_name(
            process=process,
        )

        process_label = self._get_process_label(
            process=process,
        )

        process_description = self._get_process_description(
            process=process,
        )

        children: list[Any] = [
            html.Div(
                [
                    html.H6(
                        process_label,
                        style={
                            "marginBottom": "4px",
                        },
                    ),
                    html.P(
                        process_description,
                        style={
                            "marginBottom": "12px",
                            "fontSize": "0.9rem",
                            "opacity": 0.8,
                        },
                    )
                    if process_description
                    else None,
                ]
            ),
            html.Div(
                [
                    *self._build_detector_controls(
                        process=process,
                    ),
                    *self._build_setting_controls(
                        process=process,
                    ),
                ],
                style={
                    "display": "flex",
                    "alignItems": "end",
                    "gap": "12px",
                    "flexWrap": "wrap",
                },
            ),
            html.Div(
                self._build_process_action_buttons(
                    process_name=process_name,
                    supports_automatic_action=bool(
                        getattr(
                            process,
                            "supports_automatic_action",
                            False,
                        )
                    ),
                    supports_clear=bool(
                        getattr(
                            process,
                            "supports_clear",
                            False,
                        )
                    ),
                ),
                style={
                    "display": "flex",
                    "gap": "8px",
                    "marginTop": "12px",
                },
            ),
            html.Div(
                id=self.ids.process_status(
                    process_name=process_name,
                ),
                style={
                    "marginTop": "8px",
                    "fontSize": "0.85rem",
                    "opacity": 0.85,
                },
            ),
        ]

        return dbc.Card(
            id=self.ids.process_controls_container(
                process_name=process_name,
            ),
            children=dbc.CardBody(
                [
                    child
                    for child in children
                    if child is not None
                ],
            ),
            style={
                "marginTop": "12px",
            },
        )

    def _build_detector_controls(
        self,
        *,
        process: Any,
    ) -> list[Any]:
        """
        Build detector dropdowns for a peak process.
        """
        process_name = self._get_process_name(
            process=process,
        )

        channel_labels = self._get_detector_channel_labels(
            process=process,
        )

        detector_controls: list[Any] = []

        for channel_name in self._get_required_detector_channels(
            process=process,
        ):
            label = channel_labels.get(
                channel_name,
                f"{channel_name.replace('_', ' ').title()} channel",
            )

            detector_controls.append(
                self._build_detector_dropdown_control(
                    dropdown_id=self.ids.process_detector_dropdown(
                        process_name=process_name,
                        channel_name=channel_name,
                    ),
                    label=label,
                    placeholder=f"Select {label.lower()}",
                )
            )

        return detector_controls

    def _build_setting_controls(
        self,
        *,
        process: Any,
    ) -> list[Any]:
        """
        Build process setting controls.
        """
        process_name = self._get_process_name(
            process=process,
        )

        setting_controls: list[Any] = []

        for setting in self._get_process_settings(
            process=process,
        ):
            setting_name = self._get_setting_value(
                setting=setting,
                name="name",
                default=None,
            )

            if not isinstance(setting_name, str) or not setting_name:
                continue

            setting_kind = str(
                self._get_setting_value(
                    setting=setting,
                    name="kind",
                    default="integer",
                )
            )

            setting_label = str(
                self._get_setting_value(
                    setting=setting,
                    name="label",
                    default=setting_name.replace("_", " ").title(),
                )
            )

            setting_help = str(
                self._get_setting_value(
                    setting=setting,
                    name="help",
                    default=self._get_setting_value(
                        setting=setting,
                        name="description",
                        default="",
                    ),
                )
                or ""
            )

            setting_default_value = self._get_setting_value(
                setting=setting,
                name="default_value",
                default=self._get_setting_value(
                    setting=setting,
                    name="default",
                    default=None,
                ),
            )

            setting_minimum = self._get_setting_value(
                setting=setting,
                name="min_value",
                default=self._get_setting_value(
                    setting=setting,
                    name="minimum",
                    default=None,
                ),
            )

            setting_maximum = self._get_setting_value(
                setting=setting,
                name="max_value",
                default=self._get_setting_value(
                    setting=setting,
                    name="maximum",
                    default=None,
                ),
            )

            setting_step = self._get_setting_value(
                setting=setting,
                name="step",
                default=None,
            )

            setting_id = self.ids.process_setting(
                process_name=process_name,
                setting_name=setting_name,
            )

            if setting_kind in ("integer", "int"):
                setting_controls.append(
                    self._build_integer_setting_control(
                        input_id=setting_id,
                        label=setting_label,
                        tooltip_text=setting_help,
                        value=int(
                            setting_default_value
                            if setting_default_value is not None
                            else 1
                        ),
                        minimum=int(
                            setting_minimum
                            if setting_minimum is not None
                            else 1
                        ),
                        maximum=int(
                            setting_maximum
                            if setting_maximum is not None
                            else 50
                        ),
                        step=int(
                            setting_step
                            if setting_step is not None
                            else 1
                        ),
                    )
                )
                continue

            if setting_kind in ("float", "number"):
                setting_controls.append(
                    self._build_float_setting_control(
                        input_id=setting_id,
                        label=setting_label,
                        tooltip_text=setting_help,
                        value=float(
                            setting_default_value
                            if setting_default_value is not None
                            else 0.0
                        ),
                        minimum=float(setting_minimum)
                        if setting_minimum is not None
                        else None,
                        maximum=float(setting_maximum)
                        if setting_maximum is not None
                        else None,
                        step=float(
                            setting_step
                            if setting_step is not None
                            else 0.01
                        ),
                    )
                )
                continue

            if setting_kind in ("text", "string", "str"):
                setting_controls.append(
                    self._build_text_setting_control(
                        input_id=setting_id,
                        label=setting_label,
                        tooltip_text=setting_help,
                        value=str(setting_default_value or ""),
                        placeholder=str(
                            self._get_setting_value(
                                setting=setting,
                                name="placeholder",
                                default="",
                            )
                        ),
                    )
                )
                continue

            if setting_kind in ("select", "dropdown"):
                setting_options = self._get_setting_value(
                    setting=setting,
                    name="options",
                    default=[],
                )

                setting_controls.append(
                    self._build_select_setting_control(
                        dropdown_id=setting_id,
                        label=setting_label,
                        tooltip_text=setting_help,
                        options=self._normalize_dropdown_options(
                            options=setting_options,
                        ),
                        value=setting_default_value,
                        placeholder=str(
                            self._get_setting_value(
                                setting=setting,
                                name="placeholder",
                                default="Select value",
                            )
                        ),
                    )
                )
                continue

        return setting_controls

    def _build_setting_label(
        self,
        *,
        label: str,
        tooltip_text: str,
        target_id: str,
    ) -> html.Div:
        """
        Build a setting label with an optional hover tooltip.
        """
        tooltip_text = str(
            tooltip_text or "",
        ).strip()

        label_children: list[Any] = [
            dbc.Label(
                label,
                style={
                    "marginBottom": "0px",
                    "fontSize": "0.85rem",
                },
            )
        ]

        if tooltip_text:
            tooltip_target_id = f"{target_id}-help"

            label_children.extend(
                [
                    html.Span(
                        "ⓘ",
                        id=tooltip_target_id,
                        style={
                            "marginLeft": "6px",
                            "cursor": "help",
                            "fontSize": "0.82rem",
                            "opacity": 0.75,
                            "userSelect": "none",
                        },
                    ),
                    dbc.Tooltip(
                        tooltip_text,
                        target=tooltip_target_id,
                        placement="top",
                    ),
                ]
            )

        return html.Div(
            label_children,
            style={
                "display": "flex",
                "alignItems": "center",
                "marginBottom": "4px",
            },
        )

    def _build_graph_toggle_control(
        self,
        *,
        switch_id: str,
        label: str = "Show graph",
        value: Optional[list[str]] = None,
    ) -> dbc.Checklist:
        """
        Build the graph visibility toggle.
        """
        return dbc.Checklist(
            id=switch_id,
            options=[
                {
                    "label": label,
                    "value": "enabled",
                }
            ],
            value=value if value is not None else ["enabled"],
            switch=True,
            inline=True,
            persistence=True,
            persistence_type="session",
        )

    def _build_number_of_bins_control(
        self,
        *,
        container_id: str,
        input_id: str,
        value: int = 100,
        minimum: int = 1,
        maximum: int = 10_000,
        step: int = 1,
        label: str = "Bins",
    ) -> html.Div:
        """
        Build the histogram bin count control.
        """
        return html.Div(
            id=container_id,
            children=[
                dbc.Label(
                    label,
                    html_for=input_id,
                    style={
                        "marginBottom": "4px",
                        "fontSize": "0.85rem",
                    },
                ),
                dbc.Input(
                    id=input_id,
                    type="number",
                    value=value,
                    min=minimum,
                    max=maximum,
                    step=step,
                    size="sm",
                    style={
                        "width": "110px",
                    },
                    persistence=True,
                    persistence_type="session",
                ),
            ],
        )

    def _build_graph_controls(
        self,
        *,
        container_id: str,
        nbins_control_container_id: str,
        nbins_input_id: str,
        number_of_bins: int = 100,
    ) -> html.Div:
        """
        Build graph controls that are not part of the shared graph component.

        Axis scale controls are now rendered by Scatter2DGraph below the graph.
        """
        return html.Div(
            id=container_id,
            children=[
                self._build_number_of_bins_control(
                    container_id=nbins_control_container_id,
                    input_id=nbins_input_id,
                    value=number_of_bins,
                ),
            ],
            style={
                "display": "flex",
                "alignItems": "center",
                "gap": "16px",
                "flexWrap": "wrap",
                "marginBottom": "8px",
            },
        )

    def _build_graph_container(
        self,
        *,
        container_id: str,
        graph_id: str,
        axis_scale_toggle_id: str,
    ) -> html.Div:
        """
        Build the graph container with shared 2D scatter controls.
        """
        return html.Div(
            id=container_id,
            children=[
                Scatter2DGraph.build_component(
                    component_ids=Scatter2DGraphIds(
                        graph=graph_id,
                        axis_scale_toggle=axis_scale_toggle_id,
                    ),
                    figure=Scatter2DGraph.build_empty_figure(
                        message="Upload an FCS file and select a peak process.",
                    ),
                    x_log_enabled=self._get_default_xscale() == "log",
                    y_log_enabled=self._get_default_yscale() == "log",
                    graph_style={
                        "height": "850px",
                        "width": "100%",
                    },
                )
            ],
            style={
                "display": "block",
            },
        )

    def _build_detector_dropdown_control(
        self,
        *,
        dropdown_id: Any,
        label: str,
        value: Any = None,
        placeholder: str = "Select detector",
    ) -> html.Div:
        """
        Build a detector dropdown used by a peak process.
        """
        return html.Div(
            [
                dbc.Label(
                    label,
                    style={
                        "marginBottom": "4px",
                        "fontSize": "0.85rem",
                    },
                ),
                dcc.Dropdown(
                    id=dropdown_id,
                    options=[],
                    value=value,
                    placeholder=placeholder,
                    clearable=True,
                    persistence=True,
                    persistence_type="session",
                ),
            ],
            style={
                "minWidth": "220px",
                "flex": "1 1 220px",
            },
        )

    def _build_integer_setting_control(
        self,
        *,
        input_id: Any,
        label: str,
        tooltip_text: str = "",
        value: int,
        minimum: int = 1,
        maximum: int = 50,
        step: int = 1,
    ) -> html.Div:
        """
        Build an integer process setting input.
        """
        target_id = self._stringify_component_id(
            component_id=input_id,
        )

        return html.Div(
            [
                self._build_setting_label(
                    label=label,
                    tooltip_text=tooltip_text,
                    target_id=target_id,
                ),
                dbc.Input(
                    id=input_id,
                    type="number",
                    value=value,
                    min=minimum,
                    max=maximum,
                    step=step,
                    size="sm",
                    persistence=True,
                    persistence_type="session",
                ),
            ],
            style={
                "width": "130px",
            },
        )

    def _build_float_setting_control(
        self,
        *,
        input_id: Any,
        label: str,
        tooltip_text: str = "",
        value: float,
        minimum: Optional[float] = None,
        maximum: Optional[float] = None,
        step: float = 0.01,
    ) -> html.Div:
        """
        Build a floating point process setting input.
        """
        target_id = self._stringify_component_id(
            component_id=input_id,
        )

        input_kwargs: dict[str, Any] = {
            "id": input_id,
            "type": "number",
            "value": value,
            "step": step,
            "size": "sm",
            "persistence": True,
            "persistence_type": "session",
        }

        if minimum is not None:
            input_kwargs["min"] = minimum

        if maximum is not None:
            input_kwargs["max"] = maximum

        return html.Div(
            [
                self._build_setting_label(
                    label=label,
                    tooltip_text=tooltip_text,
                    target_id=target_id,
                ),
                dbc.Input(
                    **input_kwargs,
                ),
            ],
            style={
                "width": "150px",
            },
        )

    def _build_text_setting_control(
        self,
        *,
        input_id: Any,
        label: str,
        tooltip_text: str = "",
        value: str = "",
        placeholder: str = "",
    ) -> html.Div:
        """
        Build a text process setting input.
        """
        target_id = self._stringify_component_id(
            component_id=input_id,
        )

        return html.Div(
            [
                self._build_setting_label(
                    label=label,
                    tooltip_text=tooltip_text,
                    target_id=target_id,
                ),
                dbc.Input(
                    id=input_id,
                    type="text",
                    value=value,
                    placeholder=placeholder,
                    size="sm",
                    persistence=True,
                    persistence_type="session",
                ),
            ],
            style={
                "minWidth": "180px",
            },
        )

    def _build_select_setting_control(
        self,
        *,
        dropdown_id: Any,
        label: str,
        tooltip_text: str = "",
        options: list[dict[str, Any]],
        value: Any = None,
        placeholder: str = "Select value",
    ) -> html.Div:
        """
        Build a dropdown process setting input.
        """
        target_id = self._stringify_component_id(
            component_id=dropdown_id,
        )

        return html.Div(
            [
                self._build_setting_label(
                    label=label,
                    tooltip_text=tooltip_text,
                    target_id=target_id,
                ),
                dcc.Dropdown(
                    id=dropdown_id,
                    options=options,
                    value=value,
                    placeholder=placeholder,
                    clearable=True,
                    persistence=True,
                    persistence_type="session",
                ),
            ],
            style={
                "minWidth": "180px",
            },
        )

    def _build_process_action_buttons(
        self,
        *,
        process_name: str,
        supports_automatic_action: bool,
        supports_clear: bool,
        run_label: str = "Run",
        clear_label: str = "Clear",
    ) -> list[Any]:
        """
        Build action buttons for a peak process.
        """
        buttons: list[Any] = []

        if supports_automatic_action:
            buttons.append(
                dbc.Button(
                    run_label,
                    id=self.ids.process_action_button(
                        process_name=process_name,
                        action_name="run",
                    ),
                    n_clicks=0,
                    size="sm",
                    color="primary",
                )
            )

        if supports_clear:
            buttons.append(
                dbc.Button(
                    clear_label,
                    id=self.ids.process_action_button(
                        process_name=process_name,
                        action_name="clear",
                    ),
                    n_clicks=0,
                    size="sm",
                    color="secondary",
                    outline=True,
                )
            )

        return buttons

    def _build_script_status(self) -> html.Div:
        """
        Build the shared peak script status output.
        """
        return html.Div(
            id=self.ids.script_status,
            style={
                "marginTop": "8px",
            },
        )

    def _get_axis_scale_toggle_id(self) -> str:
        """
        Return the shared axis scale toggle ID.

        Prefer an explicit axis_scale_toggle ID. Fall back to a deterministic ID
        only to avoid breaking older ID classes while migrating.
        """
        axis_scale_toggle_id = getattr(
            self.ids,
            "axis_scale_toggle",
            None,
        )

        if isinstance(axis_scale_toggle_id, str) and axis_scale_toggle_id:
            return axis_scale_toggle_id

        if callable(axis_scale_toggle_id):
            resolved_axis_scale_toggle_id = axis_scale_toggle_id()

            if isinstance(resolved_axis_scale_toggle_id, str) and resolved_axis_scale_toggle_id:
                return resolved_axis_scale_toggle_id

        return f"{self.ids.graph_hist}-axis-scale-toggle"

    def _get_default_runtime_config(self) -> RuntimeConfig:
        """
        Return the default runtime configuration.
        """
        return RuntimeConfig.from_default_profile()

    def _get_default_number_of_bins(self) -> int:
        """
        Return the default number of histogram bins.
        """
        runtime_config = self._get_default_runtime_config()

        return runtime_config.get_int(
            self.config.number_of_bins_runtime_config_path,
            default=self.config.default_number_of_bins,
        )

    def _get_default_xscale(self) -> str:
        """
        Return the default x axis scale for the shared peak graph toggle.
        """
        runtime_config = self._get_default_runtime_config()

        return self._normalize_axis_scale(
            runtime_config.get_str(
                "calibration.histogram_xscale",
                default="linear",
            ),
            default="linear",
        )


    def _get_default_yscale(self) -> str:
        """
        Return the default y axis scale for the shared peak graph toggle.
        """
        runtime_config = self._get_default_runtime_config()

        return self._normalize_axis_scale(
            runtime_config.get_str(
                "calibration.histogram_yscale",
                default=runtime_config.get_str(
                    "calibration.histogram_scale",
                    default="log",
                ),
            ),
            default="log",
        )


    def _normalize_axis_scale(
        self,
        value: Any,
        *,
        default: str,
    ) -> str:
        """
        Normalize an axis scale value.
        """
        value_string = str(value or "").strip().lower()

        if value_string in (
            "linear",
            "log",
        ):
            return value_string

        return default

    def _get_process_name(
        self,
        *,
        process: Any,
    ) -> str:
        """
        Return the canonical process name.
        """
        for attribute_name in ("name", "process_name"):
            value = getattr(
                process,
                attribute_name,
                None,
            )

            if isinstance(value, str) and value:
                return value

        raise AttributeError(
            "Peak process must expose a non empty name or process_name attribute."
        )

    def _get_process_label(
        self,
        *,
        process: Any,
    ) -> str:
        """
        Return the user visible process label.
        """
        for attribute_name in (
            "label",
            "process_label",
            "display_name",
            "title",
            "name",
            "process_name",
        ):
            value = getattr(
                process,
                attribute_name,
                None,
            )

            if isinstance(value, str) and value:
                return value

        return self._get_process_name(
            process=process,
        )

    def _get_process_description(
        self,
        *,
        process: Any,
    ) -> str:
        """
        Return the user visible process description.
        """
        value = getattr(
            process,
            "description",
            "",
        )

        if isinstance(value, str):
            return value

        return ""

    def _get_required_detector_channels(
        self,
        *,
        process: Any,
    ) -> list[str]:
        """
        Return required detector channel names for a process.
        """
        if hasattr(process, "get_required_detector_channels"):
            channel_names = process.get_required_detector_channels()

            if channel_names is None:
                return []

            return [
                str(channel_name)
                for channel_name in channel_names
            ]

        channel_names = getattr(
            process,
            "required_detector_channels",
            [],
        )

        if channel_names is None:
            return []

        return [
            str(channel_name)
            for channel_name in channel_names
        ]

    def _get_detector_channel_labels(
        self,
        *,
        process: Any,
    ) -> dict[str, str]:
        """
        Return user visible detector channel labels for a process.
        """
        if hasattr(process, "get_detector_channel_labels"):
            labels = process.get_detector_channel_labels()

            if isinstance(labels, dict):
                return {
                    str(key): str(value)
                    for key, value in labels.items()
                }

        labels = getattr(
            process,
            "detector_channel_labels",
            None,
        )

        if isinstance(labels, dict):
            return {
                str(key): str(value)
                for key, value in labels.items()
            }

        return {}

    def _get_process_settings(
        self,
        *,
        process: Any,
    ) -> list[Any]:
        """
        Return process setting declarations.
        """
        if hasattr(process, "get_settings"):
            settings = process.get_settings()

            if settings is None:
                return []

            return list(settings)

        settings = getattr(
            process,
            "settings",
            [],
        )

        if settings is None:
            return []

        return list(settings)

    def _get_setting_value(
        self,
        *,
        setting: Any,
        name: str,
        default: Any,
    ) -> Any:
        """
        Return a setting value from either a dictionary or an object.
        """
        if isinstance(setting, dict):
            return setting.get(
                name,
                default,
            )

        return getattr(
            setting,
            name,
            default,
        )

    def _normalize_dropdown_options(
        self,
        *,
        options: Any,
    ) -> list[dict[str, Any]]:
        """
        Convert simple option declarations to Dash dropdown options.
        """
        if options is None:
            return []

        normalized_options: list[dict[str, Any]] = []

        for option in options:
            if isinstance(option, dict):
                normalized_options.append(
                    option,
                )
                continue

            normalized_options.append(
                {
                    "label": str(option),
                    "value": option,
                }
            )

        return normalized_options

    def _stringify_component_id(
        self,
        *,
        component_id: Any,
    ) -> str:
        """
        Convert a Dash component id into a string safe for tooltip targets.
        """
        if isinstance(component_id, dict):
            return json.dumps(
                component_id,
                sort_keys=True,
                separators=(",", ":"),
            ).replace("{", "").replace("}", "").replace('"', "").replace(":", "-").replace(",", "-")

        return str(
            component_id,
        )