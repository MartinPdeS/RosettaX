"""Generate a clearly labelled synthetic example of the exported PDF report."""

import argparse
from pathlib import Path

import numpy as np

from RosettaX.workflow.apply_calibration.report import (
    build_apply_report_payload,
    build_apply_report_pdf_bytes,
)
from RosettaX.workflow.apply_calibration.services import (
    ApplyCalibrationFilesResult,
    ApplyCalibrationRequest,
    CalibrationApplication,
)


def generate_example_report(output_path: Path) -> None:
    """Render the production report composer using synthetic fluorescence data."""
    measured = np.asarray([900.0, 8400.0, 76000.0, 680000.0])
    reference = np.asarray([1000.0, 10000.0, 100000.0, 1000000.0])
    log_reference = np.log10(reference)
    slope, intercept = np.polyfit(np.log10(measured), log_reference, 1)
    fitted = slope * np.log10(measured) + intercept
    r_squared = 1 - np.sum((log_reference - fitted) ** 2) / np.sum((log_reference - log_reference.mean()) ** 2)
    calibration = {
        "calibration_type": "fluorescence",
        "schema_version": "1.0",
        "name": "Synthetic FITC MESF example",
        "source_file": "synthetic_reference_beads.fcs",
        "source_channel": "FITC-A",
        "output_quantity": "MESF",
        "applied_output_channel_name": "FITC_MESF",
        "fit_model": "log10(y)=slope*log10(x)+intercept",
        "fit_metrics": {"r_squared": float(r_squared), "point_count": 4},
        "parameters": {"slope": float(slope), "intercept": float(intercept), "prefactor": float(10 ** intercept)},
        "reference_points": [
            {"measured_value": float(x), "reference_value": float(y)}
            for x, y in zip(measured, reference)
        ],
        "payload": {"x_definition": "Intensity [a.u.]", "y_definition": "Intensity [MESF]"},
        "metadata": {"sample_kind": "Synthetic demonstration", "reference_lot": "DEMO-001"},
        "export_notes": "Illustrative data only. No experimental files were processed.",
    }
    request = ApplyCalibrationRequest(
        uploaded_fcs_paths=["synthetic_sample_a.fcs", "synthetic_sample_b.fcs"],
        export_columns=["Time", "SSC-A"],
        calibrations=[CalibrationApplication(
            selected_calibration="synthetic_fitc_mesf.json", calibration_payload=calibration,
        )],
    )
    result = ApplyCalibrationFilesResult(
        payload_bytes=b"", download_filename="synthetic_calibrated_samples.zip",
        source_channel="FITC-A", output_channels=["FITC_MESF", "Time", "SSC-A"],
        file_count=2, warnings=["SYNTHETIC EXAMPLE: No experimental files were processed."],
        status="Demonstration of a two-file fluorescence export.",
    )
    payload = build_apply_report_payload(
        request=request, result=result,
        calibration_summary={
            "file_name": "synthetic_fitc_mesf.json", "calibration_type": "fluorescence",
            "source_channel": "FITC-A", "output_quantity": "MESF",
        },
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(build_apply_report_pdf_bytes(report_payload=payload))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("example_report.pdf"))
    arguments = parser.parse_args()
    generate_example_report(arguments.output)
    print(arguments.output.resolve())
