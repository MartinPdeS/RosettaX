RosettaX
========

.. image:: https://raw.githubusercontent.com/MartinPdeS/RosettaX/master/RosettaX/assets/logo_light.png
   :alt: RosettaX logo

.. list-table::
   :widths: 10 25 25, 25
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

It provides local graphical workflows for fluorescence and scattering
calibration, combining FCS data loading, histogram inspection, peak
identification, calibration fitting, runtime profile management, and reusable
calibration export in a single interface.

The goal of RosettaX is to make calibration workflows explicit, inspectable,
repeatable, and easier to maintain across experiments. The application is
designed as a practical bridge between experimental cytometry data, optical
modeling, detector settings, calibration references, and downstream analysis.


Overview
********

Flow cytometry calibration is often distributed across several disconnected
tools: instrument software, notebooks, scripts, spreadsheets, manually selected
peaks, copied constants, and exported configuration files. This fragmentation
makes calibration procedures difficult to audit, reproduce, compare, and reuse.

RosettaX brings these steps into a structured application. A calibration session
can be configured, inspected, fitted, saved, and reused without separating the
scientific model from the practical workflow. This is particularly useful when
calibration results need to remain traceable across instruments, detector
settings, reference materials, and analysis pipelines.

RosettaX currently focuses on two main calibration workflows:

* fluorescence calibration
* scattering calibration

The fluorescence workflow supports calibration from reference intensity data.
The scattering workflow connects measured cytometry signals with optical
parameters such as particle size, refractive index, detector configuration, and
scattering intensity.


Features
********

RosettaX currently provides:

* fluorescence calibration workflows
* scattering calibration workflows
* FCS data loading
* interactive histogram inspection
* peak identification and peak finding
* calibration fitting
* reusable calibration export
* runtime profile management
* detector and optical parameter presets
* support for default and custom parameter configurations
* local graphical application behavior suitable for repeated calibration work


Why RosettaX
************

RosettaX is intended to reduce the amount of manual and implicit work involved
in flow cytometry calibration.

Typical calibration workflows often require users to move between acquisition
software, custom scripts, spreadsheets, and manually recorded parameters. This
can make it difficult to know exactly which data, peaks, settings, assumptions,
and fitted models produced a given calibration result.

RosettaX addresses this by keeping the workflow organized around explicit
steps:

* load the relevant cytometry data
* select or define the calibration context
* inspect the signal distributions
* identify the calibration peaks
* fit the calibration relation
* review the result
* export a reusable calibration file

This makes the calibration process easier to document, compare, repeat, and
adapt to new experiments.


Typical Workflow
****************

A typical RosettaX session follows these steps:

#. launch the local application
#. load or select a runtime profile
#. import the relevant FCS data
#. choose the fluorescence or scattering calibration workflow
#. configure the detector, optical, and calibration parameters
#. inspect histograms and identify calibration peaks
#. fit the calibration model
#. review the calibration result
#. save the calibration for later reuse

The exact procedure depends on the selected workflow, but the application is
organized so that each step remains visible and traceable.


Scientific Scope
****************

RosettaX is intended for research and development workflows involving flow
cytometry calibration. It focuses on calibration analysis and calibration file
generation rather than instrument control.

The application is especially relevant when experimental cytometry data,
reference materials, optical parameters, detector settings, and reusable
analysis profiles need to be managed together in a structured workflow.

For scattering calibration, RosettaX is designed to connect measured cytometry
signals with optical modeling concepts, including particle size, refractive
index, collection geometry, detector configuration, and scattering intensity.
This makes it suitable for workflows where optical interpretation and
instrument calibration need to remain linked.


Data Handling
*************

RosettaX runs locally.

The application does not upload FCS files, calibration profiles, calibration
results, or generated configuration files to a remote service. Data remain on
the machine running the software unless the user explicitly moves, uploads, or
shares them outside the application.


Project Status
**************

RosettaX is currently in alpha development.

The application is usable for development, testing, and iterative calibration
workflow design. However, the public API, internal organization, and graphical
workflows may still change. New users should expect active development and
occasional breaking changes.

Current development priorities include:

* improving workflow robustness
* expanding automated tests
* improving documentation
* adding reproducible examples
* strengthening calibration validation
* refining the graphical interface
* improving packaging and release workflows


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

The application opens a browser based interface served from the local machine.
It is intended for local calibration workflows and does not require a remote
server.


Documentation
*************

The documentation is available here:

`RosettaX documentation <https://martinpdes.github.io/RosettaX/>`_

The documentation is expected to evolve with the application. At this stage, the
README provides the high level overview, while the full documentation contains
more detailed usage information.


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

For substantial changes, please open an issue first so that the intended
direction can be discussed before implementation.


Citation
********

If you use RosettaX in scientific work, please cite the repository and the
archived Zenodo release:

.. code-block:: text

   Martin Poinsinet de Sivry Houle.
   RosettaX: Interactive flow cytometry calibration software.
   https://github.com/MartinPdeS/RosettaX
   https://doi.org/10.5281/zenodo.19846629

A formal citation file may be added in a future release.


Contact
*******

RosettaX is developed by `Martin Poinsinet de Sivry Houle <https://github.com/MartinPdeS>`_.

For collaboration, questions, or feedback:

`martin.poinsinet.de.sivry@gmail.com <mailto:martin.poinsinet.de.sivry@gmail.com?subject=RosettaX>`_


License
*******

RosettaX is distributed under the GNU Affero General Public License v3.0 or
later.

See the repository ``LICENSE`` file for the full license text.

Commercial licensing, support, validation, or custom deployment agreements may
be discussed with the author.


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