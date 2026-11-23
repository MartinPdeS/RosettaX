"""Render the settings profile editor."""

import dash_bootstrap_components as dbc
from ...ids import Ids
from . import schema, services
from dash import dcc, html
from RosettaX.utils.runtime_config import RuntimeConfig
from typing import Any

CATEGORY_DESCRIPTIONS = {
    "fluorescence": "Reference values, peak detection, and startup data.",
    "scattering": "Particle and detector models, peak detection, and startup data.",
    "apply_calibration": "Target model, plot axes, and event limits for applying calibrations.",
    "figure_style": "Chart dimensions, markers, labels, and grid lines.",
    "metadata": "Operator and instrument information included in supported exports.",
    "misc": "Theme and visibility defaults for the interface.",
}


class ProfileEditorLayout:
    """Edit the defaults stored in a browser profile."""

    def __init__(
        self,
        *,
        ids: type[Ids.Default],
        field_ids: dict[str, str],
        categories: list[tuple[str, str]],
    ) -> None:
        self.ids = ids
        self.field_ids = field_ids
        self.categories = categories

    def get_layout(self) -> html.Div:
        """Build the profile controls and all editable categories."""
        initial_values = services.build_form_store_from_runtime_config(
            RuntimeConfig.from_default_profile()
        )
        first_category = self.categories[0][0]

        return html.Div(
            [
                dcc.Store(id=self.ids.saved_values),
                self._build_profile_controls_card(),
                html.Div(
                    [
                        html.Nav(
                            dcc.RadioItems(
                                id=self.ids.category,
                                options=[
                                    {"label": title, "value": key}
                                    for key, title in self.categories
                                ],
                                value=first_category,
                                className="settings-categories",
                            ),
                            **{"aria-label": "Settings categories"},
                        ),
                        html.Div(
                            [
                                self._build_category(
                                    key=key,
                                    title=title,
                                    values=initial_values,
                                    hidden=key != first_category,
                                )
                                for key, title in self.categories
                            ],
                            className="settings-panels",
                        ),
                    ],
                    className="settings-workspace",
                ),
                self._build_save_bar(),
            ],
            className="settings-editor",
        )

    def _build_profile_controls_card(self) -> html.Section:
        """Build the profile selector and management actions."""
        return html.Section(
            [
                html.Div(
                    [
                        html.Label(
                            "Profile to edit",
                            htmlFor=self.ids.values_profile_dropdown,
                            className="settings-label",
                        ),
                        dcc.Dropdown(
                            id=self.ids.values_profile_dropdown,
                            options=services.build_profile_options(),
                            clearable=False,
                            placeholder="Select a profile",
                            persistence=True,
                            persistence_type="session",
                            disabled=True,
                        ),
                        html.P(
                            "Saved in this browser. Use the sidebar to load a profile into your workflows.",
                            className="settings-help",
                        ),
                    ],
                    className="settings-profile-select",
                ),
                html.Details(
                    [
                        html.Summary("Manage profiles"),
                        html.Label(
                            "New profile name",
                            htmlFor=self.ids.copy_name,
                            className="settings-label",
                        ),
                        html.Div(
                            [
                                dbc.Input(
                                    id=self.ids.copy_name,
                                    placeholder="Profile name",
                                    maxlength=100,
                                ),
                                dbc.Button(
                                    "Create copy",
                                    id=self.ids.copy_button,
                                    color="secondary",
                                    outline=True,
                                    disabled=True,
                                ),
                            ],
                            className="settings-copy",
                        ),
                        html.P(
                            "Copies the saved defaults from the selected profile.",
                            className="settings-help",
                        ),
                        dbc.Button(
                            "Delete profile",
                            id=self.ids.delete_button,
                            color="danger",
                            outline=True,
                            size="sm",
                            disabled=True,
                        ),
                        dcc.ConfirmDialog(id=self.ids.delete_confirmation),
                    ],
                    className="settings-management",
                ),
            ],
            className="settings-profile",
            **{"aria-label": "Profile"},
        )

    def _build_category(
        self, *, key: str, title: str, values: dict[str, Any], hidden: bool
    ) -> html.Section:
        """Build a category and keep its controls mounted between visits."""
        return html.Section(
            [
                html.Header(
                    [
                        html.H2(title),
                        html.P(CATEGORY_DESCRIPTIONS[key], className="settings-help"),
                    ],
                    className="settings-category-heading",
                ),
                *[
                    html.Fieldset(
                        [
                            html.Legend(group_title, className="settings-visually-hidden" if group_title == title else None),
                            html.Div(
                                [
                                    self._build_field(name=name, value=values.get(name))
                                    for name in names
                                ],
                                className="settings-fields",
                            ),
                        ],
                        className="settings-group",
                    )
                    for group_title, names in schema.section_field_groups(key)
                ],
            ],
            id=self.ids.category_panel(category=key),
            hidden=hidden,
            className="settings-panel",
            **{"aria-label": title},
        )

    def _build_field(self, *, name: str, value: Any) -> html.Div:
        """Render a control from its existing runtime schema definition."""
        definition = schema.FIELD_DEFINITION_BY_NAME[name]
        component_id = self.field_ids[name]
        if definition.component_kind == "dropdown":
            component = dcc.Dropdown(
                id=component_id,
                options=definition.options or [],
                value=value,
                clearable=False,
                searchable=False,
            )
        else:
            limits = {}
            if definition.component_kind == "number":
                runtime_field = RuntimeConfig.SCHEMA[definition.runtime_path]
                limits = {
                    "min": runtime_field.minimum
                    if definition.min_value is None
                    else definition.min_value,
                    "max": runtime_field.maximum
                    if definition.max_value is None
                    else definition.max_value,
                    "step": definition.step,
                }
            component = dbc.Input(
                id=component_id,
                type=definition.component_kind,
                value=value,
                placeholder=definition.placeholder,
                **limits,
            )

        return html.Div(
            [
                html.Label(
                    definition.label, htmlFor=component_id, className="settings-label"
                ),
                component,
            ]
        )

    def _build_save_bar(self) -> html.Div:
        """Keep draft status and save actions in reach while editing."""
        return html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            "Loading profile…", id=self.ids.edit_status, role="status"
                        ),
                        dbc.Alert(
                            id=self.ids.save_confirmation,
                            is_open=False,
                            class_name="settings-feedback",
                        ),
                    ],
                    className="settings-status",
                ),
                html.Div(
                    [
                        dbc.Button(
                            "Discard changes",
                            id=self.ids.revert_button,
                            color="secondary",
                            outline=True,
                            disabled=True,
                        ),
                        dbc.Button(
                            "Save changes",
                            id=self.ids.save_changes_button,
                            color="primary",
                            disabled=True,
                        ),
                    ],
                    className="settings-actions",
                ),
            ],
            className="settings-save-bar",
        )
