# -*- coding: utf-8 -*-

import logging
from typing import Any, Optional

import dash
import dash_bootstrap_components as dbc

from RosettaX.pages.p00_sidebar.ids import SidebarIds
from RosettaX.pages.p03_scattering.sections import s04_table_services as services
from RosettaX.pages.p03_scattering.state import ScatteringPageState
from RosettaX.utils import styling
from RosettaX.utils.runtime_config import RuntimeConfig


logger = logging.getLogger(__name__)


class ReferenceTable:
    """
    Scattering calibration standard table section.

    Responsibilities
    ----------------
    - Render the scattering calibration standard table.
    - Render the add row button.
    - Render the standard coupling computation action.
    - Populate the table from the default runtime profile at layout creation.
    - Rebuild the table from runtime profile values when a profile is loaded.
    - Synchronize table schema with the selected Mie model.
    - Compute modeled coupling values from the current calibration standard
      optical and particle parameters.
    - Store the calibration standard parameter payload in the scattering page state.

    Ownership rule
    --------------
    This section owns the calibration standard table and the standard coupling
    computation action. The calibration section reads the table when fitting the
    instrument response.
    """

    sphere_table_columns = services.sphere_table_columns
    core_shell_table_columns = services.core_shell_table_columns

    def __init__(
        self,
        page: Any,
    ) -> None:
        self.page = page
        self.ids = page.ids.Calibration

        logger.debug(
            "Initialized Scattering ReferenceTable section with page=%r",
            page,
        )

    def get_layout(self) -> dbc.Card:
        """
        Build the scattering calibration standard table layout.
        """
        logger.debug("Building Scattering ReferenceTable layout.")

        return dbc.Card(
            [
                self._build_header(),
                self._build_body(),
            ]
        )

    def _get_layout(self) -> dbc.Card:
        """
        Compatibility alias for older section loading code.
        """
        return self.get_layout()

    def _build_header(self) -> dbc.CardHeader:
        """
        Build the section header.
        """
        return dbc.CardHeader(
            "4. Calibration standard table",
        )

    def _build_body(self) -> dbc.CardBody:
        """
        Build the section body.
        """
        return dbc.CardBody(
            [
                self._build_reference_table_section(),
                dash.html.Div(
                    style={
                        "height": "12px",
                    },
                ),
                self._build_compute_model_block(),
            ]
        )

    def _build_reference_table_section(self) -> dash.html.Div:
        """
        Build the calibration standard table block.
        """
        default_columns, default_rows = self._build_default_table_state()

        return dash.html.Div(
            [
                dash.html.H5("Calibration standard table"),
                dash.html.Div(
                    (
                        "This table defines the calibration standard used to infer "
                        "the instrument response. Edit the standard particle geometry "
                        "directly here. Measured peak positions are optional at this "
                        "stage. First click Compute Standard Coupling to fill the "
                        "modeled coupling column. Then fit the instrument response in "
                        "the next section."
                    ),
                    style={
                        "marginBottom": "10px",
                        "opacity": 0.8,
                    },
                ),
                dash.dash_table.DataTable(
                    id=self.ids.bead_table,
                    columns=default_columns,
                    data=default_rows,
                    **styling.DATATABLE,
                ),
                dash.html.Div(
                    [
                        dash.html.Button(
                            "Add row",
                            id=self.ids.add_row_btn,
                            n_clicks=0,
                        )
                    ],
                    style={
                        "marginTop": "10px",
                    },
                ),
            ]
        )

    def _build_compute_model_block(self) -> dash.html.Div:
        """
        Build the standard coupling computation block.
        """
        return dash.html.Div(
            [
                self._build_compute_model_button(),
                dash.html.Div(
                    (
                        "This step fills the modeled coupling column for the "
                        "calibration standard using the current optical and particle "
                        "parameters."
                    ),
                    style={
                        "marginTop": "8px",
                        "opacity": 0.75,
                    },
                ),
            ]
        )

    def _build_compute_model_button(self) -> dash.html.Button:
        """
        Build the standard coupling computation button.
        """
        return dash.html.Button(
            "Compute Standard Coupling",
            id=self.ids.compute_model_btn,
            n_clicks=0,
            style={
                "marginTop": "12px",
            },
        )

    def _build_default_table_state(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """
        Build initial table columns and rows from the default runtime profile.
        """
        runtime_config = RuntimeConfig.from_default_profile()

        return services.build_table_state_from_runtime_config(
            runtime_config=runtime_config,
        )

    def register_callbacks(self) -> None:
        """
        Register calibration standard table callbacks.
        """
        logger.debug("Registering scattering calibration standard table callbacks.")

        self._register_table_default_population_callback()
        self._register_table_callbacks()
        self._register_compute_model_callback()
        self._register_post_compute_cleanup_callback()

    def _register_table_default_population_callback(self) -> None:
        """
        Populate the table from runtime defaults.

        If a sidebar profile has been loaded, the table is always rebuilt from
        the new runtime profile. Existing user edited rows are intentionally
        discarded in that case.

        If no profile load is involved, the table is only populated when it is
        effectively empty.
        """

        @dash.callback(
            dash.Output(
                self.ids.bead_table,
                "columns",
                allow_duplicate=True,
            ),
            dash.Output(
                self.ids.bead_table,
                "data",
                allow_duplicate=True,
            ),
            dash.Input("runtime-config-store", "data"),
            dash.Input(SidebarIds.profile_load_event_store, "data"),
            dash.State(self.page.ids.Parameters.mie_model, "value"),
            dash.State(self.ids.bead_table, "data"),
            prevent_initial_call=True,
        )
        def populate_table_from_runtime_defaults_callback(
            runtime_config_data: Any,
            profile_load_event_data: Any,
            mie_model: Any,
            current_rows: Optional[list[dict[str, Any]]],
        ) -> tuple[Any, Any]:
            runtime_config = RuntimeConfig.from_dict(
                runtime_config_data if isinstance(runtime_config_data, dict) else None
            )

            resolved_mie_model = services.resolve_mie_model(
                runtime_config.get_str(
                    "particle_model.mie_model",
                    default=mie_model or "Solid Sphere",
                )
            )

            should_rebuild_table = services.should_rebuild_table_from_runtime_config(
                mie_model=resolved_mie_model,
                profile_load_event_data=profile_load_event_data,
                current_rows=current_rows,
            )

            normalized_current_rows = services.normalize_table_rows(
                mie_model=resolved_mie_model,
                current_rows=current_rows,
            )

            user_data_column_ids = services.get_user_data_column_ids_for_model(
                resolved_mie_model,
            )

            logger.debug(
                "populate_table_from_runtime_defaults_callback called with "
                "triggered_id=%r should_rebuild_table=%r "
                "profile_load_event_data=%r resolved_mie_model=%r "
                "user_data_column_ids=%r current_rows=%r",
                dash.ctx.triggered_id,
                should_rebuild_table,
                profile_load_event_data,
                resolved_mie_model,
                user_data_column_ids,
                normalized_current_rows,
            )

            if not should_rebuild_table:
                logger.debug(
                    "Calibration standard table already contains user data and no "
                    "profile load was requested. Leaving it unchanged."
                )

                return dash.no_update, dash.no_update

            columns, rows = services.build_table_state_from_runtime_config(
                runtime_config=runtime_config,
            )

            logger.debug(
                "Rebuilt scattering calibration standard table from runtime config. "
                "columns=%r rows=%r",
                columns,
                rows,
            )

            return columns, rows

    def _register_table_callbacks(self) -> None:
        """
        Register schema synchronization, add row, and edit normalization callbacks.
        """

        @dash.callback(
            dash.Output(
                self.ids.bead_table,
                "columns",
                allow_duplicate=True,
            ),
            dash.Output(
                self.ids.bead_table,
                "data",
                allow_duplicate=True,
            ),
            dash.Input(self.page.ids.Parameters.mie_model, "value"),
            dash.State(self.ids.bead_table, "data"),
            prevent_initial_call=True,
        )
        def sync_table_schema_from_model(
            mie_model: Any,
            current_rows: Optional[list[dict[str, Any]]],
        ) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
            resolved_mie_model = services.resolve_mie_model(
                mie_model,
            )

            next_columns = services.get_table_columns_for_model(
                resolved_mie_model,
            )

            next_rows = services.remap_table_rows_to_model(
                mie_model=resolved_mie_model,
                current_rows=current_rows,
            )

            logger.debug(
                "sync_table_schema_from_model returning resolved_mie_model=%r "
                "column_count=%d row_count=%d",
                resolved_mie_model,
                len(next_columns),
                len(next_rows),
            )

            return next_columns, next_rows

        @dash.callback(
            dash.Output(
                self.ids.bead_table,
                "data",
                allow_duplicate=True,
            ),
            dash.Input(self.ids.add_row_btn, "n_clicks"),
            dash.State(self.page.ids.Parameters.mie_model, "value"),
            dash.State(self.ids.bead_table, "data"),
            prevent_initial_call=True,
        )
        def add_row(
            n_clicks: int,
            mie_model: Any,
            rows: Optional[list[dict[str, Any]]],
        ) -> list[dict[str, Any]]:
            logger.debug(
                "add_row called with n_clicks=%r mie_model=%r row_count=%r",
                n_clicks,
                mie_model,
                None if rows is None else len(rows),
            )

            next_rows = services.add_empty_row_for_model(
                mie_model=mie_model,
                rows=rows,
            )

            resolved_mie_model = services.resolve_mie_model(
                mie_model,
            )

            logger.debug(
                "add_row returning resolved_mie_model=%r new_row_count=%d",
                resolved_mie_model,
                len(next_rows),
            )

            return next_rows

        @dash.callback(
            dash.Output(
                self.ids.bead_table,
                "data",
                allow_duplicate=True,
            ),
            dash.Input(self.ids.bead_table, "data_timestamp"),
            dash.State(self.page.ids.Parameters.mie_model, "value"),
            dash.State(self.ids.bead_table, "data"),
            prevent_initial_call=True,
        )
        def normalize_table_after_user_edit(
            data_timestamp: Any,
            mie_model: Any,
            current_rows: Optional[list[dict[str, Any]]],
        ) -> list[dict[str, Any]]:
            logger.debug(
                "normalize_table_after_user_edit called with data_timestamp=%r "
                "mie_model=%r row_count=%r",
                data_timestamp,
                mie_model,
                None if current_rows is None else len(current_rows),
            )

            resolved_mie_model = services.resolve_mie_model(
                mie_model,
            )

            normalized_rows = services.normalize_table_rows(
                mie_model=resolved_mie_model,
                current_rows=current_rows,
            )

            logger.debug(
                "normalize_table_after_user_edit returning resolved_mie_model=%r "
                "row_count=%d",
                resolved_mie_model,
                len(normalized_rows),
            )

            return normalized_rows

    def _register_compute_model_callback(self) -> None:
        """
        Register standard coupling computation.
        """

        @dash.callback(
            dash.Output(
                self.ids.bead_table,
                "data",
                allow_duplicate=True,
            ),
            dash.Output(
                self.page.ids.State.page_state_store,
                "data",
                allow_duplicate=True,
            ),
            dash.Input(self.ids.compute_model_btn, "n_clicks"),
            dash.State(self.page.ids.Parameters.mie_model, "value"),
            dash.State(self.ids.bead_table, "data"),
            dash.State(self.page.ids.Parameters.medium_refractive_index_custom, "value"),
            dash.State(self.page.ids.Parameters.particle_refractive_index_custom, "value"),
            dash.State(self.page.ids.Parameters.core_refractive_index_custom, "value"),
            dash.State(self.page.ids.Parameters.shell_refractive_index_custom, "value"),
            dash.State(self.page.ids.Parameters.wavelength_nm, "value"),
            dash.State(self.page.ids.Parameters.detector_numerical_aperture, "value"),
            dash.State(self.page.ids.Parameters.detector_cache_numerical_aperture, "value"),
            dash.State(self.page.ids.Parameters.blocker_bar_numerical_aperture, "value"),
            dash.State(self.page.ids.Parameters.detector_sampling, "value"),
            dash.State(self.page.ids.Parameters.detector_phi_angle_degree, "value"),
            dash.State(self.page.ids.Parameters.detector_gamma_angle_degree, "value"),
            dash.State(self.page.ids.State.page_state_store, "data"),
            prevent_initial_call=True,
        )
        def compute_model(
            n_clicks: int,
            mie_model: Any,
            current_rows: Optional[list[dict[str, Any]]],
            medium_refractive_index: Any,
            particle_refractive_index: Any,
            core_refractive_index: Any,
            shell_refractive_index: Any,
            wavelength_nm: Any,
            detector_numerical_aperture: Any,
            detector_cache_numerical_aperture: Any,
            blocker_bar_numerical_aperture: Any,
            detector_sampling: Any,
            detector_phi_angle_degree: Any,
            detector_gamma_angle_degree: Any,
            page_state_payload: Any,
        ) -> tuple[list[dict[str, str]], dict[str, Any]]:
            logger.debug(
                "compute_model called with n_clicks=%r mie_model=%r row_count=%r",
                n_clicks,
                mie_model,
                None if current_rows is None else len(current_rows),
            )

            resolved_mie_model = services.resolve_mie_model(
                mie_model,
            )

            calibration_standard_parameters_payload = services.build_scattering_parameters_payload(
                mie_model=resolved_mie_model,
                medium_refractive_index=medium_refractive_index,
                particle_refractive_index=particle_refractive_index,
                core_refractive_index=core_refractive_index,
                shell_refractive_index=shell_refractive_index,
                wavelength_nm=wavelength_nm,
                detector_numerical_aperture=detector_numerical_aperture,
                detector_cache_numerical_aperture=detector_cache_numerical_aperture,
                blocker_bar_numerical_aperture=blocker_bar_numerical_aperture,
                detector_sampling=detector_sampling,
                detector_phi_angle_degree=detector_phi_angle_degree,
                detector_gamma_angle_degree=detector_gamma_angle_degree,
            )

            page_state = ScatteringPageState.from_dict(
                page_state_payload if isinstance(page_state_payload, dict) else None
            )

            page_state = page_state.update(
                scattering_parameters_payload=calibration_standard_parameters_payload,
            )

            computed_rows = services.compute_model_for_rows(
                mie_model=resolved_mie_model,
                current_rows=current_rows,
                medium_refractive_index=medium_refractive_index,
                particle_refractive_index=particle_refractive_index,
                core_refractive_index=core_refractive_index,
                shell_refractive_index=shell_refractive_index,
                wavelength_nm=wavelength_nm,
                detector_numerical_aperture=detector_numerical_aperture,
                detector_cache_numerical_aperture=detector_cache_numerical_aperture,
                blocker_bar_numerical_aperture=blocker_bar_numerical_aperture,
                detector_sampling=detector_sampling,
                detector_phi_angle_degree=detector_phi_angle_degree,
                detector_gamma_angle_degree=detector_gamma_angle_degree,
                logger=logger,
            )

            logger.debug(
                "compute_model returning resolved_mie_model=%r row_count=%d",
                resolved_mie_model,
                len(computed_rows),
            )

            return computed_rows, page_state.to_dict()

    def _register_post_compute_cleanup_callback(self) -> None:
        """
        Clear table selection after standard coupling computation.
        """

        @dash.callback(
            dash.Output(self.ids.bead_table, "active_cell"),
            dash.Output(self.ids.bead_table, "selected_cells"),
            dash.Input(self.ids.compute_model_btn, "n_clicks"),
            prevent_initial_call=True,
        )
        def clear_table_selection_after_compute(
            _n_clicks: int,
        ) -> tuple[None, list]:
            logger.debug(
                "Clearing scattering calibration standard table selection after "
                "Compute Standard Coupling."
            )

            return None, []