RosettaX
========

.. image:: https://raw.githubusercontent.com/MartinPdeS/RosettaX/master/RosettaX/assets/logo_light.png
   :alt: RosettaX logo

.. list-table::
   :widths: 10 25 25
   :header-rows: 0

   * - Meta
     - |python|
     - |docs|
     - |zenodo|
   * - Testing
     - |ci/cd|
     - |coverage|
     -
   * - PyPI
     - |PyPi|
     - |PyPi_download|
     -
   * - Anaconda
     - |anaconda|
     - |anaconda_download|
     -


RosettaX is an interactive calibration application for flow cytometry.

It provides structured fluorescence and scattering calibration workflows that
combine FCS data loading, histogram inspection, peak identification, calibration
fitting, profile management, and reusable calibration export in a single
graphical interface.

The project aims to make calibration workflows easier to inspect, repeat,
document, and reuse across experiments. It is designed as a practical bridge
between calibration data, optical modeling, instrument settings, and downstream
analysis.


Features
********

RosettaX currently provides tools for:

* fluorescence calibration workflows
* scattering calibration workflows
* FCS data loading
* profile based configuration management
* interactive histogram inspection
* peak identification and peak finding
* calibration fitting
* calibration export
* reusable saved calibrations
* detector and optical parameter presets
* session friendly graphical interface behavior
* support for default and custom parameter configurations


Why RosettaX
************

Flow cytometry calibration workflows are often fragmented across instrument
software, notebooks, scripts, spreadsheets, manual peak selection, and copied
calibration constants.

This makes calibration procedures difficult to inspect, reproduce, and maintain.

RosettaX brings these operations into one application so that the full workflow
becomes explicit: data are loaded, peaks are inspected, models are fitted,
parameters are saved, and calibration results can be reused later.

The application is particularly useful when you want to:

* standardize calibration procedures
* reduce manual copy paste operations
* keep instrument and processing defaults organized
* compare settings across runs
* save reusable calibration results
* build a cleaner calibration workflow for long term use


Typical Workflow
****************

A typical RosettaX workflow is:

#. launch the application
#. load or select a runtime profile
#. import the relevant FCS data
#. select the fluorescence or scattering workflow
#. configure the relevant detector and calibration parameters
#. inspect histograms and identify calibration peaks
#. fit the calibration model
#. review the calibration result
#. save the calibration for later reuse

The exact workflow depends on whether fluorescence or scattering calibration is
being performed, but the interface is organized to keep each step explicit and
traceable.


Scientific Scope
****************

RosettaX is intended for research and development workflows involving flow
cytometry calibration.

The application focuses on practical calibration tasks rather than instrument
control. It is especially relevant when calibration data, optical parameters,
detector settings, and reusable analysis profiles need to be kept together in a
structured workflow.

The scattering calibration workflow is designed to connect measured cytometry
data with optical modeling concepts such as particle size, refractive index,
detector configuration, and scattering intensity.


Project Status
**************

RosettaX is currently in alpha development.

The application is usable for development, testing, and iterative calibration
workflow design, but the public API and internal organization may still change.
New users should expect active development and occasional breaking changes.

Current development priorities include:

* improving workflow robustness
* expanding automated tests
* improving documentation
* adding reproducible examples
* strengthening calibration validation
* polishing the graphical interface


Installation
************

PyPI
====

.. code-block:: bash

   pip install RosettaX

Anaconda
========

.. code-block:: bash

   conda install -c martinpdes rosettax

From Source
===========

.. code-block:: bash

   git clone https://github.com/MartinPdeS/RosettaX.git
   cd RosettaX
   pip install -e .


Usage
*****

After installation, launch RosettaX with:

.. code-block:: bash

   rosettax

This starts the local graphical calibration application.

RosettaX is intended to run locally. Data remain on the machine running the
software unless the user explicitly moves or shares them outside the
application.


Documentation
*************

The documentation is available here:

`RosettaX documentation <https://martinpdes.github.io/RosettaX/>`_

The documentation is expected to evolve together with the application. At this
stage, the README provides the high level overview, while the full
documentation contains more detailed usage information.


Development
***********

Install the project in editable mode with development dependencies:

.. code-block:: bash

   pip install -e ".[dev,testing,documentation]"

Run the test suite with:

.. code-block:: bash

   pytest

Run tests with coverage using:

.. code-block:: bash

   pytest --cov=RosettaX

The repository includes configuration for testing, coverage, documentation, and
continuous integration. These tools are intended to support reproducible
development as the project matures.


Contributing
************

Contributions are welcome.

Useful contributions include:

* bug reports
* workflow suggestions
* documentation improvements
* test cases
* calibration examples
* user interface improvements
* support for additional calibration workflows

For substantial changes, opening an issue first is recommended so the intended
direction can be discussed before implementation.


Citation
********

If you use RosettaX in scientific work, please cite the repository for now:

.. code-block:: text

   Martin Poinsinet de Sivry Houle.
   RosettaX: Interactive flow cytometry calibration software.
   https://github.com/MartinPdeS/RosettaX

A formal citation entry may be added later.


Contact
*******

RosettaX is developed by `Martin Poinsinet de Sivry Houle <https://github.com/MartinPdeS>`_.

For collaboration, questions, or feedback:

`martin.poinsinet.de.sivry@gmail.com <mailto:martin.poinsinet.de.sivry@gmail.com?subject=RosettaX>`_


License
*******

Please refer to the repository license file for licensing information.


.. |zenodo| image:: https://zenodo.org/badge/1087203577.svg
  :target: https://doi.org/10.5281/zenodo.19846629


.. |python| image:: https://img.shields.io/pypi/pyversions/rosettax.svg
   :alt: Python
   :target: https://www.python.org/

.. |docs| image:: https://github.com/martinpdes/rosettax/actions/workflows/deploy_documentation.yml/badge.svg
   :target: https://martinpdes.github.io/RosettaX/
   :alt: Documentation Status

.. |PyPi| image:: https://badge.fury.io/py/RosettaX.svg
   :alt: PyPI version
   :target: https://pypi.org/project/RosettaX/

.. |PyPi_download| image:: https://img.shields.io/pypi/dm/rosettax.svg
   :alt: PyPI downloads
   :target: https://pypistats.org/packages/rosettax

.. |ci/cd| image:: https://github.com/martinpdes/rosettax/actions/workflows/deploy_coverage.yml/badge.svg
   :target: https://martinpdes.github.io/RosettaX/actions
   :alt: Test Status

.. |anaconda_download| image:: https://anaconda.org/martinpdes/rosettax/badges/downloads.svg
   :alt: Anaconda downloads
   :target: https://anaconda.org/martinpdes/rosettax

.. |anaconda| image:: https://anaconda.org/martinpdes/rosettax/badges/version.svg
   :alt: Anaconda version
   :target: https://anaconda.org/martinpdes/rosettax

.. |coverage| image:: https://raw.githubusercontent.com/MartinPdeS/RosettaX/python-coverage-comment-action-data/badge.svg
   :alt: Test coverage
   :target: https://htmlpreview.github.io/?https://github.com/MartinPdeS/RosettaX/blob/python-coverage-comment-action-data/htmlcov/index.html