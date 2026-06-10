RosettaX documentation
======================

**Date**: |today|, **Version**: |version|

RosettaX calibrates exported FCS data for fluorescence and scattering workflows
and then re-applies saved calibrations to experimental files. This reference is
written for users who want to understand what the software is doing under the
hood: which models are fitted, how refractive indices are computed, what is
saved in calibration files, and which checks run before exports are produced.


Start here
----------

If you want the technical picture first, read these pages in order:

#. :doc:`theory`
#. :doc:`workflows/index`
#. :doc:`references`
#. :doc:`reports`

If you need first-run guidance or debugging help, use the in-app Help page and
the support pages listed below.


Documentation map
-----------------

.. toctree::
    :maxdepth: 2
    :caption: Under the hood

    theory
    workflows/index
    references
    reports

.. toctree::
    :maxdepth: 2
    :caption: Getting started and debugging

    quickstart
    interface
    troubleshooting

.. toctree::
    :maxdepth: 2
    :caption: API and examples

    code
    gallery/index.rst