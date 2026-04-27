# -*- coding: utf-8 -*-

from typing import Any, Optional
import logging

import dash
import numpy as np

from .base import BasePeakWorkflowAdapter


logger = logging.getLogger(__name__)


class FluorescencePeakWorkflowAdapter(BasePeakWorkflowAdapter):
    """
    Adapter for the fluorescence calibration peak workflow.

    Responsibilities
    ----------------
    - Retrieve the page-owned fluorescence backend.
    - Convert automatic or manual peak workflow results into scalar x values.
    - Append scalar x values into the fluorescence calibration table.
    - Clear the measured fluorescence peak column when requested.

    Non responsibilities
    --------------------
    - This adapter does not create backends.
    - This adapter does not store or resolve FCS file paths.
    - This adapter does not read FCS files directly.
    - This adapter does not build histograms.
    - This adapter does not perform peak detection itself.

    The fluorescence page owns the uploaded file context and the backend lifecycle.
    The shared peak workflow only consumes a backend-like object already exposed by
    the page.
    """

    peak_lines_payload_keys: tuple[str, ...] = (
        "fluorescence_peak_lines_payload",
        "peak_lines_payload",
        "peak_lines",
    )

    default_peak_lines_payload_key: str = "fluorescence_peak_lines_payload"

    fluorescence_intensity_column_name: str = "col2"

    fluorescence_intensity_column_candidates: tuple[str, ...] = (
        "col2",
        "Intensity",
        "intensity",
        "Fluorescence intensity",
        "fluorescence_intensity",
        "Measured fluorescence",
        "measured_fluorescence",
        "Peak position",
        "peak_position",
        "Peak",
        "peak",
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

    def get_backend(self, uploaded_fcs_path: Any = None) -> Any:
        """
        Return the page-owned backend compatible with the shared peak workflow.

        ``uploaded_fcs_path`` is accepted only for interface compatibility with
        ``BasePeakWorkflowAdapter``. It is intentionally not used here.
        """
        from RosettaX.pages.p02_fluorescence.backend import BackEnd

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
        Append x axis peak values to the fluorescence calibration table.

        Manual graph clicks append exactly one scalar x value. Automatic peak
        detection appends one scalar x value for every detected peak.
        """
        del context

        if getattr(
            result,
            "clear_existing_table_peaks",
            False,
        ):
            return self.clear_fluorescence_peak_column(
                table_data=table_data,
            )

        x_values_to_append = self.extract_x_values_to_append(
            result=result,
        )

        if not x_values_to_append:
            logger.debug(
                "Fluorescence peak process produced no x values to append."
            )

            return dash.no_update

        logger.debug(
            "Appending fluorescence peak x values to table: count=%d values=%r",
            len(x_values_to_append),
            x_values_to_append,
        )

        return self.append_x_values_to_fluorescence_table(
            table_data=table_data,
            x_values=x_values_to_append,
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

        Examples
        --------
        ``{"x": 12.3, "y": 45.6}`` becomes ``[12.3]``.

        ``[{"x": 1, "y": 2}, {"x": 3, "y": 4}]`` becomes ``[1, 3]``.

        ``np.array([1, 2, 3])`` becomes ``[1, 2, 3]``.
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

    def append_x_values_to_fluorescence_table(
        self,
        *,
        table_data: Optional[list[dict[str, Any]]],
        x_values: list[Any],
    ) -> list[dict[str, Any]]:
        """
        Append x values to the next empty fluorescence table rows.

        Existing filled rows are preserved. New rows are created when there is no
        empty fluorescence intensity cell left.
        """
        rows = self.normalize_table_data(
            table_data=table_data,
        )

        if not rows:
            rows = [
                self.build_empty_fluorescence_table_row(),
            ]

        target_column_name = self.find_first_existing_column_name(
            table_data=rows,
            candidate_column_names=self.fluorescence_intensity_column_candidates,
        )

        if target_column_name is None:
            target_column_name = self.fluorescence_intensity_column_name

        for x_value in x_values:
            normalized_x_value = self.normalize_single_x_value_for_table(
                value=x_value,
            )

            if normalized_x_value == "":
                continue

            empty_row_index = self.find_first_empty_value_row_index(
                rows=rows,
                column_name=target_column_name,
            )

            if empty_row_index is None:
                rows.append(
                    self.build_empty_fluorescence_table_row(),
                )
                empty_row_index = len(rows) - 1

            rows[empty_row_index][target_column_name] = normalized_x_value

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
        values like ``{"x": ..., "y": ...}`` from being written into the
        fluorescence intensity column.
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
            (str, int, float, bool),
        ):
            return normalized_value

        return str(
            normalized_value,
        )

    def clear_fluorescence_peak_column(
        self,
        *,
        table_data: Optional[list[dict[str, Any]]],
    ) -> Any:
        """
        Clear the fluorescence measured peak column.
        """
        rows = self.normalize_table_data(
            table_data=table_data,
        )

        if not rows:
            return dash.no_update

        target_column_name = self.find_first_existing_column_name(
            table_data=rows,
            candidate_column_names=self.fluorescence_intensity_column_candidates,
        )

        if target_column_name is None:
            target_column_name = self.fluorescence_intensity_column_name

        for row in rows:
            row[target_column_name] = ""

        return self.normalize_table_data(
            table_data=rows,
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

            if isinstance(
                value,
                str,
            ) and not value.strip():
                return row_index

        return None

    def build_empty_fluorescence_table_row(self) -> dict[str, str]:
        """
        Build an empty fluorescence calibration table row.
        """
        return {
            "col1": "",
            "col2": "",
        }