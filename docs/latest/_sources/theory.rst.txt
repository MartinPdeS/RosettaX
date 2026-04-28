:orphan:

.. _theory:

Theoretical background
======================

RosettaX is built around the idea that flow cytometry calibration should remain
explicit from the raw measurement space to the exported calibration relation.

In many workflows, calibration is performed through a combination of acquisition
software, exported FCS files, manual peak selection, spreadsheets, optical
models, and downstream analysis scripts. Each of these steps can be valid on its
own, but the full calibration chain often becomes difficult to inspect and
reproduce once parameters are copied between tools.

RosettaX provides a structured interface for this process. It does not attempt
to control the cytometer. Instead, it focuses on the calibration analysis step:
loading cytometry data, inspecting signal distributions, identifying reference
populations, fitting calibration relations, and exporting reusable calibration
files.

The purpose of this section is to describe the physical and numerical concepts
behind the calibration workflows implemented in RosettaX.


Flow cytometry measurements
***************************

Flow cytometry measures particles or cells as they pass through an interrogation
region, usually defined by a focused optical beam and a hydrodynamically focused
sample stream. As each particle crosses the beam, it produces optical signals
that are detected by one or more photodetectors.

Common signal channels include:

* forward scatter, often associated with low angle scattered light
* side scatter, often associated with larger angle scattered light
* fluorescence channels, associated with emitted light from fluorophores
* trigger channels, used by the instrument to decide whether an event should be
  recorded

The recorded data are usually exported as FCS files. Each row in an FCS file
corresponds to an event, and each column corresponds to a measured feature or
channel. Depending on the instrument and acquisition settings, these features
may include pulse height, pulse area, pulse width, or other processed signal
quantities.

RosettaX works with these exported measurements. It treats the FCS file as the
experimental input and uses calibration references to convert instrument signal
values into more interpretable calibrated quantities.


Events, signals, and features
*****************************

A flow cytometry event is not a direct measurement of a particle property. It is
the result of several physical and electronic steps:

#. the particle crosses the illuminated interrogation volume
#. light is scattered or emitted
#. part of this light is collected by the optical system
#. the optical power reaches a detector
#. the detector converts optical power into an electrical signal
#. analog and digital electronics process the signal
#. triggering logic decides whether the signal is stored as an event
#. event features are extracted from the time dependent pulse

The values stored in an FCS file are therefore processed observables. They are
not usually raw optical powers.

For calibration, this distinction matters. A calibration relation should be
interpreted as a mapping between a measured instrument observable and a chosen
reference quantity. The exact meaning of this relation depends on the selected
channel, feature type, detector configuration, and calibration model.

For example, a calibration may relate a fluorescence channel to a reference
fluorescence intensity, or it may relate a scattering channel to a modeled
scattering quantity for particles of known optical properties.


Calibration as a mapping problem
********************************

Calibration can be viewed as a mapping between two spaces:

* the instrument measurement space
* the reference or model space

The instrument measurement space is formed by the values measured by the
cytometer. These values may be arbitrary detector units, digitizer counts,
scaled channel values, or transformed quantities depending on the instrument
and export settings.

The reference space is defined by the calibration material or model. In
fluorescence calibration, this may be a known reference intensity. In scattering
calibration, this may be a modeled scattering signal computed from particle
diameter, refractive index, wavelength, collection geometry, and detector
configuration.

The calibration task is to estimate a function

.. math::

   y = f(x)

where ``x`` is the measured signal value and ``y`` is the calibrated reference
quantity.

Depending on the workflow, the relation may also be represented in the opposite
direction,

.. math::

   x = g(y)

where the measured signal is modeled as a function of the reference quantity.

Both views are useful. The first is useful when applying a calibration to
experimental data. The second is useful when fitting expected instrument
responses from known reference populations.


Reference populations
*********************

A calibration reference usually contains several distinguishable populations.
These populations may be beads, particles, or samples with known or modeled
properties.

A good reference population should satisfy several practical conditions:

* it should be measurable above the relevant noise floor
* it should produce a distinguishable peak or mode
* its reference value should be known or computable
* it should span the useful dynamic range of the instrument
* it should be stable enough for repeated measurements
* it should be appropriate for the channel being calibrated

In practice, reference populations are identified from histograms or density
plots. RosettaX provides tools to inspect these distributions and associate
detected peaks with calibration reference values.

The calibration quality depends strongly on the quality of this association.
Incorrect peak assignment, unresolved populations, saturated channels, or
poorly separated peaks can produce misleading calibration fits.


Histograms and peak identification
**********************************

Calibration workflows often begin by inspecting one dimensional or two
dimensional signal distributions.

For a one dimensional channel, a histogram estimates the distribution of event
values. Peaks in the histogram may correspond to reference populations,
background events, unresolved mixtures, or instrument artifacts.

For a two dimensional representation, density plots can reveal whether
populations are well separated, whether a channel contains correlated
structure, or whether a selected peak is actually a projection of several
overlapping populations.

Peak identification is therefore not only a numerical task. It is also a
quality control step.

When selecting calibration peaks, the user should consider:

* whether the population is clearly separated from neighboring populations
* whether the population is above the detection threshold
* whether the peak position is stable under reasonable binning choices
* whether the peak is affected by saturation or clipping
* whether the selected channel and feature type are appropriate
* whether the number of events is sufficient for a stable estimate

RosettaX is designed to make this step inspectable rather than hidden. The user
can review the distribution, identify the relevant peaks, and verify that the
calibration points are physically reasonable before exporting a calibration.


Fluorescence calibration
************************

Fluorescence calibration relates measured fluorescence channel values to a
reference fluorescence scale.

A fluorescence measurement depends on several factors:

* excitation wavelength and optical power
* fluorophore absorption
* fluorophore emission spectrum
* quantum yield
* optical filters
* collection efficiency
* detector responsivity
* electronic gain
* acquisition settings
* background and noise

In many practical calibration workflows, these factors are not modeled
individually. Instead, reference materials with known or assigned fluorescence
values are measured, and a calibration relation is fitted between measured
channel values and reference intensities.

This produces an empirical mapping from instrument units to calibrated
fluorescence units.

The general workflow is:

#. measure a fluorescence reference sample
#. identify the measured peak positions
#. assign each peak to its known reference value
#. fit a calibration relation
#. review the residuals and the usable range
#. export the calibration result

The fitted relation may be linear, log linear, polynomial, or another model
depending on the assumptions of the workflow and the response of the detector
chain.

A simple linear relation has the form

.. math::

   y = a x + b

where ``x`` is the measured channel value, ``y`` is the calibrated reference
value, ``a`` is the gain factor, and ``b`` is the offset.

For many cytometry applications, the useful response may be approximately
linear only over a limited range. Saturation, background subtraction, nonlinear
amplification, compensation, or exported scaling may all affect the apparent
relation.

The fitted calibration should therefore be interpreted within the range covered
by the reference populations. Extrapolation outside the measured calibration
range should be treated carefully.


Scattering calibration
**********************

Scattering calibration relates measured scatter signals to optical scattering
quantities predicted from a physical model.

When a particle is illuminated, it redirects part of the incident optical field.
The angular distribution and total scattered intensity depend on the particle
properties and optical configuration.

Important parameters include:

* particle diameter
* particle refractive index
* surrounding medium refractive index
* illumination wavelength
* incident polarization
* collection angle
* numerical aperture
* detector geometry
* optical throughput
* detector responsivity

For spherical particles, scattering is often modeled using Mie theory. Mie
theory provides an exact solution of Maxwell's equations for a homogeneous
sphere in a homogeneous medium illuminated by a plane wave.

The model produces quantities such as:

* scattering efficiency
* extinction efficiency
* angular scattering amplitudes
* differential scattering intensity
* collected optical power over a detector acceptance region

For cytometry calibration, the relevant quantity is usually not the total
scattered power over all angles. Instead, it is the portion of scattered light
that is collected by the instrument optics and routed to a specific detector.

This means that the optical model must account for the collection geometry.
Forward scatter and side scatter channels do not measure the same angular
region, and they may not respond similarly to particle size or refractive index.


Size parameter and refractive index contrast
********************************************

A central dimensionless quantity in scattering theory is the size parameter,

.. math::

   x = \frac{2 \pi r n_m}{\lambda}

where ``r`` is the particle radius, ``n_m`` is the refractive index of the
surrounding medium, and ``lambda`` is the wavelength in vacuum.

The scattering response depends strongly on the size parameter and on the
relative refractive index,

.. math::

   m = \frac{n_p}{n_m}

where ``n_p`` is the particle refractive index.

Small particles with weak refractive index contrast may scatter very little
light. In the Rayleigh regime, the scattering intensity approximately scales
with the sixth power of particle radius,

.. math::

   I_\mathrm{sca} \propto r^6

This scaling is only an approximation for sufficiently small particles, but it
is useful for intuition. It shows why small changes in particle size can produce
large changes in scattering signal.

For extracellular vesicles, lipoproteins, small beads, and other submicron
particles, this strong size dependence is particularly important. The measured
scatter distribution may be dominated by the largest particles even if smaller
particles are far more numerous.


Angular collection
******************

A flow cytometer does not usually collect all scattered light. Each scatter
channel collects a limited angular range determined by the optical design.

A simplified collected signal can be written as an angular integral,

.. math::

   S = C \int_{\Omega_D} I_\mathrm{sca}(\theta, \phi) \, d\Omega

where ``I_sca`` is the angular scattering intensity, ``Omega_D`` is the
detector collection solid angle, and ``C`` is an instrument dependent
proportionality factor.

This expression emphasizes three important points.

First, the collected signal depends on the detector geometry. A particle may
produce strong scattering at angles that are not collected by a given channel.

Second, the forward and side scatter responses can have different size and
refractive index dependence.

Third, the absolute scaling factor is usually instrument dependent. Unless all
optical throughput, detector responsivity, gain, and processing steps are known,
the measured channel value should be calibrated empirically.


Calibration curves and monotonicity
***********************************

A scattering calibration often requires a relation between a particle property
and a predicted scatter signal. For example, a bead diameter may be mapped to a
predicted collected scattering intensity.

However, scattering curves are not always monotonic. Mie resonances and angular
collection effects can produce oscillations, plateaus, or multiple particle
sizes that yield similar collected signals.

This has important consequences.

If the relation between diameter and signal is not monotonic, then the inverse
problem is ambiguous. A single measured signal may correspond to multiple
possible diameters or optical configurations.

For calibration workflows, RosettaX therefore treats monotonicity as an
important quality criterion. When a model relation is used as a target
calibration curve, the usable branch should be inspected. A calibration based
on a non monotonic region can produce unstable or physically ambiguous results.

In practical terms, the user should verify:

* whether the calibration range is monotonic
* whether the selected reference populations fall on a single branch
* whether the inverse mapping is unique over the intended range
* whether extrapolation would cross a non monotonic region
* whether the channel geometry is appropriate for the target size range


Instrument response
*******************

The optical signal produced by a particle is not the final value stored in an
FCS file.

The measured value is affected by the instrument response, including:

* optical transmission
* filter transmission
* detector responsivity
* analog gain
* electronic bandwidth
* digitization
* baseline processing
* pulse detection
* trigger thresholds
* exported feature definitions

A simplified measurement model can be written as

.. math::

   x_\mathrm{meas} = h(S_\mathrm{optical}) + \epsilon

where ``S_optical`` is the collected optical signal, ``h`` represents the
instrument response, and ``epsilon`` represents noise and residual variability.

In ideal conditions, ``h`` may be approximated as a linear function over a
limited dynamic range. In real instruments, the response may include offsets,
nonlinearities, saturation, filtering, baseline correction, or proprietary
processing.

This is why RosettaX focuses on empirical calibration using measured reference
data. The optical model provides the target reference values, but the measured
instrument response is estimated from experimental data.


Noise and detection limits
**************************

Calibration is most reliable when reference populations are well above the
noise floor and well separated from background.

In low signal regimes, several effects can complicate calibration:

* detector noise
* shot noise
* electronic noise
* background light
* autofluorescence
* coincident particles
* unresolved reference populations
* thresholding bias
* feature extraction variability

The lower limit of detection is especially important for small particle
scattering. Particles that produce signals close to the background may not form
stable peaks, and their measured distributions may be distorted by triggering
and event selection.

If a reference population is only partially detected, the measured peak may not
represent the true population response. It may represent only the high signal
tail that crossed the event threshold.

For this reason, calibration points near the detection limit should be reviewed
carefully. They may be useful for understanding instrument sensitivity, but they
may be unsuitable for fitting a stable calibration relation.


Triggering and selection bias
*****************************

Flow cytometers record events only when the acquisition logic decides that a
signal satisfies the trigger condition. This means the recorded event
population can be biased relative to the particles that passed through the
interrogation region.

A trigger condition may depend on:

* one selected channel
* one selected pulse feature
* a threshold
* hysteresis
* debounce logic
* coincidence behavior
* electronic filtering
* digital processing

If the trigger channel is not the same as the calibration channel, the recorded
events may be selected by one physical observable and calibrated in another.
This can affect the apparent distribution and peak positions.

For example, a sample triggered on side scatter may have a different recorded
population than the same sample triggered on fluorescence or forward scatter.

When interpreting calibration results, it is therefore important to know:

* which channel was used for triggering
* whether the reference populations were fully detected
* whether the selected peaks are affected by thresholding
* whether the same trigger settings were used across measurements
* whether the calibration will be applied to data acquired under compatible
  conditions


Pulse features
**************

A particle crossing the interrogation region produces a time dependent pulse.
The FCS file may contain several features extracted from this pulse.

Common pulse features include:

* height
* area
* width

Pulse height is often related to the maximum signal amplitude. Pulse area is
related to the integrated signal over the event duration. Pulse width is related
to the temporal extent of the event.

These features are not interchangeable. Their relationship depends on particle
velocity, beam shape, signal processing, and event extraction.

For calibration, the selected feature should match the intended interpretation.
A calibration built from pulse height should not be applied blindly to pulse
area unless the relationship between the two is known and stable.

RosettaX therefore keeps calibration workflows organized around explicit
channel and feature choices.


Fitting calibration relations
*****************************

Once measured peak positions and reference values are associated, RosettaX can
fit a calibration relation.

The fitting problem can be written generally as

.. math::

   y_i = f(x_i; \boldsymbol{\theta}) + \epsilon_i

where ``x_i`` are the measured peak positions, ``y_i`` are the reference
values, ``f`` is the calibration model, ``theta`` are the fitted parameters,
and ``epsilon_i`` are residual errors.

The choice of model should reflect the expected instrument response and the
calibration range. A more complex model is not always better. It may fit the
reference points more closely while producing unstable interpolation or
unreasonable extrapolation.

When reviewing a calibration fit, the user should inspect:

* the fitted curve
* the calibration points
* the residuals
* the dynamic range covered by the references
* the behavior near the lower and upper ends of the range
* whether the relation is physically plausible
* whether the model will be used for interpolation or extrapolation

A calibration fit should be considered a model with assumptions, not just a
numerical conversion table.


Interpolation and extrapolation
*******************************

Calibration is most reliable within the range spanned by the reference
populations. Applying a calibration inside this range is interpolation.
Applying it outside this range is extrapolation.

Interpolation can still be affected by model choice, noise, and reference
quality, but it is generally better constrained than extrapolation.

Extrapolation is riskier because the fitted relation is being used outside the
region where it was supported by data. In this case, nonlinear detector
response, saturation, noise floor effects, or non monotonic scattering behavior
can produce large errors.

For this reason, exported calibrations should be interpreted together with
their valid range. Users should avoid applying a calibration to signal values
far outside the reference range unless the extrapolation has been explicitly
validated.


Calibration export
******************

A useful calibration result should be reusable. It should not exist only as a
plot or as values copied manually from one script to another.

RosettaX therefore supports calibration export. The exported calibration should
contain enough information to identify:

* the calibration type
* the fitted parameters
* the reference data used for the fit
* the measured peak positions
* the selected channel and feature
* the model assumptions
* the runtime profile or relevant settings
* the software version when available

The exact contents may evolve with the application, but the goal remains the
same: exported calibrations should be traceable and reusable in downstream
analysis.

A calibration file should be treated as part of the experimental record.


Runtime profiles
****************

Runtime profiles are used to organize repeated calibration settings.

A profile may contain default parameters such as detector names, channel
choices, optical assumptions, reference material settings, or workflow options.
This avoids repeatedly entering the same information and reduces the chance of
copying inconsistent values between calibration sessions.

Profiles are not a substitute for experimental metadata. Instead, they provide a
structured way to keep frequently reused assumptions and application settings
together.

When using profiles, users should ensure that the selected profile corresponds
to the instrument configuration and reference materials used in the actual
measurement.


Local execution and reproducibility
***********************************

RosettaX is designed to run locally. The application serves a graphical
interface from the user's machine and does not require a remote calibration
server.

Local execution has practical advantages:

* FCS files remain on the user's machine
* calibration work can be performed without uploading data
* local files and profiles can be reused across sessions
* the workflow can be integrated into laboratory data management practices

Reproducibility depends on more than local execution. A reproducible calibration
workflow should also preserve:

* input FCS files or their identifiers
* reference material information
* selected peaks
* fitted model type
* fitted parameters
* software version
* runtime profile
* acquisition settings
* relevant instrument metadata

RosettaX is intended to make these elements easier to organize, but users
should still maintain complete experimental records when using calibration
results for scientific reporting.


Limitations
***********

RosettaX does not make calibration automatically correct. It provides a
structured workflow, but the quality of the result still depends on the quality
of the input data, reference materials, model assumptions, and user choices.

Important limitations include:

* FCS data may already contain instrument specific processing
* proprietary instrument internals may be unknown
* reference populations may overlap or be partially detected
* scattering models require assumptions about size, refractive index, and
  collection geometry
* calibration fits may be unreliable outside the reference range
* peak identification may require user review
* low signal populations may be biased by triggering and detection limits
* exported calibration files are only valid under compatible acquisition and
  analysis conditions

These limitations are not specific to RosettaX. They are general features of
calibration workflows in flow cytometry. RosettaX aims to make them more
visible and easier to manage.


Best practices
**************

For reliable calibration workflows, users should follow several practical
guidelines.

Use appropriate reference materials
===================================

The reference material should be suitable for the channel and dynamic range
being calibrated. Reference populations should be detectable, separable, and
matched to the intended measurement regime.

Inspect the data before fitting
===============================

Do not fit a calibration relation blindly. Inspect histograms, density plots,
peak positions, and possible background populations before accepting the
calibration points.

Avoid unsupported extrapolation
===============================

Use calibrations primarily within the range covered by the reference
populations. Treat extrapolated values as uncertain unless the extrapolation has
been validated independently.

Keep acquisition settings consistent
====================================

Calibration is only transferable when the relevant acquisition and processing
conditions are compatible. Changes in detector gain, trigger settings, optical
configuration, filters, or exported feature definitions can invalidate a
calibration.

Review monotonicity for scattering calibration
==============================================

When a scattering model is used, verify that the relevant calibration branch is
monotonic over the intended range. Non monotonic scattering relations can make
inverse calibration ambiguous.

Preserve calibration metadata
=============================

Save the calibration file, runtime profile, reference material information, FCS
file identifiers, acquisition settings, and software version whenever possible.
These elements are necessary for later interpretation.


Summary
*******

RosettaX treats calibration as a structured mapping between measured flow
cytometry signals and reference or model based quantities.

For fluorescence workflows, this mapping is usually empirical and based on
reference intensity populations. For scattering workflows, the mapping connects
measured scatter signals with optical models that depend on particle size,
refractive index, wavelength, and collection geometry.

In both cases, the calibration result is only meaningful when the reference
populations, measured peaks, fitted relation, acquisition settings, and model
assumptions remain traceable.

RosettaX is designed to make this calibration chain explicit, inspectable, and
reusable.