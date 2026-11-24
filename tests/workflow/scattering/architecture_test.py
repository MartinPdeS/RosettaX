"""The numerical workflow remains usable independently of Dash pages."""

# Run pytest before application imports so the suite loads its own dependency setup.
if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))


import subprocess
import sys


def test_scattering_backend_import_does_not_load_pages() -> None:
    """Check scattering backend import does not load pages."""
    subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; from RosettaX.workflow.scattering.backend import BackEnd; "
            "assert not any(name.startswith('RosettaX.pages') for name in sys.modules)",
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def test_legacy_backend_import_preserves_class_identity() -> None:
    """Check legacy backend import preserves class identity."""
    from RosettaX.pages.p03_scattering.backend import BackEnd as PageBackEnd
    from RosettaX.workflow.scattering.backend import BackEnd

    assert PageBackEnd is BackEnd
