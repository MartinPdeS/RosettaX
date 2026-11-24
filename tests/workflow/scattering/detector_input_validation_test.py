"""Validation feedback for editable detector settings."""

if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))

import pytest
from RosettaX.pages.p03_scattering.sections.s03_model.input_validation import (
    detector_input_validity,
)


@pytest.mark.parametrize("change, invalid_indices", [
    ({"wavelength_nm": "-1"}, [0]),
    ({"detector_na": "nan"}, [1]),
    ({"detector_na": "1.4"}, [1]),
    ({"cache_na": "1.1"}, [2]),
    ({"blocker_na": "1.1"}, [3]),
    ({"sampling": "1"}, [4]),
    ({"sampling": "2.5"}, [4]),
    ({"phi_degree": "361"}, [5]),
    ({"gamma_degree": ""}, [6]),
    ({"wavelength_nm": "405.5"}, []),
])
def test_detector_validation_marks_only_invalid_fields(change, invalid_indices):
    """Validate finite values, physical bounds, and integral sample counts."""
    values = {
        "wavelength_nm": 405, "detector_na": 1, "cache_na": 0,
        "blocker_na": 0.1, "sampling": 1000, "phi_degree": 18,
        "gamma_degree": 0, "medium_refractive_index": 1.33,
    }
    values.update(change)
    validity = detector_input_validity(**values)
    assert [index for index, valid in enumerate(validity) if not valid] == invalid_indices
