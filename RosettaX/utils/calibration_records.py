# -*- coding: utf-8 -*-
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_fluorescence_calibration_record(
    *,
    name: str,
    source_file: Optional[str],
    source_channel: Optional[str],
    gating_channel: Optional[str],
    gating_threshold: Optional[float],
    slope: float,
    intercept: float,
    r_squared: Optional[float],
    reference_points: list[dict[str, Any]],
    notes: str = "",
) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "calibration_type": "fluorescence",
        "name": str(name).strip(),
        "created_at": _utc_now_iso(),
        "source_file": source_file,
        "source_channel": source_channel,
        "gating_channel": gating_channel,
        "gating_threshold": gating_threshold,
        "fit_model": "linear",
        "fit_metrics": {
            "r_squared": r_squared,
            "point_count": len(reference_points),
        },
        "parameters": {
            "slope": float(slope),
            "intercept": float(intercept),
        },
        "reference_points": reference_points,
        "export_notes": str(notes),
        "payload": {
            "slope": float(slope),
            "intercept": float(intercept),
        },
    }


def build_scattering_calibration_record(
    *,
    name: str,
    source_file: Optional[str],
    source_channel: Optional[str],
    fit_model: str,
    parameters: dict[str, Any],
    fit_metrics: Optional[dict[str, Any]] = None,
    reference_points: Optional[list[dict[str, Any]]] = None,
    notes: str = "",
) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "calibration_type": "scattering",
        "name": str(name).strip(),
        "created_at": _utc_now_iso(),
        "source_file": source_file,
        "source_channel": source_channel,
        "fit_model": str(fit_model),
        "fit_metrics": fit_metrics or {},
        "parameters": parameters,
        "reference_points": reference_points or [],
        "export_notes": str(notes),
        "payload": parameters,
    }


def extract_calibration_summary(record: dict[str, Any]) -> dict[str, Any]:
    nested_payload = record.get("payload", {}) or {}

    fit_metrics = nested_payload.get("fit_metrics", {}) or {}
    parameters = nested_payload.get("parameters", {}) or {}

    calibration_type = (
        nested_payload.get("calibration_type")
        or record.get("calibration_type")
        or record.get("kind")
        or "unknown"
    )

    calibration_name = (
        record.get("name")
        or nested_payload.get("name")
        or "Unnamed calibration"
    )

    created_at = (
        record.get("created_at")
        or nested_payload.get("created_at")
    )

    source_file = nested_payload.get("source_file")
    source_channel = nested_payload.get("source_channel")
    gating_channel = nested_payload.get("gating_channel")
    gating_threshold = nested_payload.get("gating_threshold")
    fit_model = nested_payload.get("fit_model")

    r_squared = fit_metrics.get("r_squared")
    point_count = fit_metrics.get("point_count")

    if point_count is None:
        reference_points = nested_payload.get("reference_points", []) or []
        point_count = len(reference_points) if isinstance(reference_points, list) else None

    if not parameters:
        legacy_payload = nested_payload.get("payload", {}) or {}
        parameters = {
            key: value
            for key, value in {
                "slope": legacy_payload.get("slope"),
                "intercept": legacy_payload.get("intercept"),
                "prefactor": legacy_payload.get("prefactor"),
            }.items()
            if value is not None
        }

    notes = nested_payload.get("export_notes", "")

    return {
        "schema_version": nested_payload.get("schema_version", record.get("schema")),
        "calibration_type": calibration_type,
        "name": calibration_name,
        "created_at": created_at,
        "source_file": source_file,
        "source_channel": source_channel,
        "gating_channel": gating_channel,
        "gating_threshold": gating_threshold,
        "fit_model": fit_model,
        "r_squared": r_squared,
        "point_count": point_count,
        "parameters": parameters,
        "notes": notes,
    }

def load_calibration_record(path: Path) -> dict[str, Any]:
    import json

    return json.loads(Path(path).read_text(encoding="utf-8"))