# -*- coding: utf-8 -*-

import json
import logging
from html import escape
from pathlib import Path
from urllib.parse import unquote

from dash import Dash
from flask import Response, jsonify, request
from werkzeug.exceptions import RequestEntityTooLarge

from RosettaX.utils.paths import (
    resolve_calibration_file_path as resolve_safe_calibration_file_path,
)
from RosettaX.utils.streamed_uploads import (
    DEFAULT_STREAMED_UPLOAD_DIRECTORY,
    stage_streamed_upload,
)
from RosettaX.utils.upload_limits import format_upload_size

logger = logging.getLogger(__name__)


def resolve_calibration_file_path(folder: str, file_name: str) -> Path:
    """
    Resolve a calibration JSON file path safely within the allowed calibration folders.
    """
    return resolve_safe_calibration_file_path(
        folder=folder,
        file_name=file_name,
    )


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


def build_calibration_json_error_document() -> str:
    """
    Build a generic standalone HTML error document for calibration JSON failures.
    """
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Could not open calibration</title>
</head>
<body>
    <h2>Could not open calibration</h2>
    <pre>The requested calibration file could not be opened.</pre>
</body>
</html>
"""


def register_server_routes(app: Dash) -> None:
    """
    Register Flask routes that should bypass Dash page routing.
    """
    logger.debug("Registering Flask server routes")

    @app.server.post("/api/uploads/stream")
    def receive_streamed_upload():
        """Persist a raw request body and return an opaque upload token."""
        encoded_filename = request.headers.get("X-RosettaX-Filename", "")

        try:
            streamed_upload = stage_streamed_upload(
                stream=request.stream,
                filename=unquote(encoded_filename),
                content_length=request.content_length,
                staging_directory=Path(
                    app.server.config.get(
                        "ROSETTAX_STREAMED_UPLOAD_DIRECTORY",
                        DEFAULT_STREAMED_UPLOAD_DIRECTORY,
                    )
                ),
                max_upload_bytes=app.server.config.get("ROSETTAX_MAX_UPLOAD_BYTES"),
            )
            return jsonify(
                {
                    "token": streamed_upload.token,
                    "filename": streamed_upload.filename,
                    "size_bytes": streamed_upload.size_bytes,
                }
            )
        except RequestEntityTooLarge:
            max_upload_bytes = app.server.config.get("ROSETTAX_MAX_UPLOAD_BYTES")
            size_text = (
                format_upload_size(max_upload_bytes) if max_upload_bytes else "configured limit"
            )
            return jsonify(
                {
                    "error": f"Upload exceeds the maximum file size of {size_text}."
                }
            ), 413
        except ValueError as exception:
            logger.warning("Rejected streamed upload: %s", exception)
            return jsonify({"error": str(exception)}), 400
        except Exception as exception:
            logger.exception("Failed to receive streamed upload")
            return jsonify(
                {"error": f"Upload failed: {type(exception).__name__}: {exception}"}
            ), 500

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

            error_document = build_calibration_json_error_document()

            return Response(error_document, mimetype="text/html", status=400)
