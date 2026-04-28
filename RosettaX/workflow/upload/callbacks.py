# -*- coding: utf-8 -*-

from typing import Any
import logging

from dash import Input
from dash import Output
from dash import State
from dash import callback

from RosettaX.workflow.upload import services
from RosettaX.workflow.upload.adapters import UploadAdapter
from RosettaX.workflow.upload.models import UploadCallbackResult
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

    _register_filename_display_callback(
        page=page,
        ids=ids,
        adapter=adapter,
        logger=logger,
    )

    _register_upload_callback(
        page=page,
        ids=ids,
        adapter=adapter,
        config=config,
        logger=logger,
    )


def _register_filename_display_callback(
    *,
    page: Any,
    ids: Any,
    adapter: UploadAdapter,
    logger: logging.Logger,
) -> None:
    """
    Register the filename display callback.
    """

    @callback(
        Output(ids.upload_filename, "children"),
        Input(page.ids.State.page_state_store, "data"),
    )
    def show_uploaded_filename(
        page_state_payload: Any,
    ) -> str:
        page_state = adapter.page_state_from_payload(
            page_state_payload,
        )

        uploaded_filename = adapter.get_uploaded_filename(
            page_state,
        )

        logger.debug(
            "show_uploaded_filename called with uploaded_filename=%r",
            uploaded_filename,
        )

        return services.build_loaded_filename_text(
            uploaded_filename,
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
    ) -> tuple[Any, Any]:
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

        result = UploadCallbackResult(
            page_state_payload=next_page_state.to_dict(),
            runtime_config_data=upload_state.runtime_config_data,
        )

        logger.debug(
            "handle_upload returning for card_title=%r uploaded_fcs_path=%r uploaded_filename=%r",
            config.card_title,
            upload_state.uploaded_fcs_path,
            upload_state.uploaded_filename,
        )

        return result.to_tuple()