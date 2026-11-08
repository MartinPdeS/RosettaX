"""Data quality review card for scattering calibration."""

import dash
import dash_bootstrap_components as dbc
from . import services
from RosettaX.utils import ui_forms


class DataQuality:
    """Assemble the optional scattering data quality review."""

    def __init__(self, *, page, section_number: int, card_color: str) -> None:
        self.page = page
        self.section_number = section_number
        self.card_color = card_color

    def get_layout(self) -> dbc.Card:
        """Build the quality review card."""
        ids = self.page.ids.Quality
        return dbc.Card([
            dbc.CardHeader(ui_forms.build_title_with_info(
                title=f"{self.section_number}. Review data quality",
                tooltip_target_id=ids.description_target,
                tooltip_id=ids.description_tooltip,
                tooltip_text=(
                    "Inspect the selected FCS channels and recent peak-detection "
                    "diagnostics for invalid values, detector saturation, rejected "
                    "peaks, and calibration readiness. This review is optional."
                ),
            )),
            dbc.CardBody([
                dash.html.P("Inspect the selected channels and the latest peak detection before fitting. This review is optional."),
                dbc.Button("Test data quality", id=ids.run, color="primary", n_clicks=0),
                dash.dcc.Store(id=ids.snapshot),
                dash.html.Div("Select a file and detector channels, then test data quality.", id=ids.result, style={"marginTop": "12px"}),
            ], style=ui_forms.build_workflow_section_body_style()),
        ])

    def register_callbacks(self) -> None:
        """Register the review action and invalidate it when its inputs change."""
        ids = self.page.ids
        peak_ids = ids.Scattering

        @dash.callback(
            dash.Output(ids.Quality.snapshot, "data"),
            dash.Output(ids.Quality.result, "children"),
            dash.Input(ids.Quality.run, "n_clicks"),
            dash.Input(ids.State.page_state_store, "data"),
            dash.Input(peak_ids.process_dropdown, "value"),
            dash.Input(peak_ids.process_detector_dropdown_pattern(), "value"),
            dash.Input(peak_ids.process_setting_pattern(), "value"),
            dash.Input(peak_ids.advanced_mode_switch, "value"),
            dash.Input(peak_ids.data_filter_switch, "value"),
            dash.Input(peak_ids.axis_scale_toggle, "value"),
            dash.Input(ids.Upload.max_events_for_plots_input, "value"),
            dash.Input(ids.Calibration.bead_table, "data"),
            dash.Input(peak_ids.process_status_pattern(), "children"),
            dash.State(peak_ids.process_detector_dropdown_pattern(), "id"),
            dash.State(peak_ids.process_status_pattern(), "id"),
            dash.State(ids.Quality.snapshot, "data"),
            prevent_initial_call=True,
        )
        def review_quality(clicks, page_state, process, detector_values, settings, advanced, data_filter, axis_scale, max_events, table, statuses, detector_ids, status_ids, snapshot):
            del clicks
            state = page_state if isinstance(page_state, dict) else {}
            file_path = state.get("uploaded_fcs_path")
            selected_channels = [value for identifier, value in zip(detector_ids or [], detector_values or []) if identifier.get("process") == process and value]
            selected_status = next((services.status_text(value=value) for identifier, value in zip(status_ids or [], statuses or []) if identifier.get("process") == process), "")
            signature = {"file": file_path, "process": process, "detectors": detector_values, "settings": settings, "advanced": advanced, "filter": data_filter, "axis_scale": axis_scale, "max_events": max_events, "table": table, "statuses": statuses}
            if dash.ctx.triggered_id != ids.Quality.run:
                if snapshot and snapshot != signature:
                    return None, dbc.Alert("Inputs or peak results changed. Test data quality again and rerun peak detection if its settings changed.", color="warning")
                return dash.no_update, dash.no_update
            if not file_path or not selected_channels:
                return None, dbc.Alert("Load an FCS file and select at least one detector channel first.", color="warning")
            try:
                report = services.inspect_channels(file_path=file_path, channels=selected_channels)
            except (OSError, ValueError, KeyError, RuntimeError) as error:
                return None, dbc.Alert(f"Could not inspect the selected file or channels: {error}", color="danger")
            peak_count = services.count_measured_peaks(table_data=table)
            children = [dash.html.H5("File and signal quality"), dash.html.P(f"File: {state.get('uploaded_filename') or file_path}; total events: {report['total_events'] or 'unavailable'}. Statistics below use up to the first 100,000 events." )]
            for channel in report["channels"]:
                count = channel["count"]
                def fraction(value):
                    return f"{value:,} ({100 * value / count:.2f}%)" if count else "0 (no events)"
                range_text = f"{channel['range']:g}; at or above range − 1: {fraction(channel['at_range'])}" if channel["range"] is not None else "unavailable"
                children.append(dash.html.P(f"{channel['channel']} — sampled: {count:,}; non-finite: {fraction(channel['nonfinite'])}; zero: {fraction(channel['zero'])}; negative: {fraction(channel['negative'])}; metadata detector range: {range_text}."))
            children.extend([dash.html.H5("Peak detection and calibration readiness"), dash.html.P(f"Algorithm: {process or 'not selected'}. Measured peaks currently in the calibration table: {peak_count}."), dash.html.P(selected_status or "No peak detection diagnostics available. Run peak detection to see its results.", style={"whiteSpace": "pre-wrap"}), dash.html.P("Peak diagnostics describe the last detection run; rerun it after changing its settings. Check reference assignments before fitting." )])
            if peak_count <= 2:
                children.append(dbc.Alert("Two or fewer measured peaks are available. A two-point fit provides limited evidence of calibration quality.", color="warning"))
            return signature, children
