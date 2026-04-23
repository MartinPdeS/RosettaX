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
   * - Testing
     - |ci/cd|
     - |coverage|
   * - PyPI
     - |PyPi|
     - |PyPi_download|
   * - Anaconda
     - |anaconda|
     - |anaconda_download|


RosettaX is an interactive application for fluorescence and scattering calibration workflows in flow cytometry.
It is designed to make calibration setup, visualization, fitting, profile management, and result reuse more accessible through a structured graphical interface.

The project aims to provide a practical bridge between calibration data, optical modeling, and reusable experimental settings, with a focus on clarity, reproducibility, and day to day usability.

Features
********

RosettaX currently provides tools for:

* fluorescence calibration workflows
* scattering calibration workflows
* profile based configuration management
* interactive histogram inspection and peak finding
* calibration fitting and export
* reusable saved calibrations
* session friendly user interface behavior
* support for both default and custom parameter configurations

Why RosettaX
************

Calibration workflows often become fragmented across notebooks, scripts, spreadsheets, and instrument specific manual steps.
RosettaX brings these operations into a single application so that the workflow becomes easier to inspect, repeat, and maintain.

The application is particularly useful when you want to:

* standardize calibration procedures
* reduce manual copy paste operations
* keep instrument and processing defaults organized
* compare settings across runs
* build a cleaner calibration workflow for long term use

Project Status
**************

RosettaX is actively under development.
The codebase is evolving quickly, and the application is already usable for development, testing, and iterative workflow design.
Interfaces, internal organization, and features may continue to change as the project matures.

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

Documentation
*************

The documentation is available here:

`RosettaX documentation <https://martinpdes.github.io/RosettaX/>`_

Getting Started
***************

A typical usage flow is:

#. launch the application
#. load or select a profile
#. import the relevant FCS data
#. configure the fluorescence or scattering workflow
#. inspect histograms and identify peaks
#. fit the calibration
#. save the calibration for later reuse

The exact workflow depends on whether you are working in fluorescence or scattering mode, but the interface is structured to keep the process explicit and easy to follow.

Contributing
************

Contributions are welcome.

If you would like to improve RosettaX, you can:

* open an issue to report a bug
* suggest a feature or workflow improvement
* submit a pull request
* help improve documentation and examples

For substantial changes, opening an issue first is recommended so the direction can be discussed before implementation.

Contact
*******

RosettaX is developed by `Martin Poinsinet de Sivry Houle <https://github.com/MartinPdS>`_.

For collaboration, questions, or feedback:

`martin.poinsinet.de.sivry@gmail.ca <mailto:martin.poinsinet.de.sivry@gmail.ca?subject=RosettaX>`_

License
*******

Please refer to the repository license file for licensing information.


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