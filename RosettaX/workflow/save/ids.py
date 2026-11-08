
from dataclasses import dataclass


@dataclass(frozen=True)
class SaveIds:
    """
    Shared ID factory for reusable save sections.

    The generated IDs are page specific through the prefix, while the Python API
    remains identical for fluorescence and scattering save sections.
    """

    prefix: str

    @property
    def collapse(self) -> str:
        return f"{self.prefix}-save-collapse"

    @property
    def save_calibration_btn(self) -> str:
        return f"{self.prefix}-save-calibration-btn"

    @property
    def file_name(self) -> str:
        return f"{self.prefix}-file-name"

    @property
    def output_channel_name(self) -> str:
        return f"{self.prefix}-output-channel-name"

    @property
    def save_out(self) -> str:
        return f"{self.prefix}-save-out"

    @property
    def review_summary(self) -> str:
        return f"{self.prefix}-save-review-summary"

    @property
    def review_acknowledgment(self) -> str:
        return f"{self.prefix}-save-review-acknowledgment"

    @property
    def download(self) -> str:
        return f"{self.prefix}-save-download"

    @property
    def description_target(self) -> str:
        """Return the ID for the save section information badge."""
        return f"{self.prefix}-save-description-target"

    @property
    def description_tooltip(self) -> str:
        """Return the ID for the save section description tooltip."""
        return f"{self.prefix}-save-description-tooltip"
