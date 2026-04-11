# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any, Optional

import dash
import dash_bootstrap_components as dbc

from RosettaX.utils.reader import FCSFile


@dataclass(frozen=True)
class ApplySectionResult:
    status: Any = dash.no_update
    export_column_options: Any = dash.no_update
    export_column_values: Any = dash.no_update

    def to_tuple(self) -> tuple:
        return (
            self.status,
            self.export_column_options,
            self.export_column_values,
        )


class ApplySection:
    def __init__(self, page) -> None:
        self.page = page

    def get_layout(self) -> dbc.Card:
        return dbc.Card(
            [
                self._build_header(),
                self._build_body(),
            ]
        )

    def _build_header(self) -> dbc.CardHeader:
        return dbc.CardHeader("3. Apply and export")

    def _build_body(self) -> dbc.CardBody:
        return dbc.CardBody(
            [
                self._build_export_columns_section(),
                dash.html.Div(style={"height": "12px"}),
                self._build_action_button_row(),
                dash.html.Div(style={"height": "10px"}),
                self._build_status_alert(),
            ]
        )

    def _build_export_columns_section(self) -> dash.html.Div:
        return dash.html.Div(
            [
                dash.html.Div(
                    "Additional columns to export",
                    style={"marginBottom": "6px"},
                ),
                dash.dcc.Dropdown(
                    id=self.page.ids.Export.export_columns_dropdown,
                    options=[],
                    value=[],
                    multi=True,
                    placeholder="Select extra columns to export",
                    clearable=True,
                ),
                dash.html.Div(style={"height": "6px"}),
                dash.html.Small(
                    "The calibrated target channel will always be included. "
                    "These extra columns will be exported unchanged.",
                    style={"opacity": 0.75},
                ),
            ]
        )

    def _build_action_button_row(self) -> dash.html.Div:
        return dash.html.Div(
            [
                dbc.Button(
                    "Apply & export",
                    id=self.page.ids.Export.apply_and_export_button,
                    n_clicks=0,
                    color="primary",
                ),
            ],
            style={
                "display": "flex",
                "alignItems": "center",
                "gap": "12px",
            },
        )

    def _build_status_alert(self) -> dbc.Alert:
        return dbc.Alert(
            "Status will appear here.",
            id=self.page.ids.Export.status,
            color="secondary",
            style={"marginBottom": "0px"},
        )

    def register_callbacks(self) -> None:
        @dash.callback(
            dash.Output(self.page.ids.Export.export_columns_dropdown, "options"),
            dash.Output(self.page.ids.Export.export_columns_dropdown, "value"),
            dash.Input(self.page.ids.Stores.uploaded_fcs_path_store, "data"),
            dash.State(self.page.ids.Export.export_columns_dropdown, "value"),
            prevent_initial_call=False,
        )
        def populate_export_columns(
            uploaded_fcs_path: Any,
            current_export_columns: Any,
        ) -> tuple:
            resolved_uploaded_fcs_path = self._resolve_uploaded_fcs_path(uploaded_fcs_path)

            if not resolved_uploaded_fcs_path:
                return ApplySectionResult(
                    export_column_options=[],
                    export_column_values=[],
                ).to_tuple()[1:]

            try:
                with FCSFile(str(resolved_uploaded_fcs_path), writable=False) as fcs_file:
                    column_names = [str(name) for name in fcs_file.get_column_names()]
            except Exception:
                return ApplySectionResult(
                    export_column_options=[],
                    export_column_values=[],
                ).to_tuple()[1:]

            options = [{"label": column_name, "value": column_name} for column_name in column_names]
            allowed_values = {option["value"] for option in options}

            if isinstance(current_export_columns, list):
                resolved_values = [
                    str(value)
                    for value in current_export_columns
                    if str(value) in allowed_values
                ]
            else:
                resolved_values = []

            return options, resolved_values

        @dash.callback(
            dash.Output(self.page.ids.Export.status, "children"),
            dash.Input(self.page.ids.Export.apply_and_export_button, "n_clicks"),
            dash.State(self.page.ids.Stores.selected_calibration_path_store, "data"),
            dash.State(self.page.ids.ChannelPicker.dropdown, "value"),
            dash.State(self.page.ids.Export.export_columns_dropdown, "value"),
            prevent_initial_call=True,
        )
        def apply_and_export_calibration(
            n_clicks: int,
            selected_calibration: Any,
            target_channel: Any,
            export_columns: Any,
        ) -> tuple:
            del n_clicks

            if not selected_calibration:
                return ApplySectionResult(
                    status="Select a calibration first.",
                ).to_tuple()[:1]

            if not target_channel:
                return ApplySectionResult(
                    status="Select a target channel first.",
                ).to_tuple()[:1]

            resolved_export_columns = self._normalize_export_columns(export_columns)
            final_export_columns = self._build_final_export_columns(
                target_channel=target_channel,
                export_columns=resolved_export_columns,
            )

            return ApplySectionResult(
                status=(
                    f'Apply & export requested using calibration "{selected_calibration}" '
                    f'on channel "{target_channel}". '
                    f'Exported columns: {", ".join(final_export_columns)}.'
                ),
            ).to_tuple()[:1]

    @staticmethod
    def _resolve_uploaded_fcs_path(uploaded_fcs_path: Any) -> Optional[str]:
        if uploaded_fcs_path is None:
            return None

        if isinstance(uploaded_fcs_path, list):
            if not uploaded_fcs_path:
                return None
            return str(uploaded_fcs_path[0])

        return str(uploaded_fcs_path)

    @staticmethod
    def _normalize_export_columns(export_columns: Any) -> list[str]:
        if not isinstance(export_columns, list):
            return []

        return [str(column) for column in export_columns if str(column).strip()]

    @staticmethod
    def _build_final_export_columns(
        *,
        target_channel: Any,
        export_columns: list[str],
    ) -> list[str]:
        target_channel_str = str(target_channel)

        final_columns = [target_channel_str]
        for column_name in export_columns:
            if column_name != target_channel_str:
                final_columns.append(column_name)

        return final_columns