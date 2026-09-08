Fluorescence workflow
=====================

Use the fluorescence workflow when you have a bead or reference sample with
known fluorescence values and want to map one exported detector column onto that
reference scale.


What enters the fit
-------------------

RosettaX builds fluorescence calibration points from a table of paired values:

* measured detector intensity in arbitrary units
* assigned calibrated reference intensity for the matching bead population

Those pairs usually come from histogram peak review plus manual verification of
the reference table. The important point is that RosettaX fits the pairs you
approve. Peak selection and reference assignment are therefore part of the model
definition, not just UI preparation.


Regression model
----------------

The implemented fluorescence regression is a log-log linear fit:

.. math::

	\log_{10}(y) = m \log_{10}(x) + b

which RosettaX also stores in its equivalent power-law form:

.. math::

	y = 10^b x^m

Before fitting, RosettaX removes any pair where the measured intensity or the
reference intensity is missing, non-finite, or not strictly positive. The fit
itself uses ``numpy.polyfit`` on the log10-transformed arrays.


Fit diagnostics
---------------

RosettaX stores:

* slope
* intercept
* prefactor
* ``R^2``
* point count

These values are saved directly into the calibration payload so the fit can be
reviewed without reopening the original session.


Saved payload
-------------

The fluorescence payload preserves the full interpretation context needed by the
apply workflow:

* source file name
* source channel
* optional gating channel
* optional gating threshold
* fit model string
* fit metrics
* fit parameters
* reference points
* a compact compatibility payload used downstream during apply

In practice, this means the saved JSON preserves both the calibration equation
and the table of bead-reference pairs that justified it.
