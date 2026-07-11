# -*- coding: utf-8 -*-

import logging
from typing import Any, Optional

import dash
import numpy as np

from RosettaX.workflow.parameters.refractive_index import (
    format_refractive_index_display,
    resolve_refractive_index_source_value,
)

from .base import BasePeakWorkflowAdapter

logger = logging.getLogger(__name__)


class ScatteringPeakWorkflowAdapter(BasePeakWorkflowAdapter):
    """
    Adapter for the scattering calibration peak workflow.

    Responsibilities
    ----------------
    - Retrieve the page-owned scattering backend.
    - Convert automatic or manual peak workflow results into scalar x values.
    - Append scalar x values into the scattering calibration table.
    - Clear the measured peak column when requested.

    Non responsibilities
    --------------------
    - This adapter does not create backends.
    - This adapter does not store or resolve FCS file paths.
    - This adapter does not read FCS files directly.
    - This adapter does not perform peak detection itself.

    The scattering page owns the uploaded file context and the backend lifecycle.
    The shared peak workflow only consumes a backend-like object already exposed by
    the page.
    """

    peak_lines_payload_keys: tuple[str, ...] = (
        "scattering_peak_lines_payload",
        "peak_lines_payload",
        "peak_lines",
    )

    default_peak_lines_payload_key: str = "scattering_peak_lines_payload"
    peak_table_sort_order_runtime_config_path: str = (
        "scattering_calibration.peak_table_sort_order"
    )

    scattering_peak_column_name: str = "measured_peak_position"

    scattering_peak_column_candidates: tuple[str, ...] = (
        "measured_peak_position",
        "Measured scatter",
        "measured_scatter",
        "Scattering intensity",
        "scattering_intensity",
        "Intensity",
        "intensity",
        "Peak position",
        "peak_position",
        "Peak",
        "peak",
    )

    mie_model_column_candidates: tuple[str, ...] = (
        "mie_model",
        "Mie model",
        "Model",
        "model",
    )

    automatic_peak_position_names: tuple[str, ...] = (
        "new_peak_positions",
        "new_x_positions",
        "detected_peak_positions",
        "automatic_peak_positions",
        "peak_positions",
        "x_positions",
        "x_values",
    )

    manual_peak_position_names: tuple[str, ...] = (
        "clicked_x",
        "clicked_x_position",
        "clicked_point",
        "new_point",
        "manual_x",
        "manual_x_position",
    )

    scattering_geometry_column_names: tuple[str, ...] = (
        "particle_diameter_nm",
        "core_diameter_nm",
        "shell_thickness_nm",
        "outer_diameter_nm",
    )

    def get_backend(self, uploaded_fcs_path: Any = None) -> Any:
        """
        Return the page-owned backend compatible with the shared peak workflow.

        ``uploaded_fcs_path`` is accepted only for interface compatibility with
        ``BasePeakWorkflowAdapter``. It is intentionally not used here.
        """
        from RosettaX.pages.p03_scattering.backend import BackEnd

        backend = BackEnd()
        backend.fcs_file_path = uploaded_fcs_path
        return backend

    def apply_peak_process_result_to_table(
        self,
        *,
        table_data: Optional[list[dict[str, Any]]],
        result: Any,
        context: dict[str, Any],
        logger: logging.Logger,
    ) -> Any:
        """
        Append x axis peak values to the scattering calibration table.

        Manual graph clicks append exactly one scalar x value. Automatic peak
        detection appends one scalar x value per detected peak.
        """
        mie_model = resolve_mie_model(
            context.get("mie_model"),
        )

        if getattr(
            result,
            "clear_existing_table_peaks",
            False,
        ):
            return self.clear_scattering_peak_column(
                table_data=table_data,
                mie_model=mie_model,
            )

        should_replace_existing_table_peaks = bool(
            context.get("replace_existing_table_peaks")
        )

        working_table_data = table_data

        if should_replace_existing_table_peaks:
            working_table_data = self.clear_scattering_peak_column(
                table_data=table_data,
                mie_model=mie_model,
            )

        table_prefill_rows = self.extract_table_prefill_rows_from_result(
            result=result,
        )

        if table_prefill_rows:
            logger.debug(
                "Applying scattering script table prefill rows: count=%d",
                len(table_prefill_rows),
            )

            prefilled_rows = self.apply_table_prefill_rows(
                table_data=working_table_data,
                table_prefill_rows=table_prefill_rows,
                mie_model=mie_model,
            )
            return fill_missing_refractive_indices(
                rows=prefilled_rows,
                mie_model=mie_model,
                runtime_config_data=context.get("runtime_config_data"),
                process_name=context.get("process_name"),
            )

        x_values_to_append = self.extract_x_values_to_append(
            result=result,
        )

        if not x_values_to_append:
            logger.debug("Scattering peak process produced no x values to append.")

            if should_replace_existing_table_peaks:
                return working_table_data

            return dash.no_update

        logger.debug(
            "Appending scattering peak x values to table: count=%d values=%r",
            len(x_values_to_append),
            x_values_to_append,
        )

        peak_table_sort_order = self.resolve_peak_table_sort_order(
            context=context,
        )

        appended_rows = self.append_x_values_to_scattering_table(
            table_data=working_table_data,
            x_values=x_values_to_append,
            mie_model=mie_model,
            descending=peak_table_sort_order == "descending",
        )
        return fill_missing_refractive_indices(
            rows=appended_rows,
            mie_model=mie_model,
            runtime_config_data=context.get("runtime_config_data"),
            process_name=context.get("process_name"),
        )

    def extract_x_values_to_append(
        self,
        *,
        result: Any,
    ) -> list[Any]:
        """
        Extract x values to append to the table.

        Priority
        --------
        1. Automatic peak arrays, keeping all detected peak values.
        2. Manual click values, keeping only the latest click.
        3. Peak line payload arrays, keeping all available values.
        """
        if result is None:
            return []

        automatic_value = self.extract_first_existing_attribute_or_key(
            source=result,
            names=self.automatic_peak_position_names,
        )

        if automatic_value is not None:
            return self.extract_x_scalars_from_any_value(
                value=automatic_value,
                keep_only_latest=False,
            )

        manual_value = self.extract_first_existing_attribute_or_key(
            source=result,
            names=self.manual_peak_position_names,
        )

        if manual_value is not None:
            return self.extract_x_scalars_from_any_value(
                value=manual_value,
                keep_only_latest=True,
            )

        peak_lines_payload = getattr(
            result,
            "peak_lines_payload",
            None,
        )

        if peak_lines_payload is None and isinstance(
            result,
            dict,
        ):
            peak_lines_payload = result.get(
                "peak_lines_payload",
            )

        if isinstance(
            peak_lines_payload,
            dict,
        ):
            x_values = self.extract_x_values_from_peak_lines_payload(
                peak_lines_payload=peak_lines_payload,
                keep_only_latest=False,
            )

            if x_values:
                return x_values

        return []

    def extract_first_existing_attribute_or_key(
        self,
        *,
        source: Any,
        names: tuple[str, ...],
    ) -> Any:
        """
        Return the first non None value found as an attribute or dictionary key.
        """
        for name in names:
            value = getattr(
                source,
                name,
                None,
            )

            if value is not None:
                return value

        if isinstance(
            source,
            dict,
        ):
            for name in names:
                value = source.get(
                    name,
                    None,
                )

                if value is not None:
                    return value

        return None

    def extract_x_scalars_from_any_value(
        self,
        *,
        value: Any,
        keep_only_latest: bool,
    ) -> list[Any]:
        """
        Extract only scalar x values from an arbitrary payload.
        """
        raw_x_values = self.collect_raw_x_values(
            value=value,
        )

        normalized_x_values = [
            self.normalize_single_x_value_for_table(
                value=raw_x_value,
            )
            for raw_x_value in raw_x_values
        ]

        normalized_x_values = [
            normalized_x_value
            for normalized_x_value in normalized_x_values
            if normalized_x_value != ""
        ]

        if keep_only_latest and normalized_x_values:
            return [
                normalized_x_values[-1],
            ]

        return normalized_x_values

    def collect_raw_x_values(
        self,
        *,
        value: Any,
    ) -> list[Any]:
        """
        Collect raw x values from nested values without normalizing them.
        """
        if value is None:
            return []

        if isinstance(
            value,
            dict,
        ):
            for key in (
                "x",
                "clicked_x",
                "clicked_x_position",
                "x_position",
                "position",
                "value",
                "peak_position",
            ):
                if key in value:
                    return [
                        value[key],
                    ]

            for key in self.automatic_peak_position_names:
                if key in value:
                    return self.collect_raw_x_values(
                        value=value[key],
                    )

            return []

        if isinstance(
            value,
            np.ndarray,
        ):
            if value.ndim == 0:
                return [
                    value.item(),
                ]

            raw_x_values: list[Any] = []

            for item in value.reshape(
                -1,
            ).tolist():
                raw_x_values.extend(
                    self.collect_raw_x_values(
                        value=item,
                    )
                )

            return raw_x_values

        if isinstance(
            value,
            np.generic,
        ):
            return [
                value.item(),
            ]

        if isinstance(
            value,
            (list, tuple),
        ):
            raw_x_values = []

            for item in value:
                raw_x_values.extend(
                    self.collect_raw_x_values(
                        value=item,
                    )
                )

            return raw_x_values

        return [
            value,
        ]

    def extract_x_values_from_peak_lines_payload(
        self,
        *,
        peak_lines_payload: dict[str, Any],
        keep_only_latest: bool,
    ) -> list[Any]:
        """
        Extract x values from a peak line payload.
        """
        candidate_values: list[Any] = []

        points = peak_lines_payload.get(
            "points",
        )

        if isinstance(
            points,
            list,
        ):
            candidate_values.extend(
                points,
            )

        for key in (
            "new_peak_positions",
            "new_x_positions",
            "x_positions",
            "positions",
            "peak_positions",
            "x_values",
            "values",
        ):
            if key not in peak_lines_payload:
                continue

            candidate_values.append(
                peak_lines_payload.get(
                    key,
                )
            )

        if not candidate_values:
            return []

        return self.extract_x_scalars_from_any_value(
            value=candidate_values,
            keep_only_latest=keep_only_latest,
        )

    def extract_latest_x_value_from_peak_lines_payload(
        self,
        *,
        peak_lines_payload: dict[str, Any],
    ) -> Any:
        """
        Extract only the latest x value from a peak line payload.
        """
        x_values = self.extract_x_values_from_peak_lines_payload(
            peak_lines_payload=peak_lines_payload,
            keep_only_latest=True,
        )

        if x_values:
            return x_values[-1]

        return None

    def extract_single_x_value_from_mapping(
        self,
        *,
        mapping: dict[str, Any],
    ) -> Any:
        """
        Extract one x value from a dictionary.
        """
        for key in (
            "x",
            "clicked_x",
            "clicked_x_position",
            "x_position",
            "position",
            "value",
            "peak_position",
        ):
            if key in mapping:
                return mapping[key]

        return None

    def append_x_values_to_scattering_table(
        self,
        *,
        table_data: Optional[list[dict[str, Any]]],
        x_values: list[Any],
        mie_model: str,
        descending: bool,
    ) -> list[dict[str, Any]]:
        """
        Append x values to the next empty scattering table rows.

        Existing filled rows are preserved. New rows are created when there is no
        empty ``measured_peak_position`` cell left.
        """
        rows = self.normalize_table_data(
            table_data=table_data,
        )

        if not rows:
            rows = [
                build_empty_table_row(
                    mie_model=mie_model,
                ),
            ]

        target_column_name = self.find_first_existing_column_name(
            table_data=rows,
            candidate_column_names=self.scattering_peak_column_candidates,
        )

        if target_column_name is None:
            target_column_name = self.scattering_peak_column_name

        normalized_x_values = [
            self.normalize_single_x_value_for_table(
                value=x_value,
            )
            for x_value in x_values
        ]

        normalized_x_values = self.sort_peak_table_values(
            values=normalized_x_values,
            descending=descending,
        )

        for normalized_x_value in normalized_x_values:
            empty_row_index = self.find_first_empty_value_row_index(
                rows=rows,
                column_name=target_column_name,
            )

            if empty_row_index is None:
                rows.append(
                    build_empty_table_row(
                        mie_model=mie_model,
                    )
                )
                empty_row_index = len(rows) - 1

            rows[empty_row_index][target_column_name] = normalized_x_value

            self.ensure_row_matches_mie_model(
                row=rows[empty_row_index],
                mie_model=mie_model,
            )

        return self.normalize_table_data(
            table_data=rows,
        )

    def normalize_single_x_value_for_table(
        self,
        *,
        value: Any,
    ) -> Any:
        """
        Convert one x value to a Dash DataTable scalar.

        Dictionaries are explicitly reduced to their x component. This prevents
        values like {"x": ..., "y": ...} from being written into
        ``measured_peak_position``.
        """
        if isinstance(
            value,
            dict,
        ):
            extracted_x_value = self.extract_single_x_value_from_mapping(
                mapping=value,
            )

            if extracted_x_value is None:
                return ""

            return self.normalize_single_x_value_for_table(
                value=extracted_x_value,
            )

        if isinstance(
            value,
            np.ndarray,
        ):
            if value.ndim == 0:
                return self.normalize_single_x_value_for_table(
                    value=value.item(),
                )

            if value.size == 1:
                return self.normalize_single_x_value_for_table(
                    value=value.reshape(
                        -1,
                    )[0],
                )

            return ""

        if isinstance(
            value,
            np.generic,
        ):
            return self.normalize_single_x_value_for_table(
                value=value.item(),
            )

        if isinstance(
            value,
            (list, tuple),
        ):
            if not value:
                return ""

            return self.normalize_single_x_value_for_table(
                value=value[-1],
            )

        normalized_value = self.normalize_datatable_value(
            value=value,
        )

        if isinstance(
            normalized_value,
            bool,
        ):
            return normalized_value

        if isinstance(normalized_value, (int, float)):
            return round(float(normalized_value), 1)

        if isinstance(normalized_value, str):
            try:
                return round(float(normalized_value.strip()), 1)
            except ValueError:
                return normalized_value

        return str(
            normalized_value,
        )

    def clear_scattering_peak_column(
        self,
        *,
        table_data: Optional[list[dict[str, Any]]],
        mie_model: str,
    ) -> list[dict[str, Any]]:
        """
        Clear the scattering measured peak column.
        """
        rows = self.normalize_table_data(
            table_data=table_data,
        )

        if not rows:
            rows = [
                build_empty_table_row(
                    mie_model=mie_model,
                )
                for _ in range(3)
            ]

        target_column_name = self.find_first_existing_column_name(
            table_data=rows,
            candidate_column_names=self.scattering_peak_column_candidates,
        )

        if target_column_name is None:
            target_column_name = self.scattering_peak_column_name

        for row in rows:
            row[target_column_name] = ""

            self.ensure_row_matches_mie_model(
                row=row,
                mie_model=mie_model,
            )

        return ensure_minimum_row_count(
            rows=self.normalize_table_data(
                table_data=rows,
            ),
            mie_model=mie_model,
            minimum_row_count=3,
        )

    def ensure_row_matches_mie_model(
        self,
        *,
        row: dict[str, Any],
        mie_model: str,
    ) -> None:
        """
        Ensure a row contains the columns expected by the selected Mie model.
        """
        template_row = build_empty_table_row(
            mie_model=mie_model,
        )

        for key, value in template_row.items():
            row.setdefault(
                key,
                value,
            )

    def find_first_empty_value_row_index(
        self,
        *,
        rows: list[dict[str, Any]],
        column_name: str,
    ) -> Optional[int]:
        """
        Return the first row where the target column is empty.
        """
        for row_index, row in enumerate(
            rows,
        ):
            value = row.get(
                column_name,
                "",
            )

            if value is None:
                return row_index

            if (
                isinstance(
                    value,
                    str,
                )
                and not value.strip()
            ):
                return row_index

        return None

    def apply_table_prefill_rows(
        self,
        *,
        table_data: Optional[list[dict[str, Any]]],
        table_prefill_rows: list[dict[str, Any]],
        mie_model: str,
    ) -> list[dict[str, Any]]:
        """
        Merge semantic script-provided rows into the scattering table.
        """
        rows = self.normalize_table_data(
            table_data=table_data,
        )

        while len(rows) < len(table_prefill_rows):
            rows.append(
                build_empty_table_row(
                    mie_model=mie_model,
                )
            )

        for row_index, semantic_row in enumerate(table_prefill_rows):
            merged_row = dict(
                rows[row_index] if row_index < len(rows) else build_empty_table_row(mie_model=mie_model),
            )

            geometry_was_updated = False

            if "measured_peak_position" in semantic_row:
                merged_row[self.scattering_peak_column_name] = self.normalize_single_x_value_for_table(
                    value=semantic_row.get("measured_peak_position"),
                )

            for column_name in self.scattering_geometry_column_names:
                if column_name not in semantic_row:
                    continue

                merged_row[column_name] = self.normalize_datatable_value(
                    value=semantic_row.get(column_name),
                )
                geometry_was_updated = True

            if "particle_refractive_index" in semantic_row:
                merged_row["particle_refractive_index"] = self.normalize_datatable_value(
                    value=semantic_row.get("particle_refractive_index"),
                )

            if "medium_refractive_index" in semantic_row:
                merged_row["medium_refractive_index"] = self.normalize_datatable_value(
                    value=semantic_row.get("medium_refractive_index"),
                )

            for refractive_index_column in (
                "core_refractive_index",
                "shell_refractive_index",
            ):
                if refractive_index_column in semantic_row:
                    merged_row[refractive_index_column] = self.normalize_datatable_value(
                        value=semantic_row.get(refractive_index_column),
                    )

            self.ensure_row_matches_mie_model(
                row=merged_row,
                mie_model=mie_model,
            )

            if geometry_was_updated and mie_model == "Core/Shell Sphere":
                merged_row["outer_diameter_nm"] = build_outer_diameter_value(
                    core_diameter_nm=merged_row.get("core_diameter_nm"),
                    shell_thickness_nm=merged_row.get("shell_thickness_nm"),
                )

            if geometry_was_updated:
                merged_row["expected_coupling"] = ""
                merged_row["expected_cross_section_nm2"] = ""

            rows[row_index] = merged_row

        return ensure_minimum_row_count(
            rows=self.normalize_table_data(
                table_data=rows,
            ),
            mie_model=mie_model,
            minimum_row_count=3,
        )


def fill_missing_refractive_indices(
    *,
    rows: list[dict[str, Any]],
    mie_model: str,
    runtime_config_data: Any,
    process_name: Any = None,
) -> list[dict[str, Any]]:
    """Fill blank particle and medium refractive-index cells from runtime optics."""
    if not isinstance(runtime_config_data, dict):
        return rows

    particle_model = runtime_config_data.get("particle_model", {})
    optics = runtime_config_data.get("optics", {})

    if not isinstance(particle_model, dict) or not isinstance(optics, dict):
        return rows

    resolved_rows = [dict(row) for row in rows]
    wavelength_nm = optics.get("wavelength_nm", 488.0)
    force_rosetta_materials = str(process_name or "").strip().startswith(
        "Rosetta Script"
    )
    refractive_index_specs = [
        (
            "medium_refractive_index",
            optics.get("medium_refractive_index_source"),
            optics.get("medium_refractive_index"),
        ),
    ]

    if force_rosetta_materials:
        refractive_index_specs = [
            ("medium_refractive_index", "water", 1.333),
        ]

    if mie_model == "Solid Sphere":
        refractive_index_specs.append(
            (
                "particle_refractive_index",
                (
                    "polystyrene"
                    if force_rosetta_materials
                    else particle_model.get("particle_refractive_index_source")
                ),
                (
                    1.59
                    if force_rosetta_materials
                    else particle_model.get("particle_refractive_index")
                ),
            )
        )
    elif mie_model == "Core/Shell Sphere":
        refractive_index_specs.extend(
            [
                (
                    "core_refractive_index",
                    particle_model.get("core_refractive_index_source"),
                    particle_model.get("core_refractive_index"),
                ),
                (
                    "shell_refractive_index",
                    particle_model.get("shell_refractive_index_source"),
                    particle_model.get("shell_refractive_index"),
                ),
            ]
        )

    for column_name, source_value, fallback_value in refractive_index_specs:
        if fallback_value in (None, ""):
            continue

        try:
            refractive_index = resolve_refractive_index_source_value(
                source_value,
                wavelength_nm=wavelength_nm,
                fallback_value=fallback_value,
            )
        except (TypeError, ValueError):
            continue

        formatted_value = format_refractive_index_display(
            refractive_index,
            source_value=source_value,
        )

        for row in resolved_rows:
            if force_rosetta_materials or row.get(column_name) in (None, ""):
                row[column_name] = formatted_value

    return resolved_rows


def resolve_mie_model(
    mie_model: Any,
) -> str:
    """
    Resolve the Mie model name used by the scattering reference table.
    """
    mie_model_string = str(
        mie_model or "",
    ).strip()

    if mie_model_string == "Core/Shell Sphere":
        return "Core/Shell Sphere"

    return "Solid Sphere"


def build_empty_table_row(
    *,
    mie_model: str,
) -> dict[str, str]:
    """
    Build an empty scattering calibration table row.
    """
    if mie_model == "Core/Shell Sphere":
        return {
            "core_diameter_nm": "",
            "shell_thickness_nm": "",
            "outer_diameter_nm": "",
            "measured_peak_position": "",
            "expected_coupling": "",
            "expected_cross_section_nm2": "",
        }

    return {
        "particle_diameter_nm": "",
        "measured_peak_position": "",
        "expected_coupling": "",
        "expected_cross_section_nm2": "",
    }


def ensure_minimum_row_count(
    *,
    rows: list[dict[str, Any]],
    mie_model: str,
    minimum_row_count: int,
) -> list[dict[str, Any]]:
    """
    Ensure a minimum number of table rows.
    """
    next_rows = [dict(row) for row in rows]

    while len(next_rows) < int(
        minimum_row_count,
    ):
        next_rows.append(
            build_empty_table_row(
                mie_model=mie_model,
            )
        )

    return next_rows


def build_outer_diameter_value(
    *,
    core_diameter_nm: Any,
    shell_thickness_nm: Any,
) -> Any:
    """
    Build the derived outer diameter value for a core-shell row.
    """
    try:
        resolved_core_diameter_nm = float(
            core_diameter_nm,
        )
        resolved_shell_thickness_nm = float(
            shell_thickness_nm,
        )
    except (TypeError, ValueError):
        return ""

    if resolved_core_diameter_nm <= 0.0:
        return ""

    if resolved_shell_thickness_nm < 0.0:
        return ""

    return float(
        resolved_core_diameter_nm + 2.0 * resolved_shell_thickness_nm,
    )
