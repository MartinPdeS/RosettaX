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

    The shared peak workflow callbacks should not know how a page stores its
    uploaded FCS path, peak lines, backend instance, or calibration table. This
    adapter provides common state handling and JSON safe DataTable utilities.
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

        backend = getattr(page, "backend", None)

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

        The returned list is flattened and converted to Dash DataTable safe
        scalar values.
        """
        if result is None:
            return []

        for attribute_name in (
            "new_peak_positions",
            "peak_values",
            "peak_positions",
            "peaks",
            "x_values",
            "values",
        ):
            value = getattr(
                result,
                attribute_name,
                None,
            )

            if value is not None:
                return self.normalize_datatable_values(
                    value=value,
                )

        if isinstance(result, dict):
            for key in (
                "new_peak_positions",
                "peak_values",
                "peak_positions",
                "peaks",
                "x_values",
                "values",
            ):
                value = result.get(key)

                if value is not None:
                    return self.normalize_datatable_values(
                        value=value,
                    )

        peak_lines_payload = getattr(
            result,
            "peak_lines_payload",
            None,
        )

        if peak_lines_payload is not None:
            return self.normalize_datatable_values(
                value=self.extract_peak_values_from_peak_lines_payload(
                    peak_lines_payload=peak_lines_payload,
                ),
            )

        return []

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
                        for key in ("x", "value", "position"):
                            if key in point:
                                values.append(point[key])
                                break

                return values

        if isinstance(peak_lines_payload, list):
            values = []

            for item in peak_lines_payload:
                if isinstance(item, dict):
                    for key in ("x", "value", "position"):
                        if key in item:
                            values.append(item[key])
                            break

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

        Every written value is converted to a JSON safe scalar. This prevents
        Dash DataTable errors caused by NumPy arrays, NumPy scalars, lists, or
        other non scalar objects.
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

        DataTable cells must not receive lists or arrays, so nested values are
        flattened before writing to rows.
        """
        if value is None:
            return []

        if isinstance(value, np.ndarray):
            if value.ndim == 0:
                return [
                    value.item(),
                ]

            return [
                item
                for item in value.reshape(-1).tolist()
            ]

        if isinstance(value, np.generic):
            return [
                value.item(),
            ]

        if isinstance(value, (list, tuple)):
            flattened_values: list[Any] = []

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

    def normalize_datatable_value(
        self,
        *,
        value: Any,
    ) -> Any:
        """
        Convert one value to a Dash DataTable compatible scalar.

        Valid Dash DataTable cell values are string, number, and boolean. Empty
        or invalid values are returned as an empty string.
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

        if isinstance(value, (list, tuple, dict)):
            return str(value)

        return str(value)