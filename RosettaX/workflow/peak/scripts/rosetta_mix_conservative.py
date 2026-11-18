"""Conservative Rosetta Script settings for scatter-peak validation."""

from .rosetta_mix_modes import RosettaMixSizeAssignmentProcess


class ConservativeRosettaScatterPeakProcess(RosettaMixSizeAssignmentProcess):
    """Use conservative scatter-fit thresholds with marker-based size assignment."""

    process_name = "Rosetta Script Conservative"
    process_label = "Rosetta Legacy"
    description = (
        "Uses stricter scatter-peak fit criteria and estimates bead sizes from "
        "the 140 nm and 380 nm fluorescent markers."
    )
    sort_order = 3

    fit_thresholds = {
        "fit_r2_threshold": 0.85,
        "fit_cv_threshold": 0.60,
        "scatter_fit_r2_threshold": 0.85,
        "scatter_fit_cv_threshold": 0.75,
    }
