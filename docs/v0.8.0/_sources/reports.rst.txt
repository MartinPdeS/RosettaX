Reports and export provenance
=============================

RosettaX now treats the PDF report as part of the export artifact rather than a
separate convenience feature. The report is generated from the apply workflow
and records what happened during that specific export run.


What the PDF is for
-------------------

The report answers a different question than the saved calibration JSON.

The JSON answers: what calibration relation was saved?

The PDF answers: what happened when that calibration was applied to this set of
files?


What is included in the report
------------------------------

The apply report can include:

* the selected calibration name and calibration type
* uploaded source file names
* output channels and extra exported columns
* warnings emitted during apply
* selected metadata copied from the saved calibration payload
* tables that summarize calibration context and apply choices
* plots or thumbnails from the calibration/apply result when available

This makes the PDF a provenance surface, not just a screenshot replacement.


How ZIP exports are handled
---------------------------

When RosettaX exports multiple calibrated FCS files as a ZIP bundle, the PDF is
embedded into that ZIP alongside the calibrated files. This keeps the report and
the generated artifacts together.

That bundling matters because apply warnings, selected output columns, and the
identity of the calibration are all part of the interpretation of the export.


How to read the JSON and PDF together
-------------------------------------

Use the calibration JSON when you need to inspect the underlying fitted model.

Use the PDF when you need to audit one export run or understand what was
produced for a collaborator.

If the JSON and PDF tell inconsistent stories, treat that as a documentation
problem and review the calibration before relying on the export.
