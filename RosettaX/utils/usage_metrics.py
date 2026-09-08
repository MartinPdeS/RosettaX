# -*- coding: utf-8 -*-

import json
import logging
import os
import platform
import threading
import ipaddress
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

try:
    import psycopg  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - handled through backend fallback.
    psycopg = None


logger = logging.getLogger(__name__)


ROSETTAX_USAGE_METRICS_PATH_ENV_VAR = "ROSETTAX_USAGE_METRICS_PATH"
ROSETTAX_USAGE_METRICS_BACKEND_ENV_VAR = "ROSETTAX_USAGE_METRICS_BACKEND"
ROSETTAX_USAGE_METRICS_DATABASE_URL_ENV_VAR = "ROSETTAX_USAGE_METRICS_DATABASE_URL"
ROSETTAX_VISIT_LOG_PATH_ENV_VAR = "ROSETTAX_VISIT_LOG_PATH"
ROSETTAX_TRACK_LOCAL_VISITS_ENV_VAR = "ROSETTAX_TRACK_LOCAL_VISITS"
DATABASE_URL_ENV_VAR = "DATABASE_URL"

METRIC_NAME_APPLY_BUTTON_CLICK_COUNT = "apply_button_click_count"
METRIC_NAME_TOTAL_CALIBRATED_FILES = "total_calibrated_files"
METRIC_NAME_HOME_PAGE_VISIT_COUNT = "home_page_visit_count"

DEFAULT_RECENT_VISIT_LIMIT = 25

_VISIT_LOG_FILE_NAME = "visit_log.jsonl"
_MAX_TIMESTAMP_LENGTH = 64
_MAX_IP_ADDRESS_LENGTH = 64
_MAX_PATH_LENGTH = 512
_MAX_USER_AGENT_LENGTH = 300

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


@dataclass(frozen=True)
class VisitEvent:
    """
    One recorded page visit with client metadata.
    """

    visited_at: str = ""
    ip_address: str = ""
    path: str = ""
    user_agent: str = ""

    @classmethod
    def from_dict(
        cls,
        payload: Any,
    ) -> "VisitEvent":
        """
        Rebuild a visit event from a serialized mapping.
        """
        if not isinstance(payload, dict):
            return cls()

        return cls(
            visited_at=_coerce_visit_text(
                payload.get("visited_at"),
                max_length=_MAX_TIMESTAMP_LENGTH,
            ),
            ip_address=_coerce_visit_text(
                payload.get("ip_address"),
                max_length=_MAX_IP_ADDRESS_LENGTH,
            ),
            path=_coerce_visit_text(
                payload.get("path"),
                max_length=_MAX_PATH_LENGTH,
            ),
            user_agent=_coerce_visit_text(
                payload.get("user_agent"),
                max_length=_MAX_USER_AGENT_LENGTH,
            ),
        )

    def to_dict(self) -> dict[str, str]:
        """
        Serialize the visit event for storage.
        """
        return asdict(self)


@dataclass(frozen=True)
class DailyVisitSeries:
    """
    Per-day visit and unique visitor counts over a continuous date range.
    """

    dates: list[str] = field(default_factory=list)
    visit_counts: list[int] = field(default_factory=list)
    unique_visitor_counts: list[int] = field(default_factory=list)


@dataclass(frozen=True)
class VisitSummary:
    """
    Aggregated view over recorded visit events for the admin dashboard.
    """

    total_visits: int = 0
    unique_visitor_count: int = 0
    visits_today: int = 0
    unique_visitors_today: int = 0
    daily: DailyVisitSeries = field(default_factory=DailyVisitSeries)
    page_visit_counts: list[tuple[str, int]] = field(default_factory=list)
    recent_visits: list[VisitEvent] = field(default_factory=list)


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


def should_track_local_visits() -> bool:
    """
    Return True if local/loopback/private IP visit tracking is explicitly enabled via env var.
    """
    raw_value = str(
        os.getenv(ROSETTAX_TRACK_LOCAL_VISITS_ENV_VAR, "false"),
    ).strip().lower()
    return raw_value in ("1", "true", "yes", "on")


def is_local_ip(ip_address: Any) -> bool:
    """
    Check whether an IP address or hostname represents a local/loopback/private address.

    Detects loopback (127.0.0.1, ::1), local hostnames (localhost, testclient, 0.0.0.0, unknown),
    private IPv4 (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16), and local/link-local IPv6.
    """
    if ip_address is None:
        return True

    text = str(ip_address).strip().lower()

    if not text or text in (
        "127.0.0.1",
        "::1",
        "localhost",
        "0.0.0.0",
        "testclient",
        "unknown",
    ):
        return True

    if "," in text:
        text = text.split(",")[0].strip()

    if ":" in text and not text.startswith("::") and text.count(":") == 1:
        text = text.split(":")[0].strip()

    try:
        ip_obj = ipaddress.ip_address(text)
        return (
            ip_obj.is_loopback
            or ip_obj.is_private
            or ip_obj.is_link_local
            or ip_obj.is_reserved
            or ip_obj.is_unspecified
        )
    except ValueError:
        return False


def record_page_visit(
    *,
    ip_address: Any,
    path: Any,
    user_agent: Any,
    visited_at: Optional[str] = None,
    include_local: bool = False,
) -> VisitEvent:
    """
    Record one page visit event with client metadata.

    Local/loopback/private IP visits are skipped by default when running locally,
    unless ROSETTAX_TRACK_LOCAL_VISITS is enabled or include_local is True.
    """
    resolved_visited_at = str(visited_at).strip() if visited_at else ""

    if not resolved_visited_at:
        resolved_visited_at = _current_utc_timestamp()

    event = VisitEvent(
        visited_at=resolved_visited_at,
        ip_address=_coerce_visit_text(
            ip_address,
            max_length=_MAX_IP_ADDRESS_LENGTH,
        ),
        path=_coerce_visit_text(
            path,
            max_length=_MAX_PATH_LENGTH,
        ) or "/",
        user_agent=_coerce_visit_text(
            user_agent,
            max_length=_MAX_USER_AGENT_LENGTH,
        ),
    )

    if is_local_ip(event.ip_address) and not include_local and not should_track_local_visits():
        logger.debug(
            "Skipping page visit recording for local IP address=%r",
            event.ip_address,
        )
        return event

    if _use_postgres_backend():
        try:
            _record_page_visit_postgres(event)
            return event
        except Exception:
            logger.exception(
                "Failed to record page visit in Postgres. Falling back to file backend."
            )

    _record_page_visit_file(event)

    return event


def load_visit_events() -> list[VisitEvent]:
    """
    Load all recorded visit events in chronological order.
    """
    if _use_postgres_backend():
        try:
            return _load_visit_events_from_postgres()
        except Exception:
            logger.exception(
                "Failed to load visit events from Postgres. Falling back to file backend."
            )

    return _load_visit_events_from_file()


def summarize_visit_events(
    events: list[VisitEvent],
    *,
    recent_limit: int = DEFAULT_RECENT_VISIT_LIMIT,
    today: Optional[str] = None,
    include_local: bool = False,
) -> VisitSummary:
    """
    Aggregate visit events into dashboard-ready counts and daily series.

    Local/loopback/private IP visits are excluded by default unless include_local is True
    or ROSETTAX_TRACK_LOCAL_VISITS is enabled.
    """
    resolved_today = str(today).strip() if today else ""

    if not resolved_today:
        resolved_today = datetime.now(timezone.utc).date().isoformat()

    filter_local = not include_local and not should_track_local_visits()

    visit_counts_by_date: dict[str, int] = {}
    visitors_by_date: dict[str, set[str]] = {}
    visit_counts_by_path: dict[str, int] = {}
    unique_visitors: set[str] = set()
    filtered_events: list[VisitEvent] = []

    for event in events:
        if filter_local and is_local_ip(event.ip_address):
            continue

        filtered_events.append(event)
        visit_date = _visit_event_date(event)

        if visit_date is not None:
            visit_counts_by_date[visit_date] = visit_counts_by_date.get(visit_date, 0) + 1

            if event.ip_address:
                visitors_by_date.setdefault(visit_date, set()).add(event.ip_address)

        if event.ip_address:
            unique_visitors.add(event.ip_address)

        resolved_path = event.path or "/"
        visit_counts_by_path[resolved_path] = visit_counts_by_path.get(resolved_path, 0) + 1

    series_dates = _continuous_date_range(visit_counts_by_date)

    daily = DailyVisitSeries(
        dates=series_dates,
        visit_counts=[visit_counts_by_date.get(day, 0) for day in series_dates],
        unique_visitor_counts=[
            len(visitors_by_date.get(day, set())) for day in series_dates
        ],
    )

    page_visit_counts = sorted(
        visit_counts_by_path.items(),
        key=lambda item: (-item[1], item[0]),
    )

    if recent_limit > 0:
        recent_visits = list(reversed(filtered_events[-recent_limit:]))
    else:
        recent_visits = []

    return VisitSummary(
        total_visits=len(filtered_events),
        unique_visitor_count=len(unique_visitors),
        visits_today=visit_counts_by_date.get(resolved_today, 0),
        unique_visitors_today=len(visitors_by_date.get(resolved_today, set())),
        daily=daily,
        page_visit_counts=page_visit_counts,
        recent_visits=recent_visits,
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


def get_visit_log_file_path() -> Path:
    """
    Resolve the server-side visit log storage path.
    """
    configured_path = str(
        os.getenv(ROSETTAX_VISIT_LOG_PATH_ENV_VAR, ""),
    ).strip()

    if configured_path:
        return Path(configured_path).expanduser().resolve()

    return _default_visit_log_file_path()


def _default_visit_log_file_path() -> Path:
    return _default_usage_metrics_file_path().parent / _VISIT_LOG_FILE_NAME


def _record_page_visit_file(event: VisitEvent) -> None:
    visit_log_file_path = get_visit_log_file_path()

    with _WRITE_LOCK:
        visit_log_file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        with visit_log_file_path.open("a", encoding="utf-8") as stream:
            stream.write(
                json.dumps(event.to_dict(), sort_keys=True) + "\n",
            )


def _load_visit_events_from_file() -> list[VisitEvent]:
    visit_log_file_path = get_visit_log_file_path()

    if not visit_log_file_path.exists():
        return []

    try:
        log_lines = visit_log_file_path.read_text(
            encoding="utf-8",
        ).splitlines()
    except Exception:
        logger.exception(
            "Failed to read visit log from visit_log_file_path=%r",
            str(visit_log_file_path),
        )
        return []

    events: list[VisitEvent] = []

    for log_line in log_lines:
        stripped_line = log_line.strip()

        if not stripped_line:
            continue

        try:
            payload = json.loads(stripped_line)
        except Exception:
            logger.warning("Skipping malformed visit log line.")
            continue

        event = VisitEvent.from_dict(payload)

        if not event.visited_at:
            continue

        events.append(event)

    return events


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


def _coerce_visit_text(value: Any, *, max_length: int) -> str:
    if value is None:
        return ""

    text = str(value).strip()

    if len(text) > max_length:
        return text[:max_length]

    return text


def _current_utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _visit_event_date(event: VisitEvent) -> Optional[str]:
    try:
        parsed_timestamp = datetime.fromisoformat(event.visited_at)
    except (TypeError, ValueError):
        return None

    return parsed_timestamp.date().isoformat()


def _continuous_date_range(visit_counts_by_date: dict[str, int]) -> list[str]:
    if not visit_counts_by_date:
        return []

    first_date = date.fromisoformat(min(visit_counts_by_date))
    last_date = date.fromisoformat(max(visit_counts_by_date))

    series_dates: list[str] = []
    current_date = first_date

    while current_date <= last_date:
        series_dates.append(current_date.isoformat())
        current_date += timedelta(days=1)

    return series_dates


def _parse_visit_timestamp(visited_at: str) -> datetime:
    try:
        parsed_timestamp = datetime.fromisoformat(visited_at)
    except (TypeError, ValueError):
        return datetime.now(timezone.utc)

    if parsed_timestamp.tzinfo is None:
        return parsed_timestamp.replace(tzinfo=timezone.utc)

    return parsed_timestamp


def _format_visit_timestamp(visited_at: Any) -> str:
    if isinstance(visited_at, datetime):
        if visited_at.tzinfo is None:
            visited_at = visited_at.replace(tzinfo=timezone.utc)

        return visited_at.astimezone(timezone.utc).isoformat(timespec="seconds")

    return str(visited_at or "")


def _ensure_postgres_page_visits_table(connection: Any) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS page_visits (
                id BIGSERIAL PRIMARY KEY,
                visited_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                ip_address TEXT NOT NULL DEFAULT '',
                path TEXT NOT NULL DEFAULT '',
                user_agent TEXT NOT NULL DEFAULT ''
            )
            """
        )


def _record_page_visit_postgres(event: VisitEvent) -> None:
    with _connect_postgres() as connection:
        _ensure_postgres_page_visits_table(connection)

        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO page_visits (visited_at, ip_address, path, user_agent)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    _parse_visit_timestamp(event.visited_at),
                    event.ip_address,
                    event.path,
                    event.user_agent,
                ),
            )

        connection.commit()


def _load_visit_events_from_postgres() -> list[VisitEvent]:
    with _connect_postgres() as connection:
        _ensure_postgres_page_visits_table(connection)

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT visited_at, ip_address, path, user_agent
                FROM page_visits
                ORDER BY visited_at, id
                """
            )
            rows = cursor.fetchall()

    return [
        VisitEvent(
            visited_at=_format_visit_timestamp(visited_at),
            ip_address=_coerce_visit_text(
                ip_address,
                max_length=_MAX_IP_ADDRESS_LENGTH,
            ),
            path=_coerce_visit_text(
                path,
                max_length=_MAX_PATH_LENGTH,
            ),
            user_agent=_coerce_visit_text(
                user_agent,
                max_length=_MAX_USER_AGENT_LENGTH,
            ),
        )
        for visited_at, ip_address, path, user_agent in rows
    ]