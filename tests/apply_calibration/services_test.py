# -*- coding: utf-8 -*-

import sys
import types
from types import SimpleNamespace

import pandas as pd


class _PyMieSimStub(types.ModuleType):
    experiment = types.SimpleNamespace()


class _PyMieSimUnitsStub(types.ModuleType):
    ureg = types.SimpleNamespace()


sys.modules.setdefault(
    "PyMieSim",
    _PyMieSimStub("PyMieSim"),
)
sys.modules.setdefault(
    "PyMieSim.units",
    _PyMieSimUnitsStub("PyMieSim.units"),
)

from RosettaX.workflow.apply_calibration import services


class Test_ApplyCalibrationServices:
    def test_build_legacy_dataframe_transformer_adds_new_calibrated_output_column(self, monkeypatch) -> None:
        monkeypatch.setattr(
            services,
            "apply_legacy_calibration_to_series",
            lambda values, calibration_payload, warning_messages=None, source_channel=None: values * 10.0,
        )

        transformer_factory = services.build_legacy_dataframe_transformer_factory(
            source_channel="FITC-A",
            output_channel_name="FITC (MESF)",
            calibration_payload={
                "source_channel": "FITC-A",
                "applied_output_channel_name": "FITC (MESF)",
            },
        )

        transformer = transformer_factory("/tmp/input.fcs")
        dataframe = pd.DataFrame(
            {
                "FITC-A": [1.0, 2.0, 3.0],
                "Time": [10.0, 11.0, 12.0],
            }
        )

        result = transformer(dataframe)

        assert list(result.columns) == ["FITC-A", "Time", "FITC (MESF)"]
        assert result["FITC-A"].tolist() == [1.0, 2.0, 3.0]
        assert result["FITC (MESF)"].tolist() == [10.0, 20.0, 30.0]
        assert result.attrs["fcs_detector_metadata_overrides"]["FITC (MESF)"]["S"] == (
            "RosettaX based on FITC-A"
        )

    def test_build_legacy_dataframe_transformer_clamps_negative_values_with_warning(self) -> None:
        transformer_factory = services.build_legacy_dataframe_transformer_factory(
            source_channel="FITC-A",
            output_channel_name="FITC (MESF)",
            calibration_payload={
                "source_channel": "FITC-A",
                "fit_model": "log10(y)=slope*log10(x)+intercept",
                "parameters": {
                    "slope": 1.0,
                    "intercept": 0.0,
                },
            },
            warnings=[],
        )

        transformer = transformer_factory("/tmp/input.fcs")
        dataframe = pd.DataFrame(
            {
                "FITC-A": [-1.0, 0.0, 10.0],
            }
        )

        result = transformer(dataframe)

        assert result["FITC (MESF)"].tolist() == [0.0, 0.0, 10.0]

    def test_build_success_message_appends_warning_text(self) -> None:
        message = services.build_success_message(
            selected_calibrations=['fitc.json -> "FITC (MESF)"'],
            source_channels=["FITC-A"],
            file_count=1,
            output_channels=["FITC (MESF)"],
            warnings=['Clamped 3 negative event(s) to 0 before applying log calibration to "FITC-A".'],
        )

        assert "Applied calibration(s)" in message
        assert "Warning:" in message
        assert 'Clamped 3 negative event(s) to 0 before applying log calibration to "FITC-A".' in message

    def test_resolve_unique_output_channel_name_appends_suffix_when_name_is_reserved(self) -> None:
        resolved_name = services.resolve_unique_output_channel_name(
            preferred_name="FITC (MESF)",
            reserved_names={"FITC-A", "FITC (MESF)", "FITC (MESF) 2"},
        )

        assert resolved_name == "FITC (MESF) 3"

    def test_apply_calibration_to_fcs_files_uses_saved_scattering_output_channel_name(self, monkeypatch) -> None:
        monkeypatch.setattr(
            services.io,
            "build_input_export_columns",
            lambda source_channels, export_columns: list(export_columns),
        )
        monkeypatch.setattr(
            services.io,
            "build_exported_fcs_bytes",
            lambda uploaded_fcs_path, input_export_columns, dataframe_transformer: b"payload",
        )
        monkeypatch.setattr(
            services.io,
            "build_export_filename",
            lambda uploaded_fcs_path, output_channels: "export.fcs",
        )

        result = services.apply_calibration_to_fcs_files(
            request=services.ApplyCalibrationRequest(
                uploaded_fcs_paths=["/tmp/input.fcs"],
                export_columns=["Time"],
                calibrations=[
                    services.CalibrationApplication(
                        selected_calibration="scatter.json",
                        calibration_payload={
                            "calibration_type": "scattering",
                            "version": 2,
                            "source_channel": "SSC-A",
                            "applied_output_channel_name": "Diameter (nm)",
                        },
                        scattering_target_model_parameters=object(),
                    ),
                ],
            ),
        )

        assert result.output_channels == ["Diameter (nm)"]
        assert '"Diameter (nm)"' in result.status

    def test_build_scattering_dataframe_transformer_factory_passes_resolved_output_channel_names(self, monkeypatch) -> None:
        captured_arguments = {}

        def _fake_apply_scattering_calibration_to_dataframe(**kwargs):
            captured_arguments.update(kwargs)
            return SimpleNamespace(
                dataframe=kwargs["dataframe"],
                output_columns=list(kwargs["output_channel_names"]),
                warnings=[],
                target_mie_relation=None,
            )

        monkeypatch.setattr(
            services,
            "apply_scattering_calibration_to_dataframe",
            _fake_apply_scattering_calibration_to_dataframe,
        )

        transformer_factory = services.build_scattering_dataframe_transformer_factory(
            source_channel="SSC-A",
            output_channel_names=["Diameter (nm)"],
            calibration_payload={
                "source_channel": "SSC-A",
                "applied_output_channel_name": "Diameter (nm)",
            },
            target_model_parameters=object(),
        )

        transformer = transformer_factory("/tmp/input.fcs")
        dataframe = pd.DataFrame({"SSC-A": [1.0, 2.0]})

        result = transformer(dataframe)

        assert result.equals(dataframe)
        assert captured_arguments["output_channel_names"] == ["Diameter (nm)"]
