
import dash
import logging
from ..core import detectors
from typing import Any

logger = logging.getLogger(__name__)


def register_detector_dropdown_callbacks(
    *,
    ids: Any,
    adapter: Any,
    page_state_store_id: str,
) -> None:
    """
    Register detector dropdown callbacks for the peak workflow.

    Parameters
    ----------
    ids
        Peak section ID factory.
    adapter
        Page specific peak workflow adapter.
    page_state_store_id
        Dash store ID containing the page state.
    """

    system_model_id = getattr(ids, "system_model", None)
    system_inputs = [dash.Input(system_model_id, "value")] if system_model_id else []

    @dash.callback(
        dash.Output(
            ids.process_detector_dropdown_pattern(),
            "options",
        ),
        dash.Output(
            ids.process_detector_dropdown_pattern(),
            "value",
        ),
        dash.Input(page_state_store_id, "data"),
        dash.Input(ids.process_dropdown, "value"),
        dash.Input("runtime-config-store", "data"),
        dash.Input(
            {
                "type": ids.rosetta_auto_select_detectors_type,
                "process": dash.ALL,
            },
            "n_clicks",
            allow_optional=True,
        ),
        dash.State(
            ids.process_detector_dropdown_pattern(),
            "id",
        ),
        dash.State(
            ids.process_detector_dropdown_pattern(),
            "options",
        ),
        dash.State(
            ids.process_detector_dropdown_pattern(),
            "value",
        ),
        *system_inputs,
        prevent_initial_call=False,
    )
    def populate_detector_dropdowns(
        page_state_payload: Any,
        selected_process: Any,
        runtime_config_data: Any,
        auto_select_clicks: Any,
        detector_dropdown_ids: list[dict[str, Any]],
        current_detector_options: list[Any],
        current_detector_values: list[Any],
        instrument_catalog_key: str | None = None,
    ) -> tuple[list[list[dict[str, Any]]], list[Any]]:
        page_state = adapter.get_page_state_from_payload(
            page_state_payload,
        )

        uploaded_fcs_path = adapter.get_uploaded_fcs_path(
            page_state=page_state,
        )

        resolved_options, resolved_values = detectors.populate_peak_script_detector_dropdowns(
            uploaded_fcs_path=uploaded_fcs_path,
            detector_dropdown_ids=detector_dropdown_ids,
            reset_rosetta_v1=(
                str(selected_process or "").startswith("Rosetta Script")
                and ids.process_dropdown in dash.ctx.triggered_prop_ids.values()
            ),
            auto_select_rosetta_v1=(
                isinstance(dash.ctx.triggered_id, dict)
                and dash.ctx.triggered_id.get("type") == ids.rosetta_auto_select_detectors_type
                and dash.ctx.triggered_id.get("process") == selected_process
            ),
            auto_select_process_name=(
                str(dash.ctx.triggered_id.get("process"))
                if isinstance(dash.ctx.triggered_id, dict)
                and dash.ctx.triggered_id.get("type") == ids.rosetta_auto_select_detectors_type
                and dash.ctx.triggered_id.get("process") == selected_process
                else None
            ),
            current_detector_values=current_detector_values,
            instrument_catalog_key=instrument_catalog_key,
            refresh_inferred_channels=bool(system_model_id and dash.ctx.triggered_id == system_model_id),

            runtime_config_data=runtime_config_data,
            detector_selection_runtime_config_path=getattr(
                adapter,
                "detector_selection_runtime_config_path",
                None,
            ),
            logger=logger,
        )

        if (
            isinstance(current_detector_options, list)
            and resolved_options == current_detector_options
            and resolved_values == (current_detector_values or [])
        ):
            # Keep detector dropdown outputs stable to avoid emitting synthetic
            # detector-change events when unrelated page state updates occur.
            no_update_count = len(detector_dropdown_ids or [])
            return (
                [dash.no_update] * no_update_count,
                [dash.no_update] * no_update_count,
            )

        return resolved_options, resolved_values
