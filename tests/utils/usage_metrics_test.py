# -*- coding: utf-8 -*-

from pathlib import Path

import pytest

from RosettaX.utils import usage_metrics


class Test_UsageMetrics:
    def test_usage_metrics_round_trip_click_and_file_counters(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        metrics_file_path = tmp_path / "usage_metrics.json"

        monkeypatch.setenv(
            usage_metrics.ROSETTAX_USAGE_METRICS_PATH_ENV_VAR,
            str(metrics_file_path),
        )

        assert usage_metrics.load_usage_metrics() == usage_metrics.UsageMetrics()

        usage_metrics.record_apply_button_click()
        usage_metrics.record_apply_button_click()
        usage_metrics.record_calibrated_files(
            file_count=7,
        )

        assert usage_metrics.load_usage_metrics() == usage_metrics.UsageMetrics(
            apply_button_click_count=2,
            total_calibrated_files=7,
        )

    def test_usage_metrics_ignores_invalid_payload_values(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        metrics_file_path = tmp_path / "usage_metrics.json"
        metrics_file_path.write_text(
            '{"apply_button_click_count": "abc", "total_calibrated_files": -3}',
            encoding="utf-8",
        )

        monkeypatch.setenv(
            usage_metrics.ROSETTAX_USAGE_METRICS_PATH_ENV_VAR,
            str(metrics_file_path),
        )

        assert usage_metrics.load_usage_metrics() == usage_metrics.UsageMetrics(
            apply_button_click_count=0,
            total_calibrated_files=0,
        )