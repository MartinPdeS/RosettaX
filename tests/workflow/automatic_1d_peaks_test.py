# -*- coding: utf-8 -*-

import numpy as np

from RosettaX.workflow.peak.scripts.automatic_1d_peaks import (
    Automatic1DPeaksProcess,
)


class Test_Automatic1DPeaksProcess:
    def test_estimate_peak_prominences_keeps_right_edge_peak(self) -> None:
        process = Automatic1DPeaksProcess()

        counts = np.asarray(
            [1.0, 3.0, 2.0, 1.0, 4.0, 8.0],
            dtype=float,
        )

        candidate_indices = process.find_local_maxima_indices(
            counts=counts,
        )
        prominences = process.estimate_peak_prominences(
            counts=counts,
            candidate_indices=candidate_indices,
        )

        prominence_by_index = {
            int(candidate_indices[index]): float(prominences[index])
            for index in range(candidate_indices.size)
        }

        assert counts.size - 1 in prominence_by_index
        assert prominence_by_index[counts.size - 1] > 0.0
