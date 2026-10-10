# RosettaX SoftwareX submission checklist

This concise draft follows the SoftwareX Original Software Publication
structure. Confirm the current journal requirements immediately before
submission.

## Included in the draft

- [x] Descriptive software title, short abstract, and six keywords.
- [x] Single-column `elsarticle` layout with line numbers.
- [x] Code and executable-software metadata tables.
- [x] Motivation, software description, illustrative workflow, impact, and
  conclusions sections.
- [x] Data-availability and generative-AI disclosure statements.
- [x] Separate highlights file.
- [x] References to the tagged source, documentation, and Zenodo record.

## Requires author confirmation

- [ ] Confirm the corresponding author, institutional postal address, and email.
- [ ] Confirm all author names, affiliations, and CRediT roles.
- [ ] Confirm funding and competing-interest declarations.
- [ ] Confirm that v0.9.0 is the release evaluated in the manuscript, or update
  every version-specific link and metadata row together.
- [ ] Confirm that Zenodo DOI `10.5281/zenodo.19846629` resolves to the submitted
  release, or make a version-specific archive.
- [ ] Confirm the PyMieSim version and citation appropriate to the submitted
  RosettaX release.
- [ ] Add validation results or a worked example only after the underlying
  inputs, expected outputs, and interpretation have been independently reviewed.
- [ ] Confirm the generative-AI disclosure accurately reflects author use and
  oversight.

## Final packaging checks

- [ ] Keep the main text within the journal's current word limit.
- [ ] Build from a clean checkout with `latexmk -pdf rosettax.tex`.
- [ ] Verify every URL, DOI, email address, software version, and license.
- [ ] Inspect the PDF at final size and upload the LaTeX source package and
  `highlights.txt` as required.
