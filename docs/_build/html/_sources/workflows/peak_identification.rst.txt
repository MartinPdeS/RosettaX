Peak identification scripts
===========================

Before a calibration fit can be run, every calibration-standard population
needs a measured scatter (or fluorescence) peak position assigned to it in the
calibration-standard table. RosettaX provides several peak-identification
scripts that place those values automatically or let you click them manually.

The active script is selected from the *Peak identification method* dropdown
above the graph. All scripts write their results into the same
*Measured peak position* column, so you can switch between scripts or
finish with manual corrections without redoing the rest of the workflow.


Manual 1D
---------

**Graph type**: 1D histogram. **Input channels**: primary.

Click anywhere on the 1D histogram to record that x-position as a peak. Each
click appends one value. Suitable when populations are well separated and you
prefer explicit control over which peak corresponds to which standard row.

Use this when automatic methods produce spurious detections on noisy or
unusual data.


Manual 2D
---------

**Graph type**: 2D scatter. **Input channels**: primary, secondary (typically
scattering vs. fluorescence).

Click anywhere on the 2D scatter plot to record the x-position of that point.
The y-axis value is used only for display; only the x-value enters the table.
Useful when 1D histograms show heavy overlap but populations are visually
separable in 2D.


Automatic 1D
------------

**Graph type**: 1D histogram. **Input channels**: primary.

Detects up to *N* peaks automatically in a single detector channel.
The algorithm:

1. Builds a log-binned histogram of the raw events.
2. Smooths the histogram with a Gaussian-shaped kernel.
3. Finds local maxima and scores each by prominence (peak height above the
   surrounding valley floor).
4. Selects the *N* highest-prominence, sufficiently separated peaks.
5. Maps each selected histogram bin center back to the original intensity scale.

Use this for fluorescence calibration or any scattering dataset where a single
channel captures all populations cleanly.


Prominence 1D
-------------

**Graph type**: 1D histogram. **Input channels**: primary, with an optional
fluorescence gate.

An extended version of Automatic 1D that supports gating a subset of events
before running peak detection. Prominence is estimated from the smoothed
histogram using left- and right-valley minima, providing better separation of
closely spaced peaks compared to simple height thresholding.

Use this when populations partly overlap in the primary channel and a
fluorescence gate can isolate the sub-population of interest.


Prominence 2D
-------------

**Graph type**: 2D scatter. **Input channels**: primary, secondary.

Applies a 2D density peak-detection method. The algorithm projects events into
a 2D histogram, smooths it, and then identifies density maxima by prominence
in two dimensions. Returns the x-position of each detected cluster centroid.

Use this for bead mixtures where scatter and fluorescence together disambiguate
populations that would overlap in 1D.


Gated K-means 1D
----------------

**Graph type**: 1D histogram. **Input channels**: primary, with an optional
fluorescence or scatter gate.

Runs K-means clustering on the 1D event values, where *K* equals the number
of peaks requested. Events can optionally be filtered by a fluorescence or
scatter gate before clustering. Returns the cluster centroid of each group as
the peak position.

Use this when peaks are well separated but histogram prominence varies
significantly across populations, making prominence-based methods inconsistent.


Gated K-means 2D
----------------

**Graph type**: 2D scatter. **Input channels**: primary, secondary.

Runs K-means clustering directly in 2D scatter-fluorescence space. Each
cluster centroid contributes its x-coordinate as a peak position. Colour-coded
cluster membership is shown on the graph.

Use this when 2D structure is the most reliable discriminator and you want an
explicit cluster assignment rather than a density maximum.


Rosetta
-------

**Graph type**: 2D scatter. **Input channels**: scattering, green fluorescence.

Purpose-built for the Exometry Rosetta bead mixture (CAL003 and later).
The algorithm follows the MATLAB-described approach from the Exometry method:

1. **Fluorescence peak finding.** Find, fit, and validate all fluorescence
   peaks in 1D using log-binned histograms, per-peak Gaussian fits, and
   quality checks (R², CV, minimum event count, saturation guard).
2. **Baseline identification.** The highest-count validated fluorescence peak
   is treated as the baseline noise population, which corresponds to the
   non-fluorescent beads leaking into the green-fluorescence channel.
3. **Marker classification.** The remaining one or two fluorescence peaks are
   the fluorescent marker beads (140 nm and 380 nm in CAL003). When only one
   marker is found, the saturation state of the fluorescence detector
   determines whether it is the dim or the bright marker. When two are found,
   the lower-intensity peak is labeled *Dim marker* and the higher is labeled
   *Bright marker*.
4. **Marker scatter peaks.** For each marker peak, events are gated by a
   symmetric sigma window around the fluorescence fit mean, and the scatter
   distribution of those gated events is fitted to find the marker scatter
   position.
5. **Non-fluorescent gate.** Events with fluorescence below the baseline mean
   plus *baseline gate width* × σ are selected. This gate removes all
   fluorescent marker beads from the scatter analysis.
6. **Non-fluorescent scatter peaks.** The gated scatter distribution is
   submitted to the same find-fit-validate pipeline used for fluorescence.
   Validated peaks are inserted into the calibration-standard table.

The script stops with an informative status message if:

* no fluorescence peaks can be validated,
* no marker peaks are found after removing the baseline,
* more than two marker peaks are detected (ambiguous mixture state), or
* no scatter peaks survive validation in the non-fluorescent gate.

**Settings exposed in the UI:**

.. list-table::
   :header-rows: 1
   :widths: 30 10 60

   * - Setting
     - Default
     - Effect
   * - Maximum scatter peaks
     - 8
     - Upper bound on the number of non-fluorescent bead populations to return.
   * - Minimum fit R²
     - 0.80
     - Minimum Gaussian fit quality for a peak to be accepted. Applies to both
       fluorescence and scatter fits. Lower values accept noisier peaks.
   * - Baseline gate width (σ)
     - 2.0
     - Non-fluorescent events are those with fluorescence ≤ baseline mean +
       this multiplier × baseline σ. Increasing this value widens the
       non-fluorescent gate and may include dim marker events; decreasing it
       tightens the gate at the risk of excluding small beads near the baseline.

The workflow does not use marker positions to anchor bead-to-diameter
assignments directly. That assignment is determined by the calibration-standard
table preset (e.g. *Rosetta Mix*) in the scattering model section.
