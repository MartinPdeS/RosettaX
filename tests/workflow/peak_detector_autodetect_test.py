"""Regression tests for workflow peak detector autodetect."""

# Run pytest before application imports so the suite loads its own dependency setup.
if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))


import json
import pytest
import sys
import types
from pathlib import Path
from RosettaX.utils.fcs_metadata import FCSMetadata


class _DashBootstrapComponentsSentinel:
    """Callable component sentinel for lightweight Dash Bootstrap test setup."""

    def __call__(self, *args, **kwargs):
        """Provide the callable behavior required by this test double."""
        return None

    def __getattr__(self, name):
        """Handle dynamic attribute lookup for this test double."""
        return self


class _DashBootstrapComponentsStub(types.ModuleType):
    """Minimal Dash Bootstrap components used by the unit tests."""

    def __getattr__(self, name):
        """Handle dynamic attribute lookup for this test double."""
        return _DashBootstrapComponentsSentinel()


sys.modules.setdefault(
    "dash_bootstrap_components",
    _DashBootstrapComponentsStub("dash_bootstrap_components"),
)

from RosettaX.workflow.detector import configuration as detector_configuration
from RosettaX.workflow.peak.core import detectors
from typing import Self


def build_metadata(
    *,
    instrument_name: str,
    column_names: list[str],
) -> FCSMetadata:
    """Build metadata for this test."""
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
    """Test double for fake fcsfile."""

    def __init__(self, metadata: FCSMetadata) -> None:
        """Initialize the state required by this test double."""
        self.metadata = metadata

    def __enter__(self) -> Self:
        """Return the test reader when entering its context."""
        return self

    def __exit__(self, exc_type, exc, traceback) -> bool:
        """Handle context cleanup for the test reader."""
        return False

    def get_metadata(self) -> FCSMetadata:
        """Return the FCS metadata prepared for this test."""
        return self.metadata


class Test_DetectorAutoDetect:
    """Regression checks for detector auto detect."""

    def test_infer_default_detector_channel_uses_instrument_rule_for_role(
        self,
        tmp_path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Check infer default detector channel uses instrument rule for role."""
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
        """Check detect detector preset from uploaded FCS uses preset alias field."""
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
        """Check detect detector preset from uploaded FCS supports cytek aurora aliases."""
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
        """Check infer default detector channel uses packaged attune rule."""
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
        """Check detect detector preset from uploaded FCS supports nanofcm aliases."""
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

        assert resolved_preset == "nanoFCM NanoAnalyzer FSC"

    def test_infer_default_detector_channel_uses_packaged_nanofcm_rule(
        self,
    ) -> None:
        """Check infer default detector channel uses packaged nanofcm rule."""
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

        assert resolved_channel == "405LALS(Area)"

    def test_infer_default_detector_channel_prefers_fluorescence_for_green_role(
        self,
    ) -> None:
        """Check infer default detector channel prefers fluorescence for green role."""
        metadata = build_metadata(
            instrument_name="nanoFCM NanoAnalyzer",
            column_names=["405Blu(Area)", "405ALS(Peak)", "FITC-A"],
        )

        resolved_channel = detectors.infer_default_detector_channel(
            column_names=metadata.column_names,
            metadata=metadata,
            detector_role="green_fluorescence",
            selection_mode="auto-detect",
        )

        assert resolved_channel == "FITC-A"

    def test_detect_detector_preset_from_uploaded_fcs_name_heuristic_prefers_scatter_preset(
        self,
        tmp_path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Check detect detector preset from uploaded FCS name heuristic prefers scatter preset."""
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
            ("405SALS(Area)", "fsc"),
            ("405LALS(Area)", "ssc"),
            ("LASL", "ssc"),
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
        """Check classify detector channel family supports common aliases."""
        assert detector_configuration.classify_detector_channel_family(
            channel_name,
        ) == expected_family

    def test_detect_detector_preset_from_uploaded_fcs_supports_sals_aliases(
        self,
        tmp_path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Check detect detector preset from uploaded FCS supports sals aliases."""
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

        assert resolved_preset is None

    def test_detect_detector_preset_from_uploaded_fcs_maps_lals_aliases_to_fsc(
        self,
        tmp_path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Check detect detector preset from uploaded FCS maps lals aliases to FSC."""
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

        assert resolved_preset == "BD FACSCanto II SSC"

    def test_classify_detector_preset_family_falls_back_to_name_when_channel_is_generic(
        self,
    ) -> None:
        """Check classify detector preset family falls back to name when channel is generic."""
        assert detector_configuration.classify_detector_preset_family(
            {
                "name": "Apogee - Side",
                "channel": "Weighted",
            }
        ) == "ssc"

    def test_resolve_detector_angular_weights_uses_preset_sampling_when_missing(
        self,
    ) -> None:
        """Check resolve detector angular weights uses preset sampling when missing."""
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
        """Check detect wavelength nm from detector channel uses explicit channel names."""
        assert detector_configuration.detect_wavelength_nm_from_detector_channel(
            channel_name,
        ) == expected_wavelength_nm

    def test_detect_detector_preset_from_uploaded_fcs_requires_selected_detector_channel(
        self,
        tmp_path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Check detect detector preset from uploaded FCS requires selected detector channel."""
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
        """Check detect detector preset from uploaded FCS returns none when channel family conflicts."""
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
        """Check resolve runtime detector preset preserves explicit non generic preset."""
        resolved_preset = detector_configuration.resolve_runtime_detector_preset(
            "BD FACSCanto II FSC",
        )

        assert resolved_preset == "BD FACSCanto II FSC"

    def test_resolve_runtime_detector_preset_returns_none_for_empty_default(self) -> None:
        """Check resolve runtime detector preset returns none for empty default."""
        resolved_preset = detector_configuration.resolve_runtime_detector_preset(
            "",
        )

        assert resolved_preset is None

    def test_infer_default_detector_channel_falls_back_to_name_heuristic(
        self,
        tmp_path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Check infer default detector channel falls back to name heuristic."""
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
        """Check infer default detector channel can skip auto detect rules."""
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


@pytest.mark.parametrize(
    ("channels", "role", "expected"),
    [
        (["405SALS(Peak)", "405LALS(Peak)", "488Grn(Peak)"], "scattering", "405LALS(Peak)"),
        (["405SALS(Peak)", "405LALS(Peak)", "488Grn(Peak)"], "green_fluorescence", "488Grn(Peak)"),
        (["FSC-A", "SSC-A", "FITC-A"], "scattering", "SSC-A"),
        (["FSC-A", "SSC-A", "FITC-A"], "green_fluorescence", "FITC-A"),
        (["FSC-A", "Time"], "scattering", None),
        (["FSC-A", "Time"], "green_fluorescence", None),
        (["SSC-A", "SSC-H"], "scattering", None),
        (["FITC-A", "FL1-A"], "green_fluorescence", None),
        (["V525/50-A", "B535/30-A", "B535/30-H"], "green_fluorescence", "B535/30-A"),
        (["B525/50-A", "B535/30-A"], "green_fluorescence", None),
        (["B535/30-H", "B535/30-W"], "green_fluorescence", None),
        (["405LALS(Area)", "405LALS(Peak)"], "scattering", "405LALS(Peak)"),
        (["405Grn(Peak)", "488Grn(Area)", "488Grn(Peak)"], "green_fluorescence", "488Grn(Peak)"),
    ],
)
def test_rosetta_v1_selects_only_unambiguous_channels(channels, role, expected):
    """V1 avoids choosing unrelated or ambiguous channels automatically."""
    assert detectors.infer_rosetta_v1_channel(column_names=channels, detector_role=role) == expected


def test_rosetta_v1_dropdowns_autodetect_and_preserve_user_selection(monkeypatch):
    """V1 selects channels only on request and otherwise retains user choices."""
    metadata = build_metadata(
        instrument_name="unknown",
        column_names=["405SALS(Peak)", "405LALS(Peak)", "405Grn(Peak)", "488Grn(Peak)"],
    )
    fake_file = FakeFCSFile(metadata)
    fake_file.get_column_names = lambda: metadata.column_names
    monkeypatch.setattr(detectors, "FCSFile", lambda path: fake_file)
    dropdowns = [
        {"process": "Rosetta Script V1", "channel": "scattering"},
        {"process": "Rosetta Script V1", "channel": "green_fluorescence"},
    ]

    _, initial = detectors.populate_peak_script_detector_dropdowns(
        uploaded_fcs_path="example.fcs", detector_dropdown_ids=dropdowns,
        current_detector_values=[None, None], logger=detectors.logger,
    )
    _, detected = detectors.populate_peak_script_detector_dropdowns(
        uploaded_fcs_path="example.fcs", detector_dropdown_ids=dropdowns,
        current_detector_values=["405SALS(Peak)", None],
        auto_select_rosetta_v1=True, logger=detectors.logger,
    )
    _, preserved = detectors.populate_peak_script_detector_dropdowns(
        uploaded_fcs_path="example.fcs", detector_dropdown_ids=dropdowns,
        current_detector_values=["405SALS(Peak)", "488Grn(Peak)"], logger=detectors.logger,
    )

    _, reset = detectors.populate_peak_script_detector_dropdowns(
        uploaded_fcs_path="example.fcs", detector_dropdown_ids=dropdowns,
        current_detector_values=["405LALS(Peak)", "488Grn(Peak)"],
        reset_rosetta_v1=True, logger=detectors.logger,
    )

    assert initial == [None, None]
    assert reset == [None, None]
    assert detected == ["405LALS(Peak)", "405Grn(Peak)"]
    assert preserved == ["405SALS(Peak)", "488Grn(Peak)"]


def test_rosetta_v1_prefers_green_channel_matching_scatter_wavelength():
    """Prefer green fluorescence excited at the selected scatter wavelength."""
    assert detectors.infer_rosetta_v1_channel(
        column_names=["405Grn(Peak)", "488Grn(Peak)"],
        detector_role="green_fluorescence",
        preferred_wavelength_nm=405,
    ) == "405Grn(Peak)"


def test_rosetta_v1_detects_green_filter_in_bundled_lsrii_sample():
    """Identify the green filter while leaving ambiguous scatter measurements unset."""
    sample_path = Path(__file__).resolve().parents[2] / "RosettaX/assets/sample-files/bd_lsrii_rosetta_beads.fcs"
    with detectors.FCSFile(sample_path) as fcs:
        channels = fcs.get_column_names()
    assert detectors.infer_rosetta_v1_channel(column_names=channels, detector_role="green_fluorescence") == "B535/30-A"
    assert detectors.infer_rosetta_v1_channel(column_names=channels, detector_role="scattering") is None


def test_rosetta_suggestions_explain_filter_and_ambiguous_scattering():
    """Give a reason for the filter suggestion and list unresolved candidates."""
    channel, explanation = detectors.resolve_rosetta_v1_suggestion(
        column_names=["B535/30-A", "B535/30-H"], detector_role="green_fluorescence",
    )
    assert channel == "B535/30-A"
    assert "green emission filter" in explanation
    channel, explanation = detectors.resolve_rosetta_v1_suggestion(
        column_names=["SSC-A", "SSC-H"], detector_role="scattering",
    )
    assert channel is None
    assert "SSC-A" in explanation and "SSC-H" in explanation


def test_rosetta_uses_unambiguous_instrument_preference():
    """Use instrument preferences only when one listed channel is present."""
    rule = {"name": "Example", "detector_channels": {"scattering": ["SSC-A", "SSC-H"]}}
    channel, explanation = detectors.resolve_rosetta_v1_suggestion(
        column_names=["SSC-A"], detector_role="scattering", matched_rule=rule,
    )
    assert channel == "SSC-A"
    assert "Example" in explanation
    channel, _ = detectors.resolve_rosetta_v1_suggestion(
        column_names=["SSC-A", "SSC-H"], detector_role="scattering", matched_rule=rule,
    )
    assert channel is None
