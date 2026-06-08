# -*- coding: utf-8 -*-

import json
import logging
import os
import platform
import threading
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)


ROSETTAX_USAGE_METRICS_PATH_ENV_VAR = "ROSETTAX_USAGE_METRICS_PATH"

_WRITE_LOCK = threading.Lock()


@dataclass(frozen=True)
class UsageMetrics:
    """
    Server-side aggregate usage counters.
    """

    apply_button_click_count: int = 0
    total_calibrated_files: int = 0

    @classmethod
    def from_dict(
        cls,
        payload: Any,
    ) -> "UsageMetrics":
        """
        Rebuild usage metrics from a serialized mapping.
        """
        if not isinstance(payload, dict):
            return cls()

        return cls(
            apply_button_click_count=_coerce_non_negative_int(
                payload.get("apply_button_click_count"),
            ),
            total_calibrated_files=_coerce_non_negative_int(
                payload.get("total_calibrated_files"),
            ),
        )

    def to_dict(self) -> dict[str, int]:
        """
        Serialize usage metrics for storage.
        """
        return asdict(self)


def load_usage_metrics() -> UsageMetrics:
    """
    Load the persisted usage counters.
    """
    metrics_file_path = get_usage_metrics_file_path()

    if not metrics_file_path.exists():
        return UsageMetrics()

    try:
        payload = json.loads(
            metrics_file_path.read_text(
                encoding="utf-8",
            )
        )
    except Exception:
        logger.exception(
            "Failed to read usage metrics from metrics_file_path=%r",
            str(metrics_file_path),
        )
        return UsageMetrics()

    return UsageMetrics.from_dict(
        payload,
    )


def record_apply_button_click() -> UsageMetrics:
    """
    Increment the apply button click counter.
    """
    return _update_usage_metrics(
        apply_button_click_delta=1,
        calibrated_files_delta=0,
    )


def record_calibrated_files(
    *,
    file_count: int,
) -> UsageMetrics:
    """
    Increment the total calibrated file count.
    """
    return _update_usage_metrics(
        apply_button_click_delta=0,
        calibrated_files_delta=max(0, int(file_count)),
    )


def get_usage_metrics_file_path() -> Path:
    """
    Resolve the server-side usage metrics storage path.
    """
    configured_path = str(
        os.getenv(ROSETTAX_USAGE_METRICS_PATH_ENV_VAR, ""),
    ).strip()

    if configured_path:
        return Path(configured_path).expanduser().resolve()

    return _default_usage_metrics_file_path()


def _default_usage_metrics_file_path() -> Path:
    system_name = platform.system()
    home_directory = Path.home()

    if system_name == "Darwin":
        return home_directory / "Library" / "Application Support" / "RosettaX" / "usage_metrics.json"

    if system_name == "Windows":
        local_app_data = str(os.getenv("LOCALAPPDATA", "")).strip()
        if local_app_data:
            return Path(local_app_data).expanduser().resolve() / "RosettaX" / "usage_metrics.json"

    return home_directory / ".local" / "share" / "RosettaX" / "usage_metrics.json"


def _update_usage_metrics(
    *,
    apply_button_click_delta: int,
    calibrated_files_delta: int,
) -> UsageMetrics:
    metrics_file_path = get_usage_metrics_file_path()

    with _WRITE_LOCK:
        current_metrics = load_usage_metrics()
        next_metrics = UsageMetrics(
            apply_button_click_count=(
                current_metrics.apply_button_click_count + int(apply_button_click_delta)
            ),
            total_calibrated_files=(
                current_metrics.total_calibrated_files + int(calibrated_files_delta)
            ),
        )
        _write_usage_metrics(
            metrics_file_path=metrics_file_path,
            metrics=next_metrics,
        )

    return next_metrics


def _write_usage_metrics(
    *,
    metrics_file_path: Path,
    metrics: UsageMetrics,
) -> None:
    metrics_file_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    temporary_file_path = metrics_file_path.with_suffix(
        f"{metrics_file_path.suffix}.tmp",
    )
    temporary_file_path.write_text(
        json.dumps(metrics.to_dict(), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    temporary_file_path.replace(
        metrics_file_path,
    )


def _coerce_non_negative_int(value: Any) -> int:
    try:
        resolved_value = int(value)
    except Exception:
        return 0

    if resolved_value < 0:
        return 0

    return resolved_value