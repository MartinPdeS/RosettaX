import inspect
import logging
from typing import Any

import numpy as np
import plotly.graph_objs as go

from RosettaX.utils import plottings
from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.workflow.plotting.axis_ranges import (
    apply_stable_2d_axis_ranges as apply_stable_2d_axis_ranges,
)
from RosettaX.workflow.plotting.axis_ranges import (
    compute_stable_axis_range as compute_stable_axis_range,
)
from RosettaX.workflow.plotting.scatter2d import Scatter2DGraph

from .. import registry
from ..scripts.base import (
    resolve_edge_artifact_filter_enabled,
)
from . import (
    detectors,
    graph_histogram,
    graph_overlays,
    graph_scatter,
    graph_settings,
)
from .graph_interaction import (
    _is_rosetta_script_process_name as _is_rosetta_script_process_name,
)
from .graph_interaction import (
    add_peak_workflow_post_layout_overlays as add_peak_workflow_post_layout_overlays,
)
from .graph_interaction import (
    apply_peak_workflow_interaction_revision as apply_peak_workflow_interaction_revision,
)
from .graph_interaction import (
    axis_scale_selection_is_log as axis_scale_selection_is_log,
)
from .graph_interaction import (
    build_peak_workflow_uirevision as build_peak_workflow_uirevision,
)
from .graph_interaction import (
    is_enabled as is_enabled,
)
from .graph_interaction import (
    scale_selection_is_log as scale_selection_is_log,
)
from .graph_interaction import (
    unique_finite_preserving_order as unique_finite_preserving_order,
)

logger = logging.getLogger(__name__)


def build_peak_workflow_graph_figure(
    *,
    backend: Any,
    uploaded_fcs_path: Any,
    process_name: Any,
    detector_dropdown_ids: list[dict[str, Any]],
    detector_dropdown_values: list[Any],
    process_setting_ids: list[dict[str, Any]],
    process_setting_values: list[Any],
    graph_toggle_value: Any,
    advanced_mode_value: Any = None,
    data_filter_value: Any = None,
    xscale_selection: Any = None,
    yscale_selection: Any = None,
    nbins: Any = None,
    peak_lines_payload: Any = None,
    max_events_for_plots: Any = None,
    marker_size: Any = None,
    marker_opacity: Any = None,
    runtime_config_data: Any = None,
) -> go.Figure:
    """
    Build the graph for the selected peak workflow process.

    This function is the public API used by the Dash callback. The implementation
    is delegated to PeakWorkflowGraphBuilder.
    """
    return PeakWorkflowGraphBuilder(
        backend=backend,
        uploaded_fcs_path=uploaded_fcs_path,
        process_name=process_name,
        detector_dropdown_ids=detector_dropdown_ids,
        detector_dropdown_values=detector_dropdown_values,
        process_setting_ids=process_setting_ids,
        process_setting_values=process_setting_values,
        graph_toggle_value=graph_toggle_value,
        advanced_mode_value=advanced_mode_value,
        data_filter_value=data_filter_value,
        xscale_selection=xscale_selection,
        yscale_selection=yscale_selection,
        nbins=nbins,
        peak_lines_payload=peak_lines_payload,
        max_events_for_plots=max_events_for_plots,
        marker_size=marker_size,
        marker_opacity=marker_opacity,
        runtime_config_data=runtime_config_data,
    ).build()


class PeakWorkflowGraphBuilder:
    """Dispatch peak processes and assemble their graph figures.

    Histogram, scatter, overlay, payload, and display helpers own the rendering
    details. This builder retains the process context and public graph API.
    """

    default_margin: dict[str, int] = {
        "l": 80,
        "r": 30,
        "t": 55,
        "b": 70,
    }

    rejected_x_fill_color = "rgba(20, 20, 20, 0.16)"
    rejected_y_fill_color = "rgba(20, 20, 20, 0.22)"
    accepted_y_fill_color = "rgba(38, 196, 78, 0.20)"
    fluorescence_helper_fill_color = "rgba(64, 138, 255, 0.12)"

    def __init__(
        self,
        *,
        backend: Any,
        uploaded_fcs_path: Any,
        process_name: Any,
        detector_dropdown_ids: list[dict[str, Any]],
        detector_dropdown_values: list[Any],
        process_setting_ids: list[dict[str, Any]],
        process_setting_values: list[Any],
        graph_toggle_value: Any,
        advanced_mode_value: Any = None,
        data_filter_value: Any = None,
        xscale_selection: Any = None,
        yscale_selection: Any = None,
        nbins: Any = None,
        peak_lines_payload: Any = None,
        max_events_for_plots: Any = None,
        marker_size: Any = None,
        marker_opacity: Any = None,
        runtime_config_data: Any = None,
    ) -> None:
        self.backend = backend
        self.uploaded_fcs_path = uploaded_fcs_path
        self.process_name = process_name
        self.detector_dropdown_ids = detector_dropdown_ids or []
        self.detector_dropdown_values = detector_dropdown_values or []
        self.process_setting_ids = process_setting_ids or []
        self.process_setting_values = process_setting_values or []
        self.graph_toggle_value = graph_toggle_value
        self.advanced_mode_value = advanced_mode_value
        self.data_filter_value = data_filter_value
        self.xscale_selection = xscale_selection
        self.yscale_selection = yscale_selection
        self.nbins = nbins
        self.peak_lines_payload = peak_lines_payload
        self.max_events_for_plots = max_events_for_plots
        self.marker_size = marker_size
        self.marker_opacity = marker_opacity
        self.runtime_config_data = runtime_config_data

        self.runtime_config = RuntimeConfig.from_dict(
            runtime_config_data if isinstance(runtime_config_data, dict) else None
        )

        self.resolved_process_name = registry.resolve_process_name(
            process_name,
        )

        self.process = registry.get_process_instance(
            process_name=self.resolved_process_name,
        )

        self.detector_channels: dict[str, Any] = {}
        self.process_settings: dict[str, Any] = {}
        self._stable_histogram_count_values: np.ndarray | None = None

    def build(self) -> go.Figure:
        """
        Build the complete Plotly figure.
        """
        validation_figure = self._validate_context()

        if validation_figure is not None:
            return validation_figure

        self.detector_channels = self._resolve_detector_channels()

        missing_channel_names = self._get_missing_detector_channel_names()

        if missing_channel_names:
            return plottings._make_info_figure(
                self._build_missing_detector_message(
                    missing_channel_names=missing_channel_names,
                )
            )

        self.process_settings = self._build_process_settings()

        figure = self._build_process_specific_figure()

        graph_settings.apply_axis_types(
            self,
            figure=figure,
        )

        graph_histogram.apply_stable_1d_histogram_y_range(
            self,
            figure=figure,
        )

        graph_settings.apply_runtime_visualization_settings(
            self,
            figure=figure,
        )

        figure.update_layout(
            margin=self.default_margin,
        )

        return figure

    def _validate_context(self) -> go.Figure | None:
        """
        Validate the graph context.

        Returns an information figure when the context is not usable.
        """
        if not is_enabled(
            self.graph_toggle_value,
        ):
            return plottings._make_info_figure(
                "Graph disabled.",
            )

        if not str(self.uploaded_fcs_path or "").strip():
            return plottings._make_info_figure(
                "Upload an FCS file first.",
            )

        if self.backend is None:
            return plottings._make_info_figure(
                "No backend available for this file.",
            )

        if self.process is None:
            return plottings._make_info_figure(
                "Select a valid peak process.",
            )

        return None

    def _resolve_detector_channels(self) -> dict[str, Any]:
        """
        Resolve detector channel selections for the selected process.
        """
        return detectors.resolve_detector_channels_for_process(
            detector_dropdown_ids=self.detector_dropdown_ids,
            detector_dropdown_values=self.detector_dropdown_values,
            process_name=self.resolved_process_name,
        )

    def _get_missing_detector_channel_names(self) -> list[str]:
        """
        Return required detector channels that do not have selected columns.
        """
        missing_channel_names: list[str] = []

        for channel_name in graph_settings.get_required_detector_channels(self):
            if not str(self.detector_channels.get(channel_name) or "").strip():
                missing_channel_names.append(
                    str(
                        channel_name,
                    )
                )

        return missing_channel_names

    def _build_missing_detector_message(
        self,
        *,
        missing_channel_names: list[str],
    ) -> str:
        """
        Build a user visible missing detector message.
        """
        if len(missing_channel_names) == 1:
            return f"Select the {missing_channel_names[0]} detector channel first."

        return "Select the required detector channels first."

    def _build_process_settings(self) -> dict[str, Any]:
        """
        Build a dictionary of process setting values for the selected process.
        """
        process_settings = build_process_settings(
            process_setting_ids=self.process_setting_ids,
            process_setting_values=self.process_setting_values,
            process_name=self.resolved_process_name,
        )

        process_settings["filter_edge_artifacts"] = self.data_filter_value

        return process_settings

    def _edge_artifact_filter_is_enabled(self) -> bool:
        """
        Return whether shared zero/saturation filtering is enabled.
        """
        return resolve_edge_artifact_filter_enabled(
            process_settings=self.process_settings,
            default=True,
        )

    def _build_process_specific_figure(self) -> go.Figure:
        """
        Build the selected process figure.
        """
        custom_figure = self._try_build_custom_process_figure()

        if custom_figure is not None:
            return custom_figure

        graph_type = getattr(
            self.process,
            "graph_type",
            None,
        )

        if graph_type == "1d_histogram":
            return graph_histogram.build_default_1d_histogram_figure(self)

        if graph_type == "2d_scatter":
            return graph_scatter.build_default_2d_scatter_figure(self)

        return plottings._make_info_figure(
            "No graph implementation is available for this peak process.",
        )

    def _try_build_custom_process_figure(self) -> go.Figure | None:
        """
        Let a process provide its own figure implementation when available.
        """
        for method_name in (
            "build_graph_figure",
            "build_figure",
            "build_plot",
        ):
            method = getattr(
                self.process,
                method_name,
                None,
            )

            if not callable(method):
                continue

            figure = self._call_with_supported_arguments(
                method,
                backend=self.backend,
                uploaded_fcs_path=self.uploaded_fcs_path,
                process_name=self.resolved_process_name,
                detector_channels=self.detector_channels,
                process_settings=self.process_settings,
                peak_lines_payload=self.peak_lines_payload,
                n_bins_for_plots=graph_settings.resolve_number_of_bins(self),
                nbins=graph_settings.resolve_number_of_bins(self),
                max_events_for_plots=graph_settings.resolve_max_events_for_plots(self),
                max_events_for_analysis=graph_settings.resolve_max_events_for_plots(
                    self
                ),
                xscale_selection=self.xscale_selection,
                yscale_selection=self.yscale_selection,
                runtime_config_data=self.runtime_config_data,
            )

            if getattr(self.process, "graph_type", None) == "2d_scatter":
                Scatter2DGraph.apply_formatting(
                    figure=figure,
                    title=str(
                        getattr(
                            self.process,
                            "process_label",
                            "2D scatter",
                        )
                    ),
                    x_axis_title=str(
                        figure.layout.xaxis.title.text or "x",
                    ),
                    y_axis_title=str(
                        figure.layout.yaxis.title.text or "y",
                    ),
                    x_axis_type="log"
                    if graph_settings.x_axis_is_log(self)
                    else "linear",
                    y_axis_type="log"
                    if graph_settings.y_axis_is_log(self)
                    else "linear",
                    show_grid=graph_settings.show_grid_by_default(self),
                    hovermode="closest",
                    uirevision=f"peak_workflow_{self.resolved_process_name}_2d_scatter",
                )

                figure = graph_overlays.add_2d_overlays(
                    self,
                    figure=figure,
                )

                if self._advanced_mode_is_enabled():
                    figure = graph_overlays.add_2d_advanced_overlays(
                        self,
                        figure=figure,
                    )

            return figure

        return None

    def _advanced_mode_is_enabled(self) -> bool:
        """
        Return whether advanced mode is enabled for graph diagnostics.
        """
        return is_enabled(
            self.advanced_mode_value,
        )

    def _is_rosetta_script_process(self) -> bool:
        """
        Return whether the currently selected process is the Rosetta Script.
        """
        return _is_rosetta_script_process_name(
            self.resolved_process_name,
        )

    def _call_with_supported_arguments(
        self,
        callable_object: Any,
        **candidate_arguments: Any,
    ) -> Any:
        """
        Call a function with only the keyword arguments it accepts.
        """
        signature = inspect.signature(
            callable_object,
        )

        accepts_arbitrary_keywords = any(
            parameter.kind == inspect.Parameter.VAR_KEYWORD
            for parameter in signature.parameters.values()
        )

        if accepts_arbitrary_keywords:
            return callable_object(
                **candidate_arguments,
            )

        accepted_arguments = {
            argument_name: argument_value
            for argument_name, argument_value in candidate_arguments.items()
            if argument_name in signature.parameters
        }

        return callable_object(
            **accepted_arguments,
        )


def build_process_settings(
    *,
    process_setting_ids: list[dict[str, Any]],
    process_setting_values: list[Any],
    process_name: str,
) -> dict[str, Any]:
    """
    Build a dictionary of process setting values for the selected process.

    Kept as a module level helper for compatibility with older imports.
    """
    resolved_process_name = registry.resolve_process_name(
        process_name,
    )

    process_settings: dict[str, Any] = {}

    for process_setting_id, process_setting_value in zip(
        process_setting_ids or [],
        process_setting_values or [],
        strict=False,
    ):
        if not isinstance(process_setting_id, dict):
            continue

        if process_setting_id.get("process") != resolved_process_name:
            continue

        setting_name = process_setting_id.get(
            "setting",
        )

        if not isinstance(setting_name, str):
            continue

        process_settings[setting_name] = process_setting_value

    return process_settings
