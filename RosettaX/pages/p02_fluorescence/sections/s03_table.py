# -*- coding: utf-8 -*-

from typing import Any, Optional
import logging

import dash
import dash_bootstrap_components as dbc

from RosettaX.pages.p00_sidebar.ids import SidebarIds
from RosettaX.utils import ui_forms
from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.workflow.table.fluorescence import FluorescenceReferenceTable
from RosettaX.workflow.table.layout import ReferenceTableConfig
from RosettaX.workflow.table.layout import ReferenceTableLayout


logger = logging.getLogger(__name__)


class ReferenceTable:
    """
    Fluorescence calibration reference table section.

    Responsibilities
    ----------------
    - Configure the fluorescence reference table layout.
    - Populate the table from the default runtime profile at layout creation.
    - Rebuild the table from runtime profile values when a sidebar profile is loaded.
    - Preserve user edited rows during ordinary runtime store updates.
    - Own the add row callback.
    - Keep the existing table ID used by peak detection and calibration callbacks.

    Ownership rule
    --------------
    This section owns fluorescence reference table behavior. Generic table
    rendering is delegated to ``ReferenceTableLayout``.
    """

    calibrated_intensity_column_name = FluorescenceReferenceTable.column_calibrated_intensity
    measured_intensity_column_name = FluorescenceReferenceTable.column_measured_intensity

    bead_table_columns = FluorescenceReferenceTable.columns
    user_data_column_ids = FluorescenceReferenceTable.user_data_column_ids

    def __init__(
        self,
        page: Any,
    ) -> None:
        self.page = page
        self.ids = page.ids.Calibration

        self.reference_table_tooltip_target_id = f"{self.ids.bead_table}-reference-table-info-target"
        self.reference_table_tooltip_id = f"{self.ids.bead_table}-reference-table-info-tooltip"

        self.config = ReferenceTableConfig(
            card_title=self._build_card_title(),
            table_title=None,
            description=None,
            add_row_button_label="Add row",
            body_style_key="body_scroll",
            show_table_title=False,
        )

        self.layout_builder = ReferenceTableLayout(
            ids=self.ids,
            config=self.config,
            table_columns=self.bead_table_columns,
            table_data=self._build_default_bead_rows(),
        )

        logger.debug(
            "Initialized Fluorescence ReferenceTable section with page=%r",
            page,
        )

    def get_layout(self) -> dbc.Card:
        """
        Build the fluorescence reference table layout.
        """
        logger.debug("Building Fluorescence ReferenceTable layout.")

        card = self.layout_builder.get_layout()

        return ui_forms.apply_workflow_section_card_style(
            card=card,
            header_font_weight="750",
            header_font_size="1.02rem",
        )

    def _build_card_title(self) -> dash.html.Div:
        """
        Build the card title with compact hover help.
        """
        return ui_forms.build_title_with_info(
            title="3. Calibration reference table",
            tooltip_target_id=self.reference_table_tooltip_target_id,
            tooltip_id=self.reference_table_tooltip_id,
            tooltip_text=(
                "Enter the known MESF values for the fluorescence calibration "
                "beads and use the fluorescence peak detection section to fill "
                "the measured peak positions. This table is the source of truth "
                "for the fluorescence calibration fit."
            ),
        )

    def _build_default_bead_rows(self) -> list[dict[str, str]]:
        """
        Build initial table rows from the default runtime profile.
        """
        runtime_config = RuntimeConfig.from_default_profile()

        return self.build_bead_rows_from_runtime_config(
            runtime_config=runtime_config,
        )

    def register_callbacks(self) -> None:
        """
        Register reference table callbacks.
        """
        logger.debug("Registering fluorescence reference table callbacks.")

        self._register_runtime_table_sync_callback()
        self._register_add_row_callback()

    def _register_runtime_table_sync_callback(self) -> None:
        """
        Register runtime config to table synchronization.
        """

        @dash.callback(
            dash.Output(
                self.ids.bead_table,
                "data",
                allow_duplicate=True,
            ),
            dash.Input("runtime-config-store", "data"),
            dash.Input(SidebarIds.profile_load_event_store, "data"),
            dash.State(self.ids.bead_table, "data"),
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

    def _register_add_row_callback(self) -> None:
        """
        Register the add row callback.
        """

        @dash.callback(
            dash.Output(
                self.ids.bead_table,
                "data",
                allow_duplicate=True,
            ),
            dash.Input(self.ids.add_row_btn, "n_clicks"),
            dash.State(self.ids.bead_table, "data"),
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

    def build_bead_rows_from_runtime_config(
        self,
        *,
        runtime_config: RuntimeConfig,
    ) -> list[dict[str, str]]:
        """
        Build fluorescence calibration table rows from a runtime configuration.

        Compatibility wrapper for older imports.
        """
        rows = FluorescenceReferenceTable.build_rows_from_runtime_config(
            runtime_config=runtime_config,
        )

        logger.debug(
            "Built fluorescence reference table rows from runtime config. rows=%r",
            rows,
        )

        return rows