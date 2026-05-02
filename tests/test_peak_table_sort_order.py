# -*- coding: utf-8 -*-

import logging

from RosettaX.workflow.peak.adapters.fluorescence import FluorescencePeakWorkflowAdapter
from RosettaX.workflow.peak.adapters.scattering import ScatteringPeakWorkflowAdapter

logger = logging.getLogger(__name__)


class Test_FluorescencePeakTableSortOrder:
    def test_apply_peak_process_result_to_table_sorts_values_ascending_by_default(self):
        adapter = FluorescencePeakWorkflowAdapter()

        table_result = adapter.apply_peak_process_result_to_table(
            table_data=[
                {"col1": "1", "col2": ""},
                {"col1": "10", "col2": ""},
                {"col1": "100", "col2": ""},
            ],
            result={
                "new_peak_positions": [30, 10, 20],
            },
            context={},
            logger=logger,
        )

        assert [row["col2"] for row in table_result] == [10, 20, 30]

    def test_apply_peak_process_result_to_table_sorts_values_descending_from_runtime_config(
        self,
    ):
        adapter = FluorescencePeakWorkflowAdapter()

        table_result = adapter.apply_peak_process_result_to_table(
            table_data=[
                {"col1": "1", "col2": ""},
                {"col1": "10", "col2": ""},
                {"col1": "100", "col2": ""},
            ],
            result={
                "new_peak_positions": [30, 10, 20],
            },
            context={
                "runtime_config_data": {
                    "fluorescence_calibration": {
                        "peak_table_sort_order": "descending",
                    },
                },
            },
            logger=logger,
        )

        assert [row["col2"] for row in table_result] == [30, 20, 10]


class Test_ScatteringPeakTableSortOrder:
    def test_apply_peak_process_result_to_table_sorts_values_descending_from_runtime_config(
        self,
    ):
        adapter = ScatteringPeakWorkflowAdapter()

        table_result = adapter.apply_peak_process_result_to_table(
            table_data=[
                {"particle_diameter_nm": "100", "measured_peak_position": ""},
                {"particle_diameter_nm": "200", "measured_peak_position": ""},
                {"particle_diameter_nm": "300", "measured_peak_position": ""},
            ],
            result={
                "new_peak_positions": [30, 10, 20],
            },
            context={
                "mie_model": "Solid Sphere",
                "runtime_config_data": {
                    "scattering_calibration": {
                        "peak_table_sort_order": "descending",
                    },
                },
            },
            logger=logger,
        )

        assert [row["measured_peak_position"] for row in table_result] == [30, 20, 10]
