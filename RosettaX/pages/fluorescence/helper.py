from typing import Any, Optional
from pathlib import Path
import base64
import tempfile
from dataclasses import dataclass
import numpy as np
import plotly.graph_objs as go

from RosettaX.backend import BackEnd

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
        backend = BackEnd(file_path)
        columns = list(getattr(backend.fcs_file, "data").columns)

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


class CalibrationSetupStore:
    @staticmethod
    def save_fluorescent_setup(sidebar_data: Optional[dict[str, Any]], *, name: str, payload: dict[str, Any]) -> dict[str, Any]:
        next_sidebar = dict(sidebar_data or {})
        next_sidebar.setdefault("Fluorescent", [])
        next_sidebar.setdefault("Scatter", [])
        next_sidebar.setdefault("payloads", {})

        next_sidebar["Fluorescent"] = list(next_sidebar["Fluorescent"])
        if name not in next_sidebar["Fluorescent"]:
            next_sidebar["Fluorescent"].append(name)

        next_sidebar["payloads"][f"Fluorescent/{name}"] = dict(payload)
        return next_sidebar

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




def write_upload_to_tempfile(*, contents: str, filename: str) -> str:
    header, b64data = contents.split(",", 1)
    raw = base64.b64decode(b64data)

    suffix = Path(filename).suffix or ".bin"
    tmp_dir = Path(tempfile.gettempdir()) / "rosettax_uploads"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    out_path = tmp_dir / f"{next(tempfile._get_candidate_names())}{suffix}"
    out_path.write_bytes(raw)
    return str(out_path)

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
    def get_column_values(backend: BackEnd, column: str, *, max_points: Optional[int] = None) -> np.ndarray:
        values = backend.fcs_file.data[str(column)].to_numpy(dtype=float)
        values = np.asarray(values, dtype=float)
        values = values[np.isfinite(values)]

        if max_points is not None and values.size > int(max_points):
            values = values[: int(max_points)]

        return values

    @staticmethod
    def apply_gate(*, fluorescence_values: np.ndarray, scattering_values: np.ndarray, threshold: float) -> np.ndarray:
        fluorescence_values = np.asarray(fluorescence_values, dtype=float)
        scattering_values = np.asarray(scattering_values, dtype=float)

        mask = np.isfinite(fluorescence_values) & np.isfinite(scattering_values)
        mask = mask & (scattering_values >= float(threshold))

        return fluorescence_values[mask]

    @staticmethod
    def make_histogram_with_lines(
        *,
        values: np.ndarray,
        nbins: int,
        xaxis_title: str,
        line_positions: list[float],
        line_labels: list[str],
        overlay_values: Optional[np.ndarray] = None,
        base_name: str = "all events",
        overlay_name: str = "gated events",
        title: Optional[str] = None,
    ) -> go.Figure:
        values = np.asarray(values, dtype=float)
        values = values[np.isfinite(values)]

        overlay = None
        if overlay_values is not None:
            overlay = np.asarray(overlay_values, dtype=float)
            overlay = overlay[np.isfinite(overlay)]

        fig = go.Figure()

        fig.add_trace(
            go.Histogram(
                x=values,
                nbinsx=int(nbins),
                name=str(base_name),
                opacity=0.55 if overlay is not None else 1.0,
                bingroup="hist",
            )
        )

        if overlay is not None:
            fig.add_trace(
                go.Histogram(
                    x=overlay,
                    nbinsx=int(nbins),
                    name=str(overlay_name),
                    opacity=0.85,
                    bingroup="hist",
                )
            )

        for x, label in zip(line_positions, line_labels):
            try:
                xv = float(x)
            except Exception:
                continue
            if not np.isfinite(xv):
                continue

            fig.add_shape(
                type="line",
                x0=xv,
                x1=xv,
                y0=0,
                y1=1,
                xref="x",
                yref="paper",
                line={"width": 2, "dash": "dash"},
            )

            fig.add_annotation(
                x=xv,
                y=1.02,
                xref="x",
                yref="paper",
                text=str(label),
                showarrow=False,
                textangle=-45,
                xanchor="left",
                yanchor="bottom",
                align="left",
                bgcolor="rgba(255,255,255,0.6)",
            )

        fig.update_layout(
            title="" if title is None else str(title),
            xaxis_title=xaxis_title,
            yaxis_title="Count",
            bargap=0.02,
            showlegend=(overlay is not None),
            separators=".,",
            barmode="overlay",
            hovermode="x unified",
            xaxis={"showspikes": True, "spikemode": "across", "spikesnap": "cursor"},
        )

        return fig