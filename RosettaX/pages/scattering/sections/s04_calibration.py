import logging
from dataclasses import dataclass
from typing import Any, Optional

import dash
import dash_bootstrap_components as dbc


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CalibrationActionResult:
    result_out: Any = dash.no_update

    def to_tuple(self) -> tuple:
        return (self.result_out,)


class CalibrationSection:
    def __init__(self, page) -> None:
        self.page = page
        logger.debug("Initialized scatter CalibrationSection with page=%r", page)

    def get_layout(self) -> dbc.Card:
        logger.debug("Building scatter calibration section layout.")
        return dbc.Card(
            [
                self._build_header(),
                self._build_collapse(),
            ]
        )

    def _get_layout(self) -> dbc.Card:
        return self.get_layout()

    def _build_header(self) -> dbc.CardHeader:
        logger.debug("Building scatter calibration header.")
        return dbc.CardHeader("3. Calibration")

    def _build_collapse(self) -> dbc.Collapse:
        logger.debug("Building scatter calibration collapse.")
        return dbc.Collapse(
            self._build_body(),
            id=self.page.ids.Export.collapse,
            is_open=True,
        )

    def _build_body(self) -> dbc.CardBody:
        logger.debug("Building scatter calibration body.")
        return dbc.CardBody(
            dash.html.Div(
                [
                    self._build_run_calibration_row(),
                    self._build_spacing(),
                    self._build_interpolation_block(),
                    self._build_spacing(),
                    self._build_result_output(),
                ],
                style=self._build_body_style(),
            )
        )

    def _build_body_style(self) -> dict:
        style = {
            "display": "flex",
            "flexDirection": "column",
            "gap": "6px",
            **self.page.style["body_scroll"],
        }
        logger.debug("Scatter calibration body style=%r", style)
        return style

    def _build_run_calibration_row(self) -> dash.html.Div:
        logger.debug("Building run calibration row.")
        return dash.html.Div(
            [
                self._build_run_calibration_button(),
                self._build_file_name_input(),
                self._build_save_export_button(),
            ],
            style={"display": "flex", "alignItems": "center", "gap": "8px", "flexWrap": "wrap"},
        )

    def _build_run_calibration_button(self) -> dash.html.Button:
        logger.debug("Building run calibration button.")
        return dash.html.Button(
            "Run Scatter Calibration",
            id=self.page.ids.Export.run_calibration_btn,
            n_clicks=0,
        )

    def _build_file_name_input(self) -> dash.dcc.Input:
        logger.debug("Building file name input.")
        return dash.dcc.Input(
            id=self.page.ids.Export.file_name,
            type="text",
            placeholder="Enter file name",
            style={"width": "200px"},
        )

    def _build_save_export_button(self) -> dash.html.Button:
        logger.debug("Building save/export calibration button.")
        return dash.html.Button(
            "Save/Export Scatter Calibration",
            id=self.page.ids.Export.save_export_btn,
            n_clicks=0,
        )

    def _build_interpolation_block(self) -> dash.html.Div:
        logger.debug("Building interpolation block.")
        return dash.html.Div(
            [
                dash.html.Div("Interpolate (optional):"),
                self._build_interpolation_inputs_row(),
            ],
            style={"display": "flex", "flexDirection": "column", "gap": "6px"},
        )

    def _build_interpolation_inputs_row(self) -> dash.html.Div:
        logger.debug("Building interpolation inputs row.")
        return dash.html.Div(
            [
                self._build_interpolation_method_input(),
                self._build_interpolation_au_input(),
                self._build_interpolation_area_input(),
                self._build_interpolation_button(),
            ],
            style={"display": "flex", "alignItems": "center", "gap": "8px", "flexWrap": "wrap"},
        )

    def _build_interpolation_method_input(self) -> dash.dcc.Input:
        logger.debug("Building interpolation method input.")
        return dash.dcc.Input(
            id=self.page.ids.Export.interpolate_method,
            type="text",
            placeholder="Enter interpolation method",
            style={"width": "200px"},
        )

    def _build_interpolation_au_input(self) -> dash.dcc.Input:
        logger.debug("Building interpolation AU input.")
        return dash.dcc.Input(
            id=self.page.ids.Export.interpolate_au,
            type="number",
            placeholder="Enter AU value",
            style={"width": "200px"},
        )

    def _build_interpolation_area_input(self) -> dash.dcc.Input:
        logger.debug("Building interpolation area input.")
        return dash.dcc.Input(
            id=self.page.ids.Export.interpolate_area,
            type="number",
            placeholder="Enter area value nm^2",
            style={"width": "200px"},
        )

    def _build_interpolation_button(self) -> dash.html.Button:
        logger.debug("Building interpolation button.")
        return dash.html.Button(
            "Interpolate Calibration",
            id=self.page.ids.Export.interpolate_btn,
            n_clicks=0,
        )

    def _build_result_output(self) -> dash.html.Div:
        logger.debug("Building result output container.")
        return dash.html.Div(id=self.page.ids.Export.result_out)

    def _build_spacing(self) -> dash.html.Br:
        return dash.html.Br()

    def register_callbacks(self) -> None:
        logger.debug("Registering scatter calibration callbacks.")

        @dash.callback(
            dash.Output(self.page.ids.Export.result_out, "children"),
            dash.Input(self.page.ids.Export.run_calibration_btn, "n_clicks"),
            dash.State(self.page.ids.Export.file_name, "value"),
            prevent_initial_call=True,
        )
        def run_scatter_calibration(n_clicks: int, file_name: Optional[str]):
            logger.debug(
                "run_scatter_calibration called with n_clicks=%r file_name=%r",
                n_clicks,
                file_name,
            )

            if not n_clicks:
                logger.debug("No calibration click detected. Returning dash.no_update.")
                return CalibrationActionResult(result_out=dash.no_update).to_tuple()[0]

            file_name_clean = str(file_name or "").strip()
            display_name = file_name_clean or "<no file name>"

            logger.debug(
                "Scatter calibration action resolved display_name=%r for n_clicks=%r",
                display_name,
                n_clicks,
            )

            result = CalibrationActionResult(
                result_out=f"Scatter Calibration run {n_clicks} times with file name {display_name}."
            )

            logger.debug("run_scatter_calibration returning result=%r", result)
            return result.to_tuple()[0]