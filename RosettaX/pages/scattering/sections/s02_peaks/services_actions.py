# -*- coding: utf-8 -*-

from typing import Any, Optional
import logging

from RosettaX.utils import casting
from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.peak_script import get_process_instance
from RosettaX.peak_script import resolve_process_name

from .services_common import clean_optional_string
from .services_common import resolve_mie_model
from .services_graphs import build_empty_peak_lines_payload
from .services_detectors import resolve_detector_channels_for_process
from .services_tables import write_measured_positions_into_table


def resolve_manual_peak_click(
    *,
    click_data: Any,
    process_name: Any,
    uploaded_fcs_path: Any,
    detector_dropdown_ids: list[dict[str, Any]],
    detector_dropdown_values: list[Any],
    peak_lines_payload: Any,
    table_data: Optional[list[dict[str, Any]]],
    mie_model: Any,
    logger: logging.Logger,
) -> tuple[Any, dict[str, list[Any]], str]:
    """
    Resolve a manual graph click into calibration table data and peak markers.
    """
    resolved_process_name = resolve_process_name(process_name)
    process = get_process_instance(
        process_name=resolved_process_name,
    )

    if process is None or not process.supports_manual_click:
        return None, build_empty_peak_lines_payload(), ""

    detector_channels = resolve_detector_channels_for_process(
        detector_dropdown_ids=detector_dropdown_ids,
        detector_dropdown_values=detector_dropdown_values,
        process_name=resolved_process_name,
    )

    if not context_is_valid_for_process(
        process=process,
        uploaded_fcs_path=uploaded_fcs_path,
        detector_channels=detector_channels,
    ):
        return None, build_empty_peak_lines_payload(), (
            "Upload a file and select the required detector channel(s) first."
        )

    manual_result = process.add_clicked_peak(
        click_data=click_data,
        existing_peak_lines_payload=peak_lines_payload,
    )

    if manual_result is None:
        return None, build_empty_peak_lines_payload(), ""

    updated_table_data = write_measured_positions_into_table(
        table_data=table_data,
        peak_positions=manual_result.peak_positions,
        mie_model=resolve_mie_model(mie_model),
        logger=logger,
    )

    return (
        updated_table_data,
        manual_result.peak_lines_payload,
        manual_result.status,
    )


def resolve_process_action(
    *,
    triggered_action_id: Any,
    backend: Any,
    process_name: Any,
    uploaded_fcs_path: Any,
    detector_dropdown_ids: list[dict[str, Any]],
    detector_dropdown_values: list[Any],
    peak_count: Any,
    max_events_for_plots: Any,
    table_data: Optional[list[dict[str, Any]]],
    mie_model: Any,
    runtime_config_data: Any,
    logger: logging.Logger,
) -> tuple[Any, dict[str, list[Any]], str, str]:
    """
    Resolve a process action button click.

    Returns
    -------
    tuple
        table_data, peak_lines_payload, status, target_process_name
    """
    if not isinstance(triggered_action_id, dict):
        return None, build_empty_peak_lines_payload(), "", ""

    target_process_name = triggered_action_id.get("process")
    action_name = triggered_action_id.get("action")

    process = get_process_instance(
        process_name=target_process_name,
    )

    if process is None:
        return None, build_empty_peak_lines_payload(), "", ""

    detector_channels = resolve_detector_channels_for_process(
        detector_dropdown_ids=detector_dropdown_ids,
        detector_dropdown_values=detector_dropdown_values,
        process_name=target_process_name,
    )

    logger.debug(
        "Resolving process action target_process_name=%r action_name=%r "
        "detector_channels=%r selected_process_name=%r",
        target_process_name,
        action_name,
        detector_channels,
        process_name,
    )

    if action_name == "clear" and process.supports_clear:
        clear_result = process.clear_peaks()

        updated_table_data = write_measured_positions_into_table(
            table_data=table_data,
            peak_positions=clear_result.peak_positions,
            mie_model=resolve_mie_model(mie_model),
            logger=logger,
        )

        return (
            updated_table_data,
            clear_result.peak_lines_payload,
            clear_result.status,
            process.process_name,
        )

    if action_name == "run" and process.supports_automatic_action:
        if not context_is_valid_for_process(
            process=process,
            uploaded_fcs_path=uploaded_fcs_path,
            detector_channels=detector_channels,
        ):
            return (
                None,
                build_empty_peak_lines_payload(),
                "Upload a file and select the required detector channel(s) first.",
                process.process_name,
            )

        runtime_config = RuntimeConfig.from_dict(
            runtime_config_data if isinstance(runtime_config_data, dict) else None
        )

        resolved_peak_count = casting.as_int(
            peak_count,
            default=runtime_config.get_int(
                "calibration.peak_count",
                default=3,
            ),
            min_value=1,
            max_value=50,
        )

        resolved_max_events = casting.as_int(
            max_events_for_plots,
            default=runtime_config.get_int(
                "calibration.max_events_for_analysis",
                default=10000,
            ),
            min_value=1,
            max_value=5_000_000,
        )

        automatic_result = process.run_automatic_action(
            backend=backend,
            detector_channels=detector_channels,
            peak_count=resolved_peak_count,
            max_events_for_analysis=resolved_max_events,
        )

        if automatic_result is None:
            return None, build_empty_peak_lines_payload(), "", process.process_name

        updated_table_data = write_measured_positions_into_table(
            table_data=table_data,
            peak_positions=automatic_result.peak_positions,
            mie_model=resolve_mie_model(mie_model),
            logger=logger,
        )

        return (
            updated_table_data,
            automatic_result.peak_lines_payload,
            automatic_result.status,
            process.process_name,
        )

    return None, build_empty_peak_lines_payload(), "", process.process_name


def context_is_valid_for_process(
    *,
    process: Any,
    uploaded_fcs_path: Any,
    detector_channels: dict[str, Any],
) -> bool:
    """
    Validate file and detector context for a process.
    """
    if not clean_optional_string(uploaded_fcs_path):
        return False

    for channel_name in process.get_required_detector_channels():
        if not clean_optional_string(detector_channels.get(channel_name)):
            return False

    return True


def build_status_children(
    *,
    status_component_ids: list[dict[str, Any]],
    target_process_name: str,
    status: str,
) -> list[Any]:
    """
    Build children outputs for all process status components.
    """
    children: list[Any] = []

    for status_component_id in status_component_ids or []:
        if status_component_id.get("process") == target_process_name:
            children.append(status)
        else:
            children.append("")

    return children