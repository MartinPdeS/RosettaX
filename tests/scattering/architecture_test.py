"""The numerical workflow remains usable independently of Dash pages."""

import subprocess
import sys


def test_scattering_backend_import_does_not_load_pages() -> None:
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
    from RosettaX.pages.p03_scattering.backend import BackEnd as PageBackEnd
    from RosettaX.workflow.scattering.backend import BackEnd

    assert PageBackEnd is BackEnd
