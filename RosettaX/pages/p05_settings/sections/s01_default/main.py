"""Assemble the settings profile editor."""

from . import schema, services
from .callbacks import register_profile_callbacks
from .layout import ProfileEditorLayout
from dash import html
from typing import Any


class DefaultProfile:
    """Edit the defaults stored in a browser profile."""

    def __init__(self, *, page: Any) -> None:
        self.ids = page.ids.Default
        self.field_ids = services.build_form_field_ids(page)
        self.categories = [
            ("misc", "General"),
            *(
                (key, title)
                for key, title in schema.PROFILE_SECTION_ORDER
                if key != "misc"
            ),
        ]

    def get_layout(self) -> html.Div:
        """Build the editor for all settings categories."""
        return ProfileEditorLayout(
            ids=self.ids, field_ids=self.field_ids, categories=self.categories
        ).get_layout()

    def register_callbacks(self) -> None:
        """Register the editor callbacks."""
        register_profile_callbacks(
            ids=self.ids, field_ids=self.field_ids, categories=self.categories
        )
