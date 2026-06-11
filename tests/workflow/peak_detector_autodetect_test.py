# -*- coding: utf-8 -*-

import json
import sys
import types

import pytest

from RosettaX.utils.fcs_metadata import FCSMetadata


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

from RosettaX.workflow.detector import configuration as detector_configuration
from RosettaX.workflow.peak.core import detectors


def build_metadata(
    *,
    instrument_name: str,
    column_names: list[str],
) -> FCSMetadata:
    detectors_by_index = {
        index: {"N": column_name}
        for index, column_name in enumerate(column_names, start=1)
    }

    return FCSMetadata(
        file_path="example.fcs",
        header={"FCS version": "FCS3.1"},
        text={
            "Keywords": {
                "$PAR": str(len(column_names)),
                "$CYT": instrument_name,
            },
            "Detectors": detectors_by_index,
        },
        delimiter="|",
    )


class FakeFCSFile:
    def __init__(self, metadata: FCSMetadata) -> None:
        self.metadata = metadata

    def __enter__(self) -> "FakeFCSFile":
        return self

    def __exit__(self, exc_type, exc, traceback) -> bool:
        return False

    def get_metadata(self) -> FCSMetadata:
        return self.metadata


class Test_DetectorAutoDetect:
    def test_infer_default_detector_channel_uses_instrument_rule_for_role(
        self,
        tmp_path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        rules_path = tmp_path / "detector_auto_detect_rules.json"
        rules_path.write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "rules": [
                        {
                            "name": "CytoFLEX scattering",
                            "instrument_aliases": ["cytoflex s"],
                            "detector_channels": {
                                "primary": ["VSSC-A", "SSC-A"],
                            },
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(
            detectors,
            "DETECTOR_AUTO_DETECT_RULES_PATH",
            rules_path,
        )

        metadata = build_metadata(
            instrument_name="Beckman Coulter CytoFLEX S",
            column_names=["FSC-A", "SSC-A", "FL1-A"],
        )

        resolved_channel = detectors.infer_default_detector_channel(
            column_names=metadata.column_names,
            metadata=metadata,
            detector_role="primary",
            selection_mode="auto-detect",
        )

        assert resolved_channel == "SSC-A"

    def test_detect_detector_preset_from_uploaded_fcs_uses_preset_alias_field(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        metadata = build_metadata(
            instrument_name="Beckman Coulter CytoFLEX S",
            column_names=["FSC-A", "SSC-A", "FL1-A"],
        )
        monkeypatch.setattr(
            detector_configuration,
            "FCSFile",
            lambda _path: FakeFCSFile(metadata),
        )

        resolved_preset = detector_configuration.detect_detector_preset_from_uploaded_fcs(
            uploaded_fcs_path="example.fcs",
            selected_detector_channel="SSC-A",
        )

        assert resolved_preset == "Beckman Coulter CytoFLEX SSC"

    def test_detect_detector_preset_from_uploaded_fcs_supports_cytek_aurora_aliases(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        metadata = build_metadata(
            instrument_name="Cytek Aurora 5L",
            column_names=["FSC-A", "SSC-A", "FL1-A"],
        )
        monkeypatch.setattr(
            detector_configuration,
            "FCSFile",
            lambda _path: FakeFCSFile(metadata),
        )

        resolved_preset = detector_configuration.detect_detector_preset_from_uploaded_fcs(
            uploaded_fcs_path="example.fcs",
            selected_detector_channel="SSC-A",
        )

        assert resolved_preset == "Cytek Aurora SSC"

    def test_infer_default_detector_channel_uses_packaged_attune_rule(
        self,
    ) -> None:
        metadata = build_metadata(
            instrument_name="Thermo Fisher Attune NxT",
            column_names=["Time", "FSC-A", "SSC-A", "FL1-A"],
        )

        resolved_channel = detectors.infer_default_detector_channel(
            column_names=metadata.column_names,
            metadata=metadata,
            detector_role="primary",
            selection_mode="auto-detect",
        )

        assert resolved_channel == "SSC-A"

    def test_detect_detector_preset_from_uploaded_fcs_supports_nanofcm_aliases(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        metadata = build_metadata(
            instrument_name="nanoFCM NanoAnalyzer",
            column_names=["405LALS(Area)", "405SALS(Area)", "FL1-A"],
        )
        monkeypatch.setattr(
            detector_configuration,
            "FCSFile",
            lambda _path: FakeFCSFile(metadata),
        )

        resolved_preset = detector_configuration.detect_detector_preset_from_uploaded_fcs(
            uploaded_fcs_path="example.fcs",
            selected_detector_channel="405SALS(Area)",
        )

        assert resolved_preset == "nanoFCM NanoAnalyzer SSC"

    def test_infer_default_detector_channel_uses_packaged_nanofcm_rule(
        self,
    ) -> None:
        metadata = build_metadata(
            instrument_name="nanoFCM NanoAnalyzer",
            column_names=["405LALS(Area)", "405SALS(Area)", "FL1-A"],
        )

        resolved_channel = detectors.infer_default_detector_channel(
            column_names=metadata.column_names,
            metadata=metadata,
            detector_role="primary",
            selection_mode="auto-detect",
        )

        assert resolved_channel == "405SALS(Area)"

    def test_detect_detector_preset_from_uploaded_fcs_name_heuristic_prefers_scatter_preset(
        self,
        tmp_path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        rules_path = tmp_path / "detector_auto_detect_rules.json"
        rules_path.write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "rules": [],
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(
            detector_configuration,
            "DETECTOR_AUTO_DETECT_RULES_PATH",
            rules_path,
        )

        metadata = build_metadata(
            instrument_name="Beckman Coulter CytoFLEX S",
            column_names=["FSC-A", "SSC-A", "FL1-A"],
        )
        monkeypatch.setattr(
            detector_configuration,
            "FCSFile",
            lambda _path: FakeFCSFile(metadata),
        )

        resolved_preset = detector_configuration.detect_detector_preset_from_uploaded_fcs(
            uploaded_fcs_path="example.fcs",
            selected_detector_channel="SSC-A",
        )

        assert resolved_preset == "Beckman Coulter CytoFLEX SSC"

    @pytest.mark.parametrize(
        ("channel_name", "expected_family"),
        [
            ("405SALS(Area)", "ssc"),
            ("405LALS(Area)", "fsc"),
            ("LASL", "fsc"),
            ("VSSC-A", "ssc"),
            ("FSC-A", "fsc"),
            ("FL1-A", "fl"),
        ],
    )
    def test_classify_detector_channel_family_supports_common_aliases(
        self,
        channel_name: str,
        expected_family: str,
    ) -> None:
        assert detector_configuration.classify_detector_channel_family(
            channel_name,
        ) == expected_family

    def test_detect_detector_preset_from_uploaded_fcs_supports_sals_aliases(
        self,
        tmp_path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        rules_path = tmp_path / "detector_auto_detect_rules.json"
        rules_path.write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "rules": [],
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(
            detector_configuration,
            "DETECTOR_AUTO_DETECT_RULES_PATH",
            rules_path,
        )

        metadata = build_metadata(
            instrument_name="Beckman Coulter CytoFLEX S",
            column_names=["405SALS(Area)", "FL1-A"],
        )
        monkeypatch.setattr(
            detector_configuration,
            "FCSFile",
            lambda _path: FakeFCSFile(metadata),
        )

        resolved_preset = detector_configuration.detect_detector_preset_from_uploaded_fcs(
            uploaded_fcs_path="example.fcs",
            selected_detector_channel="405SALS(Area)",
        )

        assert resolved_preset == "Beckman Coulter CytoFLEX SSC"

    def test_detect_detector_preset_from_uploaded_fcs_maps_lals_aliases_to_fsc(
        self,
        tmp_path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        rules_path = tmp_path / "detector_auto_detect_rules.json"
        rules_path.write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "rules": [],
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(
            detector_configuration,
            "DETECTOR_AUTO_DETECT_RULES_PATH",
            rules_path,
        )

        metadata = build_metadata(
            instrument_name="BD FACSCanto II",
            column_names=["405LALS(Area)", "FL1-A"],
        )
        monkeypatch.setattr(
            detector_configuration,
            "FCSFile",
            lambda _path: FakeFCSFile(metadata),
        )

        resolved_preset = detector_configuration.detect_detector_preset_from_uploaded_fcs(
            uploaded_fcs_path="example.fcs",
            selected_detector_channel="405LALS(Area)",
        )

        assert resolved_preset == "BD FACSCanto II FSC"

    def test_classify_detector_preset_family_falls_back_to_name_when_channel_is_generic(
        self,
    ) -> None:
        assert detector_configuration.classify_detector_preset_family(
            {
                "name": "Apogee - Side",
                "channel": "Weighted",
            }
        ) == "ssc"

    def test_resolve_detector_angular_weights_uses_preset_sampling_when_missing(
        self,
    ) -> None:
        detector_angular_weights = detector_configuration.resolve_detector_angular_weights(
            preset_name="Apogee - Side",
            detector_sampling=None,
        )

        assert detector_angular_weights is not None
        assert detector_angular_weights.shape == (1000,)

    @pytest.mark.parametrize(
        ("channel_name", "expected_wavelength_nm"),
        [
            ("405SALS(Area)", 405),
            ("488 FSC-A", 488),
            ("561SSC-A", 561),
            ("SSC-A", None),
            ("FL1-A", None),
        ],
    )
    def test_detect_wavelength_nm_from_detector_channel_uses_explicit_channel_names(
        self,
        channel_name: str,
        expected_wavelength_nm: int | None,
    ) -> None:
        assert detector_configuration.detect_wavelength_nm_from_detector_channel(
            channel_name,
        ) == expected_wavelength_nm

    def test_detect_detector_preset_from_uploaded_fcs_requires_selected_detector_channel(
        self,
        tmp_path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        rules_path = tmp_path / "detector_auto_detect_rules.json"
        rules_path.write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "rules": [],
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(
            detector_configuration,
            "DETECTOR_AUTO_DETECT_RULES_PATH",
            rules_path,
        )

        metadata = build_metadata(
            instrument_name="Beckman Coulter CytoFLEX S",
            column_names=["FSC-A", "SSC-A", "FL1-A"],
        )
        monkeypatch.setattr(
            detector_configuration,
            "FCSFile",
            lambda _path: FakeFCSFile(metadata),
        )

        resolved_preset = detector_configuration.detect_detector_preset_from_uploaded_fcs(
            uploaded_fcs_path="example.fcs",
            selected_detector_channel="",
        )

        assert resolved_preset is None

    def test_detect_detector_preset_from_uploaded_fcs_returns_none_when_channel_family_conflicts(
        self,
        tmp_path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        rules_path = tmp_path / "detector_auto_detect_rules.json"
        rules_path.write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "rules": [],
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(
            detector_configuration,
            "DETECTOR_AUTO_DETECT_RULES_PATH",
            rules_path,
        )

        metadata = build_metadata(
            instrument_name="Beckman Coulter CytoFLEX S",
            column_names=["FSC-A", "SSC-A", "FL1-A"],
        )
        monkeypatch.setattr(
            detector_configuration,
            "FCSFile",
            lambda _path: FakeFCSFile(metadata),
        )

        resolved_preset = detector_configuration.detect_detector_preset_from_uploaded_fcs(
            uploaded_fcs_path="example.fcs",
            selected_detector_channel="FSC-A",
        )

        assert resolved_preset is None

    def test_resolve_runtime_detector_preset_preserves_explicit_non_generic_preset(
        self,
    ) -> None:
        resolved_preset = detector_configuration.resolve_runtime_detector_preset(
            "BD FACSCanto II FSC",
        )

        assert resolved_preset == "BD FACSCanto II FSC"

    def test_resolve_runtime_detector_preset_returns_none_for_empty_default(self) -> None:
        resolved_preset = detector_configuration.resolve_runtime_detector_preset(
            "",
        )

        assert resolved_preset is None

    def test_infer_default_detector_channel_falls_back_to_name_heuristic(
        self,
        tmp_path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        rules_path = tmp_path / "detector_auto_detect_rules.json"
        rules_path.write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "rules": [
                        {
                            "name": "CytoFLEX fluorescence",
                            "instrument_aliases": ["cytoflex s"],
                            "detector_channels": {
                                "primary": ["FL1-A"],
                            },
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(
            detectors,
            "DETECTOR_AUTO_DETECT_RULES_PATH",
            rules_path,
        )

        metadata = build_metadata(
            instrument_name="Unknown system",
            column_names=["Time", "SSC-H", "FL1-A"],
        )

        resolved_channel = detectors.infer_default_detector_channel(
            column_names=metadata.column_names,
            metadata=metadata,
            detector_role="primary",
            selection_mode="auto-detect",
        )

        assert resolved_channel == "SSC-H"

    def test_infer_default_detector_channel_can_skip_auto_detect_rules(
        self,
        tmp_path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        rules_path = tmp_path / "detector_auto_detect_rules.json"
        rules_path.write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "rules": [
                        {
                            "name": "CytoFLEX fluorescence",
                            "instrument_aliases": ["cytoflex s"],
                            "detector_channels": {
                                "primary": ["FL1-A"],
                            },
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(
            detectors,
            "DETECTOR_AUTO_DETECT_RULES_PATH",
            rules_path,
        )

        metadata = build_metadata(
            instrument_name="CytoFLEX S",
            column_names=["FL1-A", "SSC-A"],
        )

        resolved_channel = detectors.infer_default_detector_channel(
            column_names=metadata.column_names,
            metadata=metadata,
            detector_role="primary",
            selection_mode="name-heuristic",
        )

        assert resolved_channel == "SSC-A"