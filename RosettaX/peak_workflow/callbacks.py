# -*- coding: utf-8 -*-

from typing import Any, Optional
import logging

import dash
import plotly.graph_objs as go

from RosettaX.peak_script.registry import get_peak_process_instances
from RosettaX.peak_script.registry import get_process_instance
from RosettaX.peak_script.registry import resolve_process_name
from RosettaX.peak_workflow.detectors import populate_peak_script_detector_dropdowns
from RosettaX.peak_workflow.detectors import resolve_detector_channels_for_process
from RosettaX.peak_workflow.graphing import build_peak_workflow_graph_figure
from RosettaX.peak_workflow.graphing import is_enabled
from RosettaX.utils import casting
from RosettaX.utils import plottings
from RosettaX.utils.runtime_config import RuntimeConfig


logger = logging.getLogger(__name__)


class PeakWorkflowCallbacks:
    """
    Shared callback registration for peak workflow sections.

    Page specific behavior is supplied by a PeakWorkflowAdapter.

    Important
    ---------
    Pattern matching outputs that use ALL must always receive a list with one
    value per matched component. Returning scalar dash.no_update is invalid.
    """

    def __init__(
        self,
        *,
        page: Any,
        ids: Any,
        adapter: Any,
        table_id: str,
        page_state_store_id: str,
        max_events_input_id: Any,
        runtime_config_store_id: str = "runtime-config-store",
        mie_model_input_id: Any = None,
    ) -> None:
        self.page = page
        self.ids = ids
        self.adapter = adapter
        self.table_id = table_id
        self.page_state_store_id = page_state_store_id
        self.max_events_input_id = max_events_input_id
        self.runtime_config_store_id = runtime_config_store_id
        self.mie_model_input_id = mie_model_input_id

    def register(self) -> None:
        """
        Register all shared peak workflow callbacks.
        """
        self._register_peak_script_detector_dropdowns_callback()
        self._register_runtime_sync_callback()
        self._register_process_visibility_callback()
        self._register_manual_process_graph_visibility_callback()
        self._register_graph_visibility_callback()
        self._register_histogram_controls_visibility_callback()
        self._register_graph_callback()
        self._register_peak_workflow_mutation_callback()

    def _register_peak_script_detector_dropdowns_callback(self) -> None:
        @dash.callback(
            dash.Output(
                self.ids.process_detector_dropdown_pattern(),
                "options",
            ),
            dash.Output(
                self.ids.process_detector_dropdown_pattern(),
                "value",
            ),
            dash.Input(self.page_state_store_id, "data"),
            dash.State(
                self.ids.process_detector_dropdown_pattern(),
                "id",
            ),
            dash.State(
                self.ids.process_detector_dropdown_pattern(),
                "value",
            ),
            prevent_initial_call=False,
        )
        def populate_detector_dropdowns(
            page_state_payload: Any,
            detector_dropdown_ids: list[dict[str, Any]],
            current_detector_values: list[Any],
        ) -> tuple[list[list[dict[str, Any]]], list[Any]]:
            page_state = self.adapter.get_page_state_from_payload(
                page_state_payload,
            )

            uploaded_fcs_path = self.adapter.get_uploaded_fcs_path(
                page_state=page_state,
            )

            return populate_peak_script_detector_dropdowns(
                uploaded_fcs_path=uploaded_fcs_path,
                detector_dropdown_ids=detector_dropdown_ids,
                current_detector_values=current_detector_values,
                logger=logger,
            )

    def _register_runtime_sync_callback(self) -> None:
        @dash.callback(
            dash.Output(self.ids.peak_count_input, "value"),
            dash.Output(self.ids.nbins_input, "value"),
            dash.Output(self.ids.graph_toggle_switch, "value"),
            dash.Output(self.ids.yscale_switch, "value"),
            dash.Input(self.runtime_config_store_id, "data"),
            prevent_initial_call=False,
        )
        def sync_controls_from_runtime_store(
            runtime_config_data: Any,
        ) -> tuple[Any, Any, Any, Any]:
            runtime_config = RuntimeConfig.from_dict(
                runtime_config_data if isinstance(runtime_config_data, dict) else None
            )

            histogram_scale = runtime_config.get_str(
                "calibration.histogram_scale",
                default="log",
            )

            return (
                runtime_config.get_int(
                    "calibration.peak_count",
                    default=3,
                ),
                runtime_config.get_int(
                    "calibration.n_bins_for_plots",
                    default=100,
                ),
                ["enabled"] if runtime_config.get_show_graphs(default=True) else [],
                ["log"] if histogram_scale == "log" else [],
            )

    def _register_process_visibility_callback(self) -> None:
        @dash.callback(
            dash.Output(
                self.ids.process_controls_container_pattern(),
                "style",
            ),
            dash.Input(self.ids.process_dropdown, "value"),
            dash.State(
                self.ids.process_controls_container_pattern(),
                "id",
            ),
            prevent_initial_call=False,
        )
        def toggle_process_controls(
            process_name: Any,
            process_container_ids: list[dict[str, Any]],
        ) -> list[dict[str, Any]]:
            resolved_process_name = resolve_process_name(
                process_name,
            )

            styles: list[dict[str, Any]] = []

            for process_container_id in process_container_ids or []:
                process_name_from_id = process_container_id.get("process")

                process = get_process_instance(
                    process_name=process_name_from_id,
                )

                if process is None:
                    styles.append(
                        {
                            "display": "none",
                        }
                    )
                    continue

                styles.append(
                    process.build_visibility_style(
                        selected_process_name=resolved_process_name,
                    )
                )

            return styles

    def _register_manual_process_graph_visibility_callback(self) -> None:
        @dash.callback(
            dash.Output(
                self.ids.graph_toggle_switch,
                "value",
                allow_duplicate=True,
            ),
            dash.Input(self.ids.process_dropdown, "value"),
            dash.State(self.ids.graph_toggle_switch, "value"),
            prevent_initial_call=True,
        )
        def force_graph_visible_for_manual_process(
            process_name: Any,
            current_graph_toggle_value: Any,
        ) -> Any:
            resolved_process_name = resolve_process_name(
                process_name,
            )

            process = get_process_instance(
                process_name=resolved_process_name,
            )

            if process is not None and process.should_force_graph_visible(
                selected_process_name=resolved_process_name,
            ):
                return ["enabled"]

            return current_graph_toggle_value

    def _register_graph_visibility_callback(self) -> None:
        @dash.callback(
            dash.Output(self.ids.graph_toggle_container, "style"),
            dash.Input(self.ids.graph_toggle_switch, "value"),
            prevent_initial_call=False,
        )
        def toggle_graph_container(
            graph_toggle_value: Any,
        ) -> dict[str, str]:
            graph_enabled = is_enabled(
                graph_toggle_value,
            )

            if graph_enabled:
                return {
                    "display": "block",
                }

            return {
                "display": "none",
            }

    def _register_histogram_controls_visibility_callback(self) -> None:
        @dash.callback(
            dash.Output(
                self.ids.histogram_controls_container,
                "style",
            ),
            dash.Input(self.ids.process_dropdown, "value"),
            prevent_initial_call=False,
        )
        def toggle_histogram_controls(
            process_name: Any,
        ) -> dict[str, Any]:
            process = get_process_instance(
                process_name=process_name,
            )

            if process is not None and process.graph_type == "1d_histogram":
                return {
                    "display": "flex",
                    "alignItems": "center",
                    "gap": "16px",
                    "flexWrap": "wrap",
                }

            return {
                "display": "none",
            }

    def _register_graph_callback(self) -> None:
        @dash.callback(
            dash.Output(self.ids.graph_hist, "figure"),
            dash.Input(self.ids.graph_toggle_switch, "value"),
            dash.Input(self.ids.yscale_switch, "value"),
            dash.Input(self.page_state_store_id, "data"),
            dash.Input(self.ids.nbins_input, "value"),
            dash.State(
                self.ids.process_detector_dropdown_pattern(),
                "id",
            ),
            dash.Input(
                self.ids.process_detector_dropdown_pattern(),
                "value",
            ),
            dash.Input(self.ids.process_dropdown, "value"),
            dash.State(
                self.ids.process_setting_pattern(),
                "id",
            ),
            dash.Input(
                self.ids.process_setting_pattern(),
                "value",
            ),
            dash.State(
                self.max_events_input_id,
                "value",
                allow_optional=True,
            ),
            dash.State(self.runtime_config_store_id, "data"),
            prevent_initial_call=False,
        )
        def update_graph(
            graph_toggle_value: Any,
            yscale_selection: Any,
            page_state_payload: Any,
            nbins: Any,
            detector_dropdown_ids: list[dict[str, Any]],
            detector_dropdown_values: list[Any],
            process_name: Any,
            process_setting_ids: list[dict[str, Any]],
            process_setting_values: list[Any],
            max_events_for_plots: Any,
            runtime_config_data: Any,
        ) -> go.Figure:
            page_state = self.adapter.get_page_state_from_payload(
                page_state_payload,
            )

            uploaded_fcs_path = self.adapter.get_uploaded_fcs_path(
                page_state=page_state,
            )

            peak_lines_payload = self.adapter.get_peak_lines_payload(
                page_state=page_state,
            )

            backend = self.adapter.get_backend(
                page=self.page,
                uploaded_fcs_path=uploaded_fcs_path,
            )

            try:
                return build_peak_workflow_graph_figure(
                    backend=backend,
                    uploaded_fcs_path=uploaded_fcs_path,
                    process_name=process_name,
                    detector_dropdown_ids=detector_dropdown_ids,
                    detector_dropdown_values=detector_dropdown_values,
                    process_setting_ids=process_setting_ids,
                    process_setting_values=process_setting_values,
                    graph_toggle_value=graph_toggle_value,
                    yscale_selection=yscale_selection,
                    nbins=nbins,
                    peak_lines_payload=peak_lines_payload,
                    max_events_for_plots=max_events_for_plots,
                    runtime_config_data=runtime_config_data,
                )

            except Exception as exc:
                logger.exception("Failed to build peak workflow graph.")

                return plottings._make_info_figure(
                    f"{type(exc).__name__}: {exc}",
                )

    def _register_peak_workflow_mutation_callback(self) -> None:
        inputs = [
            dash.Input(self.ids.process_dropdown, "value"),
            dash.Input(
                self.ids.process_detector_dropdown_pattern(),
                "value",
            ),
            dash.Input(
                self.ids.process_action_button_pattern(),
                "n_clicks",
            ),
            dash.Input(self.ids.graph_hist, "clickData"),
        ]

        states = [
            dash.State(self.page_state_store_id, "data"),
            dash.State(
                self.ids.process_detector_dropdown_pattern(),
                "id",
            ),
            dash.State(
                self.ids.process_action_button_pattern(),
                "id",
            ),
            dash.State(self.ids.peak_count_input, "value"),
            dash.State(
                self.max_events_input_id,
                "value",
                allow_optional=True,
            ),
            dash.State(self.table_id, "data"),
            dash.State(self.runtime_config_store_id, "data"),
            dash.State(
                self.ids.process_status_pattern(),
                "id",
            ),
        ]

        if self.mie_model_input_id is not None:
            states.append(
                dash.State(self.mie_model_input_id, "value"),
            )

        @dash.callback(
            dash.Output(
                self.page_state_store_id,
                "data",
                allow_duplicate=True,
            ),
            dash.Output(
                self.table_id,
                "data",
                allow_duplicate=True,
            ),
            dash.Output(
                self.ids.process_status_pattern(),
                "children",
                allow_duplicate=True,
            ),
            *inputs,
            *states,
            prevent_initial_call=True,
        )
        def reduce_peak_workflow_event(
            process_name: Any,
            detector_dropdown_values: list[Any],
            action_clicks: list[Any],
            click_data: Any,
            page_state_payload: Any,
            detector_dropdown_ids: list[dict[str, Any]],
            action_ids: list[dict[str, Any]],
            peak_count: Any,
            max_events_for_plots: Any,
            table_data: Optional[list[dict[str, Any]]],
            runtime_config_data: Any,
            status_component_ids: list[dict[str, Any]],
            *optional_state_values: Any,
        ) -> tuple[Any, Any, list[Any]]:
            del action_clicks
            del action_ids

            mie_model = optional_state_values[0] if optional_state_values else None
            triggered_id = dash.ctx.triggered_id

            page_state = self.adapter.get_page_state_from_payload(
                page_state_payload,
            )

            if triggered_id == self.ids.process_dropdown:
                return self._clear_peak_context(
                    page_state=page_state,
                    process_name=process_name,
                    status_component_ids=status_component_ids,
                )

            if self._trigger_is_detector_dropdown_change(triggered_id):
                return self._clear_peak_context(
                    page_state=page_state,
                    process_name=process_name,
                    status_component_ids=status_component_ids,
                )

            if triggered_id == self.ids.graph_hist:
                return self._handle_manual_graph_click(
                    click_data=click_data,
                    process_name=process_name,
                    page_state=page_state,
                    detector_dropdown_ids=detector_dropdown_ids,
                    detector_dropdown_values=detector_dropdown_values,
                    table_data=table_data,
                    mie_model=mie_model,
                    status_component_ids=status_component_ids,
                )

            if self._trigger_is_action_button(triggered_id):
                return self._handle_process_action(
                    triggered_action_id=triggered_id,
                    process_name=process_name,
                    page_state=page_state,
                    detector_dropdown_ids=detector_dropdown_ids,
                    detector_dropdown_values=detector_dropdown_values,
                    peak_count=peak_count,
                    max_events_for_plots=max_events_for_plots,
                    table_data=table_data,
                    mie_model=mie_model,
                    runtime_config_data=runtime_config_data,
                    status_component_ids=status_component_ids,
                )

            return self._build_no_update_callback_result(
                status_component_ids=status_component_ids,
            )

    def _trigger_is_detector_dropdown_change(
        self,
        triggered_id: Any,
    ) -> bool:
        if not isinstance(triggered_id, dict):
            return False

        expected_type = self._get_detector_dropdown_pattern_type()

        return triggered_id.get("type") == expected_type

    def _trigger_is_action_button(
        self,
        triggered_id: Any,
    ) -> bool:
        if not isinstance(triggered_id, dict):
            return False

        expected_type = self._get_action_button_pattern_type()

        return triggered_id.get("type") == expected_type

    def _get_detector_dropdown_pattern_type(self) -> Any:
        pattern = self.ids.process_detector_dropdown_pattern()

        if not isinstance(pattern, dict):
            raise TypeError(
                "ids.process_detector_dropdown_pattern() must return a dictionary."
            )

        return pattern.get("type")

    def _get_action_button_pattern_type(self) -> Any:
        pattern = self.ids.process_action_button_pattern()

        if not isinstance(pattern, dict):
            raise TypeError(
                "ids.process_action_button_pattern() must return a dictionary."
            )

        return pattern.get("type")

    def _clear_peak_context(
        self,
        *,
        page_state: Any,
        process_name: Any,
        status_component_ids: list[dict[str, Any]],
    ) -> tuple[dict[str, Any], Any, list[Any]]:
        page_state = self.adapter.clear_peak_lines_payload(
            page_state=page_state,
        )

        status_children = self.build_status_children(
            status_component_ids=status_component_ids,
            target_process_name=resolve_process_name(process_name),
            status="",
        )

        return (
            page_state.to_dict(),
            dash.no_update,
            status_children,
        )

    def _handle_manual_graph_click(
        self,
        *,
        click_data: Any,
        process_name: Any,
        page_state: Any,
        detector_dropdown_ids: list[dict[str, Any]],
        detector_dropdown_values: list[Any],
        table_data: Optional[list[dict[str, Any]]],
        mie_model: Any,
        status_component_ids: list[dict[str, Any]],
    ) -> tuple[Any, Any, list[Any]]:
        resolved_process_name = resolve_process_name(
            process_name,
        )

        process = get_process_instance(
            process_name=resolved_process_name,
        )

        if process is None or not process.supports_manual_click:
            return self._build_no_update_callback_result(
                status_component_ids=status_component_ids,
            )

        uploaded_fcs_path = self.adapter.get_uploaded_fcs_path(
            page_state=page_state,
        )

        detector_channels = resolve_detector_channels_for_process(
            detector_dropdown_ids=detector_dropdown_ids,
            detector_dropdown_values=detector_dropdown_values,
            process_name=resolved_process_name,
        )

        if not self.context_is_valid_for_process(
            process=process,
            uploaded_fcs_path=uploaded_fcs_path,
            detector_channels=detector_channels,
        ):
            status = self.build_missing_context_message(
                process=process,
                uploaded_fcs_path=uploaded_fcs_path,
                detector_channels=detector_channels,
            )

            return (
                dash.no_update,
                dash.no_update,
                self.build_status_children(
                    status_component_ids=status_component_ids,
                    target_process_name=resolved_process_name,
                    status=status,
                ),
            )

        result = process.add_clicked_peak(
            click_data=click_data,
            existing_peak_lines_payload=self.adapter.get_peak_lines_payload(
                page_state=page_state,
            ),
        )

        if result is None:
            return self._build_no_update_callback_result(
                status_component_ids=status_component_ids,
            )

        page_state = self.adapter.update_peak_lines_payload(
            page_state=page_state,
            peak_lines_payload=result.peak_lines_payload,
        )

        table_result = self.adapter.apply_peak_process_result_to_table(
            table_data=table_data,
            result=result,
            context={
                "mie_model": mie_model,
                "process_name": resolved_process_name,
            },
            logger=logger,
        )

        status_children = self.build_status_children(
            status_component_ids=status_component_ids,
            target_process_name=resolved_process_name,
            status=result.status,
        )

        return (
            page_state.to_dict(),
            table_result,
            status_children,
        )

    def _handle_process_action(
        self,
        *,
        triggered_action_id: Any,
        process_name: Any,
        page_state: Any,
        detector_dropdown_ids: list[dict[str, Any]],
        detector_dropdown_values: list[Any],
        peak_count: Any,
        max_events_for_plots: Any,
        table_data: Optional[list[dict[str, Any]]],
        mie_model: Any,
        runtime_config_data: Any,
        status_component_ids: list[dict[str, Any]],
    ) -> tuple[Any, Any, list[Any]]:
        del process_name

        if not isinstance(triggered_action_id, dict):
            return self._build_no_update_callback_result(
                status_component_ids=status_component_ids,
            )

        target_process_name = triggered_action_id.get("process")
        action_name = triggered_action_id.get("action")

        process = get_process_instance(
            process_name=target_process_name,
        )

        if process is None:
            return self._build_no_update_callback_result(
                status_component_ids=status_component_ids,
            )

        uploaded_fcs_path = self.adapter.get_uploaded_fcs_path(
            page_state=page_state,
        )

        detector_channels = resolve_detector_channels_for_process(
            detector_dropdown_ids=detector_dropdown_ids,
            detector_dropdown_values=detector_dropdown_values,
            process_name=target_process_name,
        )

        if action_name == "clear" and process.supports_clear:
            result = process.clear_peaks()

            page_state = self.adapter.update_peak_lines_payload(
                page_state=page_state,
                peak_lines_payload=result.peak_lines_payload,
            )

            table_result = self.adapter.apply_peak_process_result_to_table(
                table_data=table_data,
                result=result,
                context={
                    "mie_model": mie_model,
                    "process_name": target_process_name,
                },
                logger=logger,
            )

            status_children = self.build_status_children(
                status_component_ids=status_component_ids,
                target_process_name=target_process_name,
                status=result.status,
            )

            return (
                page_state.to_dict(),
                table_result,
                status_children,
            )

        if action_name == "run" and process.supports_automatic_action:
            if not self.context_is_valid_for_process(
                process=process,
                uploaded_fcs_path=uploaded_fcs_path,
                detector_channels=detector_channels,
            ):
                status = self.build_missing_context_message(
                    process=process,
                    uploaded_fcs_path=uploaded_fcs_path,
                    detector_channels=detector_channels,
                )

                return (
                    dash.no_update,
                    dash.no_update,
                    self.build_status_children(
                        status_component_ids=status_component_ids,
                        target_process_name=target_process_name,
                        status=status,
                    ),
                )

            runtime_config = RuntimeConfig.from_dict(
                runtime_config_data if isinstance(runtime_config_data, dict) else None
            )

            resolved_peak_count = casting.as_int(
                peak_count,
                default=runtime_config.get_int(
                    "calibration.peak_count",
                    default=3,
                ),
                min_value=1,
                max_value=50,
            )

            resolved_max_events = casting.as_int(
                max_events_for_plots,
                default=runtime_config.get_int(
                    "calibration.max_events_for_analysis",
                    default=10000,
                ),
                min_value=1,
                max_value=5_000_000,
            )

            backend = self.adapter.get_backend(
                page=self.page,
                uploaded_fcs_path=uploaded_fcs_path,
            )

            result = process.run_automatic_action(
                backend=backend,
                detector_channels=detector_channels,
                peak_count=resolved_peak_count,
                max_events_for_analysis=resolved_max_events,
            )

            if result is None:
                return self._build_no_update_callback_result(
                    status_component_ids=status_component_ids,
                )

            page_state = self.adapter.update_peak_lines_payload(
                page_state=page_state,
                peak_lines_payload=result.peak_lines_payload,
            )

            table_result = self.adapter.apply_peak_process_result_to_table(
                table_data=table_data,
                result=result,
                context={
                    "mie_model": mie_model,
                    "process_name": target_process_name,
                },
                logger=logger,
            )

            status_children = self.build_status_children(
                status_component_ids=status_component_ids,
                target_process_name=target_process_name,
                status=result.status,
            )

            return (
                page_state.to_dict(),
                table_result,
                status_children,
            )

        return self._build_no_update_callback_result(
            status_component_ids=status_component_ids,
        )

    def context_is_valid_for_process(
        self,
        *,
        process: Any,
        uploaded_fcs_path: Any,
        detector_channels: dict[str, Any],
    ) -> bool:
        if not str(uploaded_fcs_path or "").strip():
            return False

        for channel_name in process.get_required_detector_channels():
            if not str(detector_channels.get(channel_name) or "").strip():
                return False

        return True

    def build_missing_context_message(
        self,
        *,
        process: Any,
        uploaded_fcs_path: Any,
        detector_channels: dict[str, Any],
    ) -> str:
        if not str(uploaded_fcs_path or "").strip():
            return "Upload an FCS file first."

        missing_channel_names: list[str] = []

        for channel_name in process.get_required_detector_channels():
            if not str(detector_channels.get(channel_name) or "").strip():
                missing_channel_names.append(
                    str(channel_name),
                )

        if len(missing_channel_names) == 1:
            return f"Select the {missing_channel_names[0]} detector channel first."

        if missing_channel_names:
            missing_channel_text = " and ".join(
                missing_channel_names,
            )

            return f"Select the {missing_channel_text} detector channels first."

        return "Upload an FCS file and select the required detector channel(s) first."

    def build_status_children(
        self,
        *,
        status_component_ids: list[dict[str, Any]],
        target_process_name: str,
        status: str,
    ) -> list[Any]:
        children: list[Any] = []

        for status_component_id in status_component_ids or []:
            if status_component_id.get("process") == target_process_name:
                children.append(
                    status,
                )

            else:
                children.append(
                    "",
                )

        return children

    def build_no_update_status_children(
        self,
        *,
        status_component_ids: list[dict[str, Any]],
    ) -> list[Any]:
        """
        Build a no-update list for wildcard status outputs.

        Dash wildcard outputs require a list or tuple with one value per matched
        component. A scalar dash.no_update is invalid.
        """
        return [
            dash.no_update
            for _ in (status_component_ids or [])
        ]

    def _build_no_update_callback_result(
        self,
        *,
        status_component_ids: list[dict[str, Any]],
    ) -> tuple[Any, Any, list[Any]]:
        """
        Build a valid no-update result for the mutation callback.
        """
        return (
            dash.no_update,
            dash.no_update,
            self.build_no_update_status_children(
                status_component_ids=status_component_ids,
            ),
        )


def get_peak_processes() -> list[Any]:
    """
    Return shared peak process instances.
    """
    return get_peak_process_instances()