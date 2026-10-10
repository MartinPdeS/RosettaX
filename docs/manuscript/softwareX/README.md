# RosettaX SoftwareX manuscript

This source package is a short draft for a SoftwareX Original Software
Publication. It uses Elsevier's single-column `elsarticle` format, line
numbers, software metadata tables, and a separate highlights file.

Build from this directory:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error rosettax.tex
```

The article uses no generated figures, so it can be compiled from a clean
checkout with a standard LaTeX installation that provides `elsarticle`. Build
products are excluded through the repository-level `.gitignore`.

Review [`SUBMISSION_CHECKLIST.md`](SUBMISSION_CHECKLIST.md) before submitting.
