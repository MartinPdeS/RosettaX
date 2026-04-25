# -*- coding: utf-8 -*-

from typing import Any

from .detector_dropdowns import register_detector_dropdown_callbacks
from .graph import register_graph_callbacks
from .mutation import register_mutation_callbacks
from .runtime_sync import register_runtime_sync_callbacks
from .visibility import register_visibility_callbacks

from RosettaX.peak_workflow.scripts import registry


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

        register_runtime_sync_callbacks(
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


def get_peak_processes() -> list[Any]:
    """
    Return shared peak process instances.
    """
    return registry.get_peak_process_instances()