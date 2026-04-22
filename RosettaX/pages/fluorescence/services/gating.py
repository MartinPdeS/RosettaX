# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any, Optional

import dash

from RosettaX.utils import casting


@dataclass(frozen=True)
class ParsedScatteringLimits:
    max_events: int
    nbins: int


def is_switch_enabled(switch_value: Any) -> bool:
    return isinstance(switch_value, list) and ("enabled" in switch_value)


def clean_channel_name(scattering_channel: Any) -> str:
    if scattering_channel is None:
        return ""

    scattering_channel_clean = str(scattering_channel).strip()

    if scattering_channel_clean.lower() == "none":
        return ""

    return scattering_channel_clean


def extract_stored_threshold(scattering_threshold_store_data: Any) -> Optional[float]:
    if not isinstance(scattering_threshold_store_data, dict):
        return None

    return casting._as_float(scattering_threshold_store_data.get("threshold"))


def build_threshold_store_payload(
    *,
    scattering_channel: str,
    threshold_value: float,
    nbins: int,
) -> dict[str, Any]:
    return {
        "scattering_channel": scattering_channel or None,
        "threshold": float(threshold_value),
        "nbins": int(nbins),
    }


def parse_limits(
    *,
    max_events_for_plots: Any,
    scattering_nbins: Any,
    default_max_events: int,
    default_nbins: int,
) -> ParsedScatteringLimits:
    max_events = casting._as_int(
        max_events_for_plots if max_events_for_plots is not None else default_max_events,
        default=default_max_events,
        min_value=1_000,
        max_value=5_000_000,
    )

    nbins = casting._as_int(
        scattering_nbins,
        default=default_nbins,
        min_value=10,
        max_value=5000,
    )

    return ParsedScatteringLimits(
        max_events=max_events,
        nbins=nbins,
    )


def resolve_threshold(
    *,
    page_backend: Any,
    must_estimate: bool,
    scattering_channel: str,
    nbins: int,
    max_events: int,
    manual_thr: Optional[float],
    store_thr: Optional[float],
    logger: Any,
) -> tuple[float, Any]:
    logger.debug(
        "resolve_threshold called with must_estimate=%r scattering_channel=%r nbins=%r "
        "max_events=%r manual_thr=%r store_thr=%r",
        must_estimate,
        scattering_channel,
        nbins,
        max_events,
        manual_thr,
        store_thr,
    )

    if must_estimate:
        if page_backend is None:
            logger.debug("resolve_threshold cannot estimate because backend is None.")
            return 0.0, dash.no_update

        if not scattering_channel:
            logger.debug("resolve_threshold cannot estimate because scattering_channel is empty.")
            return 0.0, dash.no_update

        try:
            response = page_backend.process_scattering(
                {
                    "operation": "estimate_scattering_threshold",
                    "column": scattering_channel,
                    "nbins": int(nbins),
                    "number_of_points": int(max_events),
                }
            )
        except Exception:
            logger.exception(
                "Backend threshold estimation failed for scattering_channel=%r nbins=%r max_events=%r",
                scattering_channel,
                nbins,
                max_events,
            )
            raise

        threshold_value = casting._as_float(response.get("threshold")) or 0.0

        logger.debug(
            "resolve_threshold estimated threshold_value=%r from response=%r",
            threshold_value,
            response,
        )
        return float(threshold_value), f"{float(threshold_value):.6g}"

    if manual_thr is not None:
        logger.debug("resolve_threshold using manual threshold=%r", manual_thr)
        return float(manual_thr), dash.no_update

    if store_thr is not None:
        logger.debug("resolve_threshold using stored threshold=%r", store_thr)
        return float(store_thr), dash.no_update

    logger.debug("resolve_threshold fell back to default threshold=0.0")
    return 0.0, dash.no_update