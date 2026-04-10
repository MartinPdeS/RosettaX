from typing import Any, Optional
from dataclasses import dataclass
import numpy as np

from RosettaX.pages.fluorescence.backend import BackEnd
from RosettaX.utils.reader import FCSFile
from RosettaX.utils.plottings import make_histogram_with_lines
from RosettaX.utils.casting import _as_float, _as_int
from RosettaX.utils.runtime_config import RuntimeConfig


@dataclass(frozen=True)
class ChannelOptions:
    scatter_options: list[dict[str, str]]
    fluorescence_options: list[dict[str, str]]
    scatter_value: Optional[str]
    fluorescence_value: Optional[str]


@dataclass(frozen=True)
class FluorescenceHistogramPayload:
    figure_dict: dict[str, Any]


@dataclass(frozen=True)
class FluorescencePeakResult:
    updated_table_data: list[dict[str, Any]]
    peak_lines_payload: dict[str, list[Any]]


class FileStateRefresher:
    scatter_keywords = [
        "scatter",
        "fsc",
        "ssc",
        "sals",
        "lals",
        "mals",
        "405ls",
        "488ls",
        "638ls",
        "fs-a",
        "fs-h",
        "ss-a",
        "ss-h",
    ]

    non_valid_keywords = [
        "time",
        "width",
        "diameter",
        "cross section",
    ]

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
            lower_column = str(column).strip().lower()
            is_scatter = any(keyword in lower_column for keyword in self.scatter_keywords)
            is_invalid = any(keyword in lower_column for keyword in self.non_valid_keywords)

            if is_scatter:
                scatter_options.append({"label": str(column), "value": str(column)})
            elif not is_invalid:
                fluorescence_options.append({"label": str(column), "value": str(column)})

        scatter_value = None
        fluorescence_value = None

        preferred_scatter_clean = str(preferred_scatter or "").strip()
        preferred_fluorescence_clean = str(preferred_fluorescence or "").strip()

        if preferred_scatter_clean and any(option["value"] == preferred_scatter_clean for option in scatter_options):
            scatter_value = preferred_scatter_clean
        elif scatter_options:
            scatter_value = scatter_options[0]["value"]

        if preferred_fluorescence_clean and any(
            option["value"] == preferred_fluorescence_clean for option in fluorescence_options
        ):
            fluorescence_value = preferred_fluorescence_clean
        elif fluorescence_options:
            fluorescence_value = fluorescence_options[0]["value"]

        return ChannelOptions(
            scatter_options=scatter_options,
            fluorescence_options=fluorescence_options,
            scatter_value=scatter_value,
            fluorescence_value=fluorescence_value,
        )


class FluorescenceService:
    @staticmethod
    def resolve_scattering_threshold(
        *,
        fcs_path: str,
        scattering_channel: str,
        threshold_payload: Optional[dict],
        threshold_input_value: Any,
        max_events: int,
    ) -> float:
        runtime_config = RuntimeConfig()
        threshold_value: Optional[float] = None

        if isinstance(threshold_payload, dict):
            threshold_value = _as_float(threshold_payload.get("threshold"))

        if threshold_value is None:
            threshold_value = _as_float(threshold_input_value)

        if threshold_value is None:
            backend = BackEnd(fcs_path)
            response = backend.process_scattering(
                {
                    "operation": "estimate_scattering_threshold",
                    "column": str(scattering_channel),
                    "nbins": int(runtime_config.Default.n_bins_for_plots),
                    "number_of_points": int(max_events),
                }
            )
            threshold_value = _as_float(response.get("threshold"))

        if threshold_value is None:
            threshold_value = 0.0

        return float(threshold_value)

    @staticmethod
    def gate_fluorescence_values(
        *,
        fluorescence_values: np.ndarray,
        scattering_values: np.ndarray,
        threshold: float,
    ) -> np.ndarray:
        fluorescence_values = np.asarray(fluorescence_values, dtype=float)
        scattering_values = np.asarray(scattering_values, dtype=float)

        valid_mask = np.isfinite(fluorescence_values) & np.isfinite(scattering_values)
        gate_mask = valid_mask & (scattering_values >= float(threshold))
        return fluorescence_values[gate_mask]

    @staticmethod
    def load_fluorescence_and_scattering_values(
        *,
        fcs_path: str,
        fluorescence_channel: str,
        scattering_channel: str,
        max_events: int,
    ) -> tuple[np.ndarray, np.ndarray]:
        with FCSFile(fcs_path, writable=False) as fcs_file:
            fluorescence_values = fcs_file.column_copy(
                fluorescence_channel,
                dtype=float,
                n=max_events,
            )
            scattering_values = fcs_file.column_copy(
                scattering_channel,
                dtype=float,
                n=max_events,
            )

        return (
            np.asarray(fluorescence_values, dtype=float),
            np.asarray(scattering_values, dtype=float),
        )

    @classmethod
    def build_fluorescence_histogram_figure_dict(
        cls,
        *,
        fcs_path: str,
        scattering_channel: str,
        fluorescence_channel: str,
        fluorescence_nbins: Any,
        threshold_payload: Optional[dict],
        threshold_input_value: Any,
        max_events_for_plots: Any,
    ) -> Optional[dict[str, Any]]:
        runtime_config = RuntimeConfig()

        max_events = _as_int(
            max_events_for_plots,
            default=runtime_config.Default.max_events_for_analysis,
            min_value=10_000,
            max_value=5_000_000,
        )

        nbins = _as_int(
            fluorescence_nbins,
            default=runtime_config.Default.n_bins_for_plots,
            min_value=10,
            max_value=5000,
        )

        threshold_value = cls.resolve_scattering_threshold(
            fcs_path=fcs_path,
            scattering_channel=scattering_channel,
            threshold_payload=threshold_payload,
            threshold_input_value=threshold_input_value,
            max_events=max_events,
        )

        fluorescence_values, scattering_values = cls.load_fluorescence_and_scattering_values(
            fcs_path=fcs_path,
            fluorescence_channel=fluorescence_channel,
            scattering_channel=scattering_channel,
            max_events=max_events,
        )

        gated_values = cls.gate_fluorescence_values(
            fluorescence_values=fluorescence_values,
            scattering_values=scattering_values,
            threshold=threshold_value,
        )

        figure = make_histogram_with_lines(
            values=fluorescence_values,
            overlay_values=gated_values,
            nbins=nbins,
            xaxis_title="Fluorescence (a.u.)",
            line_positions=[],
            line_labels=[],
            base_name="all events",
            overlay_name="gated events",
        )

        return figure.to_dict()

    @staticmethod
    def inject_peak_positions_into_table(
        *,
        table_data: Optional[list[dict[str, Any]]],
        peak_positions: list[float],
    ) -> list[dict[str, Any]]:
        rows = [dict(row) for row in (table_data or [])]

        finite_peak_positions: list[float] = []
        for peak_position in peak_positions:
            try:
                value = float(peak_position)
            except Exception:
                continue
            if np.isfinite(value):
                finite_peak_positions.append(value)

        if not finite_peak_positions:
            return rows

        while len(rows) < len(finite_peak_positions):
            rows.append({"col1": "", "col2": ""})

        for row_index, peak_position in enumerate(finite_peak_positions):
            current_value = rows[row_index].get("col2", "")
            if current_value is None or str(current_value).strip() == "":
                rows[row_index]["col2"] = f"{peak_position:.6g}"

        return rows

    @classmethod
    def find_fluorescence_peaks_and_prepare_outputs(
        cls,
        *,
        fcs_path: str,
        scattering_channel: str,
        fluorescence_channel: str,
        fluorescence_peak_count: Any,
        max_events_for_plots: Any,
        scattering_threshold_payload: Optional[dict],
        scattering_threshold_input_value: Any,
        table_data: Optional[list[dict[str, Any]]],
    ) -> FluorescencePeakResult:
        runtime_config = RuntimeConfig()

        max_events = _as_int(
            max_events_for_plots,
            default=runtime_config.Default.max_events_for_analysis,
            min_value=10_000,
            max_value=5_000_000,
        )

        max_peaks = _as_int(
            fluorescence_peak_count,
            default=runtime_config.Default.peak_count,
            min_value=1,
            max_value=100,
        )

        threshold_value = cls.resolve_scattering_threshold(
            fcs_path=fcs_path,
            scattering_channel=scattering_channel,
            threshold_payload=scattering_threshold_payload,
            threshold_input_value=scattering_threshold_input_value,
            max_events=max_events,
        )

        backend = BackEnd(fcs_path)
        peaks_payload = backend.find_fluorescence_peaks(
            column=fluorescence_channel,
            max_peaks=max_peaks,
            gating_column=scattering_channel,
            gating_threshold=threshold_value,
            number_of_points=max_events,
            debug=False,
        )

        peak_positions: list[float] = []
        for raw_peak_position in peaks_payload.get("peak_positions", []) or []:
            peak_position = _as_float(raw_peak_position)
            if peak_position is not None:
                peak_positions.append(float(peak_position))

        peak_labels = [f"{peak_position:.3g}" for peak_position in peak_positions]

        updated_table_data = cls.inject_peak_positions_into_table(
            table_data=table_data,
            peak_positions=peak_positions,
        )

        peak_lines_payload = {
            "positions": peak_positions,
            "labels": peak_labels,
        }

        return FluorescencePeakResult(
            updated_table_data=updated_table_data,
            peak_lines_payload=peak_lines_payload,
        )