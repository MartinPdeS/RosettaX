# -*- coding: utf-8 -*-

from typing import Any, Optional

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html

from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.utils import ui_forms
from . import schema, services


class DefaultProfile:
    def __init__(self, page) -> None:
        self.page = page

    def _field_ids(self) -> dict[str, str]:
        return services.build_form_field_ids(self.page)

    def _ordered_field_names(self) -> list[str]:
        return schema.ordered_field_names()

    def _ordered_field_definitions(self) -> list[schema.FieldDefinition]:
        return [schema.FIELD_DEFINITION_BY_NAME[name] for name in self._ordered_field_names()]

    def _get_layout(self):
        runtime_config = RuntimeConfig.from_default_profile()

        return html.Div(
            [
                self._build_hero_section(),
                html.Div(style={"height": "16px"}),
                self._build_defaults_card(runtime_config),
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

    def _build_defaults_card(self, runtime_config: RuntimeConfig) -> dbc.Card:
        return dbc.Card(
            [
                dbc.CardHeader("1. Default values"),
                dbc.CardBody(
                    [
                        dcc.Store(
                            id=self.page.ids.Default.form_store,
                            storage_type="session",
                            data=services.build_form_store_from_runtime_config(runtime_config),
                        ),
                        self._build_profile_controls_block(),
                        html.Hr(),
                        self._build_section("fluorescence", runtime_config),
                        html.Hr(),
                        self._build_section("scattering", runtime_config),
                        html.Hr(),
                        self._build_section("calibration", runtime_config),
                        html.Hr(),
                        self._build_section("visualization", runtime_config),
                        html.Hr(),
                        self._build_section("miscellaneous", runtime_config),
                        html.Div(style={"height": "12px"}),
                        self._build_save_block(),
                    ]
                ),
            ],
            className="mb-4",
        )

    def _build_profile_controls_block(self) -> html.Div:
        profile_options = services.build_profile_options()
        default_profile_value = services.resolve_default_profile_value(profile_options)

        return html.Div(
            [
                ui_forms.build_section_intro(
                    title="Profile",
                    description="Choose a saved profile to load its values into the fields below.",
                ),
                ui_forms.build_labeled_row(
                    label="Saved profile:",
                    component=ui_forms.persistent_dropdown(
                        id=self.page.ids.Default.values_profile_dropdown,
                        options=profile_options,
                        value=default_profile_value,
                        placeholder="Select profile",
                        clearable=False,
                        style={"width": "100%"},
                    ),
                ),
            ]
        )

    def _build_section(
        self,
        section_key: str,
        runtime_config: RuntimeConfig,
    ) -> html.Div:
        form_store_data = services.build_form_store_from_runtime_config(runtime_config)
        field_ids = self._field_ids()
        section_title = dict(schema.PROFILE_SECTION_ORDER)[section_key]
        section_field_names = schema.section_field_names(section_key)

        return html.Div(
            [
                ui_forms.build_section_intro(title=section_title),
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
        common_style = {"width": "100%"}

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

        raise ValueError(f"Unsupported component_kind: {field_definition.component_kind!r}")

    def _build_save_block(self) -> html.Div:
        return html.Div(
            [
                dbc.Button(
                    "Save changes",
                    id=self.page.ids.Default.save_changes_button,
                    color="primary",
                    n_clicks=0,
                ),
                dbc.Alert(
                    "",
                    id=self.page.ids.Default.save_confirmation,
                    color="success",
                    is_open=False,
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
            Output(self.page.ids.Default.form_store, "data", allow_duplicate=True),
            Input(self.page.ids.Default.values_profile_dropdown, "value"),
            prevent_initial_call=True,
        )
        def load_profile_defaults(dropdown_value: Optional[str]):
            if not dropdown_value:
                return tuple([dash.no_update] * len(ordered_field_names)) + (dash.no_update,)

            saved_profile = services.get_saved_profile(dropdown_value) or {}
            runtime_config = RuntimeConfig.from_dict(saved_profile)
            form_store_data = services.build_form_store_from_runtime_config(runtime_config)

            return services.build_output_values_from_form_store(form_store_data) + (form_store_data,)

        @callback(
            Output(self.page.ids.Default.form_store, "data"),
            *form_value_inputs,
            prevent_initial_call=False,
        )
        def sync_form_store(*form_values):
            return services.build_form_store_from_form_values(form_values)

        @callback(
            Output(self.page.ids.Default.save_confirmation, "children"),
            Output("runtime-config-store", "data"),
            Output(self.page.ids.Default.save_confirmation, "is_open"),
            Output(self.page.ids.Default.save_confirmation, "color"),
            Input(self.page.ids.Default.save_changes_button, "n_clicks"),
            State(self.page.ids.Default.values_profile_dropdown, "value"),
            State(self.page.ids.Default.form_store, "data"),
            prevent_initial_call=True,
        )
        def edit_settings(
            n_clicks: Any,
            profile_target: Optional[str],
            form_store_data: Any,
        ):
            if dash.ctx.triggered_id != self.page.ids.Default.save_changes_button:
                return dash.no_update, dash.no_update, dash.no_update, dash.no_update

            if not n_clicks:
                return dash.no_update, dash.no_update, dash.no_update, dash.no_update

            try:
                if not profile_target:
                    return (
                        "No target profile selected.",
                        dash.no_update,
                        True,
                        "danger",
                    )

                flat_runtime_payload = services.coerce_form_store_to_flat_runtime_payload(form_store_data)
                nested_profile_payload = services.build_nested_profile_payload(flat_runtime_payload)
                services.save_profile(profile_target, nested_profile_payload)

                return (
                    f"Saved profile: {profile_target}",
                    nested_profile_payload,
                    True,
                    "success",
                )

            except Exception as exc:
                return (
                    f"{type(exc).__name__}: {exc}",
                    dash.no_update,
                    True,
                    "danger",
                )

        @callback(
            Output(self.page.ids.Default.save_confirmation, "children", allow_duplicate=True),
            Output(self.page.ids.Default.save_confirmation, "is_open", allow_duplicate=True),
            Input(self.page.ids.Default.values_profile_dropdown, "value"),
            *form_value_inputs,
            prevent_initial_call=True,
        )
        def clear_save_confirmation(*_args):
            return "", False