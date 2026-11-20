# RosettaX presenter notes

## 1. RosettaX

Hi everyone. Today I want to show you RosettaX and what you can do with it. The idea is to go through the calibration workflows, look at some of the other tools, and then talk a bit about how we can validate the results across instruments.

## 2. Introduction

I'll start with a quick introduction to the app and the general idea behind calibration. Then we'll look at the workflows in a bit more detail.

## 3. What is RosettaX?

RosettaX was designed around six goals: broad calibration across fluorescence, scattering, and cross-calibration; open-source tools; an intuitive and flexible workflow; fast progress from data to results; online and local use; and reproducible analysis through saved, reusable fits.

It is the open-source successor to Rosetta and can be used at rosettax.vesiclecenter.com or run locally.

## 4. The idea behind calibration

This is a real RosettaX fit from a Cytek Aurora B2-A Rainbow bead sample. Each point pairs a measured bead peak with its known MESF reference. RosettaX fits a power law in log-log space. In this example, six bead populations give R² = 0.99807. The saved relationship can then transform new B2-A measurements into MESF units.

## 5. From data to calibrated results

This is the overall workflow: load and inspect the data, identify the bead populations, fit the calibration, and then save and apply it. The same broad steps work for fluorescence and scattering.

## 6. Fluorescence calibration

Let's start with fluorescence, using one calibration to see how the workflow fits together.

## 7. Follow one calibration

Here we load the bead FCS file, choose the detector channel, and identify the populations. We then pair the peaks with the reference values for those beads and fit the calibration. The important thing is to check that the selected peaks and values match.

## 8. Review the fit

Once we have the fit, there are three things I check before using it. Do the beads cover the range of the samples? Are the deviations small and free of a clear pattern? And do the channel and reference values match the measurement? This plot is schematic.

## 9. Apply the calibration

Once we're happy with the calibration, we load the new FCS data, check that the detector channel matches, and apply the saved result. The calibration keeps the fit and its context, including the reference choices.

After applying and exporting, we can also generate a PDF report with calibration details relevant to MIFlowCyt-EV reporting.

## 10. Scattering calibration

For scattering, we follow the same broad steps, but there are a few more things we need to specify before we can calculate the reference response.

## 11. Model the scattering response

The scattering response depends on the particles and the optical setup. So we enter the wavelength and medium, the bead sizes and material, the refractive indices, and the detector geometry.

RosettaX uses those inputs in a scattering model to predict the light collected from each reference population. We then relate the measured bead peaks to those predictions and fit the calibration. It's important to review the assumptions as well as the fit, because changing them can change the predicted response.

## 12. Tools and validation

Besides the calibration workflows, there are a few tools to help prepare and explore the data. And then I'll show the validation process we're planning across instruments.

## 13. Supporting tools

The FCS Inspector lets us check channels and acquisition metadata. Slicing lets us export selected channels while keeping all the events, and FCS Merge combines compatible acquisitions.

There's also a visualization tool for looking at distributions and relationships between channels. Cross calibration is intended to transfer a calibration from primary reference beads to routine beads. That workflow is still experimental and under development.

## 14. Cross-device validation plan

On each instrument, the validation uses two bead sets. Rosetta beads establish the calibration. Independent monodisperse reference beads provide a known diameter for evaluation.

Fit the Rosetta bead peaks, apply that calibration to the reference bead measurement, and compare the recovered diameter with the known diameter. The slide lists all ten instruments in the validation plan.

For each instrument, record the expected and recovered diameters, uncertainty where available, and agreement criteria defined before assessing the result.

## 15. Conclusion and discussion

We've seen how to make and apply a calibration, and how we can check it across instruments. To finish, I'd like to hear what would be most useful for you to try or validate next.

## 16. Try RosettaX

If you want to try it, a good place to start is one of the packaged sample FCS files. You can follow a calibration from the beginning and see where the choices come up.

I'd also be interested in your feedback on the available bead examples and on which instruments or workflows we should validate next. So, that's where I'll stop. What questions do you have?
