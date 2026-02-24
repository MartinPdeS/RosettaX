from typing import Any, Optional
from pathlib import Path
import base64
import tempfile
from dataclasses import dataclass
import numpy as np
import plotly.graph_objs as go

from RosettaX.reader import FCSFile


@dataclass(frozen=True)
class ChannelOptions:
    scatter_options: list[dict[str, str]]
    fluorescence_options: list[dict[str, str]]
    scatter_value: Optional[str]
    fluorescence_value: Optional[str]


class FileStateRefresher:
    def __init__(self, *, scatter_keywords: list[str], non_valid_keywords: list[str]) -> None:
        self.scatter_keywords = [str(k).lower() for k in scatter_keywords]
        self.non_valid_keywords = [str(k).lower() for k in non_valid_keywords]

    def options_from_file(
        self,
        file_path: str,
        *,
        preferred_scatter: Optional[str] = None,
        preferred_fluorescence: Optional[str] = None,
    ) -> ChannelOptions:
        with FCSFile(str(file_path), writable=False) as fcs_file:
            detectors = fcs_file.text["Detectors"]
            num_parameters = int(fcs_file.text["Keywords"]["$PAR"])

            columns = [
                str(detectors[index].get("N", f"P{index}"))
                for index in range(1, num_parameters + 1)
            ]

        scatter_options: list[dict[str, str]] = []
        fluorescence_options: list[dict[str, str]] = []

        for column in columns:
            lower = str(column).strip().lower()
            is_scatter = any(keyword in lower for keyword in self.scatter_keywords)
            is_invalid = any(keyword in lower for keyword in self.non_valid_keywords)

            if is_scatter:
                scatter_options.append({"label": str(column), "value": str(column)})
            elif not is_invalid:
                fluorescence_options.append({"label": str(column), "value": str(column)})

        scatter_value = None
        fluorescence_value = None

        preferred_scatter = str(preferred_scatter or "").strip()
        preferred_fluorescence = str(preferred_fluorescence or "").strip()

        if preferred_scatter and any(o["value"] == preferred_scatter for o in scatter_options):
            scatter_value = preferred_scatter
        elif scatter_options:
            scatter_value = scatter_options[0]["value"]

        if preferred_fluorescence and any(o["value"] == preferred_fluorescence for o in fluorescence_options):
            fluorescence_value = preferred_fluorescence
        elif fluorescence_options:
            fluorescence_value = fluorescence_options[0]["value"]

        return ChannelOptions(
            scatter_options=scatter_options,
            fluorescence_options=fluorescence_options,
            scatter_value=scatter_value,
            fluorescence_value=fluorescence_value,
        )


class FluorescentCalibrationService:
    def __init__(self, *, file_state: FileStateRefresher) -> None:
        self.file_state = file_state

    def channels_from_file(
        self,
        file_path: str,
        *,
        preferred_scatter: Optional[str] = None,
        preferred_fluorescence: Optional[str] = None,
    ) -> ChannelOptions:
        return self.file_state.options_from_file(
            file_path,
            preferred_scatter=preferred_scatter,
            preferred_fluorescence=preferred_fluorescence,
        )

    @staticmethod
    def get_column_values(file_path: str, column: str, *, max_points: Optional[int] = None) -> np.ndarray:
        with FCSFile(str(file_path), writable=False) as fcs_file:
            dataframe_view = fcs_file.dataframe_view

            column = str(column)
            if column not in dataframe_view.columns:
                raise ValueError(f'Column "{column}" not found in FCS data.')

            values = dataframe_view[column].to_numpy(copy=False)

        values = np.asarray(values, dtype=float)
        values = values[np.isfinite(values)]

        if max_points is not None and values.size > int(max_points):
            values = values[: int(max_points)]

        return values

class FluorescentCalibrationIds:
    page_name = "fluorescent_calibration"

    upload = f"{page_name}-upload-data"
    upload_filename = f"{page_name}-upload-file-name"
    upload_saved_as = f"{page_name}-upload-saved-as"

    upload_cache_store = f"{page_name}-upload-cache-store"
    load_file_btn = f"{page_name}-load-file-btn"
    max_events_for_plots_input = f"{page_name}-max-events-for-plots"
    upload = f"{page_name}-upload-data"
    upload_filename = f"{page_name}-upload-file-name"
    upload_saved_as = f"{page_name}-upload-saved-as"

    uploaded_fcs_path_store = f"{page_name}-uploaded-fcs-path-store"
    calibration_store = f"{page_name}-calibration-store"
    scattering_threshold_store = f"{page_name}-scattering-threshold-store"

    scattering_detector_dropdown = f"{page_name}-scattering-detector-dropdown"
    scattering_nbins_input = f"{page_name}-scattering-nbins"
    scattering_find_threshold_btn = f"{page_name}-find-scattering-threshold-btn"
    scattering_threshold_input = f"{page_name}-scattering-threshold-input"
    scattering_yscale_switch = f"{page_name}-scattering-yscale-switch"
    graph_scattering_hist = f"{page_name}-graph-scattering-hist"

    fluorescence_detector_dropdown = f"{page_name}-fluorescence-detector-dropdown"
    fluorescence_nbins_input = f"{page_name}-fluorescence-nbins"
    fluorescence_peak_count_input = f"{page_name}-fluorescence-peak-count"
    fluorescence_find_peaks_btn = f"{page_name}-find-fluorescence-peaks-btn"
    fluorescence_yscale_switch = f"{page_name}-fluorescence-yscale-switch"
    fluorescence_source_channel_store = f"{page_name}-fluorescence-source-channel-store"
    graph_fluorescence_hist = f"{page_name}-graph-fluorescence-hist"
    fluorescence_hist_store = f"{page_name}-fluorescence-hist-store"

    bead_table = f"{page_name}-bead-spec-table"
    add_row_btn = f"{page_name}-add-row-btn"
    calibrate_btn = f"{page_name}-calibrate-btn"

    graph_calibration = f"{page_name}-graph-calibration"
    slope_out = f"{page_name}-slope-out"
    intercept_out = f"{page_name}-intercept-out"
    r_squared_out = f"{page_name}-r-squared-out"

    apply_btn = f"{page_name}-apply-btn"
    preview_div = f"{page_name}-preview-div"

    channel_name = f"{page_name}-channel-name"
    file_name = f"{page_name}-file-name"

    save_btn = f"{page_name}-save-btn"
    save_out = f"{page_name}-save-out"

    export_mode = f"{page_name}-export-mode"
    export_filename = f"{page_name}-export-filename"

    sidebar_store = "apply-calibration-store"
    sidebar_content = "sidebar-content"

    add_mesf_btn = f"{page_name}-add-mesf-btn"
    save_calibration_btn = f"{page_name}-save-calibration-btn"
    export_file_btn = f"{page_name}-export-file-btn"

    export_download = f"{page_name}-export-download"

def write_upload_to_tempfile(*, contents: str, filename: str) -> str:
    header, b64data = contents.split(",", 1)
    raw = base64.b64decode(b64data)

    suffix = Path(filename).suffix or ".bin"
    tmp_dir = Path(tempfile.gettempdir()) / "rosettax_uploads"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    out_path = tmp_dir / f"{next(tempfile._get_candidate_names())}{suffix}"
    out_path.write_bytes(raw)
    return str(out_path)
