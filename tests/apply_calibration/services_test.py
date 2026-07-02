# -*- coding: utf-8 -*-

import sys
import types

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
            lambda values, calibration_payload: values * 10.0,
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

    def test_resolve_unique_output_channel_name_appends_suffix_when_name_is_reserved(self) -> None:
        resolved_name = services.resolve_unique_output_channel_name(
            preferred_name="FITC (MESF)",
            reserved_names={"FITC-A", "FITC (MESF)", "FITC (MESF) 2"},
        )

        assert resolved_name == "FITC (MESF) 3"
