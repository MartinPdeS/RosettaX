
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

    @dash.callback(
        dash.Output(ids.rosetta_v1_detector_suggestions, "children"),
        dash.Input(ids.rosetta_v1_auto_select_detectors, "n_clicks"),
        dash.Input(page_state_store_id, "data"),
        prevent_initial_call=True,
    )
    def explain_detector_suggestions(clicks: Any, page_state_payload: Any) -> Any:
        """Explain the channel suggestions made for the current FCS file."""
        if not clicks:
            return ""
        page_state = adapter.get_page_state_from_payload(page_state_payload)
        file_path = adapter.get_uploaded_fcs_path(page_state=page_state)
        if not file_path:
            return "Load an FCS file before selecting detectors."
        try:
            with detectors.FCSFile(file_path) as fcs:
                channel_names = fcs.get_column_names()
                rule = detectors.resolve_detector_auto_detect_rule(metadata=fcs.get_metadata())
        except Exception:
            logger.exception("Could not read FCS file for detector suggestions")
            return "Could not read detector names from the selected FCS file."
        scatter, scatter_reason = detectors.resolve_rosetta_v1_suggestion(
            column_names=channel_names, detector_role="scattering", matched_rule=rule,
        )
        _, fluorescence_reason = detectors.resolve_rosetta_v1_suggestion(
            column_names=channel_names,
            detector_role="green_fluorescence",
            preferred_wavelength_nm=detectors.extract_channel_wavelength_nm(channel_name=scatter),
            matched_rule=rule,
        )
        return dash.html.Div(
            [
                dash.html.Div([dash.html.Strong("Scattering: "), scatter_reason]),
                dash.html.Div([dash.html.Strong("Green fluorescence: "), fluorescence_reason]),
            ],
            style={
                "backgroundColor": "rgba(128, 128, 128, 0.08)",
                "borderRadius": "8px",
                "padding": "10px 12px",
                "fontSize": "0.88rem",
                "lineHeight": "1.5",
            },
        )

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
        dash.Input(ids.rosetta_v1_auto_select_detectors, "n_clicks", allow_optional=True),
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
                selected_process == "Rosetta Script V1"
                and ids.process_dropdown in dash.ctx.triggered_prop_ids.values()
            ),
            auto_select_rosetta_v1=(
                bool(auto_select_clicks)
                and dash.ctx.triggered_id == ids.rosetta_v1_auto_select_detectors
            ),
            current_detector_values=current_detector_values,
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
