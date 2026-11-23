"""Wire settings navigation and browser profile actions."""

import dash
import json
import logging
from ...ids import Ids
from . import schema, services
from dash import Input, Output, State, callback
from dash.exceptions import PreventUpdate
from RosettaX.application.access import can_edit_settings
from RosettaX.utils.browser_profiles import (
    BROWSER_PROFILES_STORE_ID,
    DEFAULT_PROFILE_FILENAME,
    BrowserProfileLibrary,
)
from RosettaX.utils.runtime_config import RuntimeConfig

logger = logging.getLogger(__name__)


def register_profile_callbacks(
    *,
    ids: type[Ids.Default],
    field_ids: dict[str, str],
    categories: list[tuple[str, str]],
) -> None:
    """Connect the editor to its profile library and draft controls."""
    fields = [field_ids[name] for name in schema.ordered_field_names()]
    category_keys = [key for key, _ in categories]

    dash.clientside_callback(
        f"function (selected) {{ return {json.dumps(category_keys)}.map(category => category !== selected); }}",
        [Output(ids.category_panel(category=key), "hidden") for key in category_keys],
        Input(ids.category, "value"),
    )

    dash.clientside_callback(
        f"""
        function (saved, profile, copyName, ...values) {{
            const defaultProfile = {json.dumps(DEFAULT_PROFILE_FILENAME)};
            const ready = saved?.profile === profile && Boolean(profile);
            const dirty = ready && values.some((value, index) => (value ?? null) !== saved.values[index]);
            const status = !ready ? "Loading profile…" : dirty ? "Unsaved changes" : "All changes saved";
            return [status, !dirty, !dirty, !ready || dirty,
                    !ready || dirty || !copyName?.trim(), !ready || dirty || profile === defaultProfile];
        }}
        """,
        Output(ids.edit_status, "children"),
        Output(ids.revert_button, "disabled"),
        Output(ids.save_changes_button, "disabled"),
        Output(ids.values_profile_dropdown, "disabled"),
        Output(ids.copy_button, "disabled"),
        Output(ids.delete_button, "disabled"),
        Input(ids.saved_values, "data"),
        Input(ids.values_profile_dropdown, "value"),
        Input(ids.copy_name, "value"),
        *[Input(field, "value") for field in fields],
    )

    @callback(
        Output(ids.delete_confirmation, "displayed"),
        Output(ids.delete_confirmation, "message"),
        Input(ids.delete_button, "n_clicks"),
        State(ids.values_profile_dropdown, "value"),
        State(BROWSER_PROFILES_STORE_ID, "data"),
        prevent_initial_call=True,
    )
    def confirm_profile_deletion(_clicks, profile, browser_payload):
        """Show the selected profile name in the deletion confirmation."""
        if not can_edit_settings():
            raise PreventUpdate
        library = BrowserProfileLibrary.from_dict(browser_payload)
        return True, f"Delete “{library.get_profile_label(profile)}” from this browser?"

    @callback(
        Output(ids.values_profile_dropdown, "options"),
        Output(ids.values_profile_dropdown, "value"),
        Output(ids.saved_values, "data"),
        Output(ids.save_confirmation, "children"),
        Output(ids.save_confirmation, "is_open"),
        Output(ids.save_confirmation, "color"),
        Output(ids.copy_name, "value"),
        Output(BROWSER_PROFILES_STORE_ID, "data", allow_duplicate=True),
        *[Output(field, "value") for field in fields],
        Input(ids.values_profile_dropdown, "value"),
        Input(ids.revert_button, "n_clicks"),
        Input(ids.save_changes_button, "n_clicks"),
        Input(ids.copy_button, "n_clicks"),
        Input(ids.delete_confirmation, "submit_n_clicks"),
        State(ids.copy_name, "value"),
        State(BROWSER_PROFILES_STORE_ID, "data"),
        *[State(field, "value") for field in fields],
        prevent_initial_call="initial_duplicate",
    )
    def update_profile(
        profile, _revert, _save, _copy, _delete, copy_name, browser_payload, *values
    ):
        """Load a profile or apply the requested action to the browser library."""
        action = dash.ctx.triggered_id
        if not can_edit_settings():
            raise PreventUpdate
        library = BrowserProfileLibrary.from_dict(browser_payload)
        profile = profile if profile in library.profiles else library.selected_profile
        message = ""
        color = "success"
        clear_name = dash.no_update
        next_payload = dash.no_update
        try:
            if action == ids.save_changes_button:
                next_payload = services.save_profile_form(
                    profile=profile,
                    values=values,
                    browser_payload=browser_payload,
                )
                library = BrowserProfileLibrary.from_dict(next_payload)
                message = "Profile saved."
            elif action == ids.copy_button:
                library = library.create_profile(
                    profile_name=copy_name,
                    source_profile_name=profile,
                    select_profile=True,
                )
                profile = library.selected_profile
                next_payload = library.to_dict()
                clear_name = ""
                message = "Profile copy created."
            elif action == ids.delete_confirmation:
                library = library.delete_profile(profile_name=profile)
                profile = library.selected_profile
                next_payload = library.to_dict()
                message = "Profile deleted."
        except (ValueError, FileNotFoundError) as error:
            message = str(error)
            color = "danger"
        except Exception:
            logger.exception("Could not update the settings profile")
            message = "Could not update the profile."
            color = "danger"

        if color == "danger":
            unchanged = (dash.no_update,) * 3
            return (
                *unchanged,
                message,
                True,
                color,
                *((dash.no_update,) * (2 + len(fields))),
            )

        runtime_config = RuntimeConfig.from_dict(library.get_profile_payload(profile))
        form_data = services.build_form_store_from_runtime_config(runtime_config)
        form_values = services.build_output_values_from_form_store(form_data)
        baseline = {"profile": profile, "values": list(form_values)}
        return (
            library.build_options(),
            profile,
            baseline,
            message,
            bool(message),
            color,
            clear_name,
            next_payload,
            *form_values,
        )
