# -*- coding: utf-8 -*-

from dataclasses import asdict, dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class SettingsPageState:
    """
    Single source of truth for the settings page.

    This state stores the currently selected profile, the editable form values,
    and the latest status message.
    """

    selected_profile: Optional[str] = None
    form_data: Optional[dict[str, Any]] = None
    status_message: str = ""

    @classmethod
    def empty(cls) -> "SettingsPageState":
        """
        Build an empty settings page state.

        Returns
        -------
        SettingsPageState
            Empty settings page state.
        """
        return cls()

    @classmethod
    def from_dict(cls, payload: Optional[dict[str, Any]]) -> "SettingsPageState":
        """
        Build settings page state from a serialized dictionary.

        Unknown keys are ignored so old browser sessions do not crash after
        state schema changes.

        Parameters
        ----------
        payload:
            Serialized settings page state.

        Returns
        -------
        SettingsPageState
            Parsed settings page state.
        """
        if not payload:
            return cls.empty()

        valid_keys = set(cls.__dataclass_fields__.keys())

        clean_payload = {
            key: value
            for key, value in payload.items()
            if key in valid_keys
        }

        return cls(**clean_payload)

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize settings page state.

        Returns
        -------
        dict[str, Any]
            Dictionary suitable for Dash dcc.Store.
        """
        return asdict(self)

    def update(self, **changes: Any) -> "SettingsPageState":
        """
        Return a new state with selected fields changed.

        Parameters
        ----------
        **changes:
            Field values to update.

        Returns
        -------
        SettingsPageState
            Updated immutable state.

        Raises
        ------
        KeyError
            If an unknown state field is provided.
        """
        valid_keys = set(self.__dataclass_fields__.keys())
        unknown_keys = set(changes.keys()) - valid_keys

        if unknown_keys:
            unknown_keys_text = ", ".join(sorted(unknown_keys))
            raise KeyError(f"Unknown settings page state field(s): {unknown_keys_text}")

        current_payload = self.to_dict()
        current_payload.update(changes)

        return self.from_dict(current_payload)