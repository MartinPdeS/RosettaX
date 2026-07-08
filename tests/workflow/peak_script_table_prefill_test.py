# -*- coding: utf-8 -*-

import logging

from RosettaX.workflow.peak.adapters.fluorescence import FluorescencePeakWorkflowAdapter
from RosettaX.workflow.peak.adapters.scattering import ScatteringPeakWorkflowAdapter


logger = logging.getLogger(__name__)


class Test_FluorescencePeakScriptTablePrefill:
    def test_apply_peak_process_result_to_table_merges_script_prefill_rows(self):
        adapter = FluorescencePeakWorkflowAdapter()

        table_result = adapter.apply_peak_process_result_to_table(
            table_data=[
                {"col1": "old-standard-1", "col2": "old-measured-1"},
                {"col1": "old-standard-2", "col2": "old-measured-2"},
                {"col1": "keep-standard-3", "col2": "keep-measured-3"},
            ],
            result={
                "table_prefill_rows": [
                    {
                        "measured_intensity": 12.3,
                        "calibrated_intensity": "1200 MESF",
                    },
                    {
                        "measured_intensity": 45.6,
                        "calibrated_intensity": "4500 MESF",
                    },
                ],
            },
            context={},
            logger=logger,
        )

        assert table_result == [
            {"col1": "1200 MESF", "col2": 12.3},
            {"col1": "4500 MESF", "col2": 45.6},
            {"col1": "keep-standard-3", "col2": "keep-measured-3"},
        ]


class Test_ScatteringPeakScriptTablePrefill:
    def test_apply_peak_process_result_to_table_merges_script_prefill_rows_for_solid_sphere(self):
        adapter = ScatteringPeakWorkflowAdapter()

        table_result = adapter.apply_peak_process_result_to_table(
            table_data=[
                {
                    "particle_diameter_nm": "100",
                    "measured_peak_position": "10",
                    "expected_coupling": "1.5",
                    "expected_cross_section_nm2": "20",
                },
                {
                    "particle_diameter_nm": "200",
                    "measured_peak_position": "20",
                    "expected_coupling": "2.5",
                    "expected_cross_section_nm2": "30",
                },
                {
                    "particle_diameter_nm": "300",
                    "measured_peak_position": "",
                    "expected_coupling": "3.5",
                    "expected_cross_section_nm2": "40",
                },
            ],
            result={
                "table_prefill_rows": [
                    {
                        "measured_peak_position": 111.0,
                        "particle_diameter_nm": 555.0,
                    },
                    {
                        "measured_peak_position": 222.0,
                        "particle_diameter_nm": 777.0,
                    },
                ],
            },
            context={
                "mie_model": "Solid Sphere",
            },
            logger=logger,
        )

        assert table_result == [
            {
                "particle_diameter_nm": 555.0,
                "measured_peak_position": 111.0,
                "expected_coupling": "",
                "expected_cross_section_nm2": "",
            },
            {
                "particle_diameter_nm": 777.0,
                "measured_peak_position": 222.0,
                "expected_coupling": "",
                "expected_cross_section_nm2": "",
            },
            {
                "particle_diameter_nm": "300",
                "measured_peak_position": "",
                "expected_coupling": "3.5",
                "expected_cross_section_nm2": "40",
            },
        ]

    def test_apply_peak_process_result_to_table_merges_script_prefill_rows_for_core_shell(self):
        adapter = ScatteringPeakWorkflowAdapter()

        table_result = adapter.apply_peak_process_result_to_table(
            table_data=[
                {
                    "core_diameter_nm": "90",
                    "shell_thickness_nm": "5",
                    "outer_diameter_nm": "100",
                    "measured_peak_position": "10",
                    "expected_coupling": "1.5",
                    "expected_cross_section_nm2": "20",
                },
            ],
            result={
                "table_prefill_rows": [
                    {
                        "measured_peak_position": 333.0,
                        "core_diameter_nm": 120.0,
                        "shell_thickness_nm": 15.0,
                    },
                ],
            },
            context={
                "mie_model": "Core/Shell Sphere",
            },
            logger=logger,
        )

        assert table_result == [
            {
                "core_diameter_nm": 120.0,
                "shell_thickness_nm": 15.0,
                "outer_diameter_nm": 150.0,
                "measured_peak_position": 333.0,
                "expected_coupling": "",
                "expected_cross_section_nm2": "",
            },
            {
                "core_diameter_nm": "",
                "shell_thickness_nm": "",
                "outer_diameter_nm": "",
                "measured_peak_position": "",
                "expected_coupling": "",
                "expected_cross_section_nm2": "",
            },
            {
                "core_diameter_nm": "",
                "shell_thickness_nm": "",
                "outer_diameter_nm": "",
                "measured_peak_position": "",
                "expected_coupling": "",
                "expected_cross_section_nm2": "",
            },
        ]
