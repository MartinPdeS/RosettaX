# -*- coding: utf-8 -*-

import importlib
import inspect
import logging
import pkgutil
from typing import Any


logger = logging.getLogger(__name__)


PEAK_SCRIPT_PACKAGE_NAME = "RosettaX.peak_script"


def load_peak_scripts() -> list[Any]:
    """
    Load the shared peak scripts used by the scattering peak section.

    A valid script class is any concrete class in RosettaX.peak_script that has:
    - process_name
    - get_process_option
    - get_required_detector_channels
    - build_controls

    This intentionally avoids a fluorescence specific script folder.
    """
    try:
        package = importlib.import_module(
            PEAK_SCRIPT_PACKAGE_NAME,
        )
    except Exception:
        logger.exception(
            "Failed to import shared peak script package %r.",
            PEAK_SCRIPT_PACKAGE_NAME,
        )
        return []

    scripts: list[Any] = []

    for module_info in pkgutil.iter_modules(package.__path__):
        module_name = module_info.name

        if module_name.startswith("_"):
            continue

        if module_name in {"base", "__init__"}:
            continue

        full_module_name = f"{PEAK_SCRIPT_PACKAGE_NAME}.{module_name}"

        try:
            module = importlib.import_module(
                full_module_name,
            )
        except Exception:
            logger.exception(
                "Failed to import shared peak script module %r.",
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
        "Loaded %d shared peak scripts for fluorescence section: %r",
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


def build_script_map(
    scripts: list[Any],
) -> dict[str, Any]:
    """
    Build a script lookup by process name.
    """
    return {
        str(script.process_name): script
        for script in scripts
    }


def get_default_script_name(
    scripts: list[Any],
) -> str | None:
    """
    Return the first available script name.
    """
    if not scripts:
        return None

    return str(scripts[0].process_name)