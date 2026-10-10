"""Reusable detector and preview code must load independently of Dash pages."""

# Run pytest before application imports so the suite loads its own dependency setup.
if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))


import subprocess
import sys

import pytest


@pytest.mark.parametrize(
    "module_name",
    [
        "RosettaX.workflow.detector.mesh",
        "RosettaX.workflow.parameters",
        "RosettaX.workflow.table.scattering",
        "RosettaX.workflow.upload.adapters",
        "RosettaX.workflow.peak.adapters.fluorescence",
        "RosettaX.workflow.peak.callbacks.shared",
        "RosettaX.workflow.page_session.fluorescence",
        "RosettaX.workflow.page_session.scattering",
    ],
)
def test_workflow_import_does_not_load_pages(module_name):
    """Check workflow import does not load pages."""
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


def test_all_workflow_sources_keep_page_imports_out():
    """Check every module, including imports hidden inside functions or TYPE_CHECKING."""
    import ast
    from importlib.util import resolve_name
    from pathlib import Path

    repository = Path(__file__).resolve().parents[2]
    violations = []
    for path in (repository / "RosettaX" / "workflow").rglob("*.py"):
        relative_path = path.relative_to(repository)
        package = ".".join(relative_path.parent.parts)
        for node in ast.walk(ast.parse(path.read_text())):
            imported_names = []
            if isinstance(node, ast.Import):
                imported_names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                name = "." * node.level + (node.module or "")
                name = resolve_name(name, package) if node.level else name
                imported_names = [
                    name,
                    *(f"{name}.{alias.name}" for alias in node.names),
                ]
            if any(
                name == "RosettaX.pages" or name.startswith("RosettaX.pages.")
                for name in imported_names
            ):
                violations.append(f"{relative_path}:{node.lineno}")
    assert not violations, "Workflow imports page modules: " + ", ".join(violations)
