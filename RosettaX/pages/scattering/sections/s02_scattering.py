from dataclasses import dataclass
from typing import Any, Tuple
import logging

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objs as go

from RosettaX.pages import styling
from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.utils.reader import FCSFile
from RosettaX.utils.plottings import make_histogram_with_lines, _make_info_figure
from RosettaX.utils.casting import _as_int
from RosettaX.utils.service import build_channel_options_from_file


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ScatteringCallbackInputs:
    """
    Parsed callback inputs for the scattering histogram section.
    """

    debug_enabled: bool
    scattering_channel: str
    nbins: int
    max_events: int
    yscale_selection: Any


class ScatteringSection:
    """
    Render and manage a scattering detector histogram section without thresholding.

    Responsibilities
    ----------------
    - Populate the scattering detector dropdown from the uploaded FCS file.
    - Render the detector controls and optional histogram.
    - Build a histogram view for the selected detector.
    """

    def __init__(self, page) -> None:
        self.page = page
        logger.debug("Initialized ScatteringSection with page=%r", page)

    def get_layout(self) -> dbc.Card:
        return dbc.Card(
            [
                self._build_header(),
                self._build_body(),
            ]
        )

    def _build_header(self) -> dbc.CardHeader:
        return dbc.CardHeader("2. Scattering channel")

    def _build_body(self) -> dbc.CardBody:
        return dbc.CardBody(
            [
                dash.html.Br(),
                self._build_detector_row(),
                dash.html.Br(),
                self._build_debug_switch_row(),
                dash.html.Br(),
                self._build_debug_controls_container(),
            ]
        )

    def _build_detector_row(self) -> dash.html.Div:
        return dash.html.Div(
            [
                dash.html.Div("Scattering detector:"),
                dash.dcc.Dropdown(
                    id=self.page.ids.Scattering.detector_dropdown,
                    style={"width": "500px"},
                    optionHeight=50,
                    maxHeight=500,
                    searchable=True,
                ),
            ],
            style=styling.CARD,
        )

    def _build_debug_switch_row(self) -> dash.html.Div:
        return dash.html.Div(
            [
                dbc.Checklist(
                    id=self.page.ids.Scattering.debug_switch,
                    options=[{"label": "Show histogram", "value": "enabled"}],
                    value=[],
                    switch=True,
                ),
            ],
            style=styling.CARD,
        )

    def _build_debug_controls_container(self) -> dash.html.Div:
        return dash.html.Div(
            [
                self._build_histogram_graph(),
                dash.html.Br(),
                self._build_yscale_switch(),
                dash.html.Br(),
                self._build_nbins_row(),
            ],
            id=self.page.ids.Scattering.debug_container,
            style={"display": "none"},
        )

    def _build_nbins_row(self) -> dash.html.Div:
        runtime_config = RuntimeConfig()

        return dash.html.Div(
            [
                dash.html.Div("Number of bins:"),
                dash.dcc.Input(
                    id=self.page.ids.Scattering.nbins_input,
                    type="number",
                    min=10,
                    step=10,
                    value=runtime_config.Default.n_bins_for_plots,
                    style={"width": "160px"},
                ),
            ],
            style=styling.CARD,
        )

    def _build_yscale_switch(self) -> dbc.Checklist:
        return dbc.Checklist(
            id=self.page.ids.Scattering.yscale_switch,
            options=[{"label": "Log scale (counts)", "value": "log"}],
            value=["log"],
            switch=True,
        )

    def _build_histogram_graph(self) -> dash.dcc.Loading:
        return dash.dcc.Loading(
            dash.dcc.Graph(
                id=self.page.ids.Scattering.graph_hist,
                style=self.page.style["graph"],
            ),
            type="default",
        )

    def register_callbacks(self) -> None:
        logger.debug("Registering scattering histogram callbacks.")

        @dash.callback(
            dash.Output(self.page.ids.Scattering.detector_dropdown, "options"),
            dash.Output(self.page.ids.Scattering.detector_dropdown, "value"),
            dash.Input(self.page.ids.Upload.fcs_path_store, "data"),
            dash.State(self.page.ids.Scattering.detector_dropdown, "value"),
            prevent_initial_call=False,
        )
        def populate_scattering_detector_dropdown(
            uploaded_fcs_path: Any,
            current_detector_value: Any,
        ) -> tuple:
            return self._populate_scattering_detector_dropdown(
                uploaded_fcs_path=uploaded_fcs_path,
                current_detector_value=current_detector_value,
            )

        @dash.callback(
            dash.Output(self.page.ids.Scattering.debug_container, "style"),
            dash.Input(self.page.ids.Scattering.debug_switch, "value"),
            prevent_initial_call=False,
        )
        def toggle_scattering_histogram_debug(debug_switch_value: Any) -> dict:
            return self._toggle_debug_container(debug_switch_value)

        @dash.callback(
            dash.Output(self.page.ids.Scattering.nbins_input, "value"),
            dash.Input("runtime-config-store", "data"),
            prevent_initial_call=False,
        )
        def sync_scattering_histogram_nbins_from_runtime_store(runtime_config_data: Any) -> int:
            return self._resolve_nbins_from_runtime_store(runtime_config_data)

        @dash.callback(
            dash.Output(self.page.ids.Scattering.graph_hist, "figure"),
            dash.Input(self.page.ids.Scattering.detector_dropdown, "value"),
            dash.Input(self.page.ids.Scattering.nbins_input, "value"),
            dash.Input(self.page.ids.Scattering.yscale_switch, "value"),
            dash.Input(self.page.ids.Scattering.debug_switch, "value"),
            dash.State(self.page.ids.Upload.max_events_for_plots_input, "value", allow_optional=True),
            prevent_initial_call=False,
        )
        def scattering_histogram_section(
            scattering_channel: Any,
            scattering_nbins: Any,
            yscale_selection: Any,
            debug_switch_value: Any,
            max_events_for_plots: Any,
        ) -> go.Figure:
            callback_inputs = self._parse_scattering_histogram_callback_inputs(
                scattering_channel=scattering_channel,
                scattering_nbins=scattering_nbins,
                yscale_selection=yscale_selection,
                debug_switch_value=debug_switch_value,
                max_events_for_plots=max_events_for_plots,
            )
            return self._run_scattering_histogram_callback(callback_inputs)

    def _populate_scattering_detector_dropdown(
        self,
        *,
        uploaded_fcs_path: Any,
        current_detector_value: Any,
    ) -> tuple:
        if not uploaded_fcs_path:
            logger.debug("No uploaded FCS path available. Returning empty dropdown.")
            return [], None

        try:
            channels = build_channel_options_from_file(
                uploaded_fcs_path,
                preferred_scatter=current_detector_value,
            )
        except Exception:
            logger.exception(
                "Failed to extract scattering channels from uploaded_fcs_path=%r",
                uploaded_fcs_path,
            )
            return [], None

        scattering_detector_options = list(channels.scatter_options or [])
        scattering_detector_value = channels.scatter_value

        logger.debug(
            "Resolved scattering detector dropdown with %r options and value=%r",
            len(scattering_detector_options),
            scattering_detector_value,
        )

        return scattering_detector_options, scattering_detector_value

    def _toggle_debug_container(self, debug_switch_value: Any) -> dict:
        debug_enabled = self._is_switch_enabled(debug_switch_value)
        return {"display": "block"} if debug_enabled else {"display": "none"}

    def _resolve_nbins_from_runtime_store(self, runtime_config_data: Any) -> int:
        runtime_config = RuntimeConfig()

        if not isinstance(runtime_config_data, dict):
            return runtime_config.Default.n_bins_for_plots

        return runtime_config_data.get(
            "n_bins_for_plots",
            runtime_config.Default.n_bins_for_plots,
        )

    def _parse_scattering_histogram_callback_inputs(
        self,
        *,
        scattering_channel: Any,
        scattering_nbins: Any,
        yscale_selection: Any,
        debug_switch_value: Any,
        max_events_for_plots: Any,
    ) -> ScatteringCallbackInputs:
        debug_enabled = self._is_switch_enabled(debug_switch_value)
        max_events, nbins = self._parse_limits(
            max_events_for_plots=max_events_for_plots,
            scattering_nbins=scattering_nbins,
        )
        scattering_channel_clean = self._clean_channel_name(scattering_channel)

        parsed_inputs = ScatteringCallbackInputs(
            debug_enabled=debug_enabled,
            scattering_channel=scattering_channel_clean,
            nbins=nbins,
            max_events=max_events,
            yscale_selection=yscale_selection,
        )

        logger.debug("Parsed scattering histogram callback inputs=%r", parsed_inputs)
        return parsed_inputs

    def _run_scattering_histogram_callback(
        self,
        callback_inputs: ScatteringCallbackInputs,
    ) -> go.Figure:
        logger.debug(
            "_run_scattering_histogram_callback called with callback_inputs=%r",
            callback_inputs,
        )

        return self._build_scattering_histogram(
            debug_enabled=callback_inputs.debug_enabled,
            scattering_channel=callback_inputs.scattering_channel,
            nbins=callback_inputs.nbins,
            max_events=callback_inputs.max_events,
            yscale_selection=callback_inputs.yscale_selection,
        )

    def _is_switch_enabled(self, switch_value: Any) -> bool:
        return isinstance(switch_value, list) and ("enabled" in switch_value)

    def _clean_channel_name(self, scattering_channel: Any) -> str:
        if scattering_channel is None:
            return ""

        scattering_channel_clean = str(scattering_channel).strip()

        if scattering_channel_clean.lower() == "none":
            return ""

        return scattering_channel_clean

    def _parse_limits(self, *, max_events_for_plots: Any, scattering_nbins: Any) -> Tuple[int, int]:
        runtime_config = RuntimeConfig()

        max_events = _as_int(
            max_events_for_plots if max_events_for_plots is not None else runtime_config.Default.max_events_for_analysis,
            default=runtime_config.Default.max_events_for_analysis,
            min_value=10_000,
            max_value=5_000_000,
        )

        nbins = _as_int(
            scattering_nbins,
            default=runtime_config.Default.n_bins_for_plots,
            min_value=10,
            max_value=5000,
        )

        return max_events, nbins

    def _build_scattering_histogram(
        self,
        *,
        debug_enabled: bool,
        scattering_channel: str,
        nbins: int,
        max_events: int,
        yscale_selection: Any,
    ) -> go.Figure:
        logger.debug(
            "_build_scattering_histogram called with debug_enabled=%r scattering_channel=%r "
            "nbins=%r max_events=%r yscale_selection=%r",
            debug_enabled,
            scattering_channel,
            nbins,
            max_events,
            yscale_selection,
        )

        if not debug_enabled:
            return _make_info_figure("Histogram is hidden.")

        if self.page.backend is None:
            return _make_info_figure("Backend is not available.")

        if not scattering_channel:
            return _make_info_figure("Select a scattering detector first.")

        if not getattr(self.page.backend, "file_path", None):
            return _make_info_figure("No FCS file is loaded.")

        use_log = isinstance(yscale_selection, list) and ("log" in yscale_selection)

        try:
            with FCSFile(self.page.backend.file_path, writable=False) as fcs_file:
                values = fcs_file.column_copy(scattering_channel, dtype=float, n=max_events)
        except Exception:
            logger.exception(
                "Failed to read scattering histogram values from file_path=%r channel=%r max_events=%r",
                self.page.backend.file_path,
                scattering_channel,
                max_events,
            )
            raise

        if values is None or len(values) == 0:
            return _make_info_figure("No data available for the selected detector.")

        figure = make_histogram_with_lines(
            values=values,
            nbins=nbins,
            xaxis_title="Scattering (a.u.)",
            line_positions=[],
            line_labels=[],
        )
        figure.update_yaxes(type="log" if use_log else "linear")
        figure.update_layout(separators=".,")

        return figure