# -*- coding: utf-8 -*-
from importlib import import_module
from pathlib import Path
from types import ModuleType
from typing import Any
import logging

from .base import BasePeakProcess
from .base import PeakProcessResult


logger = logging.getLogger(__name__)


_EXCLUDED_MODULE_NAMES = {
    "__init__",
    "base",
}


def discover_peak_process_modules() -> list[ModuleType]:
    """
    Discover and import peak process modules from this package.
    """
    package_directory = Path(__file__).resolve().parent
    package_name = __name__

    process_modules: list[ModuleType] = []

    for module_path in sorted(package_directory.glob("*.py")):
        module_name = module_path.stem

        if module_name in _EXCLUDED_MODULE_NAMES:
            continue

        fully_qualified_module_name = f"{package_name}.{module_name}"

        try:
            module = import_module(fully_qualified_module_name)
        except Exception:
            logger.exception(
                "Failed to import peak process module=%r path=%r",
                fully_qualified_module_name,
                str(module_path),
            )
            continue

        if get_process_instance_from_module(module) is None:
            logger.debug(
                "Ignoring module=%r because no valid peak process instance was found.",
                fully_qualified_module_name,
            )
            continue

        process_modules.append(module)

    logger.debug(
        "Discovered peak process modules=%r",
        [
            module.__name__
            for module in process_modules
        ],
    )

    return process_modules


def get_process_instance_from_module(module: ModuleType) -> BasePeakProcess | None:
    """
    Return the process instance defined by a module.

    Preferred form:
        PROCESS = MyProcess()

    Fallback:
        first object in the module that is an instance of BasePeakProcess.
    """
    process = getattr(module, "PROCESS", None)

    if isinstance(process, BasePeakProcess):
        if process_is_valid(process):
            return process
        return None

    for value in vars(module).values():
        if isinstance(value, BasePeakProcess) and process_is_valid(value):
            return value

    return None


def process_is_valid(process: BasePeakProcess) -> bool:
    """
    Validate a peak process instance.
    """
    if not isinstance(process.process_name, str) or not process.process_name.strip():
        return False

    if not isinstance(process.graph_type, str) or not process.graph_type.strip():
        return False

    if not callable(getattr(process, "build_controls", None)):
        return False

    if not callable(getattr(process, "get_required_detector_channels", None)):
        return False

    return True


def get_peak_process_instances() -> list[BasePeakProcess]:
    """
    Return discovered peak process instances.

    Discovery is intentionally done on every call during development.
    """
    process_instances: list[BasePeakProcess] = []

    for module in discover_peak_process_modules():
        process = get_process_instance_from_module(module)

        if process is None:
            continue

        process_instances.append(process)

    process_instances.sort(
        key=lambda process: (
            int(process.sort_order),
            process.process_name,
        )
    )

    logger.debug(
        "Discovered peak process instances=%r",
        [
            process.process_name
            for process in process_instances
        ],
    )

    return process_instances


def get_default_process_name() -> str:
    """
    Resolve the default peak process name.
    """
    process_instances = get_peak_process_instances()

    for process in process_instances:
        if process.process_name == "1D manual click":
            return process.process_name

    if process_instances:
        return process_instances[0].process_name

    return ""


def build_peak_process_options() -> list[dict[str, str]]:
    """
    Build peak process dropdown options.
    """
    return [
        process.get_process_option()
        for process in get_peak_process_instances()
    ]


def resolve_process_name(process_name: Any) -> str:
    """
    Resolve a selected process name to a discovered process name.
    """
    process_name_string = "" if process_name is None else str(process_name).strip()

    valid_process_names = {
        process.process_name
        for process in get_peak_process_instances()
    }

    if process_name_string in valid_process_names:
        return process_name_string

    return get_default_process_name()


def get_process_instance(
    *,
    process_name: Any,
) -> BasePeakProcess | None:
    """
    Return the process instance matching process_name.
    """
    resolved_process_name = resolve_process_name(process_name)

    for process in get_peak_process_instances():
        if process.process_name == resolved_process_name:
            return process

    return None


def resolve_detector_channel_state(
    *,
    detector_dropdown_ids: list[dict[str, Any]],
    detector_dropdown_values: list[Any],
    process_name: Any,
) -> dict[str, Any]:
    """
    Resolve detector dropdown values for the selected peak process.
    """
    resolved_process_name = resolve_process_name(process_name)

    channel_state: dict[str, Any] = {}

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

        channel_state[str(channel_name)] = detector_dropdown_value

    return channel_state


DEFAULT_PROCESS_NAME = get_default_process_name()
PEAK_PROCESS_MODULES = discover_peak_process_modules()