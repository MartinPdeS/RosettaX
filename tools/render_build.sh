#!/usr/bin/env bash
# Install using explicit project version metadata; Git history is unnecessary.
set -euo pipefail

rosettax_project_directory="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$rosettax_project_directory"

python -m pip install .
python - <<'PY'
from importlib.metadata import version
from pathlib import Path
import tomllib

installed_version = version("RosettaX")
expected_version = tomllib.loads(Path("pyproject.toml").read_text())["project"]["version"]
assert installed_version == expected_version, "Installed version differs from explicit project metadata."
print(f"Installed RosettaX version: {installed_version}")
PY
