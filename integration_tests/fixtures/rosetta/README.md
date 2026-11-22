# Rosetta script regression fixtures

These cases record the current registered modes and a historical global-fit control.
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
| Apogee | Anchor warning | — | Five sized rows after the two exclusions | Anchor warning |
| CAL003 | No validated scatter warning | Success, 3 table rows | One measured peak with no diameter | No validated scatter warning |

Success checks preserve peak count and order, measured positions in arbitrary
units, exact assigned diameters in nm, fluorescent marker coordinates, the
baseline gate, and graph labels. Position tolerances are 1% numerical regression
allowances, not experimental uncertainties. Warning checks preserve useful
measured positions where sizing can remain unresolved. Strict failures still
require empty results. Tests match short warning fragments for key outcomes.

The JSON values are static baselines captured from the current implementation,
not independently verified bead identities or evidence of absolute sizing
accuracy. In particular, the older Sensitive mode's assignments are preserved
as current behavior. The Mixture mode's requirement for three validated
populations between the anchors is also covered by synthetic unit tests in
`tests/workflow/rosetta_mixture_test.py`.

Investigate failures before editing expected values. Intentional numerical or
scientific behavior changes require reviewing the recorded results; tests never
regenerate these baselines automatically.

## Mixture diagnostics

The registered Mixture mode and the historical control diverge at the scatter fit. Both baseline gates
and both marker positions match the recorded values on each sample. A replay
using the same gated events and one OpenMP thread isolated the effect of replacing
the three marker-bounded fits with the global fit. The global fit recovers the
recorded scatter centers for both files on this replay.

| Fixture | Marker-bounded fit | Effect of the lowest-peak exclusion |
| --- | --- | --- |
| Apogee | Seven scatter peaks pass. The fitted center of the lowest peak moves from about 2,301 to 2,241 a.u. | Six table rows have sizes after the saturation guard. The exclusion removes the row provisionally assigned 70 nm. |
| CAL003 | One center passes between the markers, near 406,686 a.u. The regional fit-window guard rejects candidates near 95,649 and 871,853 a.u. The global fit accepts nearby centers at about 99,464 and 878,306 a.u. | The exclusion removes the only sized row, provisionally assigned 125 nm. The measured middle peak remains with a blank diameter. |

To check both fits, run the regression command above with
`-k mixture --tb=short`. The failure messages show the event counts, gates,
fit candidates, sizing outcome, and any excluded row. The replay used the
checksum-pinned FCS files, Python 3.13.7, NumPy 2.2.6, SciPy 1.18.1 and
scikit-learn 1.9.1 on macOS arm64. The fitter uses its fixed seed of 1729.
The two FCS fixtures have no independently assigned peak identities.
