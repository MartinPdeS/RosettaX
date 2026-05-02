# -*- coding: utf-8 -*-

import logging
from typing import Any, Optional

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, html

from ...state import SettingsPageState
from RosettaX.utils import styling
from RosettaX.utils import ui_forms
from RosettaX.utils.runtime_config import RuntimeConfig

from . import schema
from . import services


logger = logging.getLogger(__name__)


class DefaultProfile:
    """
    Default profile settings section.

    Responsibilities
    ----------------
    - Render the default profile editor.
    - Load values from a selected saved profile.
    - Mirror form values into SettingsPageState.
    - Save edited form values back into the selected profile.

    State ownership
    ---------------
    The editable form values are mirrored into SettingsPageState instead of a
    section local dcc.Store.
    """

    vertical_spacing_px = 16

    def __init__(
        self,
        page: Any,
    ) -> None:
        self.page = page
        self.ids = page.ids.Default

    def get_layout(self):
        """
        Build the default profile editor layout.
        """
        logger.debug("DefaultProfile.get_layout rebuilding settings page.")

        form_store_data = self._build_initial_form_store_data()

        return html.Div(
            [
                self._build_hero_section(),
                self._build_vertical_spacer(),
                self._build_profile_controls_card(),
                self._build_vertical_spacer(),
                self._build_settings_sections_stack(
                    form_store_data=form_store_data,
                ),
                self._build_vertical_spacer(),
                self._build_save_card(),
            ],
            style={
                "display": "flex",
                "flexDirection": "column",
            },
        )

    def _build_hero_section(self) -> dbc.Card:
        """
        Build the page introduction card.
        """
        return dbc.Card(
            dbc.CardBody(
                [
                    ui_forms.build_section_intro(
                        title="Default values and profiles",
                        title_component="H2",
                        description=(
                            "Define the startup defaults used across RosettaX. "
                            "Profiles let you keep different configurations for "
                            "different instruments, datasets, or workflows."
                        ),
                    ),
                ],
                style={
                    "padding": "22px 24px",
                },
            ),
            style={
                "borderRadius": "14px",
            },
        )

    def _build_profile_controls_card(self) -> dbc.Card:
        """
        Build saved profile selection card.
        """
        profile_options = services.build_profile_options()

        default_profile_value = services.resolve_default_profile_value(
            profile_options,
        )

        return dbc.Card(
            [
                dbc.CardHeader(
                    "Profile",
                    style={
                        "fontWeight": "700",
                    },
                ),
                dbc.CardBody(
                    [
                        html.Div(
                            "Choose a saved profile to load its values into the fields below.",
                            style={
                                "opacity": 0.78,
                                "fontSize": "0.92rem",
                                "marginBottom": "12px",
                            },
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    ui_forms.persistent_dropdown(
                                        id=self.ids.values_profile_dropdown,
                                        options=profile_options,
                                        value=default_profile_value,
                                        placeholder="Select profile",
                                        clearable=False,
                                        style={
                                            "width": "100%",
                                        },
                                    ),
                                    md=8,
                                    lg=6,
                                ),
                            ],
                            className="g-2",
                        ),
                    ],
                    style={
                        "padding": "18px 20px",
                    },
                ),
            ],
            style={
                "borderRadius": "14px",
            },
        )

    def _build_settings_sections_stack(
        self,
        *,
        form_store_data: dict[str, Any],
    ) -> html.Div:
        """
        Build all settings sections as a vertical stack of delineated cards.
        """
        return html.Div(
            [
                self._build_section_card(
                    section_key=section_key,
                    section_title=section_title,
                    form_store_data=form_store_data,
                )
                for section_key, section_title in schema.PROFILE_SECTION_ORDER
            ],
            style={
                "display": "flex",
                "flexDirection": "column",
                "gap": "18px",
            },
        )

    def _build_section_card(
        self,
        *,
        section_key: str,
        section_title: str,
        form_store_data: dict[str, Any],
    ) -> dbc.Card:
        """
        Build one visually delineated settings section card.
        """
        section_field_names = schema.section_field_names(
            section_key,
        )

        logger.debug(
            "Settings section %r field names: %r",
            section_key,
            section_field_names,
        )

        section_style = self._section_visual_style(
            section_key,
        )

        return dbc.Card(
            [
                dbc.CardHeader(
                    [
                        html.Div(
                            section_title,
                            style={
                                "fontWeight": "750",
                                "fontSize": "1.02rem",
                            },
                        ),
                        html.Div(
                            self._section_description(
                                section_key,
                            ),
                            style={
                                "fontSize": "0.86rem",
                                "opacity": 0.76,
                                "marginTop": "3px",
                            },
                        ),
                    ],
                    style={
                        "background": section_style["header_background"],
                        "borderBottom": section_style["header_border"],
                        "padding": "13px 18px",
                        "borderTopLeftRadius": "15px",
                        "borderTopRightRadius": "15px",
                    },
                ),
                dbc.CardBody(
                    self._build_section_fields(
                        section_field_names=section_field_names,
                        form_store_data=form_store_data,
                    ),
                    style={
                        "padding": "18px",
                        "overflow": "visible",
                    },
                ),
            ],
            style={
                "borderRadius": "15px",
                "borderLeft": section_style["left_border"],
                "boxShadow": "0 0.35rem 0.9rem rgba(0, 0, 0, 0.08)",
                "overflow": "visible",
            },
        )

    def _build_section_fields(
        self,
        *,
        section_field_names: list[str],
        form_store_data: dict[str, Any],
    ) -> html.Div:
        """
        Build all fields for one section.
        """
        field_ids = self._build_field_ids()

        return html.Div(
            [
                self._build_compact_field(
                    field_name=field_name,
                    field_ids=field_ids,
                    form_store_data=form_store_data,
                )
                for field_name in section_field_names
            ],
            style={
                "display": "grid",
                "gridTemplateColumns": "repeat(auto-fit, minmax(300px, 1fr))",
                "columnGap": "20px",
                "rowGap": "16px",
            },
        )

    def _build_compact_field(
        self,
        *,
        field_name: str,
        field_ids: dict[str, str],
        form_store_data: dict[str, Any],
    ) -> html.Div:
        """
        Build one compact stacked field.
        """
        field_definition = schema.FIELD_DEFINITION_BY_NAME[field_name]

        return html.Div(
            [
                html.Label(
                    field_definition.label,
                    htmlFor=field_ids[field_name],
                    style={
                        "display": "block",
                        "fontSize": "0.86rem",
                        "fontWeight": "600",
                        "marginBottom": "5px",
                        "opacity": 0.86,
                    },
                ),
                self._build_field_component(
                    field_definition=field_definition,
                    component_id=field_ids[field_name],
                    value=form_store_data.get(field_name),
                ),
            ],
            style={
                "minWidth": "0",
            },
        )

    def _build_field_component(
        self,
        *,
        field_definition: schema.FieldDefinition,
        component_id: str,
        value: Any,
    ):
        """
        Build one field component from its schema definition.
        """
        common_style = {
            "width": "100%",
        }

        if field_definition.component_kind == "text":
            return ui_forms.persistent_input(
                id=component_id,
                type="text",
                value=value,
                placeholder=field_definition.placeholder,
                style=common_style,
            )

        if field_definition.component_kind == "number":
            return ui_forms.persistent_input(
                id=component_id,
                type="number",
                value=value,
                min=field_definition.min_value,
                max=field_definition.max_value,
                step=field_definition.step,
                placeholder=field_definition.placeholder,
                style=common_style,
            )

        if field_definition.component_kind == "dropdown":
            return ui_forms.persistent_dropdown(
                id=component_id,
                options=field_definition.options or [],
                value=value,
                clearable=False,
                searchable=False,
                style=common_style,
            )

        raise ValueError(
            f"Unsupported component_kind: {field_definition.component_kind!r}"
        )

    def _build_save_card(self) -> dbc.Card:
        """
        Build save action card.
        """
        return dbc.Card(
            dbc.CardBody(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(
                                        "Save profile changes",
                                        style={
                                            "fontWeight": "700",
                                            "fontSize": "1rem",
                                        },
                                    ),
                                    html.Div(
                                        "Changes are written to the currently selected profile.",
                                        style={
                                            "opacity": 0.72,
                                            "fontSize": "0.9rem",
                                        },
                                    ),
                                ],
                                style={
                                    "flex": "1 1 auto",
                                },
                            ),
                            dbc.Button(
                                "Save changes",
                                id=self.ids.save_changes_button,
                                color="primary",
                                n_clicks=0,
                                style={
                                    "minWidth": "150px",
                                },
                            ),
                        ],
                        style={
                            "display": "flex",
                            "alignItems": "center",
                            "justifyContent": "space-between",
                            "gap": "16px",
                            "flexWrap": "wrap",
                        },
                    ),
                    dbc.Alert(
                        "",
                        id=self.ids.save_confirmation,
                        color="success",
                        is_open=False,
                        style={
                            "marginTop": "12px",
                            "marginBottom": "0px",
                        },
                    ),
                ],
                style={
                    "padding": "18px 20px",
                },
            ),
            style={
                "borderRadius": "14px",
            },
            className="mb-4",
        )

    def _build_vertical_spacer(
        self,
        *,
        height_px: Optional[int] = None,
    ) -> html.Div:
        """
        Build a vertical spacer.
        """
        return html.Div(
            style={
                "height": f"{height_px or self.vertical_spacing_px}px",
            }
        )

    def _section_visual_style(
        self,
        section_key: str,
    ) -> dict[str, str]:
        """
        Return visual styling for one settings section.
        """
        return styling.build_section_legacy_style(
            section_key,
        )

    def _section_description(
        self,
        section_key: str,
    ) -> str:
        """
        Return a short description for one settings section.
        """
        descriptions = {
            "miscellaneous": (
                "General application preferences, startup files, and profile-wide defaults."
            ),
            "calibration": (
                "Shared controls reused by calibration, peak detection, and apply-calibration workflows."
            ),
            "fluorescence": (
                "Defaults used by the fluorescence peak-detection and MESF workflow."
            ),
            "scattering": (
                "Defaults for scattering peak detection, particle tables, and Mie-model setup."
            ),
            "visualization": (
                "Plot appearance, graph sizing, and display defaults."
            ),
        }

        return descriptions.get(
            section_key,
            "",
        )

    def _build_field_ids(self) -> dict[str, str]:
        """
        Build form field IDs from the settings schema.
        """
        return services.build_form_field_ids(
            self.page,
        )

    def _ordered_field_names(self) -> list[str]:
        """
        Return all form field names in schema order.
        """
        return schema.ordered_field_names()

    def _build_initial_form_store_data(self) -> dict[str, Any]:
        """
        Build initial form data from the default runtime profile.
        """
        runtime_config = RuntimeConfig.from_default_profile()

        return services.build_form_store_from_runtime_config(
            runtime_config,
        )

    def _build_form_value_outputs(
        self,
        *,
        field_ids: dict[str, str],
        ordered_field_names: list[str],
    ) -> list[Output]:
        """
        Build callback outputs for all form values.
        """
        return [
            Output(field_ids[field_name], "value")
            for field_name in ordered_field_names
        ]

    def _build_form_value_inputs(
        self,
        *,
        field_ids: dict[str, str],
        ordered_field_names: list[str],
    ) -> list[Input]:
        """
        Build callback inputs for all form values.
        """
        return [
            Input(field_ids[field_name], "value")
            for field_name in ordered_field_names
        ]

    def _build_page_state(
        self,
        page_state_payload: Any,
    ) -> SettingsPageState:
        """
        Build SettingsPageState from a Dash payload.
        """
        return SettingsPageState.from_dict(
            page_state_payload if isinstance(page_state_payload, dict) else None
        )

    def _build_nested_profile_payload(
        self,
        *,
        form_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Convert flat form data into the nested runtime profile payload.
        """
        flat_runtime_payload = services.coerce_form_store_to_flat_runtime_payload(
            form_data,
        )

        return services.build_nested_profile_payload(
            flat_runtime_payload,
        )

    def _build_no_update_form_response(
        self,
        *,
        ordered_field_names: list[str],
    ) -> tuple[Any, ...]:
        """
        Build no update response for the profile load callback.
        """
        return tuple(
            [dash.no_update] * len(ordered_field_names)
        ) + (dash.no_update,)

    def _build_no_update_save_response(self) -> tuple[Any, Any, Any, Any]:
        """
        Build no update response for the save callback.
        """
        return (
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
        )

    def _build_save_response(
        self,
        *,
        page_state: SettingsPageState,
        status_message: str,
        color: str,
    ) -> tuple[str, bool, str, dict[str, Any]]:
        """
        Build a save callback response and update page state status.
        """
        page_state = page_state.update(
            status_message=status_message,
        )

        return (
            status_message,
            True,
            color,
            page_state.to_dict(),
        )

    def register_callbacks(self) -> None:
        """
        Register default profile editor callbacks.
        """
        field_ids = self._build_field_ids()
        ordered_field_names = self._ordered_field_names()

        form_value_outputs = self._build_form_value_outputs(
            field_ids=field_ids,
            ordered_field_names=ordered_field_names,
        )

        form_value_inputs = self._build_form_value_inputs(
            field_ids=field_ids,
            ordered_field_names=ordered_field_names,
        )

        @callback(
            *form_value_outputs,
            Output(
                self.page.ids.State.page_state_store,
                "data",
                allow_duplicate=True,
            ),
            Input(self.ids.values_profile_dropdown, "value"),
            State(self.page.ids.State.page_state_store, "data"),
            prevent_initial_call=True,
        )
        def load_profile_defaults(
            dropdown_value: Optional[str],
            page_state_payload: Any,
        ):
            logger.debug(
                "load_profile_defaults triggered_id=%r dropdown_value=%r",
                dash.ctx.triggered_id,
                dropdown_value,
            )

            if not dropdown_value:
                return self._build_no_update_form_response(
                    ordered_field_names=ordered_field_names,
                )

            saved_profile = services.get_saved_profile(
                dropdown_value,
            ) or {}

            runtime_config = RuntimeConfig.from_dict(
                saved_profile,
            )

            form_store_data = services.build_form_store_from_runtime_config(
                runtime_config,
            )

            page_state = self._build_page_state(
                page_state_payload,
            ).update(
                selected_profile=dropdown_value,
                form_data=form_store_data,
                status_message="",
            )

            return services.build_output_values_from_form_store(
                form_store_data,
            ) + (page_state.to_dict(),)

        @callback(
            Output(self.page.ids.State.page_state_store, "data"),
            Input(self.ids.values_profile_dropdown, "value"),
            *form_value_inputs,
            State(self.page.ids.State.page_state_store, "data"),
            prevent_initial_call=False,
        )
        def sync_page_state(
            selected_profile: Optional[str],
            *callback_values: Any,
        ):
            page_state_payload = callback_values[-1]
            form_values = callback_values[:-1]

            form_store_data = services.build_form_store_from_form_values(
                form_values,
            )

            page_state = self._build_page_state(
                page_state_payload,
            ).update(
                selected_profile=selected_profile,
                form_data=form_store_data,
            )

            return page_state.to_dict()

        @callback(
            Output(self.ids.save_confirmation, "children"),
            Output(self.ids.save_confirmation, "is_open"),
            Output(self.ids.save_confirmation, "color"),
            Output(
                self.page.ids.State.page_state_store,
                "data",
                allow_duplicate=True,
            ),
            Input(self.ids.save_changes_button, "n_clicks"),
            State(self.page.ids.State.page_state_store, "data"),
            prevent_initial_call=True,
        )
        def edit_settings(
            n_clicks: Any,
            page_state_payload: Any,
        ):
            if dash.ctx.triggered_id != self.ids.save_changes_button:
                return self._build_no_update_save_response()

            if not n_clicks:
                return self._build_no_update_save_response()

            page_state = self._build_page_state(
                page_state_payload,
            )

            try:
                if not page_state.selected_profile:
                    return self._build_save_response(
                        page_state=page_state,
                        status_message="No target profile selected.",
                        color="danger",
                    )

                nested_profile_payload = self._build_nested_profile_payload(
                    form_data=page_state.form_data or {},
                )

                services.save_profile(
                    page_state.selected_profile,
                    nested_profile_payload,
                )

                return self._build_save_response(
                    page_state=page_state,
                    status_message=f"Saved profile: {page_state.selected_profile}",
                    color="success",
                )

            except Exception as exc:
                logger.exception("Failed to save settings profile.")

                return self._build_save_response(
                    page_state=page_state,
                    status_message=f"{type(exc).__name__}: {exc}",
                    color="danger",
                )

        @callback(
            Output(
                self.ids.save_confirmation,
                "children",
                allow_duplicate=True,
            ),
            Output(
                self.ids.save_confirmation,
                "is_open",
                allow_duplicate=True,
            ),
            Input(self.ids.values_profile_dropdown, "value"),
            *form_value_inputs,
            prevent_initial_call=True,
        )
        def clear_save_confirmation(*_args):
            return "", False
