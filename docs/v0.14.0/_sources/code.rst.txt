.. _source_code:

API reference
=============

This section documents the main Python interfaces exposed by RosettaX.

The package is organized into four major layers:

- ``RosettaX.application`` bootstraps the Dash application and global routes.
- ``RosettaX.pages`` contains page-specific user interface composition.
- ``RosettaX.workflow`` contains the calibration, upload, parameter, peak, and save workflows.
- ``RosettaX.utils`` contains reusable configuration, parsing, I/O, and data helpers.

For most integrations and internal extensions, the most relevant modules are:

- ``RosettaX.application.main`` for application startup.
- ``RosettaX.utils.runtime_config`` for typed runtime configuration.
- ``RosettaX.utils.reader`` and ``RosettaX.utils.fcs_metadata`` for FCS file handling.
- ``RosettaX.workflow.upload.services`` for upload payload normalization and persistence.
- ``RosettaX.workflow.parameters`` for scattering-model parameter normalization.
- ``RosettaX.workflow.calibration`` for calibration model construction.
- ``RosettaX.workflow.apply_calibration`` for applying stored calibrations to files.
- ``RosettaX.workflow.peak`` for peak detection and graph helpers.

.. toctree::
	:maxdepth: 2

	api/application
	api/utilities
	api/workflows
	api/pages


Package root
------------

.. automodule:: RosettaX
	:members:
	:show-inheritance:


Top-level package map
---------------------

``RosettaX.application``
	Application bootstrap, layout registration, callback registration, and server routes.

``RosettaX.pages``
	Dash pages and section-level composition for fluorescence, scattering, calibration, settings, and help views.

``RosettaX.workflow``
	Domain logic for data upload, parameter normalization, peak handling, calibration generation, calibration application, and exports.

``RosettaX.utils``
	Shared helpers used across both the workflow and application layers.


Documentation conventions
-------------------------

The API pages below focus on the modules that define behavior or stable extension points.
Pure wiring modules such as page IDs, Dash layout-only wrappers, and callback registration shims are documented at a higher level rather than exhaustively listing every symbol.

