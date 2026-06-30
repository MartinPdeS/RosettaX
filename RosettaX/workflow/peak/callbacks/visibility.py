# -*- coding: utf-8 -*-

from typing import Any

import dash

from .. import registry


def register_visibility_callbacks(
    *,
    ids: Any,
) -> None:
    """
    Register peak workflow visibility callbacks.
    """
    register_process_visibility_callback(
        ids=ids,
    )

    register_graph_toggle_control_visibility_callback(
        ids=ids,
    )

    register_advanced_mode_control_visibility_callback(
        ids=ids,
    )

    register_data_filter_control_visibility_callback(
        ids=ids,
    )

    register_force_graph_visible_callback(
        ids=ids,
    )

    register_graph_visibility_callback(
        ids=ids,
    )

    register_graph_helper_legend_callback(
        ids=ids,
    )

    register_status_area_visibility_callback(
        ids=ids,
    )

    register_graph_controls_visibility_callback(
        ids=ids,
    )

    register_bins_visibility_callback(
        ids=ids,
    )

    register_process_settings_visibility_callback(
        ids=ids,
    )


def graph_toggle_is_enabled(
    graph_toggle_value: Any,
) -> bool:
    """
    Return whether the graph toggle value means that the graph is visible.
    """
    if isinstance(
        graph_toggle_value,
        str,
    ):
        return graph_toggle_value == "enabled"

    if isinstance(
        graph_toggle_value,
        (list, tuple, set),
    ):
        return "enabled" in graph_toggle_value

    if isinstance(
        graph_toggle_value,
        bool,
    ):
        return graph_toggle_value

    return False


def has_selected_process(
    process_name: Any,
) -> bool:
    """
    Return whether a concrete peak process is selected.
    """
    return bool(registry.get_selected_process_name(process_name))


def build_graph_toggle_control_style(
    process_name: Any,
) -> dict[str, str]:
    """
    Build the graph toggle style for the selected process state.
    """
    if not has_selected_process(process_name):
        return {
            "display": "none",
        }

    return {
        "display": "inline-flex",
    }


def build_advanced_mode_control_style(
    process_name: Any,
) -> dict[str, str]:
    """
    Build the advanced mode toggle style for the selected process state.
    """
    return build_graph_toggle_control_style(
        process_name,
    )


def build_process_settings_container_style(
    *,
    process_name: Any,
    advanced_mode_value: Any,
) -> dict[str, Any]:
    """
    Build style for process advanced settings visibility.
    """
    if not has_selected_process(process_name):
        return {
            "display": "none",
        }

    if not graph_toggle_is_enabled(advanced_mode_value):
        return {
            "display": "none",
        }

    return {
        "display": "flex",
        "alignItems": "end",
        "gap": "12px",
        "flexWrap": "wrap",
        "marginTop": "10px",
    }


def build_graph_container_style(
    *,
    process_name: Any,
    graph_toggle_value: Any,
) -> dict[str, str]:
    """
    Build the graph container style for the selected process state.
    """
    if not has_selected_process(process_name):
        return {
            "display": "none",
        }

    if graph_toggle_is_enabled(graph_toggle_value):
        return {
            "display": "block",
        }

    return {
        "display": "none",
    }


def build_rosetta_advanced_only_style(
    *,
    process_name: Any,
    graph_toggle_value: Any,
    advanced_mode_value: Any,
) -> dict[str, Any]:
    """
    Build visibility style for Rosetta advanced-only helpers.
    """
    selected_process_name = registry.get_selected_process_name(
        process_name,
    )

    if selected_process_name != "Rosetta Script":
        return {
            "display": "block",
        }

    if not graph_toggle_is_enabled(graph_toggle_value):
        return {
            "display": "none",
        }

    if not graph_toggle_is_enabled(advanced_mode_value):
        return {
            "display": "none",
        }

    return {
        "display": "block",
    }


def register_graph_toggle_control_visibility_callback(
    *,
    ids: Any,
) -> None:
    """
    Hide the graph toggle until a peak process is selected.
    """

    @dash.callback(
        dash.Output(
            ids.graph_toggle_switch,
            "style",
        ),
        dash.Input(
            ids.process_dropdown,
            "value",
        ),
        prevent_initial_call=False,
    )
    def toggle_graph_toggle_control(
        process_name: Any,
    ) -> dict[str, str]:
        return build_graph_toggle_control_style(process_name)


def register_advanced_mode_control_visibility_callback(
    *,
    ids: Any,
) -> None:
    """
    Hide the advanced mode toggle until a peak process is selected.
    """

    @dash.callback(
        dash.Output(
            ids.advanced_mode_switch,
            "style",
        ),
        dash.Input(
            ids.process_dropdown,
            "value",
        ),
        prevent_initial_call=False,
    )
    def toggle_advanced_mode_control(
        process_name: Any,
    ) -> dict[str, str]:
        return build_advanced_mode_control_style(process_name)


def register_data_filter_control_visibility_callback(
    *,
    ids: Any,
) -> None:
    """
    Hide the shared zero/saturation filter toggle until a process is selected.
    """

    @dash.callback(
        dash.Output(
            ids.data_filter_switch,
            "style",
        ),
        dash.Input(
            ids.process_dropdown,
            "value",
        ),
        prevent_initial_call=False,
    )
    def toggle_data_filter_control(
        process_name: Any,
    ) -> dict[str, str]:
        return build_graph_toggle_control_style(process_name)


def register_process_visibility_callback(
    *,
    ids: Any,
) -> None:
    """
    Register process control card visibility callback.
    """

    @dash.callback(
        dash.Output(
            ids.process_controls_container_pattern(),
            "style",
        ),
        dash.Input(
            ids.process_dropdown,
            "value",
        ),
        dash.State(
            ids.process_controls_container_pattern(),
            "id",
        ),
        prevent_initial_call=False,
    )
    def toggle_process_controls(
        process_name: Any,
        process_container_ids: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        selected_process_name = registry.get_selected_process_name(
            process_name,
        )

        styles: list[dict[str, Any]] = []

        if not selected_process_name:
            return [
                {
                    "display": "none",
                }
                for _ in (process_container_ids or [])
            ]

        for process_container_id in process_container_ids or []:
            if not isinstance(
                process_container_id,
                dict,
            ):
                styles.append(
                    {
                        "display": "none",
                    }
                )
                continue

            process_name_from_id = process_container_id.get(
                "process",
            )

            process = registry.get_process_instance(
                process_name=process_name_from_id,
            )

            if process is None:
                styles.append(
                    {
                        "display": "none",
                    }
                )
                continue

            styles.append(
                process.build_visibility_style(
                    selected_process_name=selected_process_name,
                )
            )

        return styles


def register_force_graph_visible_callback(
    *,
    ids: Any,
) -> None:
    """
    Force the graph visible when the selected process requires a graph.

    This applies to manual click processes and to any script that sets
    force_graph_visible=True.
    """

    @dash.callback(
        dash.Output(
            ids.graph_toggle_switch,
            "value",
            allow_duplicate=True,
        ),
        dash.Input(
            ids.process_dropdown,
            "value",
        ),
        dash.State(
            ids.graph_toggle_switch,
            "value",
        ),
        prevent_initial_call=True,
    )
    def force_graph_visible_for_selected_process(
        process_name: Any,
        current_graph_toggle_value: Any,
    ) -> Any:
        selected_process_name = registry.get_selected_process_name(
            process_name,
        )

        if not selected_process_name:
            return []

        process = registry.get_process_instance(
            process_name=selected_process_name,
        )

        if process is None:
            return current_graph_toggle_value

        if process.should_force_graph_visible(
            selected_process_name=selected_process_name,
        ):
            return [
                "enabled",
            ]

        return current_graph_toggle_value


def register_graph_visibility_callback(
    *,
    ids: Any,
) -> None:
    """
    Register graph container visibility callback.
    """

    @dash.callback(
        dash.Output(
            ids.graph_toggle_container,
            "style",
        ),
        dash.Input(
            ids.process_dropdown,
            "value",
        ),
        dash.Input(
            ids.graph_toggle_switch,
            "value",
        ),
        prevent_initial_call=False,
    )
    def toggle_graph_container(
        process_name: Any,
        graph_toggle_value: Any,
    ) -> dict[str, str]:
        return build_graph_container_style(
            process_name=process_name,
            graph_toggle_value=graph_toggle_value,
        )


def register_graph_helper_legend_callback(
    *,
    ids: Any,
) -> None:
    """
    Show a plain-text Rosetta legend below the graph when relevant.
    """

    @dash.callback(
        dash.Output(
            ids.graph_helper_legend,
            "children",
        ),
        dash.Output(
            ids.graph_helper_legend,
            "style",
        ),
        dash.Input(
            ids.process_dropdown,
            "value",
        ),
        dash.Input(
            ids.graph_toggle_switch,
            "value",
        ),
        dash.Input(
            ids.advanced_mode_switch,
            "value",
        ),
        prevent_initial_call=False,
    )
    def toggle_graph_helper_legend(
        process_name: Any,
        graph_toggle_value: Any,
        advanced_mode_value: Any,
    ) -> tuple[Any, dict[str, Any]]:
        base_style = {
            "display": "none",
            "marginTop": "8px",
            "marginBottom": "14px",
            "padding": "10px 12px",
            "borderRadius": "8px",
            "backgroundColor": "#f6f9fc",
            "border": "1px solid #d6e0ea",
            "fontSize": "0.9rem",
            "lineHeight": "1.45",
            "color": "#22324a",
        }

        selected_process_name = registry.get_selected_process_name(
            process_name,
        )

        if (
            selected_process_name != "Rosetta Script"
            or not graph_toggle_is_enabled(graph_toggle_value)
            or not graph_toggle_is_enabled(advanced_mode_value)
        ):
            return "", base_style

        return (
            [
                dash.html.Div(
                    "Rosetta legend",
                    style={"fontWeight": "600", "marginBottom": "4px"},
                ),
                dash.html.Div("Green area: scattering only."),
                dash.html.Div("Blue area: fluorescence only."),
                dash.html.Div("Green dashed vertical lines: scattering peak positions."),
                dash.html.Div("Red dashed horizontal lines: fluorescence peak positions."),
            ],
            {
                **base_style,
                "display": "block",
            },
        )


def register_status_area_visibility_callback(
    *,
    ids: Any,
) -> None:
    """
    Show the below-graph status area only when relevant for the selected process.
    """

    @dash.callback(
        dash.Output(
            ids.script_status,
            "style",
        ),
        dash.Input(
            ids.process_dropdown,
            "value",
        ),
        dash.Input(
            ids.graph_toggle_switch,
            "value",
        ),
        dash.Input(
            ids.advanced_mode_switch,
            "value",
        ),
        prevent_initial_call=False,
    )
    def toggle_status_area(
        process_name: Any,
        graph_toggle_value: Any,
        advanced_mode_value: Any,
    ) -> dict[str, Any]:
        base_style = {
            "marginTop": "12px",
            "display": "flex",
            "flexDirection": "column",
            "gap": "10px",
        }

        visibility_style = build_rosetta_advanced_only_style(
            process_name=process_name,
            graph_toggle_value=graph_toggle_value,
            advanced_mode_value=advanced_mode_value,
        )

        return {
            **base_style,
            **visibility_style,
        }


def register_graph_controls_visibility_callback(
    *,
    ids: Any,
) -> None:
    """
    Register graph controls visibility callback.

    The controls container holds bins, log x, and log y. The container should be
    visible for both one dimensional histograms and two dimensional scatter
    plots. The bin subcontrol is hidden separately for scatter plots.
    """

    @dash.callback(
        dash.Output(
            ids.histogram_controls_container,
            "style",
        ),
        dash.Input(
            ids.process_dropdown,
            "value",
        ),
        prevent_initial_call=False,
    )
    def toggle_graph_controls(
        process_name: Any,
    ) -> dict[str, Any]:
        selected_process_name = registry.get_selected_process_name(
            process_name,
        )

        if not selected_process_name:
            return {
                "display": "none",
            }

        process = registry.get_process_instance(
            process_name=selected_process_name,
        )

        if process is None:
            return {
                "display": "none",
            }

        graph_type = getattr(
            process,
            "graph_type",
            None,
        )

        if graph_type in (
            "1d_histogram",
            "2d_scatter",
        ):
            return {
                "display": "flex",
                "alignItems": "center",
                "gap": "16px",
                "flexWrap": "wrap",
            }

        return {
            "display": "none",
        }


def register_bins_visibility_callback(
    *,
    ids: Any,
) -> None:
    """
    Hide the Bins control for scatter plots.

    The bin count only applies to one dimensional histogram processes. For two
    dimensional scatter selection, only log x and log y remain visible.
    """

    @dash.callback(
        dash.Output(
            ids.nbins_control_container,
            "style",
        ),
        dash.Input(
            ids.process_dropdown,
            "value",
        ),
        prevent_initial_call=False,
    )
    def toggle_bins_control(
        process_name: Any,
    ) -> dict[str, Any]:
        selected_process_name = registry.get_selected_process_name(
            process_name,
        )

        if not selected_process_name:
            return {
                "display": "none",
            }

        process = registry.get_process_instance(
            process_name=selected_process_name,
        )

        if process is None:
            return {
                "display": "none",
            }

        graph_type = getattr(
            process,
            "graph_type",
            None,
        )

        if graph_type == "1d_histogram":
            return {
                "display": "block",
            }

        return {
            "display": "none",
        }


def register_process_settings_visibility_callback(
    *,
    ids: Any,
) -> None:
    """
    Show advanced setting controls only for the selected process in advanced mode.
    """

    @dash.callback(
        dash.Output(
            ids.process_settings_container_pattern(),
            "style",
        ),
        dash.Input(
            ids.process_dropdown,
            "value",
        ),
        dash.Input(
            ids.advanced_mode_switch,
            "value",
        ),
        dash.State(
            ids.process_settings_container_pattern(),
            "id",
        ),
        prevent_initial_call=False,
    )
    def toggle_process_settings_containers(
        process_name: Any,
        advanced_mode_value: Any,
        settings_container_ids: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        selected_process_name = registry.get_selected_process_name(
            process_name,
        )

        styles: list[dict[str, Any]] = []

        for settings_container_id in settings_container_ids or []:
            if not isinstance(settings_container_id, dict):
                styles.append(
                    {
                        "display": "none",
                    }
                )
                continue

            process_name_from_id = settings_container_id.get(
                "process",
            )

            if process_name_from_id != selected_process_name:
                styles.append(
                    {
                        "display": "none",
                    }
                )
                continue

            styles.append(
                build_process_settings_container_style(
                    process_name=process_name,
                    advanced_mode_value=advanced_mode_value,
                )
            )

        return styles
