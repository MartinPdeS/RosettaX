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
* a calibration evidence summary with recorded peak counts, measured reference
  ranges, and saved R-squared values
* selected metadata copied from the saved calibration payload
* tables that summarize calibration context and apply choices
* plots or thumbnails from the calibration/apply result when available

This makes the PDF a provenance surface, not just a screenshot replacement.

Warnings appear before the run details. A completed export does not establish
scientific acceptance: the evidence summary describes the saved fit without
inferring validity or output uncertainty. Scattering charts show the fitted
instrument response when expected coupling values are recorded; otherwise they
show standard observations without a fitted line.

Changing saved calibration contents or an individual target model invalidates
the previous report in the apply workflow.


Generate an example
-------------------

From an installed repository checkout, generate a synthetic fluorescence report:

.. code-block:: console

   python tools/generate_example_report.py --output example_report.pdf

The example uses the production PDF composer and is explicitly labelled as
synthetic. It includes a fitted calibration chart, reference table, evidence
summary, and export context; no experimental FCS files are processed.


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
