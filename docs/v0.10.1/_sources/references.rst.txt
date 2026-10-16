.. _references:

Calibration file format
=======================

RosettaX saves both fluorescence and scattering calibrations in the same outer
record structure. The shared wrapper is created by the save workflow before the
JSON download is produced.


Outer wrapper
-------------

Every saved calibration starts with the same top-level keys:

.. code-block:: text

	 {
		 "schema": "rosettax_calibration_v1",
		 "kind": "fluorescence",
		 "created_at": "2025-...",
		 "name": "Example calibration",
		 "payload": {
			 "...": "workflow-specific content"
		 }
	 }

``kind`` is either ``"fluorescence"`` or ``"scattering"``. The inner
``payload`` is where the workflow-specific model, fit parameters, reference
points, and metadata are stored.


Fluorescence payload
--------------------

The fluorescence payload currently uses schema version ``1.0`` and contains the
fields that are needed to reconstruct the empirical fit:

.. code-block:: text

	 {
		 "schema_version": "1.0",
		 "calibration_type": "fluorescence",
		 "source_file": "beads.fcs",
		 "source_channel": "FITC-A",
		 "gating_channel": "SSC-A",
		 "gating_threshold": 1200.0,
		 "fit_model": "log10(y)=slope*log10(x)+intercept; y=(10**intercept) * x**slope",
		 "fit_metrics": {
			 "r_squared": 0.998,
			 "point_count": 6
		 },
		 "parameters": {
			 "slope": 1.02,
			 "intercept": -0.13,
			 "prefactor": 0.74
		 },
		 "reference_points": [...],
		 "payload": {...}
	 }

The nested ``payload`` block is kept for downstream compatibility and contains
the same fit in a compact apply-oriented form.


Scattering payload
------------------

The scattering payload stores both the fitted instrument response and the
modeled calibration-standard relation used to produce it:

.. code-block:: text

	 {
		 "calibration_type": "scattering",
		 "version": 2,
		 "source_channel": "SSC-A",
		 "output_quantity": "estimated_coupling",
		 "instrument_response": {...},
		 "calibration_standard_mie_relation": {...},
		 "reference_table": [...],
		 "metadata": {...}
	 }

``instrument_response`` stores the linear fit parameters and ``R^2``.
``calibration_standard_mie_relation`` stores the modeled coupling relation for
the calibration standard. ``reference_table`` stores the measured peaks and the
rows that actually supported the fit. ``metadata`` stores the optical and
context fields needed to interpret the result later.


Why the file is structured this way
-----------------------------------

RosettaX separates the outer wrapper from the inner payload so the save/apply
pipeline can identify the calibration family quickly while still preserving the
full workflow-specific evidence. The practical rule is simple: the outer record
answers what kind of calibration this is, and the inner payload answers how it
was built.



