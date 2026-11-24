Scattering workflow
===================

Use the scattering workflow when the calibration depends on an optical model
rather than only on assigned reference intensities.


What is modeled
---------------

RosettaX models scattering standards with PyMieSim using a Gaussian source and a
photodiode detector configuration. The core optical inputs are:

* wavelength
* medium refractive index
* particle refractive index, or core/shell refractive indices
* detector numerical aperture
* detector cache numerical aperture
* blocker-bar numerical aperture
* detector phi angle
* detector gamma angle
* detector sampling

Detector presets can also contribute angular weights and effective geometry
corrections before the coupling values are computed.


Supported cytometer presets
---------------------------

See :doc:`systems` for the cytometers covered by Rosetta validation and their
available geometry previews.

Step 3 shows the active detector preset and wavelength. Select **Change preset**
to choose a brand, model and detector type. The geometry is displayed separately.

If your company would like RosettaX to support another cytometer, contact the
maintainer with an example FCS file, the detector naming you want recognized,
and any public optical-geometry documentation that should inform the preset.




How the calibration-standard relation is built
----------------------------------------------

RosettaX parses the calibration-standard table, keeps only rows with finite
diameter and measured-peak values, computes modeled coupling for those standard
particles, and then fits the measured peaks against those theoretical coupling
values.

The current instrument-response model is linear:

.. math::

	\mathrm{theoretical\_coupling} = m \cdot \mathrm{measured\_peak} + b

The default behavior is to force the intercept to zero. RosettaX stores the fit
parameters and ``R^2`` in the ``instrument_response`` block.


Material refractive indices
---------------------------

Material presets such as water, PBS, polystyrene, silica, PMMA, and lipid-like
media are resolved through the packaged Sellmeier bank at the selected
wavelength. Numeric presets remain numeric. This means the refractive indices
used for the fit can change with wavelength and are not treated as hard-coded
constants.


Saved payload
-------------

The scattering payload preserves both the fit and the modeled standard context:

* source channel and output quantity
* instrument-response fit parameters
* the calibration-standard Mie relation
* the reference table used for fitting
* metadata needed to reconstruct the optical assumptions later

That payload is what allows RosettaX to apply a scatter calibration later by
first converting measured peak to estimated coupling and then converting that
coupling onto a target Mie relation.
