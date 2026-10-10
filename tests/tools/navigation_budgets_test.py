"""Traffic budget checks reject regressions and incomplete smoke runs."""

# Run pytest before application imports so the suite loads its own dependency setup.
if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))


import importlib.util
from pathlib import Path

import pytest

specification = importlib.util.spec_from_file_location(
    "profile_navigation",
    Path(__file__).resolve().parents[2] / "tools/profile_navigation.py",
)
profile_navigation = importlib.util.module_from_spec(specification)
specification.loader.exec_module(profile_navigation)


@pytest.mark.parametrize("metric", ["callback_count", "callback_response_bytes"])
def test_navigation_limits_apply_to_every_repeated_transition(metric):
    """Check navigation limits apply to every repeated transition."""
    budgets = {
        "loaded /scattering": {"callback_count": 78, "callback_response_bytes": 500000}
    }
    measurement = {
        "transition": "loaded 2 /scattering",
        "callback_count": 72,
        "callback_response_bytes": 407000,
    }
    profile_navigation.check_navigation_budgets([measurement], budgets)
    measurement[metric] = budgets["loaded /scattering"][metric] + 1
    with pytest.raises(RuntimeError, match=metric):
        profile_navigation.check_navigation_budgets([measurement], budgets)


def test_navigation_limits_require_every_budgeted_transition():
    """Check navigation limits require every budgeted transition."""
    with pytest.raises(RuntimeError, match="Missing measurement: empty /fluorescence"):
        profile_navigation.check_navigation_budgets(
            [], {"empty /fluorescence": {"callback_count": 52}}
        )
