# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any, Optional
import logging

import dash
import numpy as np


@dataclass
class PeakWorkflowPageState:
    """
    Small dictionary backed page state wrapper used by the peak workflow
    adapters.

    The callback layer expects page state objects to expose ``to_dict``. This
    wrapper keeps that contract while avoiding a hard dependency on page
    specific state classes.
    """

    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """
        Return the serializable page state payload.
        """
        return dict(self.payload)


class BasePeakWorkflowAdapter:
    """
    Base adapter for page specific peak workflow behavior.

    This class owns common page state helpers and small DataTable utilities.
    Subclasses still decide which table column receives peak positions.
    """

    uploaded_fcs_path_keys: tuple[str, ...] = (
        "uploaded_fcs_path",
        "uploaded_fcs_file_path",
        "fcs_path",
    )

    peak_lines_payload_keys: tuple[str, ...] = (
        "peak_lines_payload",
        "peak_lines",
        "fluorescence_peak_lines_payload",
        "scattering_peak_lines_payload",
    )

    default_peak_lines_payload_key: str = "peak_lines_payload"

    delta_peak_value_names: tuple[str, ...] = (
        "new_peak_positions",
        "new_x_positions",
        "detected_peak_positions",
        "automatic_peak_positions",
    )

    manual_peak_value_names: tuple[str, ...] = (
        "clicked_x",
        "clicked_x_position",
        "clicked_point",
        "new_point",
        "manual_x",
        "manual_x_position",
    )

    cumulative_peak_value_names: tuple[str, ...] = (
        "peak_values",
        "peak_positions",
        "peaks",
        "x_positions",
        "x_values",
        "values",
    )

    mapping_x_value_keys: tuple[str, ...] = (
        "x",
        "clicked_x",
        "clicked_x_position",
        "x_position",
        "position",
        "value",
        "peak_position",
    )

    def get_page_state_from_payload(
        self,
        page_state_payload: Any,
    ) -> Any:
        """
        Convert the serialized Dash store payload into a page state object.
        """
        if hasattr(page_state_payload, "to_dict"):
            return page_state_payload

        if isinstance(page_state_payload, dict):
            return PeakWorkflowPageState(
                payload=dict(page_state_payload),
            )

        return PeakWorkflowPageState(
            payload={},
        )

    def get_page_state_payload(
        self,
        *,
        page_state: Any,
    ) -> dict[str, Any]:
        """
        Return a mutable dictionary representation of a page state object.
        """
        if isinstance(page_state, PeakWorkflowPageState):
            return dict(page_state.payload)

        if hasattr(page_state, "to_dict"):
            payload = page_state.to_dict()

            if isinstance(payload, dict):
                return dict(payload)

        if isinstance(page_state, dict):
            return dict(page_state)

        return {}

    def build_page_state(
        self,
        *,
        payload: dict[str, Any],
    ) -> PeakWorkflowPageState:
        """
        Build a serializable page state object from a dictionary payload.
        """
        return PeakWorkflowPageState(
            payload=payload,
        )

    def get_uploaded_fcs_path(
        self,
        *,
        page_state: Any,
    ) -> Any:
        """
        Return the uploaded FCS path stored in this page state.
        """
        payload = self.get_page_state_payload(
            page_state=page_state,
        )

        for key in self.uploaded_fcs_path_keys:
            value = payload.get(key)

            if str(value or "").strip():
                return value

        return None

    def get_peak_lines_payload(
        self,
        *,
        page_state: Any,
    ) -> Any:
        """
        Return the current peak lines payload from page state.
        """
        payload = self.get_page_state_payload(
            page_state=page_state,
        )

        for key in self.peak_lines_payload_keys:
            if key in payload:
                return payload.get(key)

        return None

    def update_peak_lines_payload(
        self,
        *,
        page_state: Any,
        peak_lines_payload: Any,
    ) -> Any:
        """
        Store the current peak lines payload in page state.
        """
        payload = self.get_page_state_payload(
            page_state=page_state,
        )

        payload[self.default_peak_lines_payload_key] = peak_lines_payload

        return self.build_page_state(
            payload=payload,
        )

    def clear_peak_lines_payload(
        self,
        *,
        page_state: Any,
    ) -> Any:
        """
        Remove all known peak line payload fields from page state.
        """
        payload = self.get_page_state_payload(
            page_state=page_state,
        )

        for key in self.peak_lines_payload_keys:
            payload.pop(key, None)

        payload[self.default_peak_lines_payload_key] = None

        return self.build_page_state(
            payload=payload,
        )

    def get_backend(
        self,
        *,
        page: Any,
        uploaded_fcs_path: Any,
    ) -> Any:
        """
        Return a backend instance for the page.
        """
        if hasattr(page, "get_backend"):
            return page.get_backend(
                uploaded_fcs_path=uploaded_fcs_path,
            )

        backend = getattr(
            page,
            "backend",
            None,
        )

        if backend is not None:
            return backend

        return None

    def apply_peak_process_result_to_table(
        self,
        *,
        table_data: Optional[list[dict[str, Any]]],
        result: Any,
        context: dict[str, Any],
        logger: logging.Logger,
    ) -> Any:
        """
        Apply a peak process result to a page table.

        Subclasses must implement this because fluorescence and scattering table
        schemas are different.
        """
        raise NotImplementedError

    def extract_peak_values_from_result(
        self,
        *,
        result: Any,
    ) -> list[Any]:
        """
        Extract peak values from common result payload shapes.

        Delta fields are preferred over cumulative fields. This prevents manual
        2D clicks from appending all previously clicked points again.
        """
        if result is None:
            return []

        delta_value = self.get_first_attribute_or_key(
            source=result,
            names=self.delta_peak_value_names,
        )

        if delta_value is not None:
            return self.normalize_datatable_values(
                value=delta_value,
            )

        manual_value = self.get_first_attribute_or_key(
            source=result,
            names=self.manual_peak_value_names,
        )

        if manual_value is not None:
            values = self.normalize_datatable_values(
                value=manual_value,
            )

            if values:
                return [
                    values[-1],
                ]

            return []

        cumulative_value = self.get_first_attribute_or_key(
            source=result,
            names=self.cumulative_peak_value_names,
        )

        if cumulative_value is not None:
            return self.normalize_datatable_values(
                value=cumulative_value,
            )

        peak_lines_payload = self.get_first_attribute_or_key(
            source=result,
            names=(
                "peak_lines_payload",
            ),
        )

        if peak_lines_payload is not None:
            return self.normalize_datatable_values(
                value=self.extract_peak_values_from_peak_lines_payload(
                    peak_lines_payload=peak_lines_payload,
                ),
            )

        return []

    def get_first_attribute_or_key(
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

        if isinstance(source, dict):
            for name in names:
                value = source.get(name)

                if value is not None:
                    return value

        return None

    def extract_peak_values_from_peak_lines_payload(
        self,
        *,
        peak_lines_payload: Any,
    ) -> list[Any]:
        """
        Extract numeric x positions from common peak line payload shapes.
        """
        if peak_lines_payload is None:
            return []

        if isinstance(peak_lines_payload, dict):
            for key in (
                "new_peak_positions",
                "new_x_positions",
                "detected_peak_positions",
                "automatic_peak_positions",
                "x",
                "xs",
                "values",
                "positions",
                "peak_values",
                "peak_positions",
                "x_positions",
            ):
                value = peak_lines_payload.get(key)

                if value is not None:
                    return self.flatten_datatable_values(
                        value=value,
                    )

            points = peak_lines_payload.get("points")

            if isinstance(points, list):
                values: list[Any] = []

                for point in points:
                    if isinstance(point, dict):
                        extracted_value = self.extract_x_value_from_mapping(
                            mapping=point,
                        )

                        if extracted_value is not None:
                            values.append(extracted_value)

                return values

        if isinstance(peak_lines_payload, list):
            values = []

            for item in peak_lines_payload:
                if isinstance(item, dict):
                    extracted_value = self.extract_x_value_from_mapping(
                        mapping=item,
                    )

                    if extracted_value is not None:
                        values.append(extracted_value)

                else:
                    values.append(item)

            return values

        return []

    def result_has_table_data(
        self,
        *,
        result: Any,
    ) -> bool:
        """
        Return whether the result already contains complete table data.
        """
        if result is None:
            return False

        if getattr(result, "table_data", None) is not None:
            return True

        if isinstance(result, dict) and result.get("table_data") is not None:
            return True

        return False

    def get_result_table_data(
        self,
        *,
        result: Any,
    ) -> Any:
        """
        Return complete table data embedded in a result object.
        """
        if getattr(result, "table_data", None) is not None:
            return self.normalize_table_data(
                table_data=getattr(result, "table_data"),
            )

        if isinstance(result, dict):
            return self.normalize_table_data(
                table_data=result.get("table_data"),
            )

        return dash.no_update

    def apply_values_to_first_matching_column(
        self,
        *,
        table_data: Optional[list[dict[str, Any]]],
        values: list[Any],
        candidate_column_names: tuple[str, ...],
    ) -> Any:
        """
        Apply values to the first matching column found in a Dash DataTable.
        """
        normalized_values = self.normalize_datatable_values(
            value=values,
        )

        if not normalized_values:
            return dash.no_update

        rows = self.normalize_table_data(
            table_data=table_data,
        )

        while len(rows) < len(normalized_values):
            rows.append({})

        target_column_name = self.find_first_existing_column_name(
            table_data=rows,
            candidate_column_names=candidate_column_names,
        )

        if target_column_name is None:
            target_column_name = candidate_column_names[0]

        for row_index, value in enumerate(normalized_values):
            rows[row_index][target_column_name] = self.normalize_datatable_value(
                value=value,
            )

        return self.normalize_table_data(
            table_data=rows,
        )

    def find_first_existing_column_name(
        self,
        *,
        table_data: list[dict[str, Any]],
        candidate_column_names: tuple[str, ...],
    ) -> Optional[str]:
        """
        Find the first candidate column name present in the current table rows.
        """
        for row in table_data:
            for candidate_column_name in candidate_column_names:
                if candidate_column_name in row:
                    return candidate_column_name

        return None

    def normalize_table_data(
        self,
        *,
        table_data: Any,
    ) -> list[dict[str, Any]]:
        """
        Convert complete table data to Dash DataTable safe rows.
        """
        if not isinstance(table_data, list):
            return []

        normalized_rows: list[dict[str, Any]] = []

        for row in table_data:
            if not isinstance(row, dict):
                continue

            normalized_rows.append(
                self.normalize_table_row(
                    row=row,
                )
            )

        return normalized_rows

    def normalize_table_row(
        self,
        *,
        row: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Convert one table row to Dash DataTable safe values.
        """
        return {
            str(key): self.normalize_datatable_value(
                value=value,
            )
            for key, value in dict(row).items()
        }

    def normalize_datatable_values(
        self,
        *,
        value: Any,
    ) -> list[Any]:
        """
        Flatten a value container and convert it to DataTable safe scalars.
        """
        normalized_values: list[Any] = []

        for flattened_value in self.flatten_datatable_values(
            value=value,
        ):
            normalized_value = self.normalize_datatable_value(
                value=flattened_value,
            )

            if normalized_value is None:
                continue

            if normalized_value == "":
                continue

            normalized_values.append(
                normalized_value,
            )

        return normalized_values

    def flatten_datatable_values(
        self,
        *,
        value: Any,
    ) -> list[Any]:
        """
        Flatten common scalar containers.

        Dictionaries are interpreted as 2D or structured peak payloads. In that
        case only the x-like coordinate is returned.
        """
        if value is None:
            return []

        if isinstance(value, dict):
            extracted_value = self.extract_x_value_from_mapping(
                mapping=value,
            )

            if extracted_value is None:
                return []

            return self.flatten_datatable_values(
                value=extracted_value,
            )

        if isinstance(value, np.ndarray):
            if value.ndim == 0:
                return [
                    value.item(),
                ]

            flattened_values: list[Any] = []

            for item in value.reshape(-1).tolist():
                flattened_values.extend(
                    self.flatten_datatable_values(
                        value=item,
                    )
                )

            return flattened_values

        if isinstance(value, np.generic):
            return [
                value.item(),
            ]

        if isinstance(value, (list, tuple)):
            flattened_values = []

            for item in value:
                flattened_values.extend(
                    self.flatten_datatable_values(
                        value=item,
                    )
                )

            return flattened_values

        return [
            value,
        ]

    def extract_x_value_from_mapping(
        self,
        *,
        mapping: dict[str, Any],
    ) -> Any:
        """
        Extract the x-like scalar from a structured peak payload.
        """
        for key in self.mapping_x_value_keys:
            if key in mapping:
                return mapping[key]

        return None

    def normalize_datatable_value(
        self,
        *,
        value: Any,
    ) -> Any:
        """
        Convert one value to a Dash DataTable compatible scalar.
        """
        if value is None:
            return ""

        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            return value

        if isinstance(value, int):
            return value

        if isinstance(value, float):
            if not np.isfinite(value):
                return ""

            return value

        if isinstance(value, np.generic):
            return self.normalize_datatable_value(
                value=value.item(),
            )

        if isinstance(value, np.ndarray):
            if value.ndim == 0:
                return self.normalize_datatable_value(
                    value=value.item(),
                )

            if value.size == 1:
                return self.normalize_datatable_value(
                    value=value.reshape(-1)[0],
                )

            return ""

        if hasattr(value, "item"):
            try:
                return self.normalize_datatable_value(
                    value=value.item(),
                )

            except (TypeError, ValueError):
                return str(value)

        if isinstance(value, dict):
            extracted_value = self.extract_x_value_from_mapping(
                mapping=value,
            )

            if extracted_value is None:
                return ""

            return self.normalize_datatable_value(
                value=extracted_value,
            )

        if isinstance(value, (list, tuple)):
            values = self.flatten_datatable_values(
                value=value,
            )

            if len(values) == 1:
                return self.normalize_datatable_value(
                    value=values[0],
                )

            return ""

        return str(value)