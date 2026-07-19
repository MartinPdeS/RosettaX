RosettaX documentation
======================

.. container:: rx-hero

    RosettaX calibrates exported FCS data for fluorescence and scattering
    workflows and then reapplies saved calibrations to experimental files.
    This reference focuses on practical workflow guidance and the modeling
    details behind each output.

    | **Date**: |today|
    | **Version**: |version|


Choose your path
----------------

.. container:: rx-card-grid

    .. container:: rx-card

        **First run and setup**

        Start here if you are configuring RosettaX for the first time or walking
        through the interface.

        - :doc:`quickstart`
        - :doc:`interface`
        - :doc:`troubleshooting`

    .. container:: rx-card

        **Calibration workflows**

        Follow the complete workflow sequence for fluorescence, scattering, peak
        identification, and apply-calibration steps.

        - :doc:`workflows/index`
        - :doc:`workflows/fluorescence`
        - :doc:`workflows/scattering`
        - :doc:`workflows/peak_identification`
        - :doc:`workflows/apply`

    .. container:: rx-card

        **Modeling and internals**

        Use these pages when you want the theory, assumptions, and implementation
        references behind the calculations and generated reports.

        - :doc:`theory`
        - :doc:`references`
        - :doc:`reports`
        - :doc:`code`


Recommended reading order
-------------------------

If you want the technical picture first, read these pages in order:

#. :doc:`theory`
#. :doc:`workflows/index`
#. :doc:`references`
#. :doc:`reports`


Full documentation map
----------------------

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