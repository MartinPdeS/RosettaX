# Real-FCS scattering regression cases

Run separately from the stubbed unit suite:

```bash
make test-scattering-fcs
```

The command uses Python 3.13 by default. To use the local virtual environment,
run `make test-scattering-fcs PYTHON=.venv/bin/python`.

The test file can also run directly with its pytest entry point:

```bash
python integration_tests/scattering_fcs_test.py
```

`scattering_fcs_test.py` discovers each JSON case in this directory. It loads
an existing repository FCS file, executes the Rosetta peak process, calls the
same scattering calibration service used by the page, serializes and reloads
the resulting calibration, and applies it to detected peaks and real events.
No reader, fitting, detector geometry, or PyMieSim functions are mocked.
The existing integration CI job collects these tests automatically.

## Initial Apogee Rosetta baseline

The input is `RosettaX/assets/sample-files/apogee_rosetta_beads_1min.fcs`.
Its FCS metadata reports Apogee A60-Micro, acquisition date 14-Aug-2023,
original filename `Rosetta_1min_0.fcs`, and 168,447 events. The checksum pins
this exact file; it is referenced in place rather than duplicated.

Detection uses the first 100,000 events, `405LALS(Peak)` scattering,
`488Grn(Peak)` fluorescence, and explicitly recorded Rosetta settings. There
is no random event sampling. The baseline fluorescence gate is 3 sigma;
saturated-event filtering and the 50% saturation guard are enabled. The two
expected positions are the usable non-fluorescent **table peaks**, not every
candidate, fluorescent guide, or saturated population displayed by the graph.

Calibration uses the packaged `Apogee - Side` detector abstraction, 405 nm
illumination, medium index 1.333, particle index 1.59, and 256 angular samples.
The dense standard relation has 128 diameter points. Sampling is deliberately
bounded for CI; effective blocker geometry and angular weights are resolved
by the production detector abstractions.

**The 400 and 799 nm assignments are illustrative trial inputs, not confirmed
identities of these two FCS populations.** Those diameters occur in the
packaged Rosetta Mix standard, but this repository has no verified mapping of
the measured peaks to bead sizes. The test checks the current numerical
behavior of this explicitly chosen configuration. It does not establish
absolute sizing accuracy, and the reference populations are used in fitting,
not held out for independent validation.

| Quantity | First peak | Second peak |
| --- | ---: | ---: |
| Detected raw scattering position | 261,763.2047 | 1,492,769.7195 |
| Trial reference diameter (nm) | 400 | 799 |
| Calibrated coupling position | 0.0000724394992 | 0.000413104244 |
| Trial equivalent diameter (nm) | 415.1155 | 797.4329 |
| Calibrated-event histogram mode | 0.000073671875 | 0.00041328125 |

The recorded zero-intercept response slope is `2.7673675243e-10`; its R-squared
is approximately 0.99763. Expected values were recorded from the current
implementation when establishing this case. They are static regression
baselines, not independently certified measurements, and tests never regenerate
them from their own outputs.

Tolerances are numerical regression allowances: 1% for raw peaks and response
slope, 1.5% for calibrated coupling peaks, and 2 nm for trial equivalent
diameters. These are not experimental uncertainty estimates. The event
histogram windows and 32-bin grids are fixed in the case; modes must stay
within one bin, with a minimum population in each window to reject missing
populations. The histogram estimator operates on actual calibrated FCS events,
separately from the Rosetta fitted-peak output.

## Adding or revising cases

Add a JSON case with its input checksum, explicit detection/calibration inputs,
reference assignments, and fixed expected values. The current runner supports
Rosetta detection and solid-sphere calibration. Use the same quantity, ordering,
and population selection when comparing recorded outputs.

Investigate a failure before changing an expectation. Record the reason for an
intentional algorithm, geometry, configuration, or input-file change in review;
do not automatically refresh baselines to make a failure pass.

When confirmed bead assignments or an independent calibration become available,
replace the trial inputs in a reviewed change. Add a held-out population or
separate reference sample, with tolerances justified by its uncertainty, to
extend numerical regression into scientific validation.
