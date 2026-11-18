"""Validation feedback for editable detector controls."""

import math
from typing import Any


def detector_input_validity(
    *, wavelength_nm: Any, detector_na: Any, cache_na: Any,
    blocker_na: Any, sampling: Any, phi_degree: Any, gamma_degree: Any,
    medium_refractive_index: Any,
) -> tuple[bool, ...]:
    """Return validity flags in the same order as the custom detector fields.

    Values use nanometers, numerical aperture, sample count, and degrees.
    The cache and blocker apertures cannot exceed the collection aperture.
    """
    def finite_number(value: Any) -> float | None:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        return number if math.isfinite(number) else None

    wavelength, aperture, cache, blocker, samples, phi, gamma, medium = (
        finite_number(value) for value in (
            wavelength_nm, detector_na, cache_na, blocker_na, sampling,
            phi_degree, gamma_degree, medium_refractive_index,
        )
    )
    aperture_valid = (
        aperture is not None and 0 < aperture <= 1.5
        and (medium is None or medium <= 0 or aperture <= medium)
    )
    return (
        wavelength is not None and wavelength > 0,
        aperture_valid,
        cache is not None and cache >= 0 and (aperture is None or cache <= aperture),
        blocker is not None and blocker >= 0 and (aperture is None or blocker <= aperture),
        samples is not None and samples >= 2 and samples.is_integer(),
        phi is not None and -360 <= phi <= 360,
        gamma is not None and -360 <= gamma <= 360,
    )
