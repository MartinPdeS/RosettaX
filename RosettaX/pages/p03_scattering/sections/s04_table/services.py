# -*- coding: utf-8 -*-

import logging
from typing import Any, Optional

from RosettaX.utils import RuntimeConfig
from RosettaX.workflow import table, parameters, calibration

logger = logging.getLogger(__name__)


class ScatteringCalibrationStandardTable:
    """
    Helpers for the scattering calibration standard table section.
    """

    sphere_table_columns = parameters.table.sphere_table_columns
    core_shell_table_columns = parameters.table.core_shell_table_columns

    @classmethod
    def build_state_from_runtime_config(
        cls,
        *,
        runtime_config: RuntimeConfig,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """
        Build scattering calibration standard table columns and rows from runtime configuration.
        """
        resolved_mie_model = parameters.table.resolve_mie_model(
            runtime_config.get_str(
                "particle_model.mie_model",
                default=parameters.table.MIE_MODEL_SOLID_SPHERE,
            )
        )

        columns = parameters.table.get_table_columns_for_model(
            resolved_mie_model,
        )

        rows = parameters.table.populate_table_from_runtime_defaults(
            mie_model=resolved_mie_model,
            runtime_particle_diameters_nm=runtime_config.get_path(
                "particle_model.particle_diameter_nm",
                default=[],
            ),
            runtime_core_diameters_nm=runtime_config.get_path(
                "particle_model.core_diameter_nm",
                default=[],
            ),
            runtime_shell_thicknesses_nm=runtime_config.get_path(
                "particle_model.shell_thickness_nm",
                default=[],
            ),
        )

        if not rows:
            rows = parameters.table.build_empty_rows_for_model(
                resolved_mie_model,
                row_count=3,
            )

        logger.debug(
            "Built scattering calibration standard table state from runtime config. resolved_mie_model=%r columns=%r rows=%r",
            resolved_mie_model,
            columns,
            rows,
        )

        return columns, rows

    @classmethod
    def get_columns_for_model(
        cls,
        mie_model: Any,
    ) -> list[dict[str, Any]]:
        """
        Return scattering calibration standard table columns for a Mie model.
        """
        return parameters.table.get_table_columns_for_model(
            mie_model,
        )

    @classmethod
    def get_user_data_column_ids_for_model(
        cls,
        mie_model: Any,
    ) -> list[str]:
        """
        Return table columns that should count as user data for a Mie model.
        """
        resolved_mie_model = parameters.table.resolve_mie_model(
            mie_model,
        )

        return table.services.get_column_ids(
            columns=parameters.table.get_table_columns_for_model(
                resolved_mie_model,
            ),
        )

    @classmethod
    def normalize_rows(
        cls,
        *,
        mie_model: Any,
        rows: Optional[list[dict[str, Any]]],
    ) -> list[dict[str, Any]]:
        """
        Normalize scattering table rows for a Mie model.
        """
        return parameters.table.normalize_table_rows(
            mie_model=parameters.table.resolve_mie_model(
                mie_model,
            ),
            current_rows=rows,
        )

    @classmethod
    def table_is_effectively_empty(
        cls,
        *,
        mie_model: Any,
        rows: Optional[list[dict[str, Any]]],
    ) -> bool:
        """
        Return whether the scattering calibration standard table has no useful data.
        """
        resolved_mie_model = parameters.table.resolve_mie_model(
            mie_model,
        )

        return table.services.table_is_effectively_empty(
            rows=cls.normalize_rows(
                mie_model=resolved_mie_model,
                rows=rows,
            ),
            user_data_column_ids=cls.get_user_data_column_ids_for_model(
                resolved_mie_model,
            ),
        )

    @classmethod
    def should_rebuild_from_runtime_config(
        cls,
        *,
        mie_model: Any,
        profile_load_event_data: Any,
        current_rows: Optional[list[dict[str, Any]]],
    ) -> bool:
        """
        Decide whether a runtime configuration update should overwrite the table.
        """
        resolved_mie_model = parameters.table.resolve_mie_model(
            mie_model,
        )

        return table.services.should_rebuild_table_from_runtime_config(
            profile_load_was_requested=table.services.profile_load_was_requested(
                profile_load_event_data=profile_load_event_data,
            ),
            current_rows=cls.normalize_rows(
                mie_model=resolved_mie_model,
                rows=current_rows,
            ),
            user_data_column_ids=cls.get_user_data_column_ids_for_model(
                resolved_mie_model,
            ),
        )

    @classmethod
    def remap_rows_to_model(
        cls,
        *,
        mie_model: Any,
        current_rows: Optional[list[dict[str, Any]]],
    ) -> list[dict[str, str]]:
        """
        Remap current table rows to a Mie model schema.
        """
        return parameters.table.remap_table_rows_to_model(
            mie_model=parameters.table.resolve_mie_model(
                mie_model,
            ),
            current_rows=current_rows,
        )

    @classmethod
    def add_empty_row(
        cls,
        *,
        mie_model: Any,
        rows: Optional[list[dict[str, Any]]],
    ) -> list[dict[str, Any]]:
        """
        Add one empty scattering calibration standard row.
        """
        resolved_mie_model = parameters.table.resolve_mie_model(
            mie_model,
        )

        return table.services.append_empty_row(
            rows=rows,
            empty_row=parameters.table.build_empty_row_for_model(
                resolved_mie_model,
            ),
        )

    @classmethod
    def reset_rows_for_model(
        cls,
        *,
        mie_model: Any,
        row_count: int = 3,
    ) -> list[dict[str, str]]:
        """
        Reset the scattering calibration standard table.
        """
        return parameters.table.build_empty_rows_for_model(
            parameters.table.resolve_mie_model(
                mie_model,
            ),
            row_count=row_count,
        )

    @classmethod
    def clear_measured_peak_positions(
        cls,
        *,
        rows: Optional[list[dict[str, Any]]],
    ) -> list[dict[str, Any]]:
        """
        Clear measured peak positions.
        """
        return table.services.clear_columns(
            rows=rows,
            column_ids=[
                parameters.table.COLUMN_MEASURED_PEAK_POSITION,
            ],
        )

    @classmethod
    def clear_expected_coupling(
        cls,
        *,
        rows: Optional[list[dict[str, Any]]],
    ) -> list[dict[str, Any]]:
        """
        Clear expected coupling values.
        """
        return table.services.clear_columns(
            rows=rows,
            column_ids=[
                parameters.table.COLUMN_EXPECTED_COUPLING,
            ],
        )

    @classmethod
    def build_parameters_payload(
        cls,
        *,
        mie_model: Any,
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
    ) -> dict[str, Any]:
        """
        Build the serializable calibration standard Mie parameter payload.
        """
        resolved_mie_model = parameters.table.resolve_mie_model(
            mie_model,
        )

        return calibration.mie_relation.build_mie_parameter_payload(
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

    @classmethod
    def compute_model_for_rows(
        cls,
        *,
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
        logger: logging.Logger,
    ) -> list[dict[str, str]]:
        """
        Compute modeled coupling values for the scattering calibration standard rows.
        """
        resolved_mie_model = parameters.table.resolve_mie_model(
            mie_model,
        )

        if not current_rows:
            return parameters.table.build_empty_rows_for_model(
                resolved_mie_model,
                row_count=3,
            )

        return parameters.services.compute_model_for_rows(
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


sphere_table_columns = ScatteringCalibrationStandardTable.sphere_table_columns
core_shell_table_columns = ScatteringCalibrationStandardTable.core_shell_table_columns


def build_table_state_from_runtime_config(
    *,
    runtime_config: RuntimeConfig,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Compatibility wrapper.
    """
    return ScatteringCalibrationStandardTable.build_state_from_runtime_config(
        runtime_config=runtime_config,
    )


def get_user_data_column_ids_for_model(
    mie_model: Any,
) -> list[str]:
    """
    Compatibility wrapper.
    """
    return ScatteringCalibrationStandardTable.get_user_data_column_ids_for_model(
        mie_model,
    )


def should_rebuild_table_from_runtime_config(
    *,
    mie_model: Any,
    profile_load_event_data: Any,
    current_rows: Optional[list[dict[str, Any]]],
) -> bool:
    """
    Compatibility wrapper.
    """
    return ScatteringCalibrationStandardTable.should_rebuild_from_runtime_config(
        mie_model=mie_model,
        profile_load_event_data=profile_load_event_data,
        current_rows=current_rows,
    )


def table_is_effectively_empty(
    *,
    mie_model: Any,
    rows: Optional[list[dict[str, Any]]],
) -> bool:
    """
    Compatibility wrapper.
    """
    return ScatteringCalibrationStandardTable.table_is_effectively_empty(
        mie_model=mie_model,
        rows=rows,
    )


def add_empty_row_for_model(
    *,
    mie_model: Any,
    rows: Optional[list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """
    Compatibility wrapper.
    """
    return ScatteringCalibrationStandardTable.add_empty_row(
        mie_model=mie_model,
        rows=rows,
    )


def compute_model_for_rows(
    *,
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
    logger: logging.Logger,
) -> list[dict[str, str]]:
    """
    Compatibility wrapper.
    """
    return ScatteringCalibrationStandardTable.compute_model_for_rows(
        mie_model=mie_model,
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


def build_scattering_parameters_payload(
    *,
    mie_model: Any,
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
) -> dict[str, Any]:
    """
    Compatibility wrapper.
    """
    return ScatteringCalibrationStandardTable.build_parameters_payload(
        mie_model=mie_model,
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


def build_section(*args, **kwargs):
    """
    Build the scattering s04_table section instance.
    """
    from .main import ReferenceTable

    return ReferenceTable(*args, **kwargs)
