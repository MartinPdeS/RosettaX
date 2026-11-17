Apply-calibration workflow
==========================

Use the apply workflow to add calibrated outputs to one or more experimental
FCS files using an existing saved calibration.


Request validation
------------------

RosettaX does not apply a calibration unless the request is structurally valid.
Before computation begins it checks that:

* at least one FCS file was uploaded
* a calibration was selected
* the selected calibration includes a non-empty payload
* the payload resolves to a source channel

If any of those checks fail, the workflow stops before file export.


Calibration-type specific checks
--------------------------------

Fluorescence apply is comparatively direct because the saved payload already
contains the empirical transformation.

Scattering apply requires additional target-model information. RosettaX checks
that target parameters are present for scattering payloads and validates the
requested target model before inversion is attempted. That includes diameter
range parsing and refractive-index validation for solid-sphere or core/shell
targets.


Monotonicity guardrails for scattering
--------------------------------------

Scattering apply converts measured values to estimated coupling and then to
equivalent diameter through a target Mie relation. That second step only has a
single-valued inverse on monotonic intervals.

RosettaX therefore checks whether the full target relation is strictly
monotonic. If it is not, the workflow automatically selects the largest
monotonic branch and emits a warning. The export still succeeds, but the report
and result payload make it clear that branch selection happened.


Outputs and provenance
----------------------

Before writing files, RosettaX also normalizes the requested export columns so
the output artifact is consistent. The final export can include calibrated FCS
files, extra selected columns, warnings, and a PDF report. When the export is a
ZIP bundle, the PDF is placed inside that ZIP so the provenance stays attached
to the calibrated files.
