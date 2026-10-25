# Contributing to RosettaX

RosettaX contributions should keep fluorescence and scattering calibration
workflows clearly separated. Add behaviour-first tests for changes, preserve
packaged resource loading, and document physical assumptions and units.

Install development dependencies with `pip install -e .[testing,dev]`, then
use `make editable` and the focused tests described in `AGENTS.md`. Do not
commit generated documentation or build output. The release helper maintains
the tracked `RosettaX/_version.py`.

Before a pull request, run the relevant tests and `make quality`. Release
commands use semantic versioning: `make release patch`, `make release minor`,
or `make release major` creates and pushes the release commit and exact tag.
Use `make tag VERSION=vX.Y.Z` for a local-only release tag.

## Release compatibility policy

RosettaX supports the Python versions and operating systems covered by the
unit-test matrix in [`.github/workflows/unit-tests.yml`](.github/workflows/unit-tests.yml).
Published desktop bundles are built and smoke-tested on macOS, Windows, and
Linux from their release tag.

Saved calibration records use the `rosettax_calibration_v1` wrapper. Changes
that make an existing calibration file or runtime profile unreadable require a
documented migration path and a major release. Backward-compatible fields and
new optional payload fields may be released in a minor version; fixes that
preserve those file contracts belong in patch releases.

Before creating a release, verify the relevant workflow tests, the package
entry-point smoke test, and the platform bundle smoke tests. Release notes
must call out user-visible workflow changes, supported-platform changes, and
any required calibration or profile migration.

## Shared release versioning

Versions are explicit in `[project].version`; builds never derive versions from
Git. Install the pinned release tool in the interpreter used by Make:

```sh
python -m pip install "martinpdes-maintenance==0.2.2"
make release-check PYTHON=python
```

The `release` extra declares the same tool. The Makefile calls the installed module directly, and
`[tool.mps-maintenance]` declares the package's release files. Use
`python -m martinpdes_maintenance.cli tag vX.Y.Z --dry-run` to preview changes from a clean,
full checkout. The tool aligns configured metadata, commits, and creates an
annotated tag; it never pushes. Existing Makefile publishing shortcuts retain
their push behavior. Fetch remote tags first. With no release tags, `next` uses
the explicit project version as its starting point.
