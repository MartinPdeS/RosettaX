# RosettaX colleague presentation plan

## Purpose

Prepare a 25–28 minute presentation for laboratory colleagues who work with flow-cytometry data and already understand the mathematics behind calibration. Give them a short refresher, then focus on how RosettaX turns those methods into a practical, inspectable workflow: which data and choices enter, what the app shows for review, and what is preserved for reuse.

## Audience takeaways

By the end, colleagues should be able to:

1. See how familiar calibration mathematics maps to RosettaX inputs, fit views, and saved results.
2. Follow the path from an FCS file and reference data to a calibration they can inspect and reuse.
3. Recognize which choices RosettaX exposes, which assumptions it carries through, and what they should review before comparing results.
4. Find the sample files and cross-device examples they can use to explore the workflows.

## Main narrative

The audience knows why calibration works mathematically. The talk connects that knowledge to the practical questions RosettaX helps answer: what data was loaded, which channel and peak procedure were used, how reference values were paired with observed signals, what the fit looks like, and what context travels with the saved calibration. Fluorescence and scattering share a visible path through the app, while scattering also asks the user to configure and review an optical model.

## Visual approach

Make the presentation figure-led. Each slide should have one visual that carries its main point, with only short labels or a brief takeaway beside it. Prefer figures made from RosettaX screenshots and real workflow outputs so colleagues can connect the explanation to the software they will use.

- Use a consistent visual language: blue for fluorescence, amber for scattering, and neutral gray for shared tools and workflow steps.
- Build simple editable Keynote diagrams for process and data flow. Use screenshots for the actual interface, and crop or annotate them only to direct attention to the relevant control or result.
- Use real RosettaX plots for calibration and model examples. Label axes, units, and the meaning of points and curves; remove unrelated interface clutter.
- Keep text inside diagrams to short labels. Put explanations in presenter notes rather than packing paragraphs into figures.
- Include source or sample-file details in a small caption when a figure shows experimental data. Distinguish measured examples from conceptual schemas.

### Planned figures and schemas

| Slide | Visual to build or capture | What it should make clear |
|---|---|---|
| 1 | RosettaX interface hero image or a composed screenshot strip | The talk is about the working application and its calibration workflows. |
| 2 | Calibration relationship figure using one real fluorescence fit plot | How known reference values and measured bead signals meet in the fit shown by RosettaX. |
| 3 | Context map: FCS file + channel and peak choices + reference or model settings → reviewed fit + saved calibration | The fit is one part of a result whose inputs and assumptions matter. |
| 4 | RosettaX workflow schematic: load → inspect → identify peaks → fit → save → apply | The shared workflow structure, with fluorescence and scattering marked as two paths through it. |
| 5 | Annotated sequence of 3–4 fluorescence page screenshots | Where users select data, inspect peaks, pair standards, review the fit, and save. |
| 6 | Fit plot with a compact “review these” callout layer | What the user can inspect before accepting or comparing a result. |
| 7 | Calibration JSON → select calibration → apply to new FCS → calibrated output schematic, paired with one app screenshot | How a saved calibration is carried into downstream analysis. |
| 8 | RosettaX tools map: Inspector, Slicing, Merge, Visualization, Cross calibration, linked to the calibration workflow | How the supporting tools help prepare, inspect, or transfer data around calibration. Use small screenshots or simple icons rather than feature descriptions in text. |
| 9 | Scattering model schema: standard particles and optical assumptions → modeled relation → measured channel fit | Where the optical model enters the software workflow and what the displayed curve represents. |
| 10 | Instrument comparison matrix or small-multiples plot for the available Rosetta bead examples | Which instruments/files are currently represented and which comparisons remain part of the validation effort. Label available versus planned coverage clearly. |
| 11 | One-page result review checklist arranged around a fit screenshot | The concrete checks users should make in RosettaX before reuse or comparison. |
| 12 | Simple “start here” path with links or page names for sample files and tools | How colleagues can continue hands-on after the talk. |

## Timing and slide outline

Target **23 minutes of presentation plus 3–5 minutes for questions**. Keep the main deck to 12 slides and the complete presentation to **15 slides maximum**, including any optional or expanded content. Put detailed scientific and technical material in speaker notes or backup material outside the presented deck.

| # | Slide | Time | Content and visual |
|---|---|---:|---|
| 1 | **RosettaX: making calibration workflows inspectable** | 1 min | Title, presenter, lab, and one sentence on the goal. Use a clean application screenshot as the background or side image. |
| 2 | **The calibration math, in one picture** | 2 min | A quick refresher using a RosettaX fit plot: known reference values paired with measured bead signals produce a fitted relationship. Keep equations to one small annotation; focus on what appears as data points, axes, and fit in the app. |
| 3 | **What RosettaX adds around the fit** | 2 min | Show the context needed to interpret it: source FCS data, channel, peak procedure, reference table, and instrument or model settings. Emphasize traceable choices, not a new mathematical method. |
| 4 | **The RosettaX workflow at a glance** | 1 min | Trace load → inspect → identify peaks → fit → save → apply. Show where users make decisions and where RosettaX presents information for review. |
| 5 | **Fluorescence: follow one calibration through the app** | 3.5 min | Walk through loading an FCS file, selecting a channel and peak procedure, reviewing detected peaks, pairing them with ABC/ERF/MESF reference values, inspecting the fit, and saving. Use focused screenshots. |
| 6 | **Reviewing the result before reuse** | 1.5 min | Use the fit plot and diagnostics to show what a user can check. Explain that fit quality does not establish comparability by itself; channel, gain regime, and reference bead family remain part of the context. |
| 7 | **From saved calibration to applied values** | 1.5 min | Show how RosettaX uses a saved calibration with new FCS data and what context the calibration JSON preserves for review and reuse. |
| 8 | **More than calibration: tools around the workflow** | 3 min | Give a quick guided tour of the FCS Inspector (review metadata before analysis), Slicing (select channels and export smaller files), FCS Merge (combine compatible files), FCS Visualization (explore measurements), and Cross calibration (transfer a reference to routine beads). Frame them as practical utilities around the calibration process. |
| 9 | **Scattering: where the app asks for more context** | 2.5 min | Show how wavelength, particle model and refractive indices, detector geometry, and the standard table enter the workflow. Connect these controls to the modeled relation and calibration result. |
| 10 | **Cross-device validation with Rosetta beads** | 2 min | Show the current Apogee and Northern Lights examples and the goal of covering four flow cytometers. Explain how shared bead material and downloadable files let colleagues examine the workflow across devices; do not present the collection as proof of interchangeability. |
| 11 | **What to check when interpreting a RosettaX result** | 1.5 min | Walk through practical review questions: are the right channel and peaks selected, do references match, is the fit range useful, and for scattering are geometry and particle assumptions appropriate? |
| 12 | **Try the workflows and shape the next steps** | 1.5 min | Point colleagues to the sample files and validation examples. Ask which instrument, dataset, or workflow they would like to explore next. |

**Talk time: 23 minutes.** Allow another 3–5 minutes for questions and discussion.

## Demo or GIF plan

- Use the fluorescence calibration as the main practical walkthrough. Narrate the choices and checks visible in the app: upload, select channel and peak procedure, review peaks, pair reference values, inspect the fit, save.
- Use the actual RosettaX interface and a packaged sample FCS file. Put the filename and reference preset on the slide so colleagues can repeat the example.
- If using a live demo, keep a prepared screenshot sequence or GIF as a fallback. Avoid relying on a long file upload or live model calculation to hold the presentation together.
- For scattering, use a clear diagram and one saved result; reserve a full live run for questions if time allows.
- Show the supporting tools as a fast app tour, with one sentence and a screenshot for each. Avoid a full demonstration of every utility; invite colleagues to choose one for a follow-up.

## Slide design

- Use a 16:9 Keynote layout with RosettaX branding and a restrained palette based on the existing app colors.
- Give each slide one point and one main figure or schema. Prefer application screenshots, workflow diagrams, calibration plots, and short labels over paragraphs.
- Keep fluorescence and scattering visually distinct throughout the deck.
- Use the same small progress marker for the shared workflow: **load → inspect → fit → save → apply**.
- Keep the math refresher to one fit plot and one concise relationship. Put equations, detailed parameter lists, and extra screenshots in backup slides.
- Draw process diagrams as editable Keynote shapes so they can be revised as the software changes. Keep scientific plots as clean exports from RosettaX where possible.

## Backup slides to prepare

1. Fluorescence fit details and reference-unit definitions.
2. Scattering model assumptions and detector geometry terms.
3. Calibration JSON fields and provenance.
4. Current sample-file inventory and instrument acquisition details.
5. Common failure checks: channel selection, peak selection, reference mismatch, and optical-model mismatch.
6. Expanded tool tour with a screenshot of each supporting utility.

## Claims to keep precise

- Describe the Apogee and Northern Lights files as current cross-device examples; describe four instruments as the intended validation scope.
- Present detector presets as documented, reproducible starting configurations that still need checking against the instrument and standards in use.
- Do not imply that a high fit score alone establishes scientific equivalence between calibrations.
- Distinguish the software's workflow support from independent validation of any particular instrument or dataset.

## Proposed deck file

Create the Keynote deck as `presentation/RosettaX_colleague_overview.key`. Use this outline as the structure, then add presenter notes and the final GIFs or screenshots when they are ready.
