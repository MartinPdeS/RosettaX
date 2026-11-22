"""Resolve provisional Rosetta bead identities with configured detector coupling."""

import numpy as np
from collections.abc import Callable
from RosettaX.utils.casting import as_optional_float
from RosettaX.workflow.page_session.scattering import ScatteringPageState
from RosettaX.workflow.parameters.table import MIE_MODEL_SOLID_SPHERE
from RosettaX.workflow.peak.scripts.rosetta_mix_sizing import (
    BRIGHT_MARKER_DIAMETER_NM,
    DIM_MARKER_DIAMETER_NM,
    ROSETTA_MIX_PARTICLE_DIAMETERS_NM,
)
from typing import Any

MARKER_DIAMETERS = {"Dim marker": DIM_MARKER_DIAMETER_NM, "Bright marker": BRIGHT_MARKER_DIAMETER_NM}
MAX_LOG_RESIDUAL = float(np.log(1.20))
MAX_HELD_OUT_RESIDUAL = float(np.log(1.25))
COMPETING_SCORE_MARGIN = 0.04


VALIDATION_MODEL_FIELDS = (
    "mie_model",
    "medium_refractive_index",
    "particle_refractive_index",
    "core_refractive_index",
    "shell_refractive_index",
    "wavelength_nm",
    "detector_numerical_aperture",
    "detector_cache_numerical_aperture",
    "blocker_bar_numerical_aperture",
    "detector_sampling",
    "detector_phi_angle_degree",
    "detector_gamma_angle_degree",
    "detector_configuration_preset",
    "detector_angular_weighting_json",
)


def _candidate_alignments(
    *, measurements: np.ndarray, coupling: np.ndarray, log_gain: float,
) -> list[tuple[tuple[int, int], ...]]:
    """Align ordered observations to model coupling, allowing omissions on either side."""
    residuals = np.abs(np.log(measurements)[:, None] + log_gain - np.log(coupling))
    row_count, size_count = residuals.shape
    # Keep several distinct paths so a second credible assignment can veto a
    # diameter. Skipping a measured peak costs more than accepting a close match.
    previous = [{(): 0.0} for _ in range(size_count + 1)]
    for row_index in range(row_count):
        current = [{(): (row_index + 1) * MAX_LOG_RESIDUAL}]
        for size_index in range(size_count):
            options = {path: score + MAX_LOG_RESIDUAL for path, score in previous[size_index + 1].items()}
            for path, score in current[-1].items():
                options[path] = min(options.get(path, float("inf")), score)
            residual = residuals[row_index, size_index]
            if residual <= MAX_LOG_RESIDUAL:
                for path, score in previous[size_index].items():
                    options[(*path, (row_index, size_index))] = score + float(residual)
            current.append(dict(sorted(options.items(), key=lambda item: (item[1], item[0]))[:4]))
        previous = current
    return [path for path in previous[-1] if len(path) >= 3]


def _response_fit_errors(
    *, measured: np.ndarray, expected: np.ndarray, marker_ratios: np.ndarray,
) -> list[float] | None:
    """Check leave-one-out log errors and the zero-intercept response R²."""
    ratios = np.log(expected / measured)
    errors = [
        abs(value - np.median(np.r_[np.delete(ratios, index), marker_ratios]))
        for index, value in enumerate(ratios)
    ]
    if max(errors) > MAX_HELD_OUT_RESIDUAL:
        return None
    predicted = measured * (measured @ expected) / (measured @ measured)
    variance = np.sum((expected - expected.mean()) ** 2)
    if variance <= 0 or 1.0 - np.sum((expected - predicted) ** 2) / variance <= 0.90:
        return None
    return errors


def _respects_marker_boundaries(
    *, marker_diagnostics: list[dict[str, Any]], coupled_sizes: dict[float, float], log_gain: float,
) -> bool:
    """Check modeled marker intensities against censored scatter limits."""
    for marker in marker_diagnostics:
        if "scatter_boundary" not in marker:
            continue
        role = marker["marker_role"]
        position = coupled_sizes[MARKER_DIAMETERS[role]] / np.exp(log_gain)
        boundary = marker["scatter_boundary"]
        if (role == "Bright marker" and position < boundary) or (role == "Dim marker" and position > boundary):
            return False
    return True


def match_rosetta_coupling(
    *, scatter_positions: np.ndarray, coupled_sizes: dict[float, float],
    marker_diagnostics: list[dict[str, Any]],
    diagnostics: list[str] | None = None,
) -> dict[int, float]:
    """Return bead identities agreed on by plausible fits and bootstrap samples.

    Parameters
    ----------
    scatter_positions : np.ndarray
        Positive event intensities in arbitrary units. First row is the original
        fit, followed by three paired bootstrap fits. Columns are scatter peaks.
    coupled_sizes : dict[float, float]
        The configured detector's expected coupling by CAL003 diameter in nm.
    marker_diagnostics : list[dict]
        Measured marker fits and optional censored scatter boundaries.

    diagnostics : list of str or None
        Optional output for validation findings.

    Returns
    -------
    dict[int, float]
        Agreed diameter in nm by input column. Unresolved peaks are omitted.
    """
    if (
        scatter_positions.ndim != 2 or scatter_positions.shape[0] != 4
        or not 3 <= scatter_positions.shape[1] <= 20
        or not np.all(np.isfinite(scatter_positions) & (scatter_positions > 0))
        or set(coupled_sizes) != set(ROSETTA_MIX_PARTICLE_DIAMETERS_NM)
        or any(not np.isfinite(value) or value <= 0 for value in coupled_sizes.values())
    ):
        if diagnostics is not None:
            diagnostics.append("Validation needs at least three peaks with complete, positive bootstrap measurements.")
        return {}

    marker_sizes = set(MARKER_DIAMETERS.values())
    diameters = sorted(set(coupled_sizes) - marker_sizes, key=coupled_sizes.__getitem__)
    coupling = np.array([coupled_sizes[diameter] for diameter in diameters])
    measured_markers = [item for item in marker_diagnostics if item.get("validated")]
    marker_samples = []
    for item in measured_markers:
        peak = item["selected_peak"]
        positions = np.asarray([peak["mean"], *(peak.get("bootstrap_positions") or [])])
        if positions.shape != (4,) or not np.all(np.isfinite(positions) & (positions > 0)):
            if diagnostics is not None:
                diagnostics.append("A fluorescent marker is missing usable bootstrap measurements.")
            return {}
        marker_samples.append(positions)
    if len(marker_samples) > 2:
        return {}

    if len(marker_samples) == 2:
        marker_hypotheses = [tuple(MARKER_DIAMETERS[item["marker_role"]] for item in measured_markers)]
    elif len(marker_samples) == 1:
        marker = measured_markers[0]
        confirmed = not marker.get("identity_uncertain") and any(
            item["marker_role"] != marker["marker_role"] for item in marker_diagnostics
        )
        marker_hypotheses = (
            [(MARKER_DIAMETERS[marker["marker_role"]],)] if confirmed
            else [(diameter,) for diameter in sorted(marker_sizes)]
        )
    else:
        marker_hypotheses = [()]

    consensus = None
    for replicate, positions in enumerate(scatter_positions):
        order = np.argsort(positions)
        sorted_positions = positions[order]
        if np.any(np.diff(sorted_positions) <= 0):
            if diagnostics is not None:
                diagnostics.append("Two measured peaks share a scatter position in at least one fit.")
            return {}
        scores = {}
        for marker_sizes_hypothesis in marker_hypotheses:
            marker_ratios = np.array([
                np.log(coupled_sizes[diameter] / samples[replicate])
                for diameter, samples in zip(marker_sizes_hypothesis, marker_samples, strict=True)
            ])
            possible_gains = (
                [float(np.median(marker_ratios))] if marker_ratios.size
                else np.unique(np.log(coupling[None, :] / sorted_positions[:, None]))
            )
            for log_gain in possible_gains:
                if marker_ratios.size and np.max(np.abs(marker_ratios - log_gain)) > MAX_LOG_RESIDUAL:
                    continue
                if not _respects_marker_boundaries(
                    marker_diagnostics=marker_diagnostics, coupled_sizes=coupled_sizes, log_gain=log_gain,
                ):
                    continue
                for alignment in _candidate_alignments(
                    measurements=sorted_positions, coupling=coupling, log_gain=log_gain,
                ):
                    peak_indices, size_indices = np.asarray(alignment).T
                    measured = sorted_positions[peak_indices]
                    expected = coupling[size_indices]
                    errors = _response_fit_errors(
                        measured=measured, expected=expected, marker_ratios=marker_ratios,
                    )
                    if errors is None:
                        continue
                    match = tuple(sorted((int(order[index]), diameters[size]) for index, size in alignment))
                    score = sum(errors) + (positions.size - len(alignment)) * MAX_LOG_RESIDUAL
                    scores[match] = min(scores.get(match, float("inf")), score)
        if not scores:
            if diagnostics is not None:
                sample = f"bootstrap repeat {replicate}" if replicate else "the original peak fit"
                diagnostics.append(f"No candidate passed the marker and scatter fit checks for {sample}.")
            return {}
        best = min(scores.values())
        plausible_matches = [set(match) for match, score in scores.items() if score <= best + COMPETING_SCORE_MARGIN]
        sample_consensus = set.intersection(*plausible_matches)
        if diagnostics is not None and any(match != sample_consensus for match in plausible_matches):
            diagnostics.append("Competing assignments reduced the number of unambiguous identities.")
        if diagnostics is not None and consensus is not None and not consensus <= sample_consensus:
            diagnostics.append("Some identities differed across the original fit and bootstrap repeats.")
        consensus = sample_consensus if consensus is None else consensus.intersection(sample_consensus)
        if not consensus:
            return {}
    assignments = dict(consensus or ())
    if len(assignments) >= 3:
        expected = np.array([coupled_sizes[diameter] for diameter in assignments.values()])
        if any(
            _response_fit_errors(measured=positions[list(assignments)], expected=expected, marker_ratios=np.array([]))
            is None for positions in scatter_positions
        ):
            if diagnostics is not None:
                diagnostics.append("The agreed peaks failed the final response fit checks.")
            return {}
    return assignments


def _matching_table_rows(
    *, rows: list[dict[str, Any]], evidence: dict[str, Any],
) -> dict[float, int]:
    """Map the unchanged measured table to its committed Rosetta evidence."""
    evidence_rows = evidence.get("rows") or []
    snapshot = {round(float(row["measured_peak_position"]), 1): row for row in evidence_rows}
    measured_indices = {}
    for index, row in enumerate(rows):
        position = as_optional_float(row.get("measured_peak_position"))
        if position is not None:
            if position in measured_indices:
                return {}
            measured_indices[position] = index
    if len(snapshot) != len(evidence_rows) or measured_indices.keys() != snapshot.keys():
        return {}
    if any(
        as_optional_float(rows[measured_indices[position]].get("particle_diameter_nm"))
        != as_optional_float(row.get("particle_diameter_nm"))
        for position, row in snapshot.items()
    ):
        return {}
    return measured_indices


def rosetta_validation_materials(*, rows: list[dict[str, Any]] | None) -> dict[str, list[Any]]:
    """Collect the table refractive indices used for validation by peak position."""
    return {
        str(position): [row.get("particle_refractive_index"), row.get("medium_refractive_index")]
        for row in (rows or [])
        if (position := as_optional_float(row.get("measured_peak_position"))) is not None
    }


def rosetta_confirmation_pending(
    *, current_rows: list[dict[str, Any]] | None, evidence: dict[str, Any] | None,
) -> bool:
    """Return whether unedited provisional diameters need validation."""
    return bool(
        evidence and not evidence.get("confirmed")
        and _matching_table_rows(rows=current_rows or [], evidence=evidence)
    )


def rosetta_confirmed_rows(
    *, current_rows: list[dict[str, Any]] | None, evidence: dict[str, Any] | None,
) -> int | None:
    """Count jointly supported sizes for an unchanged, model-checked table."""
    if not evidence or not evidence.get("confirmed") or not _matching_table_rows(
        rows=current_rows or [], evidence=evidence,
    ):
        return None
    if evidence.get("supported_peak_count") is not None:
        return evidence["supported_peak_count"]
    return sum(bool(row.get("particle_diameter_nm")) for row in evidence["rows"])


def update_rosetta_assignment_overlays(
    *, graph_payload: dict[str, Any] | None, evidence: dict[str, Any],
) -> dict[str, Any] | None:
    """Update graph annotations with the outcome of the coupling check."""
    if not isinstance(graph_payload, dict) or graph_payload.get("rosetta_settings_preview"):
        return graph_payload
    positions = {
        round(float(entry["position"]), 1): float(entry["position"])
        for entry in evidence["scatter"]
    }
    method = (
        "Provisional diameter retained for review"
        if not evidence.get("confirmed") or evidence.get("supported_peak_count") == 0
        else "Supported by configured detector coupling and bootstrap fits"
    )
    entries = [
        {
            "position": positions[round(float(row["measured_peak_position"]), 1)],
            "diameter_nm": float(row["particle_diameter_nm"]),
            "method": method,
        }
        for row in evidence["rows"]
        if row.get("particle_diameter_nm")
        and round(float(row["measured_peak_position"]), 1) in positions
    ]
    marker_annotations = [
        item for item in graph_payload.get("scatter_guide_annotations", []) if item.get("kind") == "marker"
    ]
    annotations = [
        {"x": item["position"], "label": f"{item['diameter_nm']:g} nm", "kind": "non_fluorescent"}
        for item in entries
    ]
    return dict(
        graph_payload,
        rosetta_size_assignments=entries,
        scatter_guide_annotations=[*marker_annotations, *annotations],
    )


def resolve_rosetta_model_rows(
    *, current_rows: list[dict[str, Any]] | None, evidence: dict[str, Any],
    compute_model: Callable[..., list[dict[str, Any]]],
    diagnostics: list[str] | None = None,
) -> tuple[list[dict[str, Any]], str, dict[str, Any] | None]:
    """Reconcile an unchanged Rosetta table with the configured solid-sphere model."""
    initial_rows = [dict(row) for row in (current_rows or [])]
    row_indices = _matching_table_rows(rows=initial_rows, evidence=evidence)
    if not row_indices:
        return initial_rows, "", None

    # Model all reference sizes using the same row materials as the final fit.
    reference_materials = {
        key: next((row[key] for row in reversed(initial_rows) if row.get(key) not in (None, "")), "")
        for key in ("particle_refractive_index", "medium_refractive_index")
    }
    modeled_rows = compute_model(current_rows=[
        {
            **reference_materials,
            "particle_diameter_nm": diameter,
        }
        for diameter in ROSETTA_MIX_PARTICLE_DIAMETERS_NM
    ])
    coupled_sizes = {}
    for row in modeled_rows:
        diameter = as_optional_float(row.get("particle_diameter_nm"))
        coupling = as_optional_float(row.get("expected_coupling"))
        if diameter is not None and coupling is not None:
            coupled_sizes[diameter] = coupling

    if set(coupled_sizes) != set(ROSETTA_MIX_PARTICLE_DIAMETERS_NM) or any(
        not np.isfinite(value) or value <= 0 for value in coupled_sizes.values()
    ):
        return initial_rows, (
            "Could not compute positive coupling for all CAL003 reference sizes. "
            "Check the detector geometry, wavelength, and solid-sphere material settings, then run Compute model again."
        ), dict(evidence, confirmed=False)

    peak_samples = [
        entry for entry in evidence["scatter"]
        if round(float(entry["position"]), 1) in row_indices
    ]
    positions = np.asarray(
        [[entry["position"], *entry["replicates"]] for entry in peak_samples], dtype=float,
    ).T
    assignments = match_rosetta_coupling(
        scatter_positions=positions, coupled_sizes=coupled_sizes,
        marker_diagnostics=evidence["markers"],
        diagnostics=diagnostics,
    )
    if not assignments:
        return initial_rows, (
            f"The detector model could not confirm any of the {len(row_indices)} Rosetta diameters. "
            "The proposed diameters are still in the table for review. "
            "Automatic calibration requires at least three confirmed bead identities."
        ), dict(
            evidence,
            rows=[initial_rows[index].copy() for index in row_indices.values()],
            confirmed=True,
            supported_peak_count=0,
        )

    for index in row_indices.values():
        initial_rows[index].update(particle_diameter_nm="", expected_coupling="", expected_cross_section_nm2="")
    for peak_index, diameter in assignments.items():
        position = round(float(peak_samples[peak_index]["position"]), 1)
        initial_rows[row_indices[position]]["particle_diameter_nm"] = diameter

    unresolved = len(row_indices) - len(assignments)
    resolved_evidence = dict(
        evidence,
        rows=[initial_rows[index].copy() for index in row_indices.values()],
        confirmed=True,
        supported_peak_count=len(assignments),
    )
    if unresolved:
        return initial_rows, (
            f"Detector model supported {len(assignments)} of {len(row_indices)} Rosetta diameters. "
            f"{unresolved} peaks remain unresolved because competing assignments or the fit checks "
            "did not support a unique diameter."
        ), resolved_evidence
    return initial_rows, "", resolved_evidence


def compute_model_with_rosetta_assignments(
    *,
    current_rows: list[dict[str, Any]] | None,
    page_state: ScatteringPageState,
    mie_model: str,
    compute_coupling: Callable[..., list[dict[str, Any]]],
) -> tuple[list[dict[str, Any]], ScatteringPageState, str]:
    """
    Compute table coupling and update the Rosetta assignment state.

    Parameters
    ----------
    current_rows : list of dict or None
        Scattering calibration table rows, including any manual edits.
    page_state : ScatteringPageState
        Current assignment evidence, peak overlays, and calibration state.
    mie_model : str
        Selected Mie model. Rosetta assignment requires the solid-sphere model.
    compute_coupling : callable
        Configured model that accepts table rows as `current_rows` and returns
        rows with theoretical coupling.

    Returns
    -------
    computed_rows : list of dict
        Table rows with theoretical coupling.
    updated_state : ScatteringPageState
        Updated evidence and overlays, with the prior calibration invalidated
        when the detector model checks matching Rosetta evidence.
    status : str
        Assignment status for the table, or an empty string.
    """
    status = ""
    checked_assignment = False
    evidence = page_state.rosetta_assignment_evidence
    if evidence and mie_model == MIE_MODEL_SOLID_SPHERE:
        current_rows, status, evidence = resolve_rosetta_model_rows(
            current_rows=current_rows,
            evidence=evidence,
            compute_model=compute_coupling,
        )
        checked_assignment = True
    elif evidence:
        status = "Select the Solid Sphere particle model to check provisional Rosetta sizes."

    computed_rows = compute_coupling(current_rows=current_rows)
    state_changes = {"rosetta_assignment_evidence": evidence}
    if checked_assignment and evidence is not None:
        state_changes.update(calibration_payload=None, calibration_saved=False)
        if evidence.get("confirmed"):
            state_changes["scattering_peak_lines_payload"] = update_rosetta_assignment_overlays(
                graph_payload=page_state.scattering_peak_lines_payload,
                evidence=evidence,
            )

    return computed_rows, page_state.update(**state_changes), status
