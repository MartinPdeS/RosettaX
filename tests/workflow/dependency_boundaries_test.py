"""Reusable detector and preview code must load independently of Dash pages."""

import subprocess
import sys

import pytest


@pytest.mark.parametrize(
    "module_name",
    ["RosettaX.workflow.detector.mesh", "RosettaX.workflow.parameters"],
)
def test_workflow_import_does_not_load_pages(module_name):
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import importlib, sys; "
            f"importlib.import_module({module_name!r}); "
            "assert not any(name.startswith('RosettaX.pages') for name in sys.modules)",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
