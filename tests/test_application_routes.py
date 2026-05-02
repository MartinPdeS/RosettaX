# -*- coding: utf-8 -*-

import dash

from RosettaX.application.routes import register_server_routes


class Test_ApplicationRoutes:
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
        register_server_routes(app)

        client = app.server.test_client()
        response = client.get("/calibration-json/fluorescence/%2E%2E/%2E%2E/secret.json")

        assert response.status_code == 400
        assert "Invalid calibration file path" in response.get_data(as_text=True)

    def test_calibration_json_route_returns_error_document_for_malformed_json(
        self,
        tmp_path,
        monkeypatch,
    ) -> None:
        fluorescence_directory = tmp_path / "fluorescence"
        fluorescence_directory.mkdir()
        (fluorescence_directory / "broken.json").write_text("{not valid json", encoding="utf-8")

        monkeypatch.setattr(
            "RosettaX.utils.directories.fluorescence_calibration",
            fluorescence_directory,
        )
        monkeypatch.setattr(
            "RosettaX.utils.directories.scattering_calibration",
            tmp_path / "scattering",
        )

        app = dash.Dash(__name__)
        register_server_routes(app)

        client = app.server.test_client()
        response = client.get("/calibration-json/fluorescence/broken.json")

        assert response.status_code == 400
        assert "Could not open calibration" in response.get_data(as_text=True)
        assert "JSONDecodeError" in response.get_data(as_text=True)
