# -*- coding: utf-8 -*-
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional
import logging
import time
import uuid

import numpy as np

from RosettaX.utils.reader import FCSFile
from RosettaX.utils.casting import _as_float, _as_int
from RosettaX.utils.plottings import make_histogram_with_lines
from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.utils.peak_detection import (
    find_1d_signal_peaks,
    inject_peak_positions_into_table,
)


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FluorescencePeakResult:
    """
    Output payload for fluorescence peak finding and table injection.
    """

    updated_table_data: list[dict[str, Any]]
    peak_lines_payload: dict[str, list[Any]]


class FluorescenceCalibration:
    """
    Linear calibration mapping intensity in arbitrary units to MESF.
    """

    def __init__(self, MESF: np.ndarray, intensity: np.ndarray):
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

        logger.debug(
            "Fitted FluorescenceCalibration with n_points=%r slope=%r intercept=%r R_squared=%r",
            x.size,
            self.slope,
            self.intercept,
            self.R_squared,
        )

    def calibrate(self, intensity: np.ndarray) -> np.ndarray:
        x = np.asarray(intensity, dtype=float)
        return self.slope * x + self.intercept

    def calculate_r_squared(self) -> float:
        y_pred = self.slope * self.intensity + self.intercept
        ss_res = np.sum((self.MESF - y_pred) ** 2)
        ss_tot = np.sum((self.MESF - self.MESF.mean()) ** 2)

        if ss_tot == 0:
            return 1.0 if ss_res == 0 else 0.0

        return float(1.0 - ss_res / ss_tot)

    def to_dict(self) -> dict[str, float]:
        return {
            "slope": float(self.slope),
            "intercept": float(self.intercept),
            "R_squared": float(self.R_squared),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "FluorescenceCalibration":
        obj = cls.__new__(cls)
        obj.slope = float(payload["slope"])
        obj.intercept = float(payload["intercept"])
        obj.R_squared = float(payload["R_squared"])
        obj.intensity = np.array([], dtype=float)
        obj.MESF = np.array([], dtype=float)
        return obj


class BackEnd:
    """
    File bound analysis backend for fluorescence and scattering operations.
    """

    def __init__(self, file_path: Optional[str | Path] = None) -> None:
        self.file_path: Optional[Path] = None

        if file_path is not None:
            self.set_file(file_path)

    def _get_runtime_config(self) -> RuntimeConfig:
        return RuntimeConfig()

    def _get_calibration_max_events_for_analysis(self) -> int:
        runtime_config = self._get_runtime_config()
        return int(
            runtime_config.get_path(
                "calibration.max_events_for_analysis",
                default=10000,
            )
        )

    def _get_calibration_n_bins_for_plots(self) -> int:
        runtime_config = self._get_runtime_config()
        return int(
            runtime_config.get_path(
                "calibration.n_bins_for_plots",
                default=100,
            )
        )

    def _get_calibration_peak_count(self) -> int:
        runtime_config = self._get_runtime_config()
        return int(
            runtime_config.get_path(
                "calibration.peak_count",
                default=4,
            )
        )

    def set_file(self, file_path: str | Path) -> None:
        file_path = Path(file_path)
        logger.debug("BackEnd.set_file called with file_path=%r", str(file_path))

        if not file_path.exists():
            raise FileNotFoundError(f"File {file_path} does not exist.")

        self.file_path = file_path

        last_exception: Optional[Exception] = None
        for _attempt in range(5):
            try:
                with FCSFile(self.file_path, writable=False) as fcs_file:
                    _ = fcs_file.text["Keywords"]
                logger.debug("Validated FCS file successfully at file_path=%r", str(file_path))
                return
            except Exception as exc:
                last_exception = exc
                time.sleep(0.05)

        raise last_exception if last_exception is not None else RuntimeError("Failed to load FCS file.")

    def get_column_names(self) -> list[str]:
        self._require_file_path()

        with FCSFile(self.file_path, writable=False) as fcs_file:
            detectors = fcs_file.text["Detectors"]
            parameter_count = int(fcs_file.text["Keywords"]["$PAR"])

            column_names = [
                str(detectors[index].get("N", f"P{index}"))
                for index in range(1, parameter_count + 1)
            ]

        logger.debug("Loaded %r detector column names.", len(column_names))
        return column_names

    def process_scattering(self, data: dict[str, Any]) -> dict[str, Any]:
        operation = data.get("operation")
        if not operation:
            raise ValueError('Missing required key "operation" in payload.')

        if operation == "estimate_scattering_threshold":
            return self.estimate_scattering_threshold(data)

        raise ValueError(f"Unsupported scattering operation: {operation}")

    def estimate_scattering_threshold(self, data: dict[str, Any]) -> dict[str, Any]:
        self._require_file_path()

        column = str(data.get("column") or "").strip()
        if not column:
            raise ValueError('Missing required key "column".')

        nbins = int(data.get("nbins", 200))
        nbins = max(10, min(5000, nbins))

        number_of_points = data.get("number_of_points", 200_000)

        with FCSFile(self.file_path, writable=False) as fcs_file:
            values = fcs_file.column_copy(column, dtype=float)

        values = np.asarray(values, dtype=float)
        values = values[np.isfinite(values)]

        if number_of_points is not None:
            values = values[: int(number_of_points)]

        if values.size < 10:
            return {
                "threshold": 0.0,
                "method": "insufficient_data",
                "n_points": int(values.size),
                "nbins": int(nbins),
            }

        threshold = self._otsu_threshold_1d(values=values, nbins=nbins)
        if threshold is None or not np.isfinite(threshold):
            threshold = self._robust_threshold_median_mad(values=values, k=3.0)

        if threshold is None or not np.isfinite(threshold):
            threshold = float(np.nanmin(values))

        result = {
            "threshold": float(threshold),
            "method": "otsu_or_fallback",
            "n_points": int(values.size),
            "nbins": int(nbins),
        }
        logger.debug("Estimated scattering threshold result=%r", result)
        return result

    def resolve_scattering_threshold(
        self,
        *,
        scattering_channel: str,
        threshold_payload: Optional[dict],
        threshold_input_value: Any,
        max_events: int,
    ) -> float:
        threshold_value: Optional[float] = None

        if isinstance(threshold_payload, dict):
            threshold_value = _as_float(threshold_payload.get("threshold"))

        if threshold_value is None:
            threshold_value = _as_float(threshold_input_value)

        if threshold_value is None:
            response = self.process_scattering(
                {
                    "operation": "estimate_scattering_threshold",
                    "column": str(scattering_channel),
                    "nbins": self._get_calibration_n_bins_for_plots(),
                    "number_of_points": int(max_events),
                }
            )
            threshold_value = _as_float(response.get("threshold"))

        if threshold_value is None:
            threshold_value = 0.0

        return float(threshold_value)

    def load_fluorescence_and_scattering_values(
        self,
        *,
        fluorescence_channel: str,
        scattering_channel: str,
        max_events: int,
    ) -> tuple[np.ndarray, np.ndarray]:
        self._require_file_path()

        with FCSFile(self.file_path, writable=False) as fcs_file:
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

    def build_fluorescence_histogram_figure_dict(
        self,
        *,
        scattering_channel: str,
        fluorescence_channel: str,
        fluorescence_nbins: Any,
        threshold_payload: Optional[dict],
        threshold_input_value: Any,
        max_events_for_plots: Any,
    ) -> dict[str, Any]:
        max_events = _as_int(
            max_events_for_plots,
            default=self._get_calibration_max_events_for_analysis(),
            min_value=10_000,
            max_value=5_000_000,
        )

        nbins = _as_int(
            fluorescence_nbins,
            default=self._get_calibration_n_bins_for_plots(),
            min_value=10,
            max_value=5000,
        )

        threshold_value = self.resolve_scattering_threshold(
            scattering_channel=scattering_channel,
            threshold_payload=threshold_payload,
            threshold_input_value=threshold_input_value,
            max_events=max_events,
        )

        fluorescence_values, scattering_values = self.load_fluorescence_and_scattering_values(
            fluorescence_channel=fluorescence_channel,
            scattering_channel=scattering_channel,
            max_events=max_events,
        )

        gated_values = self.gate_fluorescence_values(
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

    def find_fluorescence_peaks_and_prepare_outputs(
        self,
        *,
        scattering_channel: str,
        fluorescence_channel: str,
        fluorescence_peak_count: Any,
        max_events_for_plots: Any,
        scattering_threshold_payload: Optional[dict],
        scattering_threshold_input_value: Any,
        table_data: Optional[list[dict[str, Any]]],
    ) -> FluorescencePeakResult:
        max_events = _as_int(
            max_events_for_plots,
            default=self._get_calibration_max_events_for_analysis(),
            min_value=10_000,
            max_value=5_000_000,
        )

        max_peaks = _as_int(
            fluorescence_peak_count,
            default=self._get_calibration_peak_count(),
            min_value=1,
            max_value=100,
        )

        threshold_value = self.resolve_scattering_threshold(
            scattering_channel=scattering_channel,
            threshold_payload=scattering_threshold_payload,
            threshold_input_value=scattering_threshold_input_value,
            max_events=max_events,
        )

        peaks_payload = self.find_fluorescence_peaks(
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

        updated_table_data = inject_peak_positions_into_table(
            table_data=table_data,
            peak_positions=peak_positions,
            peak_column_id="col2",
            default_row_factory=lambda: {"col1": "", "col2": ""},
        )

        peak_lines_payload = {
            "positions": peak_positions,
            "labels": peak_labels,
        }

        return FluorescencePeakResult(
            updated_table_data=updated_table_data,
            peak_lines_payload=peak_lines_payload,
        )

    def fit_fluorescence_calibration(self, data: dict[str, Any]) -> dict[str, Any]:
        mesf_values, intensity_values = self._extract_mesf_intensity(data)

        calibration = FluorescenceCalibration(MESF=mesf_values, intensity=intensity_values)
        payload = calibration.to_dict()
        payload["n_points"] = int(mesf_values.size)
        return payload

    def apply_fluorescence_calibration(self, data: dict[str, Any]) -> dict[str, Any]:
        self._require_file_path()

        calibration_payload = data.get("calibration")
        if not isinstance(calibration_payload, dict):
            raise ValueError('Expected key "calibration" to be a dict.')

        column = str(data.get("column") or "").strip()
        if not column:
            raise ValueError('Missing required key "column".')

        preview_n = int(data.get("preview_n", 10))
        preview_n = max(1, preview_n)

        calibration = FluorescenceCalibration.from_dict(calibration_payload)

        with FCSFile(self.file_path, writable=False) as fcs_file:
            uncalibrated = fcs_file.column_copy(column, dtype=float)

        calibrated = calibration.calibrate(uncalibrated)
        calibrated_array = np.asarray(calibrated, dtype=float)

        return {
            "n_points": int(calibrated_array.size),
            "preview": calibrated_array[:preview_n].tolist(),
            "output_column": data.get("output_column", None),
        }

    def find_fluorescence_peaks(
        self,
        column: str,
        max_peaks: int = 10,
        min_cluster_size: int = 100,
        threshold: float = 0.0,
        gating_column: str | None = None,
        gating_threshold: float = 0.0,
        number_of_points: int | None = 40_000,
        debug: bool = False,
    ) -> dict[str, Any]:
        self._require_file_path()

        if not column:
            raise ValueError('Missing required key "column".')

        column = str(column).strip()
        if not column:
            raise ValueError('Key "column" must be a non empty string.')

        max_peaks = max(1, int(max_peaks))
        min_cluster_size = max(2, int(min_cluster_size))

        with FCSFile(self.file_path, writable=False) as fcs_file:
            fluorescence_values = fcs_file.column_copy(
                column,
                dtype=float,
                n=number_of_points if number_of_points is not None else None,
            )

            scattering_values = None
            gating_threshold_value = None

            if gating_column is not None:
                gating_column = str(gating_column).strip()
                if gating_column:
                    scattering_values = fcs_file.column_copy(
                        gating_column,
                        dtype=float,
                        n=number_of_points if number_of_points is not None else None,
                    )
                    if gating_threshold is not None:
                        gating_threshold_value = float(gating_threshold)

        fluorescence_values = np.asarray(fluorescence_values, dtype=float)

        if scattering_values is not None:
            scattering_values = np.asarray(scattering_values, dtype=float)
            mask = np.isfinite(fluorescence_values) & np.isfinite(scattering_values)

            if gating_threshold_value is not None and np.isfinite(gating_threshold_value):
                mask = mask & (scattering_values >= float(gating_threshold_value))

            values = fluorescence_values[mask]
        else:
            values = fluorescence_values[np.isfinite(fluorescence_values)]

        peak_result = find_1d_signal_peaks(
            values=values,
            max_peaks=max_peaks,
            min_cluster_size=min_cluster_size,
            threshold=threshold,
            debug=debug,
        )

        return peak_result.to_dict()

    def export_fluorescence_calibration(self, data: dict[str, Any]) -> dict[str, Any]:
        cal_payload = data.get("calibration")
        if not isinstance(cal_payload, dict):
            raise ValueError('Expected "calibration" to be a dict.')

        source_path = Path(data.get("source_path") or self.file_path)  # type: ignore[arg-type]
        if source_path is None:
            raise ValueError('Missing "source_path".')

        source_column = str(data.get("source_column") or "").strip()
        if not source_column:
            raise ValueError('Missing "source_column".')

        new_column = str(data.get("new_column") or "").strip()
        if not new_column:
            raise ValueError('Missing "new_column".')

        mode = str(data.get("mode", "save_new")).strip()
        if mode not in {"update_temp", "save_new"}:
            raise ValueError(f'"mode" must be "update_temp" or "save_new". Got "{mode}".')

        calibration = FluorescenceCalibration.from_dict(cal_payload)

        last_exception: Optional[Exception] = None
        for _attempt in range(5):
            try:
                with FCSFile(source_path, writable=False) as template:
                    dataframe = template.dataframe_copy(deep=True)

                    if source_column not in dataframe.columns:
                        raise ValueError(f'Column "{source_column}" not found.')

                    x = np.asarray(dataframe[source_column].to_numpy(copy=False), dtype=float)
                    y = np.asarray(calibration.calibrate(x), dtype=np.float32)

                    dataframe[new_column] = y

                    builder = FCSFile.builder_from_dataframe(
                        dataframe,
                        template=template,
                        force_float32=True,
                    )

                    if mode == "update_temp":
                        temporary_path = source_path.with_name(
                            f"{source_path.stem}_calibrated_{uuid.uuid4().hex}{source_path.suffix}"
                        )
                        builder.write(temporary_path)

                        return {
                            "exported_path": str(temporary_path),
                            "mode": mode,
                            "source_column": source_column,
                            "new_column": new_column,
                            "n_points": int(y.size),
                            "dtype": np.float32,
                        }

                    export_filename = str(data.get("export_filename") or "").strip()
                    if not export_filename:
                        raise ValueError('Missing "export_filename" when mode="save_new".')

                    export_name = Path(export_filename).with_suffix(".fcs").name
                    payload_bytes = builder.build_bytes()

                    if not payload_bytes:
                        raise RuntimeError("FCS export produced empty payload.")

                    return {
                        "exported_bytes": payload_bytes,
                        "export_name": export_name,
                        "mode": mode,
                        "source_column": source_column,
                        "new_column": new_column,
                        "n_points": int(y.size),
                        "dtype": np.float32,
                    }

            except Exception as exc:
                last_exception = exc
                time.sleep(0.05)

        raise last_exception if last_exception is not None else RuntimeError("Failed to export calibrated FCS.")

    def _require_file_path(self) -> None:
        if self.file_path is None:
            raise RuntimeError("No FCS file set in BackEnd. Call set_file() first.")

    @staticmethod
    def _extract_mesf_intensity(data: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
        if "MESF" in data and "intensity" in data:
            mesf_values = np.asarray(data["MESF"], dtype=float).squeeze()
            intensity_values = np.asarray(data["intensity"], dtype=float).squeeze()
        elif "table_data" in data:
            mesf_values, intensity_values = BackEnd._extract_mesf_intensity_from_table(data["table_data"])
        else:
            raise ValueError('Expected either ("MESF","intensity") or "table_data" in payload.')

        if mesf_values.size != intensity_values.size:
            raise ValueError("MESF and intensity must have the same length.")
        if mesf_values.size < 2:
            raise ValueError("Need at least 2 calibration points.")
        if not np.all(np.isfinite(mesf_values)) or not np.all(np.isfinite(intensity_values)):
            raise ValueError("MESF and intensity must be finite numbers.")

        return mesf_values, intensity_values

    @staticmethod
    def _extract_mesf_intensity_from_table(table_data: Any) -> tuple[np.ndarray, np.ndarray]:
        if not isinstance(table_data, list):
            raise ValueError("table_data must be a list of row dicts")

        mesf_values: list[float] = []
        intensity_values: list[float] = []

        for row in table_data:
            if not isinstance(row, dict):
                continue

            mesf = BackEnd._safe_float(row.get("col1"))
            intensity = BackEnd._safe_float(row.get("col2"))

            if mesf is None or intensity is None:
                continue

            mesf_values.append(mesf)
            intensity_values.append(intensity)

        if len(mesf_values) < 2:
            raise ValueError("Need at least 2 valid (MESF, intensity) points in the table.")

        return np.asarray(mesf_values, dtype=float), np.asarray(intensity_values, dtype=float)

    @staticmethod
    def _safe_float(value: Any) -> Optional[float]:
        if value is None:
            return None

        if isinstance(value, (int, float)):
            parsed_value = float(value)
            return parsed_value if np.isfinite(parsed_value) else None

        if isinstance(value, str):
            stripped_value = value.strip()
            if not stripped_value:
                return None
            try:
                parsed_value = float(stripped_value)
            except ValueError:
                return None
            return parsed_value if np.isfinite(parsed_value) else None

        return None

    @staticmethod
    def _otsu_threshold_1d(values: np.ndarray, nbins: int) -> Optional[float]:
        values = np.asarray(values, dtype=float)
        values = values[np.isfinite(values)]

        if values.size < 10:
            return None

        minimum_value = float(np.min(values))
        maximum_value = float(np.max(values))
        if not np.isfinite(minimum_value) or not np.isfinite(maximum_value) or maximum_value <= minimum_value:
            return None

        histogram, bin_edges = np.histogram(values, bins=int(nbins), range=(minimum_value, maximum_value))
        histogram = histogram.astype(float)

        total = float(np.sum(histogram))
        if total <= 0:
            return None

        probability = histogram / total
        bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])

        omega = np.cumsum(probability)
        mu = np.cumsum(probability * bin_centers)
        mu_total = mu[-1]

        denominator = omega * (1.0 - omega)
        denominator[denominator <= 0] = np.nan

        sigma_between = (mu_total * omega - mu) ** 2 / denominator
        if not np.any(np.isfinite(sigma_between)):
            return None

        best_index = int(np.nanargmax(sigma_between))
        threshold = float(bin_centers[best_index])

        return threshold if np.isfinite(threshold) else None

    @staticmethod
    def _robust_threshold_median_mad(values: np.ndarray, k: float) -> Optional[float]:
        values = np.asarray(values, dtype=float)
        values = values[np.isfinite(values)]

        if values.size < 10:
            return None

        median_value = float(np.median(values))
        mad = float(np.median(np.abs(values - median_value)))

        if not np.isfinite(median_value) or not np.isfinite(mad):
            return None

        sigma_estimate = 1.4826 * mad
        threshold = median_value + float(k) * sigma_estimate

        return float(threshold) if np.isfinite(threshold) else None