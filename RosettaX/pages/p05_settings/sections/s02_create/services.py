# -*- coding: utf-8 -*-

import json
import logging
from pathlib import Path

from ...utils import get_profile_path
from RosettaX.utils import directories


logger = logging.getLogger(__name__)


def create_profile(filename: str) -> str:
    """
    Create a new profile by copying the default profile.

    Parameters
    ----------
    filename:
        Profile name or filename.

    Returns
    -------
    str
        Status message.
    """
    profile_name = normalize_profile_name(
        filename,
    )

    source_path = Path(
        directories.default_profile,
    )

    destination_path = get_profile_path(
        profile_name,
    )

    logger.debug(
        "create_profile called with profile_name=%r source_path=%r destination_path=%r",
        profile_name,
        str(source_path),
        str(destination_path),
    )

    if not source_path.exists():
        logger.error(
            "Default profile does not exist at source_path=%r",
            str(source_path),
        )

        return f"Default profile not found: {source_path}"

    if destination_path.exists():
        logger.debug(
            "Profile already exists at destination_path=%r",
            str(destination_path),
        )

        return f"Profile '{destination_path.name}' already exists."

    try:
        destination_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with source_path.open("r", encoding="utf-8") as source_handle:
            default_profile_data = json.load(
                source_handle,
            )

        with destination_path.open("w", encoding="utf-8") as destination_handle:
            json.dump(
                default_profile_data,
                destination_handle,
                indent=4,
            )

        logger.debug(
            "Created profile destination_path=%r",
            str(destination_path),
        )

        return f"Profile '{destination_path.name}' created successfully."

    except Exception as exception:
        logger.exception(
            "Failed to create profile profile_name=%r source_path=%r destination_path=%r",
            profile_name,
            str(source_path),
            str(destination_path),
        )

        return f"{type(exception).__name__}: {exception}"


def normalize_profile_name(filename: str) -> str:
    """
    Normalize a profile name before path resolution.

    Parameters
    ----------
    filename:
        Raw profile name.

    Returns
    -------
    str
        Normalized profile name.

    Raises
    ------
    ValueError
        If the profile name is empty.
    """
    profile_name = str(
        filename or "",
    ).strip()

    if not profile_name:
        raise ValueError("Profile name cannot be empty.")

    if profile_name.endswith(".json"):
        return profile_name

    return f"{profile_name}.json"