#!/usr/bin/env python
"""Integration tests for Rosetta detection and scattering calibration on the bundled CAL003 and METVES acquisitions."""

if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v", "-rx", "-s"]))

import json
import logging
import math
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import pytest
from RosettaX.workflow.peak.core.detectors import populate_peak_script_detector_dropdowns
from RosettaX.workflow.peak.scripts.rosetta_mix_mixture import MixtureRosettaScatterPeakProcess
from RosettaX.workflow.peak.scripts.rosetta_mix_sizing import ROSETTA_MIX_PARTICLE_DIAMETERS_NM

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_DIRECTORY = REPOSITORY_ROOT / "RosettaX" / "assets" / "sample-files" / "cross_device"

# Scatter and green fluorescence are the channels used by the Rosetta script.
SAMPLES = [
    ("apogee_a60_micro_cal003_2022-01-31.fcs", "405LALS(Peak)", "405Grn(Peak)"),
    ("bd_facsymphony_a1_cal003_2022-02-11.fcs", "SSC-H", "B530/30-A"),
    ("bd_facsymphony_a1_cal003_2022-02-18.fcs", "SSC-H", "B530/30-A"),
    ("bd_facsymphony_a1_cal003_2022-11-16.fcs", "SSC-H", "BB515-H"),
    ("miltenyi_macsquant_cal003_2022-05-13.fcs", "SSC-H", "FL6-H"),
    ("beckman_coulter_cytoflex_s_cal003_2023-01-05.fcs", "SSC_1-H", "FL1-H"),
    ("bd_facscalibur_cal003_2023-02-08.fcs", "SSC-H", "FL1-H"),
]


METVES_SAMPLES = [
    ('beckman_coulter_cytoflex_s_metves_23w1.fcs', 'SSC_1-H', 'FL1-H'),
    ('beckman_coulter_cytoflex_s_metves_16p1.fcs', 'SSC_1-H', 'FL1-H'),
    ('beckman_coulter_cytoflex_lx_metves_14n1.fcs', 'SSC_1-H', 'FL1-H'),
    ('beckman_coulter_cytoflex_lx_metves_05e1.fcs', 'FL12-H', 'FL1-H'),
    ('cytek_aurora_metves_23w2.fcs', 'SSC-H', 'B2-H'),
    ('bd_facslyric_metves_20t1.fcs', 'SSC-H', 'FITC-H'),
    ('apogee_microplus_metves_06f2.fcs', 'LALS(Peak)', '405-Grn(Peak)'),
    ('beckman_coulter_cytoflex_s_metves_05e2.fcs', 'SSC_1-H', 'FL5-H'),
    ('apogee_a50_micro_metves_19s1.fcs', '405-LALS(Peak)', '405-Grn(Peak)'),
    ('cytek_aurora_metves_11k2.fcs', 'SSC-H', 'B2-H'),
    ('apogee_microplus_metves_04d1.fcs', 'LALS(Peak)', '405-Grn(Peak)'),
    ('bd_facsymphony_a1_metves_25y2.fcs', 'SSC-H', 'BB515-H'),
    ('apogee_microplus_metves_07g1.fcs', '405-LALS(Peak)', '405-Grn(Peak)'),
    ('bd_facscelesta_sorp_metves_09i1.fcs', 'SSC-H', 'B530/30-A'),
    ('beckman_coulter_cytoflex_s_metves_06f1.fcs', 'SSC_1-H', 'FL1-H'),
    ('beckman_coulter_moflo_astrios_metves_21u1.fcs', 'SSC1-Height', 'FL12-Height'),
    ('apogee_microplus_metves_07g2.fcs', 'LALS(Peak)', '405Grn(Peak)'),
    ('cytek_aurora_metves_12l1.fcs', 'SSC-H', 'B2-H'),
    ('cytek_northern_lights_metves_22v2.fcs', 'SSC-H', 'B2-H'),
    ('bd_facsymphony_a1_metves_25y1.fcs', 'SSC-H', 'BB515-H'),
    ('apogee_a60_micro_metves_22v1.fcs', '405LALS(Peak)', '405Grn(Peak)'),
    ('cytek_aurora_metves_18r1.fcs', 'SSC-H', 'B2-A'),
    ('beckman_coulter_cytoflex_lx_metves_16p2.fcs', 'SSC_1-H', 'FL1-H'),
    ('bd_facsymphony_a5_metves_08h1.fcs', 'SSC-H', 'BB515-H'),
]

# This recording resolves a marker on 488 green. Auto-select still prefers 405.
METVES_SIZING_FLUORESCENCE = {"apogee_microplus_metves_07g1.fcs": "488-Grn(Peak)"}

CHECKED_METVES_OUTCOMES = {
    'beckman_coulter_cytoflex_s_metves_23w1.fcs': ([147, 203, 296, 400, 600], ''),
    'beckman_coulter_cytoflex_s_metves_16p1.fcs': (['', 147, 203, 296, 400, 600, 799, 994], ''),
    'beckman_coulter_cytoflex_lx_metves_14n1.fcs': ([400, 600], ''),
    'beckman_coulter_cytoflex_lx_metves_05e1.fcs': ([147, 203, 296, 400, 600, 799, 994], ''),
    'cytek_aurora_metves_23w2.fcs': ([125, 147, 203, 296], ''),
    'bd_facslyric_metves_20t1.fcs': ([], 'No validated fluorescence peaks'),
    'apogee_microplus_metves_06f2.fcs': ([203, 296, 400, 600], ''),
    'beckman_coulter_cytoflex_s_metves_05e2.fcs': ([600, 799, 994], 'Found 0 validated scatter peaks'),
    'apogee_a50_micro_metves_19s1.fcs': ([125, '', '', 400, 600, 799, 994], 'Found 2 validated scatter peaks'),
    'cytek_aurora_metves_11k2.fcs': ([125, 147, 203, 296], ''),
    'apogee_microplus_metves_04d1.fcs': ([296, 400, 600, 799, 994], ''),
    'bd_facsymphony_a1_metves_25y2.fcs': ([100, 125, 147, 203, 296, 400, 600, 799, 994], ''),
    'apogee_microplus_metves_07g1.fcs': ([203, 296, 400], ''),
    'bd_facscelesta_sorp_metves_09i1.fcs': ([], '0 fluorescent marker peaks'),
    'beckman_coulter_cytoflex_s_metves_06f1.fcs': ([147, 203, 296, 400, 600, 799, 994], ''),
    'beckman_coulter_moflo_astrios_metves_21u1.fcs': ([147, 203, 296, 400, 600, 799, 994], ''),
    'apogee_microplus_metves_07g2.fcs': (['', '', '', '', '', '', ''], 'Two fluorescent candidates overlap'),
    'cytek_aurora_metves_12l1.fcs': ([125, 147, 203], ''),
    'cytek_northern_lights_metves_22v2.fcs': ([125, 147, 203], ''),
    'bd_facsymphony_a1_metves_25y1.fcs': ([], '0 fluorescent marker peaks'),
    'apogee_a60_micro_metves_22v1.fcs': ([100, 125, 147, 203, 296], ''),
    'cytek_aurora_metves_18r1.fcs': ([], '0 fluorescent marker peaks'),
    'beckman_coulter_cytoflex_lx_metves_16p2.fcs': ([203, 296, 400, 600, 799, 994], ''),
    'bd_facsymphony_a5_metves_08h1.fcs': ([147, 203, 296, 400, 600, 799], ''),
}

@pytest.mark.parametrize(
    ("filename", "scatter", "fluorescence"),
    SAMPLES + METVES_SAMPLES,
    ids=[sample[0] for sample in SAMPLES + METVES_SAMPLES],
)
def test_cross_device_catalog_auto_selects_fcs_channels(*, filename: str, scatter: str, fluorescence: str) -> None:
    """Resolve the expected channels from each FCS file through Rosetta auto-select."""
    _, selected = populate_peak_script_detector_dropdowns(
        uploaded_fcs_path=str(SAMPLE_DIRECTORY / filename),
        detector_dropdown_ids=[
            {"process": "Rosetta Script V1", "channel": "scattering"},
            {"process": "Rosetta Script V1", "channel": "green_fluorescence"},
        ],
        current_detector_values=[None, None],
        auto_select_rosetta_v1=True,
        logger=logging.getLogger(__name__),
    )
    assert selected == [scatter, fluorescence]


def resolve_test_optical_settings(*, filename: str, scatter: str) -> dict | None:
    """Select an instrument preset for the test fixture's solid-sphere standard."""
    from RosettaX.workflow.detector.configuration import (
        detect_detector_preset_from_uploaded_fcs,
        resolve_detector_configuration_values,
        resolve_detector_preset_wavelength_nm,
    )
    from RosettaX.workflow.parameters.refractive_index import calculate_sellmeier_refractive_index

    sample_path = str(SAMPLE_DIRECTORY / filename)
    preset_name = detect_detector_preset_from_uploaded_fcs(
        uploaded_fcs_path=sample_path, selected_detector_channel=scatter,
    )
    if not preset_name:
        return None
    wavelength_nm = resolve_detector_preset_wavelength_nm(preset_name=preset_name)
    assert wavelength_nm is not None, f"No wavelength for {preset_name}"
    (
        numerical_aperture,
        cache_aperture,
        blocker_aperture,
        detector_sampling,
        phi_angle_degree,
        gamma_angle_degree,
    ) = (
        resolve_detector_configuration_values(
            preset_name=preset_name,
            current_detector_numerical_aperture=None,
            current_detector_cache_numerical_aperture=None,
            current_blocker_bar_numerical_aperture=None,
            current_detector_sampling=None,
            current_detector_phi_angle_degree=None,
            current_detector_gamma_angle_degree=None,
        )
    )
    return dict(
        mie_model="Solid Sphere",
        medium_refractive_index=calculate_sellmeier_refractive_index("water", wavelength_nm=wavelength_nm),
        particle_refractive_index=calculate_sellmeier_refractive_index("polystyrene", wavelength_nm=wavelength_nm),
        core_refractive_index=None,
        shell_refractive_index=None,
        wavelength_nm=wavelength_nm,
        detector_numerical_aperture=numerical_aperture,
        detector_cache_numerical_aperture=cache_aperture,
        blocker_bar_numerical_aperture=blocker_aperture,
        detector_sampling=detector_sampling,
        detector_phi_angle_degree=phi_angle_degree,
        detector_gamma_angle_degree=gamma_angle_degree,
        detector_configuration_preset=preset_name,
        logger=logging.getLogger(__name__),
    )


def run_real_calibration(*, filename: str, scatter: str, rows: list[dict]) -> float | None:
    """Return the unrounded fit R² when a detector geometry is available."""
    from RosettaX.pages.p03_scattering.sections.s05_calibration.services import run_scattering_calibration

    settings = resolve_test_optical_settings(filename=filename, scatter=scatter)
    if settings is None:
        return None
    calibration = run_scattering_calibration(
        uploaded_fcs_path=str(SAMPLE_DIRECTORY / filename),
        detector_column=scatter,
        bead_table_data=rows,
        simulated_curve_point_count=100,
        **settings,
    )
    assert calibration.calibration_store is not None, calibration.apply_status
    return float(calibration.calibration_store["instrument_response"]["r_squared"])


def run_real_sample(
    *, filename: str, scatter: str, fluorescence: str, fit_calibration: bool = True,
) -> dict:
    """Run the Rosetta detection and, when possible, the scattering fit."""
    result = MixtureRosettaScatterPeakProcess().run_automatic_action(
        backend=SimpleNamespace(fcs_file_path=str(SAMPLE_DIRECTORY / filename)),
        detector_channels={"scattering": scatter, "green_fluorescence": fluorescence},
        peak_count=10,
        max_events_for_analysis=100_000,
        process_settings={},
    )
    assert result is not None
    rows = result.table_prefill_rows or []
    can_fit = fit_calibration and len(rows) >= 3 and all(row["particle_diameter_nm"] for row in rows) and not result.warning
    return {
        "warning": result.warning,
        "status": result.status,
        "rows": rows,
        "r_squared": run_real_calibration(filename=filename, scatter=scatter, rows=rows) if can_fit else None,
    }


def run_sample_in_subprocess(**sample) -> dict:
    """Use real PyMieSim independently of the suite's dependency stubs."""
    process = subprocess.run(
        [
            sys.executable, "-c",
            "import json, runpy, sys; "
            "run_sample = runpy.run_path(sys.argv[1])['run_real_sample']; "
            "print(json.dumps(run_sample(**json.load(sys.stdin))))",
            str(Path(__file__).resolve()),
        ],
        cwd=REPOSITORY_ROOT,
        input=json.dumps(sample),
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert process.returncode == 0, process.stderr
    return json.loads(process.stdout.strip().splitlines()[-1])


# Expected behavior at the default settings. These outcomes check the workflow
# against fixed recordings and are not independent bead identity annotations.
EXPECTED_OUTCOMES = {
    "apogee_a60_micro_cal003_2022-01-31.fcs": ("fit", [100, 125, 147, 203, 296]),
    "bd_facsymphony_a1_cal003_2022-02-11.fcs": ("missing_marker", []),
    "bd_facsymphony_a1_cal003_2022-02-18.fcs": ("missing_marker", []),
    "bd_facsymphony_a1_cal003_2022-11-16.fcs": ("fit", [100, 125, 147, 203, 296, 400, 600, 799, 994]),
    "miltenyi_macsquant_cal003_2022-05-13.fcs": ("fit", [296, 400, 600, 799, 994]),
    "beckman_coulter_cytoflex_s_cal003_2023-01-05.fcs": ("fit", [125, 147, 203, 296, 400, 600, 799, 994]),
    "bd_facscalibur_cal003_2023-02-08.fcs": ("missing_marker", []),
}


@pytest.mark.parametrize(("filename", "scatter", "fluorescence"), SAMPLES, ids=[sample[0] for sample in SAMPLES])
def test_rosetta_bead_positions_sizes_and_scattering_fit(
    *, filename: str, scatter: str, fluorescence: str,
) -> None:
    """Check assigned sizes, known diagnostic paths, and supported calibrations."""
    result = run_sample_in_subprocess(filename=filename, scatter=scatter, fluorescence=fluorescence)
    expected_outcome, expected_diameters = EXPECTED_OUTCOMES[filename]
    rows = result["rows"]
    assert [row["particle_diameter_nm"] for row in rows] == expected_diameters
    positions = [row["measured_peak_position"] for row in rows]
    assert all(math.isfinite(position) and position > 0 for position in positions)
    assert positions == sorted(set(positions))
    assert all(not diameter or diameter in ROSETTA_MIX_PARTICLE_DIAMETERS_NM for diameter in expected_diameters)

    assert result["warning"] == (expected_outcome == "missing_marker"), result["status"]
    if expected_outcome == "missing_marker":
        assert "0 fluorescent marker peaks" in result["status"]

    if expected_outcome == "fit":
        r_squared = result["r_squared"]
        assert r_squared is not None and math.isfinite(r_squared) and r_squared > 0.90
    else:
        assert result["r_squared"] is None


@pytest.mark.parametrize(
    ("filename", "scatter", "fluorescence"), METVES_SAMPLES, ids=[sample[0] for sample in METVES_SAMPLES],
)
def test_metves_rosetta_assignments_and_warnings(
    *, filename: str, scatter: str, fluorescence: str,
) -> None:
    """Check provisional diameters or the reason sizing stops on each METVES recording."""
    result = run_sample_in_subprocess(
        filename=filename,
        scatter=scatter,
        fluorescence=METVES_SIZING_FLUORESCENCE.get(filename, fluorescence),
        fit_calibration=False,
    )
    expected_diameters, warning_fragment = CHECKED_METVES_OUTCOMES[filename]
    rows = result["rows"]
    assert [row["particle_diameter_nm"] for row in rows] == expected_diameters
    positions = [row["measured_peak_position"] for row in rows]
    assert all(math.isfinite(position) and position > 0 for position in positions)
    assert positions == sorted(set(positions))
    assert result["warning"] == bool(warning_fragment), result["status"]
    if warning_fragment:
        assert warning_fragment in result["status"]
