# -*- coding: utf-8 -*-

from typing import Any
import logging

import dash_bootstrap_components as dbc

from RosettaX.utils import ui_forms
from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.workflow.table.fluorescence import FluorescenceReferenceTable
from RosettaX.workflow.table.layout import ReferenceTableConfig
from RosettaX.workflow.table.layout import ReferenceTableLayout

from . import layout as _layout
from . import callbacks as _callbacks


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
        section_number: int,
        card_color: str = "pink",
    ) -> None:
        self.page = page
        self.ids = page.ids.Calibration
        self.section_number = section_number
        self.card_color = card_color

        self.reference_table_tooltip_target_id = f"{self.ids.bead_table}-reference-table-info-target"
        self.reference_table_tooltip_id = f"{self.ids.bead_table}-reference-table-info-tooltip"

        self.config = ReferenceTableConfig(
            card_title=_layout.build_card_title(self),
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
            table_data=_layout.build_default_bead_rows(),
        )

        logger.debug(
            "Initialized Fluorescence ReferenceTable section with page=%r",
            page,
        )

    def get_layout(self) -> dbc.Card:
        """
        Build the fluorescence reference table layout.
        """
        return _layout.get_layout(self)

    def register_callbacks(self) -> None:
        """
        Register reference table callbacks.
        """
        _callbacks.register_callbacks(self)

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
