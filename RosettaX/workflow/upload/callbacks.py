# -*- coding: utf-8 -*-

import dash
from typing import Any
import logging

from dash import Input
from dash import Output
from dash import State
from dash import callback

from RosettaX.workflow.upload import services
from RosettaX.workflow.upload.adapters import UploadAdapter
from RosettaX.workflow.upload.models import UploadConfig


def register_upload_callbacks(
    *,
    page: Any,
    ids: Any,
    adapter: UploadAdapter,
    config: UploadConfig,
    logger: logging.Logger,
) -> None:
    """
    Register reusable upload callbacks.
    """
    logger.debug(
        "Registering reusable upload callbacks for card_title=%r",
        config.card_title,
    )

    _register_upload_callback(
        page=page,
        ids=ids,
        adapter=adapter,
        config=config,
        logger=logger,
    )


def _register_upload_callback(
    *,
    page: Any,
    ids: Any,
    adapter: UploadAdapter,
    config: UploadConfig,
    logger: logging.Logger,
) -> None:
    """
    Register the upload persistence callback.
    """

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
        Input(ids.upload, "contents"),
        State(ids.upload, "filename"),
        State(page.ids.State.page_state_store, "data"),
        State(config.runtime_config_store_id, "data"),
        prevent_initial_call=True,
    )
    def handle_upload(
        contents: Any,
        filename: Any,
        page_state_payload: Any,
        runtime_config_data: Any,
    ) -> tuple[Any, Any, str]:
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

        try:
            upload_state = services.build_upload_state(
                config=config,
                contents=services.clean_optional_string(
                    contents,
                ),
                filename=services.clean_optional_string(
                    filename,
                ),
                stored_fcs_path=services.clean_optional_string(
                    adapter.get_uploaded_fcs_path(
                        current_page_state,
                    ),
                ),
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

            next_page_state = adapter.update_page_state_after_upload(
                current_page_state=current_page_state,
                uploaded_fcs_path=upload_state.uploaded_fcs_path,
                uploaded_filename=upload_state.uploaded_filename,
            )

            logger.debug(
                "handle_upload returning for card_title=%r uploaded_fcs_path=%r uploaded_filename=%r",
                config.card_title,
                upload_state.uploaded_fcs_path,
                upload_state.uploaded_filename,
            )

            return (
                next_page_state.to_dict(),
                upload_state.runtime_config_data,
                services.build_loaded_filename_text(
                    upload_state.uploaded_filename,
                ),
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
            )