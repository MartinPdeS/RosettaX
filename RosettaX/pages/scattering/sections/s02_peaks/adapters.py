# -*- coding: utf-8 -*-

from typing import Any, Optional
import logging

from RosettaX.pages.scattering.backend import BackEnd
from RosettaX.pages.scattering.state import ScatteringPageState
from RosettaX.peak_workflow.adapters import PeakWorkflowAdapter
from RosettaX.peak_workflow.tables import append_positions_to_table_column
from RosettaX.peak_workflow.tables import clear_table_column


logger = logging.getLogger(__name__)


class ScatteringPeakWorkflowAdapter(PeakWorkflowAdapter):
    """
    Adapter connecting the shared peak workflow to the scattering page.

    Responsibilities
    ----------------
    - Parse the scattering page state.
    - Read and update the peak line payload in ScatteringPageState.
    - Provide a scattering backend for graphing and peak detection.
    - Write peak process results into the scattering calibration reference table.
    """

    page_kind = "scattering"

    def get_page_state_from_payload(
        self,
        page_state_payload: Any,
    ) -> ScatteringPageState:
        """
        Parse the scattering page state from Dash store data.

        Parameters
        ----------
        page_state_payload:
            Serialized page state.

        Returns
        -------
        ScatteringPageState
            Parsed page state.
        """
        return ScatteringPageState.from_dict(
            page_state_payload if isinstance(page_state_payload, dict) else None
        )

    def get_uploaded_fcs_path(
        self,
        *,
        page_state: ScatteringPageState,
    ) -> Optional[str]:
        """
        Return the uploaded scattering FCS path.

        Parameters
        ----------
        page_state:
            Scattering page state.

        Returns
        -------
        Optional[str]
            Uploaded FCS path.
        """
        return page_state.uploaded_fcs_path

    def get_peak_lines_payload(
        self,
        *,
        page_state: ScatteringPageState,
    ) -> dict[str, Any]:
        """
        Return the scattering peak line payload.

        Parameters
        ----------
        page_state:
            Scattering page state.

        Returns
        -------
        dict[str, Any]
            Peak line payload.
        """
        peak_lines_payload = getattr(
            page_state,
            "peak_lines_payload",
            None,
        )

        if isinstance(peak_lines_payload, dict):
            return peak_lines_payload

        return {
            "positions": [],
            "labels": [],
            "x_positions": [],
            "y_positions": [],
            "points": [],
        }

    def update_peak_lines_payload(
        self,
        *,
        page_state: ScatteringPageState,
        peak_lines_payload: Any,
    ) -> ScatteringPageState:
        """
        Return an updated scattering page state with a new peak line payload.

        Parameters
        ----------
        page_state:
            Current page state.

        peak_lines_payload:
            New peak line payload.

        Returns
        -------
        ScatteringPageState
            Updated page state.
        """
        return page_state.update(
            peak_lines_payload=peak_lines_payload,
        )

    def get_backend(
        self,
        *,
        page: Any,
        uploaded_fcs_path: Any,
    ) -> Any:
        """
        Return the scattering backend.

        If the page backend is missing but the uploaded FCS path is available,
        rebuild the backend. This keeps session restored pages functional.

        Parameters
        ----------
        page:
            Scattering page object.

        uploaded_fcs_path:
            Uploaded FCS path.

        Returns
        -------
        Any
            Scattering backend or None.
        """
        backend = getattr(
            page,
            "backend",
            None,
        )

        if backend is not None:
            return backend

        uploaded_fcs_path_clean = str(
            uploaded_fcs_path or "",
        ).strip()

        if not uploaded_fcs_path_clean:
            return None

        try:
            page.backend = BackEnd(
                fcs_file_path=uploaded_fcs_path_clean,
            )

            logger.debug(
                "Rebuilt scattering backend from uploaded_fcs_path=%r",
                uploaded_fcs_path_clean,
            )

            return page.backend

        except Exception:
            logger.exception(
                "Failed to rebuild scattering backend from uploaded_fcs_path=%r",
                uploaded_fcs_path_clean,
            )

            return None

    def apply_peak_process_result_to_table(
        self,
        *,
        table_data: Optional[list[dict[str, Any]]],
        result: Any,
        context: dict[str, Any],
        logger: logging.Logger,
    ) -> list[dict[str, Any]]:
        """
        Apply a peak process result to the scattering calibration table.

        Parameters
        ----------
        table_data:
            Existing calibration table rows.

        result:
            PeakProcessResult returned by a peak script.

        context:
            Workflow context. Requires ``mie_model``.

        logger:
            Logger.

        Returns
        -------
        list[dict[str, Any]]
            Updated calibration table rows.
        """
        mie_model = resolve_mie_model(
            context.get("mie_model"),
        )

        if getattr(result, "clear_existing_table_peaks", False):
            rows = clear_table_column(
                table_data=table_data,
                column_name="measured_peak_position",
            )

            return ensure_minimum_row_count(
                rows=rows,
                mie_model=mie_model,
                minimum_row_count=3,
            )

        peak_positions = getattr(
            result,
            "new_peak_positions",
            None,
        )

        if peak_positions is None:
            peak_positions = getattr(
                result,
                "peak_positions",
                [],
            )

        rows = append_positions_to_table_column(
            table_data=table_data,
            peak_positions=list(peak_positions or []),
            column_name="measured_peak_position",
            empty_row_factory=lambda: build_empty_table_row(
                mie_model=mie_model,
            ),
            logger=logger,
        )

        return ensure_minimum_row_count(
            rows=rows,
            mie_model=mie_model,
            minimum_row_count=3,
        )


def resolve_mie_model(
    mie_model: Any,
) -> str:
    """
    Resolve the Mie model name used by the scattering reference table.

    Parameters
    ----------
    mie_model:
        Raw Mie model value.

    Returns
    -------
    str
        Resolved model name.
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

    Parameters
    ----------
    mie_model:
        Resolved Mie model name.

    Returns
    -------
    dict[str, str]
        Empty row.
    """
    if mie_model == "Core/Shell Sphere":
        return {
            "core_diameter_nm": "",
            "shell_thickness_nm": "",
            "outer_diameter_nm": "",
            "measured_peak_position": "",
            "expected_coupling": "",
        }

    return {
        "particle_diameter_nm": "",
        "measured_peak_position": "",
        "expected_coupling": "",
    }


def ensure_minimum_row_count(
    *,
    rows: list[dict[str, Any]],
    mie_model: str,
    minimum_row_count: int,
) -> list[dict[str, Any]]:
    """
    Ensure a minimum number of table rows.

    Parameters
    ----------
    rows:
        Existing rows.

    mie_model:
        Resolved Mie model name.

    minimum_row_count:
        Minimum number of rows.

    Returns
    -------
    list[dict[str, Any]]
        Rows with at least ``minimum_row_count`` entries.
    """
    next_rows = [
        dict(row)
        for row in rows
    ]

    while len(next_rows) < int(minimum_row_count):
        next_rows.append(
            build_empty_table_row(
                mie_model=mie_model,
            )
        )

    return next_rows