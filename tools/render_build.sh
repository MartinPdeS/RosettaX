#!/usr/bin/env bash
# Preserve release-version metadata when Render checks out limited Git history.
set -euo pipefail

rosettax_project_directory="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$rosettax_project_directory"

if [[ "$(git rev-parse --is-shallow-repository)" == "true" ]]; then
    git fetch --unshallow --tags
else
    git fetch --tags
fi

python -m pip install .
python - <<'PY'
from importlib.metadata import version

installed_version = version("RosettaX")
assert installed_version not in {"0.0", "0.0.0"}, "Release tags were not available during the build."
print(f"Installed RosettaX version: {installed_version}")
PY
