# -*- coding: utf-8 -*-

from RosettaX.pages.p03_scattering.state import ScatteringPageState


class Test_ScatteringPageState:
    def test_from_dict_preserves_scattering_peak_lines_payload(self):
        state = ScatteringPageState.from_dict(
            {
                "uploaded_fcs_path": "/tmp/example.fcs",
                "peak_lines_payload": {
                    "positions": [1.0],
                    "labels": ["legacy"],
                },
                "scattering_peak_lines_payload": {
                    "positions": [2.0],
                    "labels": ["scattering"],
                },
            }
        )

        payload = state.to_dict()

        assert payload["peak_lines_payload"]["positions"] == [1.0]
        assert payload["scattering_peak_lines_payload"]["positions"] == [2.0]

    def test_update_keeps_scattering_peak_lines_payload_when_other_fields_change(self):
        initial_state = ScatteringPageState.from_dict(
            {
                "peak_lines_payload": {
                    "positions": [1.0],
                    "labels": ["legacy"],
                },
                "scattering_peak_lines_payload": {
                    "positions": [2.0],
                    "labels": ["scattering"],
                },
            }
        )

        updated_state = initial_state.update(
            scattering_parameters_payload={"mie_model": "Solid Sphere"},
            calibration_model_graph_payload={"data": []},
        )

        payload = updated_state.to_dict()

        assert payload["peak_lines_payload"]["positions"] == [1.0]
        assert payload["scattering_peak_lines_payload"]["positions"] == [2.0]
        assert payload["scattering_parameters_payload"] == {"mie_model": "Solid Sphere"}
