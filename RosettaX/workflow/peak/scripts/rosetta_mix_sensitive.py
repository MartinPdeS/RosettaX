"""Sensitive Rosetta Script settings for scatter-peak validation."""

from .rosetta_mix_modes import RosettaMixSizeAssignmentProcess


class SensitiveRosettaScatterPeakProcess(RosettaMixSizeAssignmentProcess):
    """Use permissive scatter-fit thresholds with marker-based size assignment."""

    process_name = "Rosetta Script Sensitive"
    process_label = "Rosetta — Sensitive"
    description = (
        "Accepts broader scatter-peak fits, so noisier or overlapping peaks may "
        "be included. Bead sizes are estimated from the 140 nm and 380 nm markers."
    )
    sort_order = 2

    fit_thresholds = {
        "fit_r2_threshold": 0.70,
        "fit_cv_threshold": 0.60,
        "scatter_fit_r2_threshold": -0.10,
        "scatter_fit_cv_threshold": 3.50,
    }
