from typing import Optional
from dataclasses import dataclass
import numpy as np

from RosettaX.reader import FCSFile
import plotly.graph_objs as go

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

    @staticmethod
    def add_vertical_lines(
        *,
        fig: go.Figure,
        line_positions: list[float],
        line_labels: Optional[list[str]] = None,
        line_width: int = 2,
        line_dash: str = "dash",
        annotation_y: float = 1.02,
    ) -> go.Figure:
        """
        Adds vertical lines (and optional labels) to an existing Plotly figure.

        Notes
        - Uses yref="paper" so the line spans the full plot height.
        - Safe to call repeatedly: it only appends new shapes/annotations.
        """
        if line_labels is None:
            line_labels = []

        # Pad labels to match positions
        if len(line_labels) < len(line_positions):
            line_labels = list(line_labels) + [""] * (len(line_positions) - len(line_labels))

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
                line={"width": int(line_width), "dash": str(line_dash)},
            )

            label_str = str(label).strip()
            if label_str:
                fig.add_annotation(
                    x=xv,
                    y=float(annotation_y),
                    xref="x",
                    yref="paper",
                    text=label_str,
                    showarrow=False,
                    textangle=-45,
                    xanchor="left",
                    yanchor="bottom",
                    align="left",
                    bgcolor="rgba(255,255,255,0.6)",
                )

        return fig