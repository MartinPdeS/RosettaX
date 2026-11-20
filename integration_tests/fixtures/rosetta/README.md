# Rosetta script regression fixtures

These cases record the behavior before reorganizing the peak-script folder.
Run them with real dependencies in an isolated process:

```bash
.venv/bin/python -m pytest integration_tests/rosetta_scripts_fcs_test.py -o addopts='' -v
```

The normal unit suite invokes them through
`tests/workflow/rosetta_real_data_test.py`, alongside the existing scattering
calibration checks. The real-dependency integration CI job also discovers them.
No FCS reader, fitter, backend, or script is mocked. Scripts are resolved through
the production registry, so moving implementation files should preserve these
checks and the saved process identifiers.

## Inputs

- `apogee.json` references the existing repository sample
  `RosettaX/assets/sample-files/summer_school/apogee_rosetta_beads_1_min.fcs`. Its SHA-256 matches
  the Downloads copy exactly, so no duplicate binary is needed. It has 168,447
  events and uses `405LALS(Peak)` and `488Grn(Peak)`.
- `cal003.json` references `20260917_Rosetta_CAL003_AnHGp_02_0.fcs` in this
  directory, copied unchanged from Downloads. It has 184,575 events and uses
  `LALS(Peak)` and `488Grn(Peak)`.

Each case pins the file checksum, event count, channels, explicit settings, and
outputs from the first 100,000 events. The production sampling limit is kept
fixed for reproducibility and CI runtime. All four displayed Rosetta modes are
covered: Strict, Sensitive, Mixture, and Custom & Diagnostics.

## Expected behavior

| Input | Strict | Sensitive | Mixture | Custom & Diagnostics |
| --- | --- | --- | --- | --- |
| Apogee | Anchor warning | Anchor warning | Success, 6 table rows | Anchor warning |
| CAL003 | No validated scatter warning | Success, 3 table rows | Success, 6 table rows | No validated scatter warning |

Success checks preserve peak count and order, measured positions in arbitrary
units, exact assigned diameters in nm, fluorescent marker coordinates, the
baseline gate, and graph labels. Position tolerances are 1% numerical regression
allowances, not experimental uncertainties. Failure checks preserve meaningful
warning categories and empty results without stale plot size annotations;
exact warning prose is deliberately not pinned.

The JSON values are static baselines captured from the current implementation,
not independently verified bead identities or evidence of absolute sizing
accuracy. In particular, the older Sensitive mode's assignments are preserved
as current behavior. The Mixture mode's requirement for three validated
populations between the anchors is also covered by synthetic unit tests in
`tests/workflow/rosetta_mixture_test.py`.

Investigate failures before editing expected values. Intentional numerical or
scientific behavior changes require reviewing the recorded results; tests never
regenerate these baselines automatically.
