
import dash
import logging
from collections.abc import Callable
from dash import Input, Output, State, callback
from RosettaX.workflow.upload import services
from RosettaX.workflow.upload.adapters import UploadAdapter
from RosettaX.workflow.upload.models import UploadConfig
from typing import Any


def register_upload_callbacks(
    *,
    page: Any,
    ids: Any,
    adapter: UploadAdapter,
    config: UploadConfig,
    logger: logging.Logger,
    table_reset: tuple[str, Callable[..., list[dict[str, Any]]]] | None = None,
) -> None:
    """
    Register the upload callback and optionally clear measurements on replacement.

    Parameters
    ----------
    table_reset : tuple or None
        Table ID and a function accepting its rows and clearing file-specific
        measurements. Used when the table lives outside page state.
    """
    logger.debug(
        "Registering reusable upload callbacks for card_title=%r",
        config.card_title,
    )
    table_outputs = [Output(table_reset[0], "data", allow_duplicate=True)] if table_reset else []
    table_states = [State(table_reset[0], "data")] if table_reset else []

    @callback(
        Output(
            page.ids.State.page_state_store,
            "data",
            allow_duplicate=True,
        ),
        Output(
            config.runtime_config_store_id,
            "data",
            allow_duplicate=True,
        ),
        Output(
            ids.upload_filename,
            "children",
            allow_duplicate=True,
        ),
        *table_outputs,
        Input(ids.upload, "contents"),
        State(ids.upload, "filename"),
        State(page.ids.State.page_state_store, "data"),
        State(config.runtime_config_store_id, "data"),
        *table_states,
        prevent_initial_call=True,
    )
    def handle_upload(
        contents: Any,
        filename: Any,
        page_state_payload: Any,
        runtime_config_data: Any,
        *table_rows: list[dict[str, Any]] | None,
    ) -> tuple[Any, ...]:
        logger.debug(
            "handle_upload called for card_title=%r with contents_type=%s filename=%r "
            "page_state_payload_type=%s runtime_config_data_type=%s",
            config.card_title,
            type(contents).__name__,
            filename,
            type(page_state_payload).__name__,
            type(runtime_config_data).__name__,
        )

        current_page_state = adapter.page_state_from_payload(
            page_state_payload,
        )
        stored_fcs_path = services.clean_optional_string(adapter.get_uploaded_fcs_path(current_page_state))

        try:
            upload_state = services.build_upload_state(
                config=config,
                contents=services.clean_optional_string(
                    contents,
                ),
                filename=services.clean_optional_string(
                    filename,
                ),
                stored_fcs_path=stored_fcs_path,
                stored_filename=services.clean_optional_string(
                    adapter.get_uploaded_filename(
                        current_page_state,
                    ),
                ),
                runtime_config_data=runtime_config_data
                if isinstance(runtime_config_data, dict)
                else None,
                logger=logger,
            )

            file_changed = upload_state.uploaded_fcs_path != stored_fcs_path
            page_state_output = dash.no_update
            if file_changed:
                page_state_output = adapter.update_page_state_after_upload(
                    current_page_state=current_page_state,
                    uploaded_fcs_path=upload_state.uploaded_fcs_path,
                    uploaded_filename=upload_state.uploaded_filename,
                ).to_dict()

            table_output = ()
            if table_reset:
                clear_measurements = table_reset[1]
                table_output = (
                    clear_measurements(rows=table_rows[0]) if file_changed and stored_fcs_path else dash.no_update,
                )

            logger.debug(
                "handle_upload returning for card_title=%r uploaded_fcs_path=%r uploaded_filename=%r",
                config.card_title,
                upload_state.uploaded_fcs_path,
                upload_state.uploaded_filename,
            )

            return (
                page_state_output,
                upload_state.runtime_config_data,
                services.build_loaded_filename_text(
                    upload_state.uploaded_filename,
                ),
                *table_output,
            )

        except Exception as exc:
            logger.exception(
                "handle_upload failed for card_title=%r filename=%r",
                config.card_title,
                filename,
            )

            return (
                dash.no_update,
                dash.no_update,
                services.build_upload_error_text(exc),
                *((dash.no_update,) if table_reset else ()),
            )
