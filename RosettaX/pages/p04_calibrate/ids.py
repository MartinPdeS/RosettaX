# -*- coding: utf-8 -*-
page_name = "apply_calibration"


class Ids:
    class Page:
        location = f"{page_name}-location"

    class State:
        page_state_store = f"{page_name}-page-state-store"

    class Stores:
        selected_calibration_path_store = f"{page_name}-selected-calibration-path-store"
        uploaded_fcs_path_store = f"{page_name}-uploaded-fcs-path-store"

    class Header:
        container = f"{page_name}-header-container"

    class CalibrationPicker:
        dropdown = f"{page_name}-calibration-dropdown"
        refresh_button = f"{page_name}-refresh-button"

    class FilePicker:
        upload = f"{page_name}-upload"
        upload_status = f"{page_name}-upload-status"
        column_consistency_alert = f"{page_name}-column-consistency-alert"

    class Export:
        download = f"{page_name}-download"
        apply_and_export_button = f"{page_name}-apply-and-export-button"
        status = f"{page_name}-status"
        export_button = f"{page_name}-export-button"
        export_columns_dropdown = f"{page_name}-export-columns-dropdown"