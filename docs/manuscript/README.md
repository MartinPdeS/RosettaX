# RosettaX manuscript

This directory contains a concise SoftwareX-style Original Software Publication
draft for RosettaX. It follows the same submission-oriented layout as the
PackLab manuscript while describing RosettaX's independent flow-cytometry
calibration workflows.

The draft intentionally does not report performance or scientific-validation
claims that have not been independently established. Before submission,
complete the author, release, and validation items in
[`softwareX/SUBMISSION_CHECKLIST.md`](softwareX/SUBMISSION_CHECKLIST.md).

Build the article locally:

```bash
cd docs/manuscript/softwareX
latexmk -pdf -interaction=nonstopmode -halt-on-error rosettax.tex
```
