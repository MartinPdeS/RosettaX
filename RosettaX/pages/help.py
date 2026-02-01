import dash
from dash import dcc, html
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/help", name="Help")

layout = dbc.Container(
    [
        html.H1("Help"),
        html.P(
            "This page explains the full workflow for building and applying a fluorescent calibration from a bead FCS file."
        ),
        html.Hr(),

        dbc.Accordion(
            [
                dbc.AccordionItem(
                    [
                        html.H4("What this tool does"),
                        html.Ul(
                            [
                                html.Li("Loads a bead FCS file and lets you select a scattering detector and a fluorescence detector."),
                                html.Li("Uses the scattering channel to estimate or manually set a threshold that removes low signal noise."),
                                html.Li("Applies that threshold to gate the data before finding fluorescence peaks."),
                                html.Li("Lets you enter bead MESF values and fits a calibration curve MESF versus intensity."),
                                html.Li("Applies and saves the calibration payload for later use."),
                            ]
                        ),
                    ],
                    title="Overview",
                ),

                dbc.AccordionItem(
                    [
                        html.H4("Step 1. Upload bead file"),
                        html.Ul(
                            [
                                html.Li("Upload a bead FCS file."),
                                html.Li("After upload, detector dropdowns are populated from the file columns."),
                                html.Li("If you do not see expected channels, confirm the file contains those parameters."),
                            ]
                        ),
                    ],
                    title="1. Upload",
                ),

                dbc.AccordionItem(
                    [
                        html.H4("Step 2. Scattering channel"),
                        html.P(
                            "Goal: find a scattering threshold that separates noise from bead events. "
                            "This threshold is used to gate the fluorescence channel before peak finding."
                        ),
                        html.Ul(
                            [
                                html.Li("Select the scattering detector."),
                                html.Li("Choose number of bins. Larger values show more detail but can look noisier."),
                                html.Li('Click "Estimate threshold" to let the backend propose a value.'),
                                html.Li("Optionally type your own threshold. The scattering histogram updates immediately."),
                            ]
                        ),
                        dbc.Alert(
                            "Tip: if you see a strong pileup near zero, raise the threshold until that region is excluded while keeping the bead distribution.",
                            color="info",
                        ),
                    ],
                    title="2. Scattering threshold",
                ),

                dbc.AccordionItem(
                    [
                        html.H4("Step 3. Fluorescence after thresholding"),
                        html.P(
                            "Goal: find fluorescence peak positions on the gated data only (after applying the scattering threshold)."
                        ),
                        html.Ul(
                            [
                                html.Li("Select the fluorescence detector."),
                                html.Li("Choose number of bins for the fluorescence histogram."),
                                html.Li("Set the number of peaks to find, then click Find peaks."),
                                html.Li("Detected peak positions are drawn as vertical lines on the histogram."),
                                html.Li("Peak modes are also inserted into the bead table Intensity (a.u.) column (first empty rows)."),
                            ]
                        ),
                        dbc.Alert(
                            "If peak finding looks wrong, first verify the scattering threshold. Bad gating is the most common reason for messy fluorescence peaks.",
                            color="warning",
                        ),
                    ],
                    title="3. Find fluorescence peaks",
                ),

                dbc.AccordionItem(
                    [
                        html.H4("Step 4. Bead specifications table"),
                        html.P(
                            "Enter bead reference values (MESF) and the corresponding measured peak intensities (a.u.)."
                        ),
                        html.Ul(
                            [
                                html.Li("Intensity (MESF) is the vendor provided reference."),
                                html.Li("Intensity (a.u.) is the measured peak mode from your fluorescence histogram."),
                                html.Li("You need at least 2 valid rows to fit a calibration."),
                                html.Li("Use Add Row if you have more bead populations."),
                            ]
                        ),
                    ],
                    title="4. Enter MESF points",
                ),

                dbc.AccordionItem(
                    [
                        html.H4("Step 5. Calibrate"),
                        html.Ul(
                            [
                                html.Li('Click "Calibrate" to fit MESF as a function of intensity.'),
                                html.Li("The plot shows your bead points and the fitted line."),
                                html.Li("Slope and intercept are displayed under the plot."),
                            ]
                        ),
                        dbc.Alert(
                            "If the fitted line looks off, check that MESF values match the correct peaks and that you did not swap MESF and intensity columns.",
                            color="danger",
                        ),
                    ],
                    title="5. Fit calibration",
                ),

                dbc.AccordionItem(
                    [
                        html.H4("Step 6. Apply and save"),
                        html.Ul(
                            [
                                html.Li('Click "Apply Calibration" to preview calibrated values for the selected fluorescence detector.'),
                                html.Li("Choose a file name and click Save to store the calibration payload in the sidebar."),
                                html.Li("Saved payloads can be reused without re fitting."),
                            ]
                        ),
                    ],
                    title="6. Apply and save",
                ),

                dbc.AccordionItem(
                    [
                        html.H4("Common issues"),
                        html.Ul(
                            [
                                html.Li("Empty plots: check that a file is uploaded and a detector is selected."),
                                html.Li("No peaks found: lower the scattering threshold or increase max peaks."),
                                html.Li("Too many small peaks: increase the scattering threshold or reduce bins."),
                                html.Li("Weird calibration: verify that each MESF value corresponds to the correct fluorescence peak."),
                                html.Li("Decimal commas: thresholds accept both comma and dot, but the UI uses dot formatting."),
                            ]
                        ),
                    ],
                    title="Troubleshooting",
                ),
            ],
            start_collapsed=True,
            always_open=False,
        ),

        html.Hr(),
        html.P(
            [
                "Still stuck? Capture screenshots of the scattering and fluorescence histograms plus your bead table, "
                "and include the selected detector names and threshold value. That is enough to diagnose most problems."
            ]
        ),
    ],
    fluid=True,
    style={"paddingTop": "24px", "paddingBottom": "48px"},
)
