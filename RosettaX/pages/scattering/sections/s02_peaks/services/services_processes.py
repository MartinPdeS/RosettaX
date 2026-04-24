# -*- coding: utf-8 -*-

from typing import Any
import logging

from RosettaX.peak_script import build_peak_process_options
from RosettaX.peak_script import get_peak_process_instances
from RosettaX.peak_script import get_process_instance
from RosettaX.peak_script import resolve_process_name


logger = logging.getLogger(__name__)


def get_peak_processes() -> list[Any]:
    """
    Return dynamically discovered peak process instances.
    """
    return get_peak_process_instances()


def get_process_instance_for_name(
    *,
    process_name: Any,
) -> Any:
    """
    Return a discovered peak process instance for a selected process name.
    """
    return get_process_instance(
        process_name=process_name,
    )


def build_process_options() -> list[dict[str, str]]:
    """
    Build peak detection process dropdown options from discovered peak scripts.
    """
    options = build_peak_process_options()

    logger.debug(
        "Built peak process options option_count=%d options=%r",
        len(options),
        options,
    )

    return options


def build_process_visibility_styles(
    *,
    process_name: Any,
    process_container_ids: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Build visibility styles for every rendered process container.
    """
    resolved_process_name = resolve_process_name(process_name)
    styles: list[dict[str, Any]] = []

    for process_container_id in process_container_ids or []:
        process_name_from_id = process_container_id.get("process")

        process = get_process_instance(
            process_name=process_name_from_id,
        )

        if process is None:
            styles.append({"display": "none"})
            continue

        styles.append(
            process.build_visibility_style(
                selected_process_name=resolved_process_name,
            )
        )

    logger.debug(
        "Resolved process visibility styles for process_name=%r "
        "resolved_process_name=%r process_container_ids=%r styles=%r",
        process_name,
        resolved_process_name,
        process_container_ids,
        styles,
    )

    return styles


def resolve_graph_toggle_for_process(
    *,
    process_name: Any,
    current_graph_toggle_value: Any,
) -> Any:
    """
    Resolve graph visibility when the selected process changes.
    """
    resolved_process_name = resolve_process_name(process_name)
    process = get_process_instance(
        process_name=resolved_process_name,
    )

    if process is not None and process.should_force_graph_visible(
        selected_process_name=resolved_process_name,
    ):
        logger.debug(
            "Forcing graph visible for process_name=%r",
            resolved_process_name,
        )
        return ["enabled"]

    return current_graph_toggle_value