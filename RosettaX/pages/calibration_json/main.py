# -*- coding: utf-8 -*-

import json
import logging
from pathlib import Path

import dash
import dash_bootstrap_components as dbc
from dash import html

from RosettaX.utils.calibration_records import extract_calibration_summary
from RosettaX.utils.calibration_summary import build_calibration_summary_card
from RosettaX.utils import directories

logger = logging.getLogger(__name__)


def _resolve_calibration_file_path(folder: str, file_name: str) -> Path:
    normalized_folder = str(folder).strip().lower()

    if normalized_folder == "fluorescence":
        base_directory = Path(directories.fluorescence_calibration)
    elif normalized_folder == "scattering":
        base_directory = Path(directories.scattering_calibration)
    else:
        raise ValueError(f"Unsupported calibration folder: {folder}")

    resolved_path = (base_directory / file_name).resolve()
    resolved_base_directory = base_directory.resolve()

    if resolved_base_directory not in resolved_path.parents:
        raise ValueError("Invalid calibration file path.")

    return resolved_path


def layout(folder: str = "", file_name: str = "", **_kwargs):
    logger.debug(
        "Rendering calibration_json page with folder=%r file_name=%r",
        folder,
        file_name,
    )

    try:
        calibration_file_path = _resolve_calibration_file_path(folder, file_name)
        record = json.loads(calibration_file_path.read_text(encoding="utf-8"))
        summary = extract_calibration_summary(record)

        return html.Div(
            [
                html.H3(f"{folder} / {file_name}"),
                html.Div(style={"height": "12px"}),
                build_calibration_summary_card(summary),
                html.Div(style={"height": "16px"}),
                dbc.Card(
                    [
                        dbc.CardHeader("Raw JSON"),
                        dbc.CardBody(
                            html.Pre(
                                json.dumps(record, indent=4, ensure_ascii=False),
                                style={
                                    "whiteSpace": "pre-wrap",
                                    "fontFamily": "monospace",
                                    "fontSize": "0.95rem",
                                    "marginBottom": "0px",
                                },
                            )
                        ),
                    ]
                ),
            ],
            style={"padding": "20px"},
        )

    except Exception as exc:
        logger.exception(
            "Failed to render calibration JSON page for folder=%r file_name=%r",
            folder,
            file_name,
        )
        return html.Div(
            [
                html.H3("Could not open calibration"),
                html.Pre(f"{type(exc).__name__}: {exc}"),
            ],
            style={"padding": "20px"},
        )


dash.register_page(
    __name__,
    path_template="/calibration-json/<folder>/<file_name>",
    name="Calibration JSON",
    layout=layout,
)