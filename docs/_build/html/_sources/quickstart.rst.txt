Quick start
===========

This page is the fastest way to decide where to begin in RosettaX.


Choose the right workflow
-------------------------

Use **Fluorescence** when you are mapping measured detector values to known
fluorescence reference values such as MESF.

Use **Scattering** when you are fitting measured scatter peaks against modeled
or tabulated scattering standards.

Use **Apply calibration** when you already trust the saved calibration JSON and
want to export calibrated FCS files.


Recommended order of work
-------------------------

#. Upload the calibration bead or standard file.
#. Inspect the selected detector and the visible peaks before fitting.
#. Review the calibration table carefully.
#. Create the calibration and inspect the fit.
#. Save the calibration JSON.
#. Reuse the calibration in the apply workflow and keep the generated PDF report.


What to inspect before saving
-----------------------------

Before saving a calibration, confirm all of the following:

* the source channel is the detector you actually intend to calibrate
* the measured peaks correspond to the expected bead populations
* the calibration table pairs the right measured values with the right references
* the fitted relation is scientifically plausible, not just numerically tidy
* the metadata is specific enough that another person could interpret the JSON later


What to inspect before applying
-------------------------------

Before exporting calibrated files, confirm all of the following:

* the selected calibration matches the intended detector and quantity
* the uploaded experimental files belong to the same interpretation context as the saved calibration
* any scattering target-model settings are still appropriate
* the exported channels and extra columns are intentional


Next pages
----------

Continue with :doc:`interface` for a page-by-page guide, then read the workflow
chapter that matches your task in :doc:`workflows/index`.
