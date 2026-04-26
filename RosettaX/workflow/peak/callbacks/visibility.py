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

    register_force_graph_visible_callback(
        ids=ids,
    )

    register_graph_visibility_callback(
        ids=ids,
    )

    register_graph_controls_visibility_callback(
        ids=ids,
    )

    register_bins_visibility_callback(
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
        resolved_process_name = registry.resolve_process_name(
            process_name,
        )

        styles: list[dict[str, Any]] = []

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
                    selected_process_name=resolved_process_name,
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
        resolved_process_name = registry.resolve_process_name(
            process_name,
        )

        process = registry.get_process_instance(
            process_name=resolved_process_name,
        )

        if process is None:
            return current_graph_toggle_value

        if process.should_force_graph_visible(
            selected_process_name=resolved_process_name,
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
            ids.graph_toggle_switch,
            "value",
        ),
        prevent_initial_call=False,
    )
    def toggle_graph_container(
        graph_toggle_value: Any,
    ) -> dict[str, str]:
        if graph_toggle_is_enabled(
            graph_toggle_value,
        ):
            return {
                "display": "block",
            }

        return {
            "display": "none",
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
        resolved_process_name = registry.resolve_process_name(
            process_name,
        )

        process = registry.get_process_instance(
            process_name=resolved_process_name,
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
        resolved_process_name = registry.resolve_process_name(
            process_name,
        )

        process = registry.get_process_instance(
            process_name=resolved_process_name,
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