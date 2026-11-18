"""Dash controls for the automatic one-dimensional peak process."""

import dash
import dash_bootstrap_components as dbc
import json
from typing import Any


class Automatic1DControls:
    """Build detector, peak-count, action, and status controls."""

    def build_controls(
        self,
        *,
        ids: Any,
    ) -> dash.html.Div:
        """
        Build Dash controls for automatic 1D peak detection.

        Parameters
        ----------
        ids:
            Peak section id factory.

        Returns
        -------
        dash.html.Div
            Process controls.
        """
        return dash.html.Div(
            [
                self._build_detector_dropdown_block(
                    ids=ids,
                    label="Detector channel",
                    channel_name="primary",
                    tooltip_text=(
                        "Detector signal used to build the 1D histogram. "
                        "Choose the channel where the calibration populations are most clearly separated. "
                        "For bead calibration, this is usually the fluorescence or scattering channel being calibrated."
                    ),
                ),
                self._build_vertical_spacer(height_px=16),
                self._build_peak_count_block(
                    ids=ids,
                    tooltip_text=(
                        "Maximum number of peaks to return. "
                        "Use the expected number of calibration populations. "
                        "If this value is too high, weak shoulders or noise maxima may be returned. "
                        "If it is too low, true populations may be omitted."
                    ),
                ),
                self._build_vertical_spacer(height_px=16),
                self._build_action_row(ids=ids),
            ],
            id=ids.process_controls_container(
                process_name=self.process_name,
            ),
            style={
                "display": "none",
                "width": "100%",
                "maxWidth": "100%",
            },
        )

    def _build_vertical_spacer(
        self,
        *,
        height_px: int,
    ) -> dash.html.Div:
        """
        Build a vertical spacer.

        Parameters
        ----------
        height_px:
            Spacer height in pixels.

        Returns
        -------
        dash.html.Div
            Spacer.
        """
        return dash.html.Div(style={"height": f"{height_px}px"})

    def _build_detector_dropdown_block(
        self,
        *,
        ids: Any,
        label: str,
        channel_name: str,
        tooltip_text: str = "",
    ) -> dash.html.Div:
        """
        Build one full-width detector dropdown block.

        Parameters
        ----------
        ids:
            Peak section id factory.

        label:
            Display label.

        channel_name:
            Logical detector channel name.

        tooltip_text:
            Text displayed on hover.

        Returns
        -------
        dash.html.Div
            Detector dropdown block.
        """
        dropdown_id = ids.process_detector_dropdown(
            process_name=self.process_name,
            channel_name=channel_name,
        )

        tooltip_target_id = self._build_tooltip_target_id(
            component_id=dropdown_id,
            suffix="help",
        )

        return dash.html.Div(
            [
                self._build_label_with_tooltip(
                    label=label,
                    tooltip_text=tooltip_text,
                    tooltip_target_id=tooltip_target_id,
                ),
                dash.dcc.Dropdown(
                    id=dropdown_id,
                    placeholder="Select detector channel",
                    optionHeight=self.dropdown_option_height_px,
                    maxHeight=self.dropdown_menu_max_height_px,
                    searchable=True,
                    clearable=False,
                    persistence=True,
                    persistence_type="session",
                    style={"width": "100%"},
                ),
            ],
            style={
                "width": "100%",
                "maxWidth": "100%",
                "display": "block",
            },
        )

    def _build_peak_count_block(
        self,
        *,
        ids: Any,
        tooltip_text: str = "",
    ) -> dash.html.Div:
        """
        Build the peak count input block.

        Parameters
        ----------
        ids:
            Peak section id factory.

        tooltip_text:
            Text displayed on hover.

        Returns
        -------
        dash.html.Div
            Peak count input block.
        """
        tooltip_target_id = self._build_tooltip_target_id(
            component_id=ids.peak_count_input,
            suffix="help",
        )

        return dash.html.Div(
            [
                self._build_label_with_tooltip(
                    label="Number of peaks to look for",
                    tooltip_text=tooltip_text,
                    tooltip_target_id=tooltip_target_id,
                ),
                dash.dcc.Input(
                    id=ids.peak_count_input,
                    type="text",
                    inputMode="numeric",
                    value=str(self.default_peak_count),
                    debounce=True,
                    persistence=True,
                    persistence_type="session",
                    style={"width": "140px"},
                ),
            ],
            style={
                "width": "100%",
                "display": "block",
            },
        )

    def _build_label_with_tooltip(
        self,
        *,
        label: str,
        tooltip_text: str,
        tooltip_target_id: str,
    ) -> dash.html.Div:
        """
        Build a label with an optional hover tooltip.

        Parameters
        ----------
        label:
            Label text.

        tooltip_text:
            Tooltip content.

        tooltip_target_id:
            HTML id attached to the help marker.

        Returns
        -------
        dash.html.Div
            Label row.
        """
        tooltip_text = str(tooltip_text or "").strip()

        children: list[Any] = [
            dash.html.Div(label, style={"fontWeight": 500})
        ]

        if tooltip_text:
            children.extend(
                [
                    dash.html.Span(
                        "ⓘ",
                        id=tooltip_target_id,
                        style={
                            "marginLeft": "6px",
                            "cursor": "help",
                            "fontSize": "0.82rem",
                            "opacity": 0.75,
                            "userSelect": "none",
                        },
                    ),
                    dbc.Tooltip(tooltip_text, target=tooltip_target_id, placement="top"),
                ]
            )

        return dash.html.Div(
            children,
            style={
                "display": "flex",
                "alignItems": "center",
                "marginBottom": "6px",
            },
        )

    def _build_tooltip_target_id(
        self,
        *,
        component_id: Any,
        suffix: str,
    ) -> str:
        """
        Build a string tooltip target id from a Dash component id.

        Parameters
        ----------
        component_id:
            Source component id.

        suffix:
            Extra suffix appended to the tooltip id.

        Returns
        -------
        str
            String id safe for dbc.Tooltip target lookup.
        """
        if isinstance(component_id, dict):
            base_identifier = json.dumps(component_id, sort_keys=True, separators=(",", ":"))

        else:
            base_identifier = str(component_id)

        safe_identifier = (
            base_identifier
            .replace("{", "")
            .replace("}", "")
            .replace('"', "")
            .replace(":", "-")
            .replace(",", "-")
            .replace(" ", "-")
            .replace(".", "-")
            .replace("/", "-")
        )

        return f"{safe_identifier}-{suffix}"

    def _build_action_row(
        self,
        *,
        ids: Any,
    ) -> dash.html.Div:
        """
        Build action controls and status output.

        Parameters
        ----------
        ids:
            Peak section id factory.

        Returns
        -------
        dash.html.Div
            Action row.
        """
        return dash.html.Div(
            [
                dbc.Button(
                    "Find peaks",
                    id=ids.process_action_button(
                        process_name=self.process_name,
                        action_name="run",
                    ),
                    n_clicks=0,
                    color="secondary",
                    outline=True,
                    size="sm",
                ),
                self.build_status_component(ids=ids),
            ],
            style={
                "display": "flex",
                "alignItems": "center",
                "gap": "12px",
                "flexWrap": "wrap",
                "width": "100%",
            },
        )

