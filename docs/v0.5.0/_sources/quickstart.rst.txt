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


Install locally from GitHub Releases
------------------------------------

If you want to run RosettaX locally without building from source, download a
prebuilt bundle from the GitHub Releases page:

`RosettaX Releases <https://github.com/MartinPdeS/RosettaX/releases>`_

1. Open the latest release and download the archive for your operating system.
2. Extract the archive in a folder where you have write permission.
3. Start RosettaX from the extracted bundle:

   * macOS/Linux: run the ``rosettax`` executable in the extracted folder.
   * Windows: run ``rosettax.exe`` in the extracted folder.

4. Keep calibrations and exports in a dedicated project directory so runs are
   easy to trace and reproduce.

Notes:

* Release artifacts are built in GitHub Actions and attached to version tags.
* If you are validating a build for regulated or shared environments, use the
  release checksums and provenance from the release page before distributing.
