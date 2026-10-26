Pages API
=========

The ``RosettaX.pages`` package contains the Dash pages that compose the user-facing workflow. These modules are mostly orchestration layers that connect layouts, page-local callbacks, and workflow services.


Page map
--------

``p00_sidebar``
    Shared sidebar controls and navigation state.

``p01_home``
    Landing page and overview content.

``p02_fluorescence``
    Fluorescence calibration upload, peak selection, table editing, and save flow.

``p03_scattering``
    Scattering calibration upload, optical model configuration, table editing, calibration fitting, and save flow.

``p04_calibrate``
    Applying previously generated calibrations to files.

``p05_settings``
    Runtime profile and default configuration management.

``p06_help``
    In-application help and supporting documentation.


Representative page modules
---------------------------

The modules below are useful when extending page behavior or tracing how the UI delegates to the workflow layer.

.. automodule:: RosettaX.pages.p03_scattering.backend
    :members:
    :show-inheritance:

.. automodule:: RosettaX.pages.p03_scattering.state
    :members:
    :show-inheritance:

.. automodule:: RosettaX.pages.p02_fluorescence.state
    :members:
    :show-inheritance:

.. automodule:: RosettaX.pages.p04_calibrate.sections.s02_calibration_picker.services
    :members:
    :show-inheritance:

.. automodule:: RosettaX.pages.p04_calibrate.sections.s03_file_picker.services
    :members:
    :show-inheritance:

.. automodule:: RosettaX.pages.p04_calibrate.sections.s04_apply.services
    :members:
    :show-inheritance:


Extension guidance
------------------

- Put reusable scientific or data-processing logic in ``RosettaX.workflow``.
- Keep page modules focused on UI state reconstruction, callback wiring, and presentation.
- Treat page-local ``state`` and ``backend`` modules as the main extension points for UI customizations.