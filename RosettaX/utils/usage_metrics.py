# -*- coding: utf-8 -*-

import json
import logging
import os
import platform
import threading
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

try:
    import psycopg  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - handled through backend fallback.
    psycopg = None


logger = logging.getLogger(__name__)


ROSETTAX_USAGE_METRICS_PATH_ENV_VAR = "ROSETTAX_USAGE_METRICS_PATH"
ROSETTAX_USAGE_METRICS_BACKEND_ENV_VAR = "ROSETTAX_USAGE_METRICS_BACKEND"
ROSETTAX_USAGE_METRICS_DATABASE_URL_ENV_VAR = "ROSETTAX_USAGE_METRICS_DATABASE_URL"
DATABASE_URL_ENV_VAR = "DATABASE_URL"

METRIC_NAME_APPLY_BUTTON_CLICK_COUNT = "apply_button_click_count"
METRIC_NAME_TOTAL_CALIBRATED_FILES = "total_calibrated_files"
METRIC_NAME_HOME_PAGE_VISIT_COUNT = "home_page_visit_count"

_WRITE_LOCK = threading.Lock()


@dataclass(frozen=True)
class UsageMetrics:
    """
    Server-side aggregate usage counters.
    """

    apply_button_click_count: int = 0
    total_calibrated_files: int = 0
    home_page_visit_count: int = 0

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
            home_page_visit_count=_coerce_non_negative_int(
                payload.get("home_page_visit_count"),
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
    if _use_postgres_backend():
        try:
            return _load_usage_metrics_from_postgres()
        except Exception:
            logger.exception("Failed to load usage metrics from Postgres. Falling back to file backend.")

    return _load_usage_metrics_from_file()


def _load_usage_metrics_from_file() -> UsageMetrics:
    """
    Load usage counters from local file storage.
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
        home_page_visit_delta=0,
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
        home_page_visit_delta=0,
    )


def record_home_page_visit() -> UsageMetrics:
    """
    Increment the home page visit counter.
    """
    return _update_usage_metrics(
        apply_button_click_delta=0,
        calibrated_files_delta=0,
        home_page_visit_delta=1,
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
    home_page_visit_delta: int,
) -> UsageMetrics:
    if _use_postgres_backend():
        try:
            return _update_usage_metrics_postgres(
                apply_button_click_delta=apply_button_click_delta,
                calibrated_files_delta=calibrated_files_delta,
                home_page_visit_delta=home_page_visit_delta,
            )
        except Exception:
            logger.exception("Failed to update usage metrics in Postgres. Falling back to file backend.")

    return _update_usage_metrics_file(
        apply_button_click_delta=apply_button_click_delta,
        calibrated_files_delta=calibrated_files_delta,
        home_page_visit_delta=home_page_visit_delta,
    )


def _update_usage_metrics_file(
    *,
    apply_button_click_delta: int,
    calibrated_files_delta: int,
    home_page_visit_delta: int,
) -> UsageMetrics:
    metrics_file_path = get_usage_metrics_file_path()

    with _WRITE_LOCK:
        current_metrics = _load_usage_metrics_from_file()
        next_metrics = UsageMetrics(
            apply_button_click_count=(
                current_metrics.apply_button_click_count + int(apply_button_click_delta)
            ),
            total_calibrated_files=(
                current_metrics.total_calibrated_files + int(calibrated_files_delta)
            ),
            home_page_visit_count=(
                current_metrics.home_page_visit_count + int(home_page_visit_delta)
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


def _use_postgres_backend() -> bool:
    backend = str(
        os.getenv(ROSETTAX_USAGE_METRICS_BACKEND_ENV_VAR, "file"),
    ).strip().lower()

    if backend != "postgres":
        return False

    if psycopg is None:
        logger.warning(
            "usage_metrics backend is set to postgres but psycopg is unavailable. "
            "Falling back to file backend."
        )
        return False

    return bool(_get_database_url())


def _get_database_url() -> str:
    configured_url = str(
        os.getenv(ROSETTAX_USAGE_METRICS_DATABASE_URL_ENV_VAR, ""),
    ).strip()

    if configured_url:
        return configured_url

    return str(
        os.getenv(DATABASE_URL_ENV_VAR, ""),
    ).strip()


def _connect_postgres():
    database_url = _get_database_url()

    if not database_url:
        raise RuntimeError("Postgres backend requested but no database URL is configured.")

    return psycopg.connect(database_url)


def _ensure_postgres_metrics_table(connection: Any) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS metrics_counters (
                metric_name TEXT PRIMARY KEY,
                metric_value BIGINT NOT NULL DEFAULT 0,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )


def _load_usage_metrics_from_postgres() -> UsageMetrics:
    with _connect_postgres() as connection:
        _ensure_postgres_metrics_table(connection)

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT metric_name, metric_value
                FROM metrics_counters
                WHERE metric_name = ANY(%s)
                """,
                ([
                    METRIC_NAME_APPLY_BUTTON_CLICK_COUNT,
                    METRIC_NAME_TOTAL_CALIBRATED_FILES,
                    METRIC_NAME_HOME_PAGE_VISIT_COUNT,
                ],),
            )
            rows = cursor.fetchall()

    values = {
        name: _coerce_non_negative_int(value)
        for name, value in rows
    }

    return UsageMetrics(
        apply_button_click_count=values.get(METRIC_NAME_APPLY_BUTTON_CLICK_COUNT, 0),
        total_calibrated_files=values.get(METRIC_NAME_TOTAL_CALIBRATED_FILES, 0),
        home_page_visit_count=values.get(METRIC_NAME_HOME_PAGE_VISIT_COUNT, 0),
    )


def _update_usage_metrics_postgres(
    *,
    apply_button_click_delta: int,
    calibrated_files_delta: int,
    home_page_visit_delta: int,
) -> UsageMetrics:
    deltas = {
        METRIC_NAME_APPLY_BUTTON_CLICK_COUNT: max(0, int(apply_button_click_delta)),
        METRIC_NAME_TOTAL_CALIBRATED_FILES: max(0, int(calibrated_files_delta)),
        METRIC_NAME_HOME_PAGE_VISIT_COUNT: max(0, int(home_page_visit_delta)),
    }

    with _connect_postgres() as connection:
        _ensure_postgres_metrics_table(connection)

        with connection.cursor() as cursor:
            for metric_name, delta in deltas.items():
                if delta <= 0:
                    continue

                cursor.execute(
                    """
                    INSERT INTO metrics_counters (metric_name, metric_value)
                    VALUES (%s, %s)
                    ON CONFLICT (metric_name)
                    DO UPDATE SET
                        metric_value = metrics_counters.metric_value + EXCLUDED.metric_value,
                        updated_at = NOW()
                    """,
                    (
                        metric_name,
                        delta,
                    ),
                )

        connection.commit()

    return _load_usage_metrics_from_postgres()