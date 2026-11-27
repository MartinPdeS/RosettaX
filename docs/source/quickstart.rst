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
#. Review the save checklist, confirm the calibration context and fit, then save
   the calibration JSON.
#. Reuse the calibration in the apply workflow and keep the generated PDF report.


Worked examples
---------------

The application is the normal place to create and save a calibration. The
examples below are deliberately small, reproducible views of the calculations
behind the two fits. They use the same fitting functions as the application, so
their displayed coefficients follow the same rules as RosettaX:

* :doc:`gallery/fluorescence_calibration` shows a log-log fluorescence fit and
  the equivalent power-law relation.
* :doc:`gallery/scattering_instrument_response` shows a zero-intercept
  scattering instrument-response fit against modeled coupling values.

Use the numbers in an example to understand the fit; do not copy them into a
calibration record. Your saved calibration must be based on your bead file,
detector channel, and approved reference table.


What to inspect before saving
-----------------------------

Before saving a calibration, confirm all of the following:

* the source channel is the detector you actually intend to calibrate
* the measured peaks correspond to the expected bead populations
* the calibration table pairs the right measured values with the right references
* the fitted relation is scientifically plausible, not just numerically tidy
* the metadata is specific enough that another person could interpret the JSON later
* the save checklist reports that the calibration, name, and output channel are ready

RosettaX keeps the workflow progress visible at the top of the calibration page.
It marks completed steps, identifies the current step, and shows later steps as
blocked until their prerequisites are complete.


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


Deployment
----------

Docker
~~~~~~

With Docker and Docker Compose installed, run from the repository checkout:

.. code-block:: bash

   docker compose up --build

Open http://localhost:8050 in your browser. The container uses Python 3.13 and
Gunicorn, runs as a non-root user, and publishes the application on the local
machine only. Compose targets ``linux/amd64`` because PyMieSim 6.0.4 provides
x86-64 Linux wheels; Docker uses emulation on Apple Silicon.

Uploads, server-side calibration files, and usage records are stored in the
``rosettax-data`` named volume and survive container recreation. User-created
profiles remain in browser storage; downloaded FCS files, calibration JSON,
and PDF reports are saved by your browser.

To use a different port or maximum upload size:

.. code-block:: bash

   ROSETTAX_PORT=8051 ROSETTAX_MAX_UPLOAD_SIZE=512MB docker compose up --build

Stop the application with Ctrl+C, or run ``docker compose down`` after starting
it with ``docker compose up --build --detach``. ``docker compose down`` retains
the data volume; adding ``--volumes`` deletes the stored application data.

For a native deployment, ``ROSETTAX_CALIBRATION_DIRECTORY`` can select a writable
directory for server-side calibration files. Without that setting, RosettaX
keeps its existing calibration directory beside the package.

``ROSETTAX_UPLOAD_DIRECTORY`` selects a writable directory for uploaded FCS
and calibration files. It defaults to ``~/.rosettax/uploads``.

The native CLI and the bundled loopback-only Compose setup allow local Settings
editing. The Gunicorn WSGI entry point defaults to hosted mode. For an HTTPS
deployment, keep ``ROSETTAX_HOSTED=true`` and set a strong
``ROSETTAX_ADMIN_TOKEN`` in the server environment. Sign in at
``/admin/login`` to access both ``/admin`` and ``/settings`` for 30 minutes.
Settings edits are saved to the administrator's browser. To change the presets
offered to public users, update the packaged profiles and redeploy.


Render
~~~~~~

For a native Python web service on Render, set the Build Command to:

.. code-block:: bash

   bash tools/render_build.sh

The script installs the package using its explicit project version and checks
that the installed version matches the project metadata. Git history is not
needed for installation.
Keep your existing Start Command and redeploy after changing the Build Command.
The home page displays the installed software version, with a checked-in version
fallback for source checkouts and standalone bundles.
