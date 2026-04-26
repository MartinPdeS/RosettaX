# -*- coding: utf-8 -*-

import json
import logging
from html import escape
from pathlib import Path

from dash import Dash
from flask import Response

from RosettaX.utils import directories


logger = logging.getLogger(__name__)


def resolve_calibration_file_path(folder: str, file_name: str) -> Path:
    """
    Resolve a calibration JSON file path safely within the allowed calibration folders.
    """
    normalized_folder = str(folder).strip().lower()

    if normalized_folder == "fluorescence":
        base_directory = Path(directories.fluorescence_calibration)
    elif normalized_folder == "scattering":
        base_directory = Path(directories.scattering_calibration)
    else:
        raise ValueError(f"Unsupported calibration folder: {folder}")

    resolved_base_directory = base_directory.resolve()
    resolved_path = (resolved_base_directory / file_name).resolve()

    if resolved_base_directory not in resolved_path.parents:
        raise ValueError("Invalid calibration file path.")

    return resolved_path


def build_calibration_json_document(
    *,
    folder: str,
    file_name: str,
    formatted_json: str,
) -> str:
    """
    Build the standalone HTML document used to display calibration JSON files.
    """
    safe_title = escape(f"{folder} / {file_name}")
    safe_formatted_json = escape(formatted_json)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>{safe_title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            margin: 24px;
            background: #ffffff;
            color: #111111;
        }}
        h2 {{
            margin: 0 0 8px 0;
        }}
        .subtitle {{
            opacity: 0.72;
            margin-bottom: 18px;
        }}
        pre {{
            white-space: pre-wrap;
            word-break: break-word;
            font-family: Menlo, Monaco, Consolas, monospace;
            font-size: 14px;
            background: #f6f8fa;
            border: 1px solid #d0d7de;
            border-radius: 8px;
            padding: 16px;
            margin: 0;
        }}
    </style>
</head>
<body>
    <h2>Calibration JSON</h2>
    <div class="subtitle">{safe_title}</div>
    <pre>{safe_formatted_json}</pre>
</body>
</html>
"""


def build_calibration_json_error_document(exception: Exception) -> str:
    """
    Build the standalone HTML error document used when calibration JSON loading fails.
    """
    safe_exception_name = escape(type(exception).__name__)
    safe_exception_message = escape(str(exception))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Could not open calibration</title>
</head>
<body>
    <h2>Could not open calibration</h2>
    <pre>{safe_exception_name}: {safe_exception_message}</pre>
</body>
</html>
"""


def register_server_routes(app: Dash) -> None:
    """
    Register Flask routes that should bypass Dash page routing.
    """
    logger.debug("Registering Flask server routes")

    @app.server.route("/calibration-json/<folder>/<path:file_name>")
    def serve_calibration_json(folder: str, file_name: str):
        logger.debug(
            "serve_calibration_json called with folder=%r file_name=%r",
            folder,
            file_name,
        )

        try:
            calibration_file_path = resolve_calibration_file_path(folder, file_name)
            calibration_record = json.loads(
                calibration_file_path.read_text(encoding="utf-8")
            )

            formatted_json = json.dumps(
                calibration_record,
                indent=4,
                ensure_ascii=False,
            )

            html_document = build_calibration_json_document(
                folder=folder,
                file_name=file_name,
                formatted_json=formatted_json,
            )

            return Response(html_document, mimetype="text/html")

        except Exception as exception:
            logger.exception(
                "Failed to serve calibration JSON for folder=%r file_name=%r",
                folder,
                file_name,
            )

            error_document = build_calibration_json_error_document(exception)

            return Response(error_document, mimetype="text/html", status=400)