Troubleshooting
===============

This page focuses on workflow problems that commonly produce misleading
calibrations or confusing exports.


Peak selection problems
-----------------------

If the detected peaks do not resemble the expected bead populations:

* verify the selected detector channel first
* check whether gating or threshold choices removed too many events
* confirm that the calibration table still pairs the correct measured peaks with the correct references


Fit looks good, interpretation looks wrong
------------------------------------------

A visually clean fit or high :math:`R^2` does not guarantee that the scientific
interpretation is correct. Re-check:

* the meaning of the selected source channel
* the assigned reference values
* whether the measured populations are actually resolved well enough to fit
* whether the chosen model assumptions still make sense for the acquisition


Scattering metadata is too thin
-------------------------------

If a saved scattering calibration is hard to interpret later, the missing
details are usually one of these:

* wavelength
* detector configuration or geometry
* refractive-index assumptions
* reference standard table context


Apply-export provenance is weak
-------------------------------

If it is hard to explain an exported calibrated file later, prefer to:

* export as a ZIP when several files are involved
* keep the PDF report with the exported artifact
* avoid ambiguous file naming for saved calibrations
