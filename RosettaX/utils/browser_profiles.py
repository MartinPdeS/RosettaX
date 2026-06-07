# -*- coding: utf-8 -*-

import logging
from dataclasses import asdict, dataclass, field
from typing import Any, Optional

from RosettaX.utils import directories
from RosettaX.utils.paths import normalize_profile_filename
from RosettaX.utils.runtime_config import RuntimeConfig


logger = logging.getLogger(__name__)


BROWSER_PROFILES_STORE_ID = "browser-profiles-store"
DEFAULT_PROFILE_FILENAME = "default_profile.json"


def build_profile_label(profile_name: str) -> str:
    """
    Build the human readable label for one profile option.
    """
    normalized_profile_name = normalize_profile_filename(profile_name)

    if normalized_profile_name.endswith(".json"):
        return normalized_profile_name[:-5]

    return normalized_profile_name


def _sort_profile_names(profile_names: list[str]) -> list[str]:
    """
    Sort profile names with the default profile first.
    """
    return sorted(
        profile_names,
        key=lambda profile_name: (
            normalize_profile_filename(profile_name) != DEFAULT_PROFILE_FILENAME,
            build_profile_label(profile_name).lower(),
        ),
    )


@dataclass(frozen=True)
class BrowserProfileLibrary:
    """
    Browser-owned profile collection persisted in local Dash storage.
    """

    profiles: dict[str, dict[str, Any]] = field(default_factory=dict)
    selected_profile: Optional[str] = None

    @classmethod
    def from_seed_data(cls) -> "BrowserProfileLibrary":
        """
        Seed the browser profile library from the packaged disk profiles.
        """
        seeded_profiles: dict[str, dict[str, Any]] = {}

        try:
            profile_names = directories.list_profiles()
        except Exception:
            logger.exception("Failed to list packaged profiles while seeding browser storage.")
            profile_names = []

        for profile_name in profile_names:
            try:
                normalized_profile_name = normalize_profile_filename(profile_name)
                seeded_profiles[normalized_profile_name] = RuntimeConfig.from_profile_name(
                    profile_name,
                ).to_dict()

            except Exception:
                logger.exception(
                    "Failed to seed packaged profile into browser storage. profile_name=%r",
                    profile_name,
                )

        if DEFAULT_PROFILE_FILENAME not in seeded_profiles:
            seeded_profiles[DEFAULT_PROFILE_FILENAME] = RuntimeConfig.from_default_profile().to_dict()

        return cls(
            profiles=seeded_profiles,
            selected_profile=cls._resolve_selected_profile_name(
                selected_profile=None,
                profile_names=seeded_profiles.keys(),
            ),
        )

    @classmethod
    def from_dict(cls, payload: Any) -> "BrowserProfileLibrary":
        """
        Rebuild the browser profile library from a serialized Dash store payload.
        """
        if not isinstance(payload, dict):
            return cls.from_seed_data()

        raw_profiles = payload.get("profiles")
        sanitized_profiles: dict[str, dict[str, Any]] = {}

        if isinstance(raw_profiles, dict):
            for raw_profile_name, raw_profile_payload in raw_profiles.items():
                try:
                    normalized_profile_name = normalize_profile_filename(
                        str(raw_profile_name or "")
                    )
                    runtime_config = RuntimeConfig.from_dict(
                        raw_profile_payload if isinstance(raw_profile_payload, dict) else None
                    )
                    sanitized_profiles[normalized_profile_name] = runtime_config.to_dict()

                except Exception:
                    logger.exception(
                        "Ignoring invalid browser profile payload. raw_profile_name=%r",
                        raw_profile_name,
                    )

        if DEFAULT_PROFILE_FILENAME not in sanitized_profiles:
            sanitized_profiles[DEFAULT_PROFILE_FILENAME] = RuntimeConfig.from_default_profile().to_dict()

        return cls(
            profiles=sanitized_profiles,
            selected_profile=cls._resolve_selected_profile_name(
                selected_profile=payload.get("selected_profile"),
                profile_names=sanitized_profiles.keys(),
            ),
        )

    @staticmethod
    def _resolve_selected_profile_name(
        *,
        selected_profile: Any,
        profile_names: Any,
    ) -> Optional[str]:
        """
        Resolve the active profile name against the available profiles.
        """
        normalized_profile_names = [
            normalize_profile_filename(profile_name)
            for profile_name in profile_names
            if str(profile_name or "").strip()
        ]

        if not normalized_profile_names:
            return None

        if selected_profile is not None:
            try:
                normalized_selected_profile = normalize_profile_filename(selected_profile)

                if normalized_selected_profile in normalized_profile_names:
                    return normalized_selected_profile

            except Exception:
                logger.exception(
                    "Ignoring invalid selected browser profile name. selected_profile=%r",
                    selected_profile,
                )

        if DEFAULT_PROFILE_FILENAME in normalized_profile_names:
            return DEFAULT_PROFILE_FILENAME

        return _sort_profile_names(normalized_profile_names)[0]

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize the browser profile library for Dash storage.
        """
        return asdict(self)

    def build_options(self) -> list[dict[str, str]]:
        """
        Build dropdown options for the available browser profiles.
        """
        return [
            {
                "label": build_profile_label(profile_name),
                "value": profile_name,
            }
            for profile_name in _sort_profile_names(list(self.profiles.keys()))
        ]

    def get_profile_payload(
        self,
        profile_name: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """
        Return one stored profile payload.
        """
        resolved_profile_name = profile_name or self.selected_profile

        if not resolved_profile_name:
            return None

        normalized_profile_name = normalize_profile_filename(resolved_profile_name)
        payload = self.profiles.get(normalized_profile_name)

        if payload is None:
            return None

        return RuntimeConfig.from_dict(payload).to_dict()

    def with_selected_profile(
        self,
        profile_name: Optional[str],
    ) -> "BrowserProfileLibrary":
        """
        Return a copy with the selected profile updated.
        """
        return BrowserProfileLibrary(
            profiles=dict(self.profiles),
            selected_profile=self._resolve_selected_profile_name(
                selected_profile=profile_name,
                profile_names=self.profiles.keys(),
            ),
        )

    def with_saved_profile(
        self,
        *,
        profile_name: str,
        profile_payload: dict[str, Any],
        select_profile: bool,
    ) -> "BrowserProfileLibrary":
        """
        Return a copy with one profile saved into browser storage.
        """
        normalized_profile_name = normalize_profile_filename(profile_name)
        validated_profile_payload = RuntimeConfig.from_dict(profile_payload).to_dict()
        next_profiles = dict(self.profiles)
        next_profiles[normalized_profile_name] = validated_profile_payload

        return BrowserProfileLibrary(
            profiles=next_profiles,
            selected_profile=self._resolve_selected_profile_name(
                selected_profile=(
                    normalized_profile_name if select_profile else self.selected_profile
                ),
                profile_names=next_profiles.keys(),
            ),
        )

    def create_profile(
        self,
        *,
        profile_name: str,
        source_profile_name: Optional[str] = None,
        select_profile: bool,
    ) -> "BrowserProfileLibrary":
        """
        Create one new profile by copying an existing profile payload.
        """
        normalized_profile_name = normalize_profile_filename(profile_name)

        if normalized_profile_name in self.profiles:
            raise ValueError(f"Profile '{normalized_profile_name}' already exists.")

        source_payload = self.get_profile_payload(source_profile_name)

        if source_payload is None:
            source_payload = self.get_profile_payload(DEFAULT_PROFILE_FILENAME)

        if source_payload is None:
            source_payload = RuntimeConfig.from_default_profile().to_dict()

        return self.with_saved_profile(
            profile_name=normalized_profile_name,
            profile_payload=source_payload,
            select_profile=select_profile,
        )

    def delete_profile(
        self,
        *,
        profile_name: str,
    ) -> "BrowserProfileLibrary":
        """
        Delete one profile from browser storage.
        """
        normalized_profile_name = normalize_profile_filename(profile_name)

        if normalized_profile_name == DEFAULT_PROFILE_FILENAME:
            raise ValueError("Cannot delete default profile. Please choose a different profile.")

        if normalized_profile_name not in self.profiles:
            raise FileNotFoundError(f"Profile '{normalized_profile_name}' not found.")

        next_profiles = dict(self.profiles)
        del next_profiles[normalized_profile_name]

        next_selected_profile = self.selected_profile

        if next_selected_profile == normalized_profile_name:
            next_selected_profile = None

        return BrowserProfileLibrary(
            profiles=next_profiles,
            selected_profile=self._resolve_selected_profile_name(
                selected_profile=next_selected_profile,
                profile_names=next_profiles.keys(),
            ),
        )