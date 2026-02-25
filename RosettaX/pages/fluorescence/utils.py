# -*- coding: utf-8 -*-
from typing import Optional

import numpy as np
import plotly.graph_objs as go


class FluorescenceCalibration:
    """
    Linear calibration mapping intensity (a.u.) to MESF.

    Model
    -----
    MESF = slope * intensity + intercept
    """

    def __init__(self, MESF: np.ndarray, intensity: np.ndarray):
        """
        Parameters
        ----------
        MESF : np.ndarray
            Molecules of Equivalent Soluble Fluorochrome.
        intensity
            Fluorescence intensity (a.u.).
        """
        x = np.asarray(intensity, dtype=float).reshape(-1)
        y = np.asarray(MESF, dtype=float).reshape(-1)

        mask = np.isfinite(x) & np.isfinite(y)
        x = x[mask]
        y = y[mask]

        if x.size < 2:
            raise ValueError("Need at least two valid points to fit calibration.")

        self.intensity = x
        self.MESF = y
        self.slope, self.intercept = np.polyfit(self.intensity, self.MESF, 1)
        self.R_squared = self.calculate_r_squared()

    def calibrate(self, intensity: np.ndarray) -> np.ndarray:
        """
        Convert intensity values (a.u.) into MESF using the fitted linear model.

        Parameters
        ----------
        intensity : np.ndarray
            Fluorescence intensity (a.u.) to calibrate.

        Returns
        -------
        np.ndarray
            Calibrated MESF values corresponding to the input intensities.
        """
        x = np.asarray(intensity, dtype=float)
        return self.slope * x + self.intercept

    def calculate_r_squared(self) -> float:
        """
        Calculate the coefficient of determination (R²) for the fitted model.

        R² = 1 - (SS_res / SS_tot)

        Returns
        -------
        float
            R² value indicating the goodness of fit (1.0 is perfect fit, 0.
        """
        y_pred = self.slope * self.intensity + self.intercept
        ss_res = np.sum((self.MESF - y_pred) ** 2)
        ss_tot = np.sum((self.MESF - self.MESF.mean()) ** 2)
        if ss_tot == 0:
            R_squared = 1.0 if ss_res == 0 else 0.0
        else:
            R_squared = 1.0 - ss_res / ss_tot
        return R_squared

    def to_dict(self) -> dict:
        """
        Serialize calibration parameters for storage in Dash (dcc.Store).

        Returns
        -------
        dict
            Dictionary containing slope, intercept, and R² for the calibration.
        """
        return {"slope": float(self.slope), "intercept": float(self.intercept), "R_squared": float(self.R_squared)}

    @classmethod
    def from_dict(cls, payload: dict) -> "FluorescenceCalibration":
        """
        Reconstruct a calibration from stored parameters.

        Notes
        -----
        This builds an instance without refitting. It is useful when you want the same API.

        Parameters
        ----------
        payload : dict
            Dictionary containing slope, intercept, and R² for the calibration.

        Returns
        -------
        FluorescenceCalibration
            An instance of FluorescenceCalibration with parameters set from the payload.
        """
        obj = cls.__new__(cls)
        obj.slope = float(payload["slope"])
        obj.intercept = float(payload["intercept"])
        obj.R_squared = float(payload["R_squared"])
        obj.intensity = np.array([], dtype=float)
        obj.MESF = np.array([], dtype=float)
        return obj


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
    """
    Build a histogram figure with optional vertical lines.

    Parameters
    ----------
    values : np.ndarray
        Array of values to plot in the histogram.
    nbins : int
        Number of bins for the histogram.
    xaxis_title : str
        Label for the x axis.
    line_positions : list[float]
        X positions for vertical lines to indicate peaks or thresholds.
    line_labels : list[str]
        Labels corresponding to each vertical line.
    overlay_values : Optional[np.ndarray]
        Optional second set of values to overlay as a second histogram (e.g. gated events).
    base_name : str
        Legend name for the main histogram.
    overlay_name : str
        Legend name for the overlay histogram.
    title : Optional[str]
        Optional title for the figure.
    """
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

    Parameters
    ----------
    fig : go.Figure
        Existing figure to add lines to.
    line_positions : list[float]
        X positions of vertical lines to add.
    line_labels : Optional[list[str]]
        Optional labels for each line. If fewer labels than positions, remaining will be empty.
    line_width : int
        Width of the vertical lines.
    line_dash : str
        Dash style for the vertical lines (e.g. "dash", "dot", "solid").
    annotation_y : float
        Y position in paper coordinates for the line labels.

    Returns
    -------
    go.Figure
        The same figure instance with new lines and annotations added.
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