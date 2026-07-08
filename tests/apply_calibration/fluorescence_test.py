# -*- coding: utf-8 -*-

import numpy as np

from RosettaX.workflow.apply_calibration.fluorescence import (
    apply_legacy_calibration_to_series,
)


def test_apply_legacy_log_calibration_clamps_negative_values_and_warns() -> None:
    warnings: list[str] = []

    calibrated = apply_legacy_calibration_to_series(
        values=np.asarray([-5.0, 0.0, 10.0], dtype=float),
        calibration_payload={
            "fit_model": "log10(y)=slope*log10(x)+intercept",
            "parameters": {
                "slope": 1.0,
                "intercept": 0.0,
            },
        },
        warning_messages=warnings,
        source_channel="FITC-A",
    )

    assert calibrated.tolist() == [0.0, 0.0, 10.0]
    assert warnings == [
        'Clamped 1 negative event(s) to 0 before applying log calibration to "FITC-A".'
    ]
