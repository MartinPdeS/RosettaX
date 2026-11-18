Interface guide
===============

RosettaX keeps its workflows separated by page so calibration building and
calibration reuse remain easy to reason about.


Application map
---------------

Home
    Entry page with workflow selection, project links, and high-level context.

Fluorescence
    Build fluorescence calibrations from bead populations and known reference values.

Scattering
    Build scattering calibrations from measured peaks and optical-model assumptions.

Apply calibration
    Apply a saved calibration to one or more FCS files and export calibrated artifacts.

Settings
    Manage runtime profile behavior and defaults.

Documentation
    In-app under-the-hood reference for model assumptions, regression logic,
    calibration file structure, and apply guardrails.

Help
    Compact support page focused on getting started, troubleshooting, and
    diagnostics.


How to read the interface
-------------------------

Most RosettaX pages follow the same pattern:

* an upload or selection surface
* a preview surface such as a graph or calibration table
* a fit or compute action
* a save or export surface

Treat this as a review pipeline rather than a sequence of buttons. If a graph,
table, or parameter block looks wrong, stop there and correct it before moving
forward.


Saved outputs
-------------

RosettaX produces two documentation-grade outputs:

* a saved calibration JSON that preserves the calibration relation and metadata
* a PDF apply report that summarizes one successful apply-export run

Those outputs are related but not interchangeable. The JSON is the reusable
calibration record. The PDF is the run summary.
