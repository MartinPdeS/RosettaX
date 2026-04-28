# -*- coding: utf-8 -*-

from typing import Any
import dash

from .detector_dropdowns import register_detector_dropdown_callbacks
from .graph import register_graph_callbacks
from .mutation import register_mutation_callbacks
from .visibility import register_visibility_callbacks
from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.workflow.plotting.scatter2d import Scatter2DGraph

from .. import registry


class PeakWorkflowCallbacks:
    """
    Shared callback registration for peak workflow sections.

    This class only wires callback groups together. Callback logic lives in the
    dedicated callback modules.
    """

    def __init__(
        self,
        *,
        page: Any,
        ids: Any,
        adapter: Any,
        table_id: str,
        page_state_store_id: str,
        max_events_input_id: Any,
        runtime_config_store_id: str = "runtime-config-store",
        mie_model_input_id: Any = None,
    ) -> None:
        self.page = page
        self.ids = ids
        self.adapter = adapter
        self.table_id = table_id
        self.page_state_store_id = page_state_store_id
        self.max_events_input_id = max_events_input_id
        self.runtime_config_store_id = runtime_config_store_id
        self.mie_model_input_id = mie_model_input_id

    def register(self) -> None:
        """
        Register all shared peak workflow callbacks.
        """
        register_detector_dropdown_callbacks(
            ids=self.ids,
            adapter=self.adapter,
            page_state_store_id=self.page_state_store_id,
        )

        self.register_runtime_sync_callbacks(
            ids=self.ids,
            runtime_config_store_id=self.runtime_config_store_id,
        )

        register_visibility_callbacks(
            ids=self.ids,
        )

        register_graph_callbacks(
            page=self.page,
            ids=self.ids,
            adapter=self.adapter,
            page_state_store_id=self.page_state_store_id,
            max_events_input_id=self.max_events_input_id,
            runtime_config_store_id=self.runtime_config_store_id,
        )

        register_mutation_callbacks(
            page=self.page,
            ids=self.ids,
            adapter=self.adapter,
            table_id=self.table_id,
            page_state_store_id=self.page_state_store_id,
            max_events_input_id=self.max_events_input_id,
            runtime_config_store_id=self.runtime_config_store_id,
            mie_model_input_id=self.mie_model_input_id,
        )

    def register_runtime_sync_callbacks(
        self,
        *,
        ids: Any,
        runtime_config_store_id: str,
    ) -> None:
        """
        Register runtime configuration synchronization callbacks.

        This callback synchronizes the shared peak workflow graph controls from
        the runtime profile.

        It intentionally does not run on initial page render. Dash session
        persistence should restore user choices for:

        - Show graph
        - Log x and Log y through the shared axis scale toggle
        - Bins

        The callback still runs when a new profile is loaded and the runtime
        config store changes during the session.
        """

        @dash.callback(
            dash.Output(ids.nbins_input, "value"),
            dash.Output(ids.graph_toggle_switch, "value"),
            dash.Output(ids.axis_scale_toggle, "value"),
            dash.Input(runtime_config_store_id, "data"),
            prevent_initial_call=True,
        )
        def sync_graph_controls_from_runtime_store(
            runtime_config_data: Any,
        ) -> tuple[Any, Any, Any]:
            runtime_config = RuntimeConfig.from_dict(
                runtime_config_data if isinstance(runtime_config_data, dict) else None
            )

            histogram_xscale = self.normalize_axis_scale(
                runtime_config.get_str(
                    "calibration.histogram_xscale",
                    default="linear",
                ),
                default="linear",
            )

            histogram_yscale = self.normalize_axis_scale(
                runtime_config.get_str(
                    "calibration.histogram_yscale",
                    default=runtime_config.get_str(
                        "calibration.histogram_scale",
                        default="log",
                    ),
                ),
                default="log",
            )

            axis_scale_toggle_values = self.build_axis_scale_toggle_values(
                xscale=histogram_xscale,
                yscale=histogram_yscale,
            )

            return (
                runtime_config.get_int(
                    "calibration.n_bins_for_plots",
                    default=100,
                ),
                ["enabled"] if runtime_config.get_show_graphs(default=True) else [],
                axis_scale_toggle_values,
            )

    def build_axis_scale_toggle_values(
        self,
        *,
        xscale: Any,
        yscale: Any,
    ) -> list[str]:
        """
        Convert normalized x and y scale values into the shared scatter toggle
        values.
        """
        axis_scale_toggle_values: list[str] = []

        if self.normalize_axis_scale(
            xscale,
            default="linear",
        ) == "log":
            axis_scale_toggle_values.append(
                Scatter2DGraph.x_log_value,
            )

        if self.normalize_axis_scale(
            yscale,
            default="linear",
        ) == "log":
            axis_scale_toggle_values.append(
                Scatter2DGraph.y_log_value,
            )

        return axis_scale_toggle_values

    def normalize_axis_scale(
        self,
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


def get_peak_processes() -> list[Any]:
    """
    Return shared peak process instances.
    """
    return registry.get_peak_process_instances()