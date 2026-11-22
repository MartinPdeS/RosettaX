"""Shared Dash controls and event settings for manual peak picking."""

import dash
import dash_bootstrap_components as dbc
from .base import resolve_enabled_toggle_value
from RosettaX.utils.runtime_config import RuntimeConfig
from typing import Any


class ManualPeakControls:
    """Build manual controls from the detector roles and axes of a process."""

    detector_controls: tuple[tuple[str, str, str], ...] = ()
    log_axes: tuple[str, ...] = ()
    snap_mode_label = "peak"
    dropdown_option_height_px = 88
    dropdown_menu_max_height_px = 620
    default_snap_to_local_mode = True
    default_max_events_for_snap = 100_000
    default_snap_histogram_bins = 500

    def get_settings(self) -> list[dict[str, Any]]:
        """Return the local snap setting for the manual picker."""
        return [{
            "name": "snap_to_local_mode",
            "label": "Snap click to local mode",
            "kind": "select",
            "default_value": "enabled" if self.default_snap_to_local_mode else "disabled",
            "options": [{"label": "Enabled", "value": "enabled"}, {"label": "Disabled", "value": "disabled"}],
            "help": (
                f"When enabled, a click is adjusted to the local {self.snap_mode_label} mode nearby "
                "instead of using the raw click position."
            ),
        }]

    def get_required_detector_channels(self) -> list[str]:
        """Return required detector roles in display order."""
        return [channel for channel, _, _ in self.detector_controls]

    def build_controls(self, *, ids: Any) -> dash.html.Div:
        """Build detector selectors, snap switches, and peak clearing controls."""
        controls = []
        for index, (channel, label, placeholder) in enumerate(self.detector_controls):
            if index:
                controls.append(dash.html.Div(style={"height": "16px"}))
            controls.append(dash.html.Div(
                [
                    dash.html.Div(label, style={"marginBottom": "6px", "fontWeight": 500}),
                    dash.dcc.Dropdown(
                        id=ids.process_detector_dropdown(process_name=self.process_name, channel_name=channel),
                        placeholder=placeholder,
                        optionHeight=self.dropdown_option_height_px,
                        maxHeight=self.dropdown_menu_max_height_px,
                        searchable=True, clearable=False, persistence=True, persistence_type="session",
                        style={"width": "100%"},
                    ),
                ],
                style={"width": "100%", "maxWidth": "100%", "display": "block"},
            ))

        switches = []
        for axis in self.log_axes:
            switches.extend((
                self._build_switch(ids=ids, label=f"Log {axis} scale", setting_name=f"{axis}_log_scale"),
                dash.html.Div(style={"height": "8px"}),
            ))
        switches.append(self._build_switch(
            ids=ids, label="Snap click to local mode", setting_name="snap_to_local_mode",
            enabled_by_default=self.default_snap_to_local_mode,
        ))
        controls.extend((
            dash.html.Div(style={"height": "18px" if self.log_axes else "12px"}),
            dash.html.Div(switches, style={"display": "block", "width": "100%"}),
            dash.html.Div(style={"height": "16px"}),
            dash.html.Div(
                [
                    dbc.Button(
                        "Clear picked peaks", id=ids.process_action_button(process_name=self.process_name, action_name="clear"),
                        n_clicks=0, color="secondary", outline=True, size="sm",
                    ),
                    self.build_status_component(ids=ids),
                ],
                style={"display": "flex", "alignItems": "center", "gap": "12px", "flexWrap": "wrap", "width": "100%"},
            ),
        ))
        return dash.html.Div(
            controls, id=ids.process_controls_container(process_name=self.process_name),
            style={"display": "none", "width": "100%", "maxWidth": "100%"},
        )

    def _build_switch(
        self, *, ids: Any, label: str, setting_name: str, enabled_by_default: bool = False,
    ) -> dbc.Checklist:
        """Build a persisted manual picker switch."""
        return dbc.Checklist(
            id=ids.process_setting(process_name=self.process_name, setting_name=setting_name),
            options=[{"label": label, "value": "enabled"}], value=["enabled"] if enabled_by_default else [],
            switch=True, persistence=True, persistence_type="session", style={"display": "block", "width": "fit-content"},
        )

    def _snap_to_local_mode_is_enabled(self, *, process_settings: dict[str, Any] | None) -> bool:
        """Resolve the local snap switch with the process default."""
        value = process_settings.get("snap_to_local_mode") if isinstance(process_settings, dict) else None
        return resolve_enabled_toggle_value(value, default=self.default_snap_to_local_mode)

    def _resolve_snap_settings(self, *, runtime_config_data: Any) -> tuple[int, int]:
        """Return the analysis event limit and configured histogram bins."""
        runtime_config = RuntimeConfig.from_dict(runtime_config_data if isinstance(runtime_config_data, dict) else None)
        return (
            runtime_config.get_int("calibration.max_events_for_analysis", default=self.default_max_events_for_snap),
            runtime_config.get_int("calibration.n_bins_for_plots", default=self.default_snap_histogram_bins),
        )
