# -*- coding: utf-8 -*-

import importlib
import inspect
import logging
import pkgutil
from typing import Any


logger = logging.getLogger(__name__)


PEAK_SCRIPT_PACKAGE_NAME = "RosettaX.workflow.peak.scripts"
DEFAULT_PROCESS_NAME = "automatic_1d"


def clean_optional_string(value: Any) -> str:
    """
    Normalize an optional string value.

    Parameters
    ----------
    value:
        Raw value.

    Returns
    -------
    str
        Cleaned string value.
    """
    if value is None:
        return ""

    cleaned_value = str(value).strip()

    if not cleaned_value:
        return ""

    if cleaned_value.lower() == "none":
        return ""

    return cleaned_value


def load_peak_scripts() -> list[Any]:
    """
    Load all shared peak scripts.

    A valid script class is any concrete class in RosettaX.peak_script that has:
    - process_name
    - get_process_option
    - get_required_detector_channels
    - build_controls

    Returns
    -------
    list[Any]
        Instantiated peak script objects.
    """
    try:
        package = importlib.import_module(
            PEAK_SCRIPT_PACKAGE_NAME,
        )

    except Exception:
        logger.exception(
            "Failed to import peak script package %r.",
            PEAK_SCRIPT_PACKAGE_NAME,
        )

        return []

    scripts: list[Any] = []

    for module_info in pkgutil.iter_modules(package.__path__):
        module_name = module_info.name

        if module_name.startswith("_"):
            continue

        if module_name in {"base", "__init__", "registry"}:
            continue

        full_module_name = f"{PEAK_SCRIPT_PACKAGE_NAME}.{module_name}"

        try:
            module = importlib.import_module(
                full_module_name,
            )

        except Exception:
            logger.exception(
                "Failed to import peak script module %r.",
                full_module_name,
            )

            continue

        script_class = find_script_class_in_module(
            module=module,
        )

        if script_class is None:
            logger.debug(
                "No valid peak script class found in module %r.",
                full_module_name,
            )

            continue

        try:
            scripts.append(
                script_class(),
            )

        except Exception:
            logger.exception(
                "Failed to instantiate peak script class %r from module %r.",
                script_class,
                full_module_name,
            )

    logger.debug(
        "Loaded %d peak scripts: %r",
        len(scripts),
        [
            getattr(script, "process_name", None)
            for script in scripts
        ],
    )

    return scripts


def find_script_class_in_module(
    *,
    module: Any,
) -> type | None:
    """
    Find the first concrete peak script class in a module.

    Parameters
    ----------
    module:
        Imported Python module.

    Returns
    -------
    type | None
        Peak script class if one is found.
    """
    candidates: list[type] = []

    for value in vars(module).values():
        if not inspect.isclass(value):
            continue

        if value.__module__ != module.__name__:
            continue

        if not hasattr(value, "process_name"):
            continue

        if not hasattr(value, "get_process_option"):
            continue

        if not hasattr(value, "get_required_detector_channels"):
            continue

        if not hasattr(value, "build_controls"):
            continue

        candidates.append(value)

    if not candidates:
        return None

    if len(candidates) > 1:
        logger.warning(
            "Multiple peak script classes found in module %r. Using %r.",
            module.__name__,
            candidates[0].__name__,
        )

    return candidates[0]


def get_peak_process_instances() -> list[Any]:
    """
    Return dynamically discovered peak process instances.

    Returns
    -------
    list[Any]
        Instantiated peak process objects.
    """
    return load_peak_scripts()


def build_script_map(
    scripts: list[Any],
) -> dict[str, Any]:
    """
    Build a script lookup by process name.

    Parameters
    ----------
    scripts:
        Peak script instances.

    Returns
    -------
    dict[str, Any]
        Mapping from process name to script instance.
    """
    return {
        str(script.process_name): script
        for script in scripts
    }


def resolve_process_name(process_name: Any) -> str:
    """
    Resolve a process name to a valid non empty string.

    Parameters
    ----------
    process_name:
        Raw process name.

    Returns
    -------
    str
        Resolved process name.
    """
    process_name_clean = clean_optional_string(
        process_name,
    )

    if process_name_clean:
        return process_name_clean

    return DEFAULT_PROCESS_NAME


def get_process_instance(
    *,
    process_name: Any,
) -> Any:
    """
    Return a discovered peak process instance for a selected process name.

    Parameters
    ----------
    process_name:
        Selected process name.

    Returns
    -------
    Any
        Matching peak process instance, or None.
    """
    resolved_process_name = resolve_process_name(
        process_name,
    )

    scripts = get_peak_process_instances()

    for script in scripts:
        if getattr(script, "process_name", None) == resolved_process_name:
            return script

    for script in scripts:
        option = script.get_process_option()

        if option.get("value") == resolved_process_name:
            return script

    return None


def build_peak_process_options() -> list[dict[str, str]]:
    """
    Build peak process dropdown options from discovered peak scripts.

    Returns
    -------
    list[dict[str, str]]
        Dropdown options.
    """
    return [
        script.get_process_option()
        for script in get_peak_process_instances()
    ]


def get_default_script_name(
    scripts: list[Any],
) -> str | None:
    """
    Return the first available script name.

    Parameters
    ----------
    scripts:
        Peak script instances.

    Returns
    -------
    str | None
        Default script name.
    """
    if not scripts:
        return None

    return str(scripts[0].process_name)


def resolve_detector_channel_state(
    *,
    detector_dropdown_ids: list[dict[str, Any]],
    detector_dropdown_values: list[Any],
    process_name: Any,
) -> dict[str, Any]:
    """
    Resolve detector dropdown values for one selected peak process.

    Parameters
    ----------
    detector_dropdown_ids:
        Pattern matched detector dropdown IDs.

    detector_dropdown_values:
        Pattern matched detector dropdown values.

    process_name:
        Selected peak process name.

    Returns
    -------
    dict[str, Any]
        Mapping from required process channel name to selected detector column.
    """
    resolved_process_name = resolve_process_name(
        process_name,
    )

    detector_channel_state: dict[str, Any] = {}

    for detector_dropdown_id, detector_dropdown_value in zip(
        detector_dropdown_ids or [],
        detector_dropdown_values or [],
        strict=False,
    ):
        if not isinstance(detector_dropdown_id, dict):
            continue

        if detector_dropdown_id.get("process") != resolved_process_name:
            continue

        channel_name = detector_dropdown_id.get("channel")

        if not channel_name:
            continue

        detector_channel_state[str(channel_name)] = detector_dropdown_value

    return detector_channel_state