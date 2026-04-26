# -*- coding: utf-8 -*-

import logging
from pathlib import Path

from ...utils import normalize_profile_filename
from RosettaX.utils import directories


logger = logging.getLogger(__name__)


DEFAULT_PROFILE_FILENAME = "default_profile.json"


def delete_profile(filename: str) -> str:
    """
    Delete a profile from the profiles directory.

    Parameters
    ----------
    filename:
        Profile name or filename.

    Returns
    -------
    str
        Status message.
    """
    try:
        normalized_filename = normalize_profile_filename(
            filename,
        )

        if normalized_filename == DEFAULT_PROFILE_FILENAME:
            return "Cannot delete default profile. Please choose a different profile."

        profile_path = Path(directories.profiles) / normalized_filename

        logger.debug(
            "delete_profile called with filename=%r normalized_filename=%r profile_path=%r",
            filename,
            normalized_filename,
            str(profile_path),
        )

        if not profile_path.exists():
            return f"Profile '{normalized_filename}' not found."

        if not profile_path.is_file():
            return f"Profile '{normalized_filename}' is not a file."

        profile_path.unlink()

        logger.debug(
            "Deleted profile profile_path=%r",
            str(profile_path),
        )

        return f"Profile '{normalized_filename}' deleted successfully."

    except Exception as exception:
        logger.exception(
            "Failed to delete profile filename=%r",
            filename,
        )

        return f"{type(exception).__name__}: {exception}"