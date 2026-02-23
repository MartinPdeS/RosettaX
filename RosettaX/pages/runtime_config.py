from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FluorescenceConfig:
    # UI visibility
    show_scattering_controls: bool = True
    show_threshold_controls: bool = True
    show_fluorescence: bool = True
    show_beads: bool = True
    show_output: bool = True
    show_save: bool = True

    # Per section debug
    debug_scattering: bool = False
    debug_fluorescence: bool = False
    debug_load: bool = False
    debug_beads: bool = False
    debug_output: bool = False
    debug_save: bool = False


@dataclass
class RuntimeConfig:
    debug: bool = False
    fluorescence: FluorescenceConfig = field(default_factory=FluorescenceConfig)

    # Tracks which attributes were explicitly set by CLI so global rules do not override them
    _explicit: set[str] = field(default_factory=set, init=False, repr=False)

    def mark_explicit(self, dotted_name: str) -> None:
        self._explicit.add(dotted_name)

    def is_explicit(self, dotted_name: str) -> bool:
        return dotted_name in self._explicit

    def apply_policy(self) -> None:
        """
        Apply global policy based on `debug`, without overriding values explicitly set by CLI.
        """
        if self.debug:
            # In debug, default to showing these controls unless user explicitly disabled them
            if not self.is_explicit("fluorescence.show_scattering_controls"):
                self.fluorescence.show_scattering_controls = True
            if not self.is_explicit("fluorescence.show_threshold_controls"):
                self.fluorescence.show_threshold_controls = True

            # In debug, default per section debug on unless user explicitly set it
            if not self.is_explicit("fluorescence.debug_scattering"):
                self.fluorescence.debug_scattering = True
            if not self.is_explicit("fluorescence.debug_fluorescence"):
                self.fluorescence.debug_fluorescence = True
        else:
            # In non debug, default to hiding the “debug only” controls unless user explicitly enabled them
            if not self.is_explicit("fluorescence.show_scattering_controls"):
                self.fluorescence.show_scattering_controls = False
            if not self.is_explicit("fluorescence.show_threshold_controls"):
                self.fluorescence.show_threshold_controls = False

            # In non debug, default per section debug off unless user explicitly enabled it
            if not self.is_explicit("fluorescence.debug_scattering"):
                self.fluorescence.debug_scattering = False
            if not self.is_explicit("fluorescence.debug_fluorescence"):
                self.fluorescence.debug_fluorescence = False


_runtime_config: Optional[RuntimeConfig] = None


def get_runtime_config() -> RuntimeConfig:
    global _runtime_config
    if _runtime_config is None:
        _runtime_config = RuntimeConfig()
        _runtime_config.apply_policy()
    return _runtime_config