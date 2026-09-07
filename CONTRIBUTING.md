# Contributing to RosettaX

RosettaX contributions should keep fluorescence and scattering calibration
workflows clearly separated. Add behaviour-first tests for changes, preserve
packaged resource loading, and document physical assumptions and units.

Install development dependencies with `pip install -e .[testing,dev]`, then
use `make editable` and the focused tests described in `AGENTS.md`. Do not
commit generated documentation, build output, or `RosettaX/_version.py`.

Before a pull request, run the relevant tests and `make quality`. Release
commands use semantic versioning: `make release patch`, `make release minor`,
or `make release major` creates and pushes the release commit and exact tag.
Use `make tag VERSION=vX.Y.Z` for a local-only release tag.
