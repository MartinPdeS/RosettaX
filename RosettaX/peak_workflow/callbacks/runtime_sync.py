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

    This callback is not called on initial page render. That is intentional:
    Dash component session persistence should be allowed to restore the user's
    last selections for Show graph, Log x, Log y, and Bins.

    The callback still updates these controls if the runtime config store changes
    later during the session.
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

        xscale = runtime_config.get_str(
            "calibration.histogram_xscale",
            default=runtime_config.get_str(
                "calibration.xscale",
                default="linear",
            ),
        )

        yscale = runtime_config.get_str(
            "calibration.histogram_yscale",
            default=runtime_config.get_str(
                "calibration.histogram_scale",
                default="log",
            ),
        )

        return (
            runtime_config.get_int(
                "calibration.n_bins_for_plots",
                default=100,
            ),
            ["enabled"] if runtime_config.get_show_graphs(default=True) else [],
            ["log"] if xscale == "log" else [],
            ["log"] if yscale == "log" else [],
        )