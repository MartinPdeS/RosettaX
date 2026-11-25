"""Execute the real Rosetta cross-device validation workflow on one FCS acquisition."""

import logging
import math
from pathlib import Path
from RosettaX.workflow.peak.scripts.rosetta_mix_mixture import (
    MixtureRosettaScatterPeakProcess,
)
from RosettaX.workflow.peak.scripts.rosetta_mix_sizing import (
    ROSETTA_MIX_PARTICLE_DIAMETERS_NM,
)
from types import SimpleNamespace


def resolve_optical_settings(*, path: Path, scatter: str) -> dict | None:
    """Select an instrument preset for the test fixture's solid-sphere standard."""
    from RosettaX.workflow.detector.configuration import (
        detect_detector_preset_from_uploaded_fcs,
        resolve_detector_configuration_values,
        resolve_detector_preset_wavelength_nm,
    )
    from RosettaX.workflow.parameters.refractive_index import (
        calculate_sellmeier_refractive_index,
    )

    sample_path = str(path)
    preset_name = detect_detector_preset_from_uploaded_fcs(
        uploaded_fcs_path=sample_path, selected_detector_channel=scatter,
    )
    if not preset_name:
        return None
    wavelength_nm = resolve_detector_preset_wavelength_nm(preset_name=preset_name)
    if wavelength_nm is None:
        raise ValueError(f"No wavelength for {preset_name}")
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


def run_real_calibration(*, path: Path, scatter: str, rows: list[dict]) -> float | None:
    """Return the unrounded fit R² when a detector geometry is available."""
    from RosettaX.pages.p03_scattering.sections.s05_calibration.services import (
        run_scattering_calibration,
    )

    settings = resolve_optical_settings(path=path, scatter=scatter)
    if settings is None:
        return None
    calibration = run_scattering_calibration(
        uploaded_fcs_path=str(path),
        detector_column=scatter,
        bead_table_data=rows,
        simulated_curve_point_count=100,
        **settings,
    )
    if calibration.calibration_store is None:
        raise ValueError(calibration.apply_status)
    return float(calibration.calibration_store["instrument_response"]["r_squared"])


def run_real_sample(
    *, path: Path, scatter: str, fluorescence: str, fit_calibration: bool = True,
) -> dict:
    """Run the Rosetta detection and, when possible, the scattering fit."""
    result = MixtureRosettaScatterPeakProcess().run_automatic_action(
        backend=SimpleNamespace(fcs_file_path=str(path)),
        detector_channels={"scattering": scatter, "green_fluorescence": fluorescence},
        peak_count=10,
        max_events_for_analysis=100_000,
        process_settings={},
    )
    if result is None:
        raise ValueError("The Rosetta workflow returned no result.")
    rows = result.table_prefill_rows or []
    provisional = result.peak_lines_payload.get("rosetta_sizing", {}).get("needs_confirmation", False)
    assigned_rows = [row for row in rows if row.get("particle_diameter_nm")]
    r_squared = None
    if not fit_calibration:
        fit_note = "calibration fit skipped by test configuration"
    elif len(assigned_rows) < 2:
        fit_note = "fewer than 2 assigned peaks"
    else:
        r_squared = run_real_calibration(path=path, scatter=scatter, rows=assigned_rows)
        fit_note = "no optical preset" if r_squared is None else ""
    return {
        "warning": result.warning,
        "status": result.status,
        "rows": rows,
        "provisional": provisional,
        "gate": result.peak_lines_payload.get("baseline_cutoff"),
        "gate_interval": result.peak_lines_payload.get("rosetta_gate_interval"),
        "r_squared": r_squared,
        "fit_note": fit_note,
        "sizing_summary": (
            result.peak_lines_payload.get("rosetta_sizing", {}).get("summary")
            or result.peak_lines_payload.get("rosetta_detection_summary", "")
        ),
    }


def check_outcome(*, result: dict, record: dict, fixture_name: str) -> None:
    """Compare peak positions, diameters in nm, warnings, and fit quality with the reviewed fixture."""
    expected_diameters = record["expected_diameters_nm"]
    warning_fragment = record["expected_warning"]
    rows = result["rows"]
    actual_diameters = [row["particle_diameter_nm"] for row in rows]
    if actual_diameters != expected_diameters:
        raise ValueError(f"Expected diameters {expected_diameters} nm, observed {actual_diameters} nm.")
    positions = [row["measured_peak_position"] for row in rows]
    if any(not math.isfinite(position) or position <= 0 for position in positions):
        raise ValueError(f"Expected finite positive peak positions, observed {positions}.")
    if positions != sorted(set(positions)):
        raise ValueError(f"Expected distinct peaks in increasing order, observed {positions}.")
    if any(diameter and diameter not in ROSETTA_MIX_PARTICLE_DIAMETERS_NM for diameter in actual_diameters):
        raise ValueError(f"Unrecognized Rosetta bead diameter in {actual_diameters}.")
    if result["warning"] != bool(warning_fragment) or warning_fragment not in result["status"]:
        raise ValueError(f"Expected warning {warning_fragment!r}, observed {result['status']!r}.")

    r_squared = result["r_squared"]
    expected_curve = record.get("expected_curve_r_squared")
    if expected_curve is not None and (r_squared is None or not math.isclose(r_squared, expected_curve, abs_tol=0.001)):
        raise ValueError(f"Expected calibration-curve R² {expected_curve} ± 0.001, observed {r_squared}.")
    if record["fit_calibration"] and rows and not warning_fragment and not result["provisional"]:
        if r_squared is None or not math.isfinite(r_squared) or r_squared <= 0.90:
            raise ValueError(f"Expected a finite calibration R² above 0.90, observed {r_squared}.")
    elif r_squared is not None:
        if not record["fit_calibration"] or sum(bool(size) for size in actual_diameters) < 2:
            raise ValueError(f"Unexpected calibration fit with R² {r_squared}.")
        if not math.isfinite(r_squared):
            raise ValueError(f"Nonfinite calibration-curve R² {r_squared}.")

    if fixture_name == "apogee_microplus_metves_04d1.fcs":
        # The fitted baseline gate is used while stable valley validation is disabled.
        if result["gate_interval"] is not None or not 1_500 < result["gate"] < 8_000:
            raise ValueError(f"Unexpected fitted baseline gate: {result['gate']}, interval {result['gate_interval']}.")
