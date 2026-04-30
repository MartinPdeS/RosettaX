# -*- coding: utf-8 -*-

from typing import Any, Optional
import logging

import dash

from RosettaX.pages.p00_sidebar.ids import SidebarIds
from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.workflow.table.fluorescence import FluorescenceReferenceTable


logger = logging.getLogger(__name__)


def register_callbacks(section) -> None:
    """
    Register reference table callbacks.
    """
    logger.debug("Registering fluorescence reference table callbacks.")

    _register_runtime_table_sync_callback(section)
    _register_add_row_callback(section)


def _register_runtime_table_sync_callback(section) -> None:
    """
    Register runtime config to table synchronization.
    """

    @dash.callback(
        dash.Output(
            section.ids.bead_table,
            "data",
            allow_duplicate=True,
        ),
        dash.Input("runtime-config-store", "data"),
        dash.Input(SidebarIds.profile_load_event_store, "data"),
        dash.State(section.ids.bead_table, "data"),
        prevent_initial_call=True,
    )
    def sync_bead_table_from_runtime_store(
        runtime_config_data: Any,
        profile_load_event_data: Any,
        current_rows: Optional[list[dict[str, Any]]],
    ) -> Any:
        if not isinstance(runtime_config_data, dict):
            logger.debug(
                "sync_bead_table_from_runtime_store received no runtime config. "
                "Keeping current table data."
            )

            return dash.no_update

        should_rebuild_table = FluorescenceReferenceTable.should_rebuild_from_runtime_config(
            profile_load_event_data=profile_load_event_data,
            current_rows=current_rows,
        )

        normalized_current_rows = FluorescenceReferenceTable.normalize_rows(
            rows=current_rows,
        )

        logger.debug(
            "sync_bead_table_from_runtime_store called with triggered_id=%r "
            "should_rebuild_table=%r profile_load_event_data=%r current_rows=%r",
            dash.ctx.triggered_id,
            should_rebuild_table,
            profile_load_event_data,
            normalized_current_rows,
        )

        if not should_rebuild_table:
            logger.debug(
                "Fluorescence reference table already contains user data "
                "and no profile load was requested. Leaving it unchanged."
            )

            return dash.no_update

        runtime_config = RuntimeConfig.from_dict(
            runtime_config_data,
        )

        resolved_rows = FluorescenceReferenceTable.build_rows_from_runtime_config(
            runtime_config=runtime_config,
        )

        logger.debug(
            "Rebuilt fluorescence reference table from runtime config. "
            "row_count=%r rows=%r",
            len(resolved_rows),
            resolved_rows,
        )

        return resolved_rows


def _register_add_row_callback(section) -> None:
    """
    Register the add row callback.
    """

    @dash.callback(
        dash.Output(
            section.ids.bead_table,
            "data",
            allow_duplicate=True,
        ),
        dash.Input(section.ids.add_row_btn, "n_clicks"),
        dash.State(section.ids.bead_table, "data"),
        prevent_initial_call=True,
    )
    def add_row(
        n_clicks: int,
        rows: Optional[list[dict[str, Any]]],
    ) -> list[dict[str, Any]]:
        logger.debug(
            "add_row called with n_clicks=%r existing_row_count=%r",
            n_clicks,
            None if rows is None else len(rows),
        )

        next_rows = FluorescenceReferenceTable.add_empty_row(
            rows=rows,
        )

        logger.debug(
            "add_row returning next_row_count=%r",
            len(next_rows),
        )

        return next_rows
