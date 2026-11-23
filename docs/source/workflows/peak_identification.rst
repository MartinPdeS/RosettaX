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
   the fluorescent marker beads (140 nm and 380 nm in CAL003). When two are
   found, the lower-intensity peak is labeled *Dim marker* and the higher is
   labeled *Bright marker*. A lone usable marker can still guide inspection of
   measured scatter peaks. If no fluorescence candidate passes the initial fit,
   Rosetta can retry above a wide, sparsely populated gap. The brighter band
   must still pass the usual marker fit checks.
4. **Marker scatter peaks.** For each marker peak, events are gated by a
   symmetric sigma window around the fluorescence fit mean, and the scatter
   distribution of those gated events is fitted to find the marker scatter
   position. If fluorescence clips above the dim marker gate, Rosetta can use
   a dominant, validated scatter population at the fluorescence ceiling to
   recover the bright anchor.
5. **Non-fluorescent gate.** The default Rosetta mode requires a low-density
   valley between the baseline and first fluorescent band. It checks that
   the valley persists across histogram resolutions and two event subsets,
   and checks for a bridge of events within scatter regions. The cutoff is
   chosen inside the shared valley. The older Rosetta modes use the fitted
   baseline and the *baseline gate width* setting.
6. **Non-fluorescent scatter peaks.** Rosetta fits the gated scatter distribution
   with a mixture model in log intensity. When both markers provide usable
   scatter positions, Rosetta fits three regions independently: below the
   140 nm marker, between the markers, and above the 380 nm marker. Each fit
   includes a small margin at the marker boundaries to account for nearby peak
   tails. With one usable scatter anchor, Rosetta fits the full gated
   distribution. It checks that moving the fluorescence cutoff within the
   valley does not materially change the relevant scatter peaks. With a
   single fluorescence marker and one usable scatter anchor, this check
   compares only peaks above that anchor. **Detect peaks** updates the
   calibration table after the detection checks pass. The lowest detected
   non-fluorescent peak is excluded from the table because acquisition limits
   and overlapping populations can distort it.

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
     - 10
     - Upper bound on the number of non-fluorescent bead populations to return.
   * - Marker fit strictness
     - 0.5
     - Controls the minimum Gaussian fit R² and maximum coefficient of variation
       (CV) for fluorescence peaks. At 0 the limits are R² ≥ 0.35 and CV ≤ 1.50.
       At 0.5 they are R² ≥ 0.70 and CV ≤ 0.60. At 1 they are R² ≥ 0.95
       and CV ≤ 0.30. Scatter and calibration checks are independent of this setting.

Changing Marker fit strictness previews the peak graph. Select **Detect peaks**
to apply the current settings to the calibration table. The Rosetta result
above the graph shows the sized rows, excluded peaks, and event count. Open
**Fit details** to inspect the accepted fits and the reasons candidates were
rejected.

When you replace the FCS file or change the Rosetta detector channels, run
**Detect peaks** again to measure peak positions for the new selection.

With two usable scatter anchors, Rosetta assigns diameters in scatter order
within each region. Each region must contain exactly the expected number of
validated peaks:

* Below 140 nm: 70, 100, and 125 nm.
* Between the markers: 147, 203, and 296 nm.
* Above 380 nm: 400, 600, 799, and 994 nm.

If a region has missing or extra peaks, its diameters are left blank and
Rosetta reports a warning. Other regions can still supply sizes. A fluorescent
marker isolated at the scatter floor or ceiling can supply an ordering
boundary. Its clipped scatter value is excluded from calibration.

If the dim marker is unresolved, Rosetta can assign 400, 600, 799, and
994 nm when the bright anchor is usable and exactly four validated scatter
peaks lie above it. If only one fluorescent band is found, Rosetta treats its usable scatter
anchor as the 380 nm marker. Rosetta warns that the dim marker was unresolved
and omits the smaller sizes from calibration. If the fallback conditions are
unmet, diameters stay blank. A complete peak count supports the assignment
but cannot identify a missing standard replaced by an unrelated peak.

Detector geometry is configured after peak detection and is used for coupling.

Overlapping or reversed fluorescent candidates are shown with their measured
scatter positions. A gate is retained as a sizing candidate only if it has
substantially stronger scatter support and is separated from the other gate.
The peak table can keep the measured positions while marker identity is
unresolved.

Select **Compute model** to calculate the expected coupling for the diameters
in the table. **Create calibration** uses the diameters currently in the table.

Purple dotted guides identify fluorescent markers. Teal dashed guides identify
non-fluorescent peaks. The angled size labels sit above their guides. The legend
below the axes identifies the fluorescence baseline gate and saturation cutoff.

For the Rosetta scripts, *Auto-select detectors* uses the instrument's scatter
and green fluorescence recommendations in
``RosettaX/assets/instrument_catalog.toml``. A recommendation must
match a column in the uploaded FCS file. If the instrument is unknown, a
recommendation is unset, or its column is missing, select the channel manually.
Any valid existing selection for that role is retained.
