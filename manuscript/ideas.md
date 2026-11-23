# RosettaX manuscript ideas

Working outline for an Original Article in *Extracellular Vesicles and Circulating Nucleic Acids* (EVCNA).

## Central question

Can a reproducible calibration workflow improve agreement between flow cytometers measuring the same extracellular vesicle (EV) reference sample, and under what conditions does the calibration remain reliable?

The proposed contribution is an open-source workflow that connects FCS data, bead peak assignments, fluorescence calibration, and detector geometry used for scatter modeling. Show what this makes possible for EV measurements. A calibration can put signals on a common scale within a shared measurement range. It does not establish particle identity or make different instruments equally sensitive.

## Claims to support

| Proposed claim | Evidence or analysis needed |
|---|---|
| RosettaX can process bead recordings from diverse cytometers. | The repository has validation recordings from 14 cytometer models. Report outcome counts per recording and model, including complete and partial results and runs that stop. Repository regression expectations describe current behavior; they are not independent bead labels. |
| The bead assignments are reliable where RosettaX assigns a diameter. | Establish reference identities independently of RosettaX. Report correct, incorrect, and unassigned peaks separately. Include merged or missing markers, clipping, and incomplete scatter ladders. Quantify errors in measured peak positions as well as size labels. |
| The resulting calibration predicts measurements outside the fitted standards. | Hold out standards or use an independent reference acquisition. Compare predicted and observed values with residuals, bias, and uncertainty. Report fitted-point agreement separately. |
| Calibration improves agreement between instruments for EV measurements. | Use the same EV reference material or matched aliquots acquired on multiple instruments. Compare raw and calibrated signals over a shared measurable range. Report bias and agreement across replicates, and retain exclusions. Confirm dataset availability before making this the central result. |
| Scatter-based size estimates depend on optical assumptions. | Report detector geometry, wavelength, and the assumed particle and medium refractive indices. Show how plausible parameter changes affect inferred size. Distinguish measured scatter from modeled diameter. |

## Methods to describe

- Record instrument and channel identities, acquisition settings, bead material and lot, nominal reference values, and event filtering. Record whether optical geometry came from a preset, a measurement, or a modeling assumption.
- Describe the Rosetta bead workflow from fluorescence marker detection through scatter peak fitting and size assignment. Explain what happens with a lone bright marker, why some regions stay unsized, and which events are excluded. Use the release evaluated in the manuscript as the source for the exact rules.
- Explain the fluorescence reference scale and report units such as MESF only when supported by the standards used. Describe how scatter coupling is calculated, fitted, and applied.
- Define the comparison unit before analysis. Summarize measurements by recording, acquisition, or instrument as appropriate. Individual events within one FCS file are not independent instrument replicates.
- Record the RosettaX commit or release, PyMieSim version, input manifests, runtime profiles, and geometry definitions. Provide scripts that regenerate the tables and figures from shareable inputs.

## Candidate figures and tables

1. **Workflow and example.** Follow one recording from detector channel selection through fitted peaks, calibration, and application to an EV dataset.
2. **Bead assignment across instruments.** Summarize correctness and coverage with counts and denominators. Include one informative failure, such as an unresolved dim marker, alongside a complete fit.
3. **Calibration accuracy.** Plot held-out reference measurements and residuals. Include fluorescence and scatter panels if both have independent reference data.
4. **EV comparison.** Show the same EV material on multiple instruments before and after calibration. Indicate the shared measurable range and quantify between-instrument agreement.
5. **Supplementary validation table.** List files, instruments, channels, reference standards, geometry sources, outcomes, and exclusions. Put sensitivity analyses and reproducibility commands in the supplement.

## Decisions for the team

- **Inventory the EV data first.** Identify paired or replicated acquisitions, the reference material, available controls, and permission to redistribute the FCS data. If there are no suitable paired measurements, narrow the claim to calibration performance on reference particles and describe the EV application as a demonstration if supported.
- **Choose a small pilot.** Start with two instruments that share a reference acquisition and have independently interpretable bead standards. Include one complete Rosetta result and one partial or stopped run. Freeze the assignment reference and agreement metrics before looking at the comparison.
- **Review the pilot before scaling.** Proceed to a cross-instrument agreement claim only if the measurements overlap in a usable range and independent reference checks support the calibrations. Otherwise, report the specific constraint and revise the manuscript question.
- **Separate the EVCNA and SoftwareX drafts.** Use the EVCNA paper to answer a measurement question. Coordinate any overlapping descriptions, data, and figures with the team before submission.

## Journal framing and reading

- [EVCNA aims and scope](https://cname.oaepublish.com/evcna/aims_and_scope)
- [EVCNA author instructions](https://www.oaepublish.com/evcna/author_instructions)
- [Cross-platform characterization of nanoparticles and fluorescent EVs](https://cname.oaepublish.com/articles/evcna.2026.33)
- [Rigor and reproducibility in single-vesicle analysis](https://www.oaepublish.com/articles/evcna.2022.28)
