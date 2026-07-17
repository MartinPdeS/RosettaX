# -*- coding: utf-8 -*-

import sys
import types
from pathlib import Path

import dash
from dash import html


class _DashBootstrapComponentsSentinel:
    def __call__(self, *args, **kwargs):
        return None

    def __getattr__(self, name):
        return self


class _DashBootstrapComponentsStub(types.ModuleType):
    def __getattr__(self, name):
        return _DashBootstrapComponentsSentinel()


sys.modules.setdefault(
    "dash_bootstrap_components",
    _DashBootstrapComponentsStub("dash_bootstrap_components"),
)

from RosettaX.application.routes import register_server_routes
from RosettaX.utils.streamed_uploads import resolve_streamed_upload


class Test_ApplicationRoutes:
    def test_streamed_upload_route_writes_request_body_and_returns_token(
        self,
        tmp_path,
    ) -> None:
        app = dash.Dash(__name__)
        app.layout = html.Div()
        app.server.config["ROSETTAX_STREAMED_UPLOAD_DIRECTORY"] = str(tmp_path)
        app.server.config["ROSETTAX_MAX_UPLOAD_BYTES"] = 1024
        app.server.config["MAX_CONTENT_LENGTH"] = 1024
        register_server_routes(app)

        response = app.server.test_client().post(
            "/api/uploads/stream",
            data=b"streamed FCS data",
            headers={
                "Content-Type": "application/octet-stream",
                "X-RosettaX-Filename": "sample%20one.fcs",
            },
        )

        assert response.status_code == 200
        payload = response.get_json()
        assert payload["filename"] == "sample_one.fcs"
        assert payload["size_bytes"] == len(b"streamed FCS data")

        upload = resolve_streamed_upload(
            payload["token"],
            staging_directory=Path(tmp_path),
            max_upload_bytes=1024,
        )
        assert upload.file_path.read_bytes() == b"streamed FCS data"

    def test_streamed_upload_route_rejects_request_above_configured_limit(
        self,
        tmp_path,
    ) -> None:
        app = dash.Dash(__name__)
        app.layout = html.Div()
        app.server.config["ROSETTAX_STREAMED_UPLOAD_DIRECTORY"] = str(tmp_path)
        app.server.config["ROSETTAX_MAX_UPLOAD_BYTES"] = 3
        app.server.config["MAX_CONTENT_LENGTH"] = 3
        register_server_routes(app)

        response = app.server.test_client().post(
            "/api/uploads/stream",
            data=b"too large",
            headers={"X-RosettaX-Filename": "sample.fcs"},
        )

        assert response.status_code == 413
        assert "maximum file size" in response.get_json()["error"]

    def test_calibration_json_route_rejects_path_traversal(
        self,
        tmp_path,
        monkeypatch,
    ) -> None:
        monkeypatch.setattr(
            "RosettaX.utils.directories.fluorescence_calibration",
            tmp_path / "fluorescence",
        )
        monkeypatch.setattr(
            "RosettaX.utils.directories.scattering_calibration",
            tmp_path / "scattering",
        )

        app = dash.Dash(__name__)
        app.layout = html.Div()
        register_server_routes(app)

        client = app.server.test_client()
        response = client.get(
            "/calibration-json/fluorescence/%2E%2E/%2E%2E/secret.json"
        )

        assert response.status_code == 400
        assert "could not be opened" in response.get_data(as_text=True)

    def test_calibration_json_route_returns_error_document_for_malformed_json(
        self,
        tmp_path,
        monkeypatch,
    ) -> None:
        fluorescence_directory = tmp_path / "fluorescence"
        fluorescence_directory.mkdir()
        (fluorescence_directory / "broken.json").write_text(
            "{not valid json", encoding="utf-8"
        )

        monkeypatch.setattr(
            "RosettaX.utils.directories.fluorescence_calibration",
            fluorescence_directory,
        )
        monkeypatch.setattr(
            "RosettaX.utils.directories.scattering_calibration",
            tmp_path / "scattering",
        )

        app = dash.Dash(__name__)
        app.layout = html.Div()
        register_server_routes(app)

        client = app.server.test_client()
        response = client.get("/calibration-json/fluorescence/broken.json")

        assert response.status_code == 400
        assert "Could not open calibration" in response.get_data(as_text=True)
        assert "could not be opened" in response.get_data(as_text=True)
