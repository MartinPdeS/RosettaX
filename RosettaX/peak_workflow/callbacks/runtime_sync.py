# -*- coding: utf-8 -*-

from typing import Any

import dash

from RosettaX.utils.runtime_config import RuntimeConfig


def register_runtime_sync_callbacks(
    *,
    ids: Any,
    runtime_config_store_id: str,
) -> None:
    """
    Register runtime configuration synchronization callbacks.

    This callback synchronizes the shared peak workflow graph controls from the
    runtime profile.

    It intentionally does not run on initial page render. Dash session
    persistence should restore user choices for:

    - Show graph
    - Log x
    - Log y
    - Bins

    The callback still runs when a new profile is loaded and the runtime config
    store changes during the session.
    """

    @dash.callback(
        dash.Output(ids.nbins_input, "value"),
        dash.Output(ids.graph_toggle_switch, "value"),
        dash.Output(ids.xscale_switch, "value"),
        dash.Output(ids.yscale_switch, "value"),
        dash.Input(runtime_config_store_id, "data"),
        prevent_initial_call=True,
    )
    def sync_graph_controls_from_runtime_store(
        runtime_config_data: Any,
    ) -> tuple[Any, Any, Any, Any]:
        runtime_config = RuntimeConfig.from_dict(
            runtime_config_data if isinstance(runtime_config_data, dict) else None
        )

        histogram_xscale = normalize_axis_scale(
            runtime_config.get_str(
                "calibration.histogram_xscale",
                default="linear",
            ),
            default="linear",
        )

        histogram_yscale = normalize_axis_scale(
            runtime_config.get_str(
                "calibration.histogram_yscale",
                default=runtime_config.get_str(
                    "calibration.histogram_scale",
                    default="log",
                ),
            ),
            default="log",
        )

        return (
            runtime_config.get_int(
                "calibration.n_bins_for_plots",
                default=100,
            ),
            ["enabled"] if runtime_config.get_show_graphs(default=True) else [],
            ["log"] if histogram_xscale == "log" else [],
            ["log"] if histogram_yscale == "log" else [],
        )


def normalize_axis_scale(
    value: Any,
    *,
    default: str,
) -> str:
    """
    Normalize an axis scale value.

    Accepted values are:

    - linear
    - log
    """
    value_string = str(value or "").strip().lower()

    if value_string in (
        "linear",
        "log",
    ):
        return value_string

    return default