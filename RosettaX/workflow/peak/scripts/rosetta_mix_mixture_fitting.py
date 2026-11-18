"""Joint log-intensity mixture fitting for experimental Rosetta scatter detection."""

import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.optimize import linear_sum_assignment
from scipy.signal import find_peaks, peak_widths
from sklearn.mixture import GaussianMixture
from typing import Any


def find_mixture_scatter_peaks(
    *,
    values: np.ndarray,
    peak_count: int,
    minimum_peak_fraction: float,
    minimum_events_per_peak: int,
    fit_r2_threshold: float,
    fit_cv_threshold: float,
    saturation_intensity: float,
    prominence_fraction: float = 0.01,
) -> dict[str, Any]:
    """Detect supported modes and fit their overlapping distributions together.

    Parameters
    ----------
    values : ndarray, shape (n,)
        Scatter intensities in arbitrary units. Only finite positive events enter
        the fit. At most 10,000 events are sampled deterministically for fitting.
    peak_count : int
        Maximum candidate peak count; a further nuisance component may model background.
    minimum_peak_fraction : float
        Compatibility argument used by the existing Rosetta fitter.
    minimum_events_per_peak : int
        Minimum effective membership in the full input population.
    fit_r2_threshold : float
        Compatibility argument; histogram R² does not determine acceptance.
    fit_cv_threshold : float
        Maximum linear-space width relative to the geometric center, using the
        existing Rosetta ``sinh(sigma * ln(10))`` width convention.
    saturation_intensity : float
        Reject centers at or above this intensity, in arbitrary units.

    prominence_fraction : float, optional
        Minimum prominence relative to the tallest smoothed bin. A separate
        local counting-noise check prevents weak histogram ripples from passing.

    Returns
    -------
    dict[str, Any]
        Existing peak-analysis contract, plus BIC and stability diagnostics.
        Accepted components require a prominent observed mode, separation of
        1.5 pooled standard deviations between supported peaks, and center drift below 0.35 fitted
        standard deviations in three bootstrap fits. These are experimental
        criteria requiring validation on representative measured datasets.
    """
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values) & (values > 0)]
    empty = {"all_peaks": [], "validated_peaks": []}
    if values.size < minimum_events_per_peak:
        return empty
    log_values = np.log10(values)
    if np.ptp(log_values) < 1e-6:
        return empty
    counts, edges = np.histogram(log_values, bins=min(256, max(64, int(np.sqrt(values.size)))))
    centers = (edges[:-1] + edges[1:]) / 2
    smoothed = gaussian_filter1d(counts.astype(float), sigma=1.5)
    # Pad the histogram so a population near an acquisition boundary is still
    # considered, then reject boundary components explicitly below.
    padded = np.pad(smoothed, 1)
    candidates, properties = find_peaks(
        padded, prominence=float(smoothed.max()) * prominence_fraction, distance=4,
    )
    widths = peak_widths(padded, candidates)[0] * (edges[1] - edges[0])
    candidates = candidates - 1
    # Propagate Poisson count variance through the same smoothing kernel.
    kernel = gaussian_filter1d(np.eye(1, 13, 6)[0], sigma=1.5)
    count_variance = np.convolve(counts.astype(float), kernel**2, mode="same")
    prominence_noise = np.sqrt(2 * np.maximum(count_variance[candidates], 1.0))
    significant = properties["prominences"] >= 2.5 * prominence_noise
    candidates, widths = candidates[significant], widths[significant]
    prominences = properties["prominences"][significant]
    if not candidates.size:
        return empty
    observed_modes = np.sort(candidates)
    strongest = np.argsort(prominences)[::-1][:max(1, int(peak_count))]
    candidates, widths = candidates[strongest], widths[strongest]
    generator = np.random.default_rng(1729)
    sample = generator.choice(log_values, size=min(log_values.size, 10_000), replace=False)[:, None]
    models = []
    for component_count in range(1, len(candidates) + 1):
        for include_background in (False, True):
            initial_means = centers[candidates[:component_count]]
            initial_deviations = np.maximum(widths[:component_count] / 2.355, 0.02)
            initial_weights = smoothed[candidates[:component_count]] * initial_deviations
            initial_weights = initial_weights / initial_weights.sum()
            if include_background:
                initial_means = np.r_[initial_means, sample.mean()]
                initial_deviations = np.r_[initial_deviations, sample.std()]
                initial_weights = np.r_[initial_weights * 0.9, 0.1]
            model = GaussianMixture(
                n_components=len(initial_means), means_init=initial_means[:, None],
                weights_init=initial_weights,
                precisions_init=(1 / initial_deviations**2)[:, None, None],
                random_state=1729, n_init=1, max_iter=500, tol=1e-4, reg_covar=1e-5,
            ).fit(sample)
            if model.converged_:
                models.append(model)
    if not models:
        return empty
    model = min(models, key=lambda fitted: fitted.bic(sample))
    means = model.means_[:, 0]
    deviations = np.sqrt(model.covariances_[:, 0, 0])
    drift = np.zeros(means.size)
    for repeat in range(3):
        resample = sample[generator.integers(0, sample.shape[0], sample.shape[0])]
        replicate = GaussianMixture(
            n_components=means.size, means_init=model.means_,
            weights_init=model.weights_, precisions_init=model.precisions_,
            random_state=repeat, n_init=1, max_iter=500, tol=1e-4, reg_covar=1e-5,
        ).fit(resample)
        # Preserve population identity across bootstrap fits using both center
        # and width. Sorting centers alone can pair a narrow peak with a broad
        # background component when they cross.
        replicate_deviations = np.sqrt(replicate.covariances_[:, 0, 0])
        center_distance = np.abs(means[:, None] - replicate.means_[:, 0]) / deviations[:, None]
        width_distance = np.abs(np.log(replicate_deviations[None, :] / deviations[:, None]))
        original_indices, replicate_indices = linear_sum_assignment(center_distance + width_distance)
        distances = center_distance[original_indices, replicate_indices]
        drift[original_indices] = np.maximum(
            drift[original_indices], distances if replicate.converged_ else np.inf,
        )
    # Background and unsupported components must not veto the separation of
    # two observed peaks. They remain in the fit to absorb tails and noise.
    mode_distances = np.abs(means[:, None] - centers[candidates][None, :])
    mode_indices = np.argmin(mode_distances, axis=1)
    mode_tolerances = np.maximum(widths[mode_indices] / 2, edges[1] - edges[0])
    component_cvs = np.sinh(deviations * np.log(10))
    # A broad component can fit two populations with its center in their valley.
    # Require evidence above counting noise before treating that center as a blend.
    valley_centers = centers_in_observed_valleys(
        fitted_centers=means, histogram_centers=centers,
        smoothed_counts=smoothed, count_variance=count_variance,
        observed_modes=observed_modes,
    )
    supported = (mode_distances[np.arange(means.size), mode_indices] <= mode_tolerances) & (
        component_cvs <= fit_cv_threshold
    ) & ~valley_centers
    # A mixture may use several components to describe one non-Gaussian mode.
    # Only the component contributing the highest modal density represents that
    # observed peak; its tail components cannot veto peak separation.
    representatives = np.zeros(means.size, dtype=bool)
    for observed_mode in range(len(candidates)):
        matched = np.flatnonzero(supported & (mode_indices == observed_mode))
        if matched.size:
            representative = matched[np.argmax(model.weights_[matched] / deviations[matched])]
            representatives[representative] = True
    all_peaks = []
    for index, (center, deviation) in enumerate(zip(means, deviations, strict=True)):
        effective_count = int(round(model.weights_[index] * values.size))
        position = float(10**center)
        cv = float(np.sinh(deviation * np.log(10)))
        mode_index = int(np.argmin(np.abs(centers[candidates] - center)))
        mode_distance = abs(centers[candidates[mode_index]] - center)
        reasons = []
        if valley_centers[index]:
            reasons.append("Fitted center lies in a resolved valley between observed populations")
        if mode_distance > max(widths[mode_index] / 2, edges[1] - edges[0]):
            reasons.append("No prominent observed mode near component center")
        if supported[index] and not representatives[index]:
            reasons.append("Additional component describing tails of the same observed mode")
        if effective_count < minimum_events_per_peak:
            reasons.append(f"Only {effective_count} effective events")
        if drift[index] > 0.35:
            reasons.append(f"Unstable center: bootstrap drift {drift[index]:.2f} sigma")
        if means.size > 1:
            separation = np.abs(means - center) / np.sqrt((deviations**2 + deviation**2) / 2)
            separation[~representatives] = np.inf
            separation[index] = np.inf
            if separation.min() < 1.5:
                reasons.append("Overlapping components are not sufficiently separated")
        if cv > fit_cv_threshold:
            reasons.append(f"CV {cv:.2f} > {fit_cv_threshold:.2f}")
        if position >= saturation_intensity:
            reasons.append("Center reaches saturation")
        if center - 2 * deviation < edges[0] or center + 2 * deviation > edges[-1]:
            reasons.append("Population may be truncated by the acquisition boundary")
        all_peaks.append({
            "mean": position, "std": position * cv, "cv": cv,
            "r2": None, "count": effective_count, "validated": not reasons,
            "rejection_reasons": reasons, "bootstrap_drift_sigma": float(drift[index]),
        })
    all_peaks.sort(key=lambda peak: peak["mean"])
    return {
        "all_peaks": all_peaks,
        "validated_peaks": [peak for peak in all_peaks if peak["validated"]],
        "method": "log_gaussian_mixture", "bic": float(model.bic(sample)),
        "fit_sample_count": int(sample.size),
    }


def centers_in_observed_valleys(
    *,
    fitted_centers: np.ndarray,
    histogram_centers: np.ndarray,
    smoothed_counts: np.ndarray,
    count_variance: np.ndarray,
    observed_modes: np.ndarray,
) -> np.ndarray:
    """Identify fitted log-intensity centers in statistically resolved valleys.

    Parameters
    ----------
    fitted_centers : ndarray, shape (k,)
        Component centers in log10 intensity.
    histogram_centers : ndarray, shape (n,)
        Increasing bin centers in log10 intensity.
    smoothed_counts : ndarray, shape (n,)
        Smoothed event counts per bin.
    count_variance : ndarray, shape (n,)
        Poisson variance propagated through the smoothing kernel.
    observed_modes : ndarray, shape (m,)
        Increasing histogram indices of significant observed maxima.

    Returns
    -------
    ndarray of bool, shape (k,)
        True where both bracketing modes exceed the center by 2.5 estimated
        standard deviations. This empirical check requires resolved modes.
        A single unresolved mode cannot establish that two populations exist.
    """
    if observed_modes.size < 2:
        return np.zeros(fitted_centers.size, dtype=bool)
    mode_centers = histogram_centers[observed_modes]
    right_indices = np.searchsorted(mode_centers, fitted_centers)
    bracketed = (right_indices > 0) & (right_indices < observed_modes.size)
    right = observed_modes[np.clip(right_indices, 1, observed_modes.size - 1)]
    left = observed_modes[np.clip(right_indices - 1, 0, observed_modes.size - 2)]
    center_counts = np.interp(fitted_centers, histogram_centers, smoothed_counts)
    center_variance = np.interp(fitted_centers, histogram_centers, count_variance)
    left_noise = np.sqrt(np.maximum(count_variance[left] + center_variance, 1.0))
    right_noise = np.sqrt(np.maximum(count_variance[right] + center_variance, 1.0))
    return bracketed & (
        smoothed_counts[left] - center_counts >= 2.5 * left_noise
    ) & (smoothed_counts[right] - center_counts >= 2.5 * right_noise)
