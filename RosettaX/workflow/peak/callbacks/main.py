
import logging
from typing import Any

from ..models import PeakConfig
from .shared import PeakWorkflowCallbacks


def register_peak_callbacks(
    *,
    page: Any,
    ids: Any,
    adapter: Any,
    config: PeakConfig,
    logger: logging.Logger,
) -> None:
    """
    Register reusable peak callbacks.

    This is intentionally a thin wrapper around the existing generic peak
    workflow callback registrar.
    """
    logger.debug(
        "Registering reusable peak callbacks with graph_title=%r",
        config.graph_title,
    )

    PeakWorkflowCallbacks(
        page=page,
        ids=ids,
        adapter=adapter,
        table_id=config.table_id,
        page_state_store_id=config.page_state_store_id,
        max_events_input_id=config.max_events_input_id,
        runtime_config_store_id=config.runtime_config_store_id,
        mie_model_input_id=config.mie_model_input_id,
        default_process_runtime_config_path=config.default_process_runtime_config_path,
    ).register()