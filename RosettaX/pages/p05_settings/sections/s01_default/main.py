# -*- coding: utf-8 -*-

from typing import Any, Optional
import logging

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, html

from ...state import SettingsPageState
from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.utils import ui_forms

from . import schema
from . import services


logger = logging.getLogger(__name__)


class DefaultProfile:
    """
    Default profile settings section.

    The editable form values are mirrored into SettingsPageState instead of a
    section-local dcc.Store.
    """

    def __init__(self, page) -> None:
        self.page = page
        self.ids = page.ids.Default

    def _field_ids(self) -> dict[str, str]:
        return services.build_form_field_ids(self.page)

    def _ordered_field_names(self) -> list[str]:
        return schema.ordered_field_names()

    def _initial_form_store_data(self) -> dict[str, Any]:
        runtime_config = RuntimeConfig.from_default_profile()

        return services.build_form_store_from_runtime_config(
            runtime_config,
        )

    def get_layout(self):
        logger.debug("DefaultProfile.get_layout rebuilding settings page.")

        initial_form_store_data = self._initial_form_store_data()

        return html.Div(
            [
                self._build_hero_section(),
                html.Div(style={"height": "16px"}),
                self._build_defaults_card(
                    initial_form_store_data,
                ),
            ]
        )

    def _build_hero_section(self) -> dbc.Card:
        return dbc.Card(
            dbc.CardBody(
                [
                    ui_forms.build_section_intro(
                        title="Default values and profiles",
                        title_component="H2",
                        description=(
                            "Use this page to define the startup defaults used across RosettaX. "
                            "Profiles let you keep different working configurations for different instruments, "
                            "datasets, or workflows, then reload them into the application when needed."
                        ),
                    ),
                ]
            )
        )

    def _build_defaults_card(
        self,
        form_store_data: dict[str, Any],
    ) -> dbc.Card:
        return dbc.Card(
            [
                dbc.CardHeader("1. Default values"),
                dbc.CardBody(
                    [
                        self._build_profile_controls_block(),
                        html.Hr(),
                        self._build_section("fluorescence", form_store_data),
                        html.Hr(),
                        self._build_section("scattering", form_store_data),
                        html.Hr(),
                        self._build_section("calibration", form_store_data),
                        html.Hr(),
                        self._build_section("visualization", form_store_data),
                        html.Hr(),
                        self._build_section("miscellaneous", form_store_data),
                        html.Div(style={"height": "12px"}),
                        self._build_save_block(),
                    ]
                ),
            ],
            className="mb-4",
        )

    def _build_profile_controls_block(self) -> html.Div:
        profile_options = services.build_profile_options()
        default_profile_value = services.resolve_default_profile_value(
            profile_options,
        )

        return html.Div(
            [
                ui_forms.build_section_intro(
                    title="Profile",
                    description="Choose a saved profile to load its values into the fields below.",
                ),
                ui_forms.build_labeled_row(
                    label="Saved profile:",
                    component=ui_forms.persistent_dropdown(
                        id=self.ids.values_profile_dropdown,
                        options=profile_options,
                        value=default_profile_value,
                        placeholder="Select profile",
                        clearable=False,
                        style={
                            "width": "100%",
                        },
                    ),
                ),
            ]
        )

    def _build_section(
        self,
        section_key: str,
        form_store_data: dict[str, Any],
    ) -> html.Div:
        field_ids = self._field_ids()
        section_title = dict(schema.PROFILE_SECTION_ORDER)[section_key]
        section_field_names = schema.section_field_names(section_key)

        logger.debug(
            "Settings section %r field names: %r",
            section_key,
            section_field_names,
        )

        return html.Div(
            [
                ui_forms.build_section_intro(
                    title=section_title,
                ),
                *[
                    ui_forms.build_labeled_row(
                        label=schema.FIELD_DEFINITION_BY_NAME[field_name].label,
                        component=self._build_field_component(
                            field_definition=schema.FIELD_DEFINITION_BY_NAME[field_name],
                            component_id=field_ids[field_name],
                            value=form_store_data.get(field_name),
                        ),
                    )
                    for field_name in section_field_names
                ],
            ]
        )

    def _build_field_component(
        self,
        *,
        field_definition: schema.FieldDefinition,
        component_id: str,
        value: Any,
    ):
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

    def _build_save_block(self) -> html.Div:
        return html.Div(
            [
                dbc.Button(
                    "Save changes",
                    id=self.ids.save_changes_button,
                    color="primary",
                    n_clicks=0,
                ),
                dbc.Alert(
                    "",
                    id=self.ids.save_confirmation,
                    color="success",
                    is_open=False,
                    style={
                        "marginTop": "10px",
                    },
                ),
            ]
        )

    def register_callbacks(self) -> None:
        field_ids = self._field_ids()
        ordered_field_names = self._ordered_field_names()

        form_value_outputs = [
            Output(field_ids[field_name], "value")
            for field_name in ordered_field_names
        ]

        form_value_inputs = [
            Input(field_ids[field_name], "value")
            for field_name in ordered_field_names
        ]

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
                return tuple(
                    [dash.no_update] * len(ordered_field_names)
                ) + (dash.no_update,)

            saved_profile = services.get_saved_profile(
                dropdown_value,
            ) or {}

            runtime_config = RuntimeConfig.from_dict(
                saved_profile,
            )

            form_store_data = services.build_form_store_from_runtime_config(
                runtime_config,
            )

            page_state = SettingsPageState.from_dict(
                page_state_payload if isinstance(page_state_payload, dict) else None
            )

            page_state = page_state.update(
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

            page_state = SettingsPageState.from_dict(
                page_state_payload if isinstance(page_state_payload, dict) else None
            )

            page_state = page_state.update(
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
                return dash.no_update, dash.no_update, dash.no_update, dash.no_update

            if not n_clicks:
                return dash.no_update, dash.no_update, dash.no_update, dash.no_update

            page_state = SettingsPageState.from_dict(
                page_state_payload if isinstance(page_state_payload, dict) else None
            )

            try:
                if not page_state.selected_profile:
                    status_message = "No target profile selected."

                    page_state = page_state.update(
                        status_message=status_message,
                    )

                    return (
                        status_message,
                        True,
                        "danger",
                        page_state.to_dict(),
                    )

                flat_runtime_payload = services.coerce_form_store_to_flat_runtime_payload(
                    page_state.form_data or {},
                )

                nested_profile_payload = services.build_nested_profile_payload(
                    flat_runtime_payload,
                )

                services.save_profile(
                    page_state.selected_profile,
                    nested_profile_payload,
                )

                status_message = f"Saved profile: {page_state.selected_profile}"

                page_state = page_state.update(
                    status_message=status_message,
                )

                return (
                    status_message,
                    True,
                    "success",
                    page_state.to_dict(),
                )

            except Exception as exc:
                logger.exception("Failed to save settings profile.")

                status_message = f"{type(exc).__name__}: {exc}"

                page_state = page_state.update(
                    status_message=status_message,
                )

                return (
                    status_message,
                    True,
                    "danger",
                    page_state.to_dict(),
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