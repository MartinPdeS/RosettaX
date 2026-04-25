# -*- coding: utf-8 -*-

from typing import Any

import dash_bootstrap_components as dbc
from dash import dcc, html

from RosettaX.workflow.peak_workflow.layouts import controls


def build_peak_process_selector(
    *,
    dropdown_id: str,
    processes: list[Any],
    value: Any = None,
    label: str = "Peak process",
) -> html.Div:
    """
    Build the process selector dropdown.
    """
    options = []

    for process in processes:
        process_name = get_process_name(
            process=process,
        )

        options.append(
            {
                "label": get_process_label(
                    process=process,
                ),
                "value": process_name,
            }
        )

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


def build_peak_process_cards(
    *,
    ids: Any,
    processes: list[Any],
) -> list[dbc.Card]:
    """
    Build one process card per registered peak process.
    """
    cards: list[dbc.Card] = []

    for process in processes:
        cards.append(
            build_peak_process_card(
                ids=ids,
                process=process,
            )
        )

    return cards


def build_peak_process_card(
    *,
    ids: Any,
    process: Any,
) -> dbc.Card:
    """
    Build a single peak process card.
    """
    process_name = get_process_name(
        process=process,
    )

    process_label = get_process_label(
        process=process,
    )

    process_description = get_process_description(
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
            build_detector_controls(
                ids=ids,
                process=process,
            )
            + build_setting_controls(
                ids=ids,
                process=process,
            ),
            style={
                "display": "flex",
                "alignItems": "end",
                "gap": "12px",
                "flexWrap": "wrap",
            },
        ),
        html.Div(
            controls.build_process_action_buttons(
                ids=ids,
                process_name=process_name,
                supports_automatic_action=bool(
                    getattr(process, "supports_automatic_action", False)
                ),
                supports_clear=bool(
                    getattr(process, "supports_clear", False)
                ),
            ),
            style={
                "display": "flex",
                "gap": "8px",
                "marginTop": "12px",
            },
        ),
        html.Div(
            id=ids.process_status(
                process_name=process_name,
            ),
            style={
                "marginTop": "8px",
                "fontSize": "0.85rem",
                "opacity": 0.85,
            },
        ),
    ]

    children = [
        child
        for child in children
        if child is not None
    ]

    return dbc.Card(
        id=ids.process_controls_container(
            process_name=process_name,
        ),
        children=dbc.CardBody(
            children,
        ),
        style={
            "marginTop": "12px",
        },
    )


def build_detector_controls(
    *,
    ids: Any,
    process: Any,
) -> list[Any]:
    """
    Build detector dropdowns for a peak process.
    """
    process_name = get_process_name(
        process=process,
    )

    detector_controls: list[Any] = []

    for channel_name in get_required_detector_channels(
        process=process,
    ):
        detector_controls.append(
            controls.build_detector_dropdown_control(
                dropdown_id=ids.process_detector_dropdown(
                    process_name=process_name,
                    channel_name=channel_name,
                ),
                label=f"{channel_name} detector",
                placeholder=f"Select {channel_name} detector",
            )
        )

    return detector_controls


def build_setting_controls(
    *,
    ids: Any,
    process: Any,
) -> list[Any]:
    """
    Build process setting controls.
    """
    process_name = get_process_name(
        process=process,
    )

    setting_controls: list[Any] = []

    for setting in get_process_settings(
        process=process,
    ):
        setting_name = get_setting_value(
            setting=setting,
            name="name",
            default=None,
        )

        if not isinstance(setting_name, str) or not setting_name:
            continue

        setting_kind = str(
            get_setting_value(
                setting=setting,
                name="kind",
                default="integer",
            )
        )

        setting_label = str(
            get_setting_value(
                setting=setting,
                name="label",
                default=setting_name.replace("_", " ").title(),
            )
        )

        setting_default_value = get_setting_value(
            setting=setting,
            name="default_value",
            default=get_setting_value(
                setting=setting,
                name="default",
                default=None,
            ),
        )

        setting_minimum = get_setting_value(
            setting=setting,
            name="min_value",
            default=get_setting_value(
                setting=setting,
                name="minimum",
                default=None,
            ),
        )

        setting_maximum = get_setting_value(
            setting=setting,
            name="max_value",
            default=get_setting_value(
                setting=setting,
                name="maximum",
                default=None,
            ),
        )

        setting_step = get_setting_value(
            setting=setting,
            name="step",
            default=None,
        )

        setting_id = ids.process_setting(
            process_name=process_name,
            setting_name=setting_name,
        )

        if setting_kind in ("integer", "int"):
            setting_controls.append(
                controls.build_integer_setting_control(
                    input_id=setting_id,
                    label=setting_label,
                    value=int(setting_default_value if setting_default_value is not None else 1),
                    minimum=int(setting_minimum if setting_minimum is not None else 1),
                    maximum=int(setting_maximum if setting_maximum is not None else 50),
                    step=int(setting_step if setting_step is not None else 1),
                )
            )
            continue

        if setting_kind in ("float", "number"):
            setting_controls.append(
                controls.build_float_setting_control(
                    input_id=setting_id,
                    label=setting_label,
                    value=float(setting_default_value if setting_default_value is not None else 0.0),
                    minimum=float(setting_minimum) if setting_minimum is not None else None,
                    maximum=float(setting_maximum) if setting_maximum is not None else None,
                    step=float(setting_step if setting_step is not None else 0.01),
                )
            )
            continue

        if setting_kind in ("text", "string", "str"):
            setting_controls.append(
                controls.build_text_setting_control(
                    input_id=setting_id,
                    label=setting_label,
                    value=str(setting_default_value or ""),
                    placeholder=str(
                        get_setting_value(
                            setting=setting,
                            name="placeholder",
                            default="",
                        )
                    ),
                )
            )
            continue

        if setting_kind in ("select", "dropdown"):
            setting_options = get_setting_value(
                setting=setting,
                name="options",
                default=[],
            )

            setting_controls.append(
                controls.build_select_setting_control(
                    dropdown_id=setting_id,
                    label=setting_label,
                    options=normalize_dropdown_options(
                        options=setting_options,
                    ),
                    value=setting_default_value,
                    placeholder=str(
                        get_setting_value(
                            setting=setting,
                            name="placeholder",
                            default="Select value",
                        )
                    ),
                )
            )
            continue

    return setting_controls


def build_peak_workflow_layout(
    *,
    ids: Any,
    processes: list[Any],
    process_dropdown_label: str = "Peak process",
    graph_title: str = "Peak workflow",
    number_of_bins: int = 100,
    xscale: str = "linear",
    yscale: str = "log",
) -> list[Any]:
    """
    Build the complete reusable peak workflow layout.
    """
    return [
        html.Div(
            [
                build_peak_process_selector(
                    dropdown_id=ids.process_dropdown,
                    processes=processes,
                    label=process_dropdown_label,
                ),
                controls.build_graph_toggle_control(
                    switch_id=ids.graph_toggle_switch,
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
            build_peak_process_cards(
                ids=ids,
                processes=processes,
            )
        ),
        html.H6(
            graph_title,
            style={
                "marginTop": "18px",
                "marginBottom": "8px",
            },
        ),
        controls.build_histogram_controls(
            container_id=ids.histogram_controls_container,
            nbins_control_container_id=ids.nbins_control_container,
            nbins_input_id=ids.nbins_input,
            xscale_switch_id=ids.xscale_switch,
            yscale_switch_id=ids.yscale_switch,
            number_of_bins=number_of_bins,
            xscale=xscale,
            yscale=yscale,
        ),
        controls.build_graph_container(
            container_id=ids.graph_toggle_container,
            graph_id=ids.graph_hist,
        ),
    ]


def get_process_name(
    *,
    process: Any,
) -> str:
    """
    Return the canonical process name.
    """
    for attribute_name in ("name", "process_name"):
        value = getattr(process, attribute_name, None)

        if isinstance(value, str) and value:
            return value

    raise AttributeError(
        "Peak process must expose a non empty name or process_name attribute."
    )


def get_process_label(
    *,
    process: Any,
) -> str:
    """
    Return the user visible process label.
    """
    for attribute_name in ("label", "display_name", "title", "name"):
        value = getattr(process, attribute_name, None)

        if isinstance(value, str) and value:
            return value

    return get_process_name(
        process=process,
    )


def get_process_description(
    *,
    process: Any,
) -> str:
    """
    Return the user visible process description.
    """
    value = getattr(process, "description", "")

    if isinstance(value, str):
        return value

    return ""


def get_required_detector_channels(
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

    channel_names = getattr(process, "required_detector_channels", [])

    if channel_names is None:
        return []

    return [
        str(channel_name)
        for channel_name in channel_names
    ]


def get_process_settings(
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

    settings = getattr(process, "settings", [])

    if settings is None:
        return []

    return list(settings)


def get_setting_value(
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


def normalize_dropdown_options(
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