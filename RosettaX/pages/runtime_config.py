from dataclasses import dataclass, field
from typing import Optional


@dataclass
class UiFlags:
    debug: bool = False

    # Fluorescence calibration page, visibility
    fluorescence_show_scattering_controls: bool = True
    fluorescence_show_threshold_controls: bool = True
    fluorescence_show_fluorescence_controls: bool = True


    # Fluorescence calibration page, debug outputs
    fluorescence_debug_scattering: bool = False
    fluorescence_debug_fluorescence: bool = False
    fluorescence_debug_load: bool = False

    _explicit: set[str] = field(default_factory=set, init=False, repr=False)

    def mark_explicit(self, field_name: str) -> None:
        self._explicit.add(field_name)

    def is_explicit(self, field_name: str) -> bool:
        return field_name in self._explicit

    def apply_policy(self) -> None:
        """
        Apply global policy based on `debug`, without overriding values explicitly set by CLI.
        """
        if self.debug:
            if not self.is_explicit("fluorescence_show_scattering_controls"):
                self.fluorescence_show_scattering_controls = True
            if not self.is_explicit("fluorescence_show_threshold_controls"):
                self.fluorescence_show_threshold_controls = True

            if not self.is_explicit("fluorescence_debug_scattering"):
                self.fluorescence_debug_scattering = True
            if not self.is_explicit("fluorescence_debug_fluorescence"):
                self.fluorescence_debug_fluorescence = True
        else:
            if not self.is_explicit("fluorescence_show_scattering_controls"):
                self.fluorescence_show_scattering_controls = False
            if not self.is_explicit("fluorescence_show_threshold_controls"):
                self.fluorescence_show_threshold_controls = False

            if not self.is_explicit("fluorescence_debug_scattering"):
                self.fluorescence_debug_scattering = False
            if not self.is_explicit("fluorescence_debug_fluorescence"):
                self.fluorescence_debug_fluorescence = False


_ui_flags: Optional[UiFlags] = None


def get_ui_flags() -> UiFlags:
    global _ui_flags
    if _ui_flags is None:
        _ui_flags = UiFlags()
        _ui_flags.apply_policy()
    return _ui_flags