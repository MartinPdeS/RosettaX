# -*- coding: utf-8 -*-

from pathlib import Path
from typing import Optional, Any
import time
import io
import uuid

import numpy as np

from RosettaX.reader import FCSFile
from RosettaX.clusterings import SigmaThresholdHDBSCAN
from RosettaX.calibration import FluorescenceCalibration


class BackEnd:
    def __init__(self, file_path: Optional[str | Path] = None) -> None:
        self.file_path: Optional[Path] = None
        self.result: Optional[dict[str, Any]] = None

        if file_path is not None:
            self.set_file(file_path)

    def set_file(self, file_path: str | Path) -> None:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File {file_path} does not exist.")

        self.file_path = file_path

        # Validate it can be opened. Do not keep it open.
        last_exc: Optional[Exception] = None
        for _attempt in range(5):
            try:
                with FCSFile(self.file_path, writable=False) as _fcs_file:
                    _ = _fcs_file.text["Keywords"]
                return
            except Exception as exc:
                last_exc = exc
                time.sleep(0.05)

        raise last_exc if last_exc is not None else RuntimeError("Failed to load FCS file.")

    def get_column_names(self) -> list[str]:
        self._require_file_path()

        with FCSFile(self.file_path, writable=False) as fcs_file:
            detectors = fcs_file.text["Detectors"]
            num_parameters = int(fcs_file.text["Keywords"]["$PAR"])

            return [
                str(detectors[index].get("N", f"P{index}"))
                for index in range(1, num_parameters + 1)
            ]

    def process_scattering(self, data: dict[str, Any]) -> dict[str, Any]:
        operation = data.get("operation")
        if not operation:
            raise ValueError('Missing required key "operation" in payload.')

        if operation == "estimate_scattering_threshold":
            return self.estimate_scattering_threshold(data)

        raise ValueError(f"Unsupported scattering operation: {operation}")

    def estimate_scattering_threshold(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Required keys
        column: str

        Optional keys
        nbins: int (default 200)
        number_of_points: int | None (default 200000)
        """
        self._require_file_path()

        column = data.get("column")
        if not column:
            raise ValueError('Missing required key "column".')
        column = str(column)

        nbins = int(data.get("nbins", 200))
        if nbins < 10:
            nbins = 10
        if nbins > 5000:
            nbins = 5000

        number_of_points = data.get("number_of_points", 200_000)

        with FCSFile(self.file_path, writable=False) as fcs_file:
            values = fcs_file.column_copy(column, dtype=float)

        values = values[np.isfinite(values)]

        if number_of_points is not None:
            values = values[: int(number_of_points)]

        if values.size < 10:
            return {"threshold": 0.0, "method": "insufficient_data", "n_points": int(values.size)}

        threshold = self._otsu_threshold_1d(values=values, nbins=nbins)
        if threshold is None or not np.isfinite(threshold):
            threshold = self._robust_threshold_median_mad(values=values, k=3.0)

        if threshold is None or not np.isfinite(threshold):
            threshold = float(np.nanmin(values))

        return {
            "threshold": float(threshold),
            "method": "otsu_or_fallback",
            "n_points": int(values.size),
            "nbins": int(nbins),
        }

    def fit_fluorescence_calibration(self, data: dict[str, Any]) -> dict[str, Any]:
        mesf_values, intensity_values = self._extract_mesf_intensity(data)

        calibration = FluorescenceCalibration(MESF=mesf_values, intensity=intensity_values)

        if not hasattr(calibration, "to_dict"):
            raise ValueError("FluorescenceCalibration must implement to_dict().")

        payload = calibration.to_dict()

        if "slope" not in payload:
            payload["slope"] = float(getattr(calibration, "slope"))
        if "intercept" not in payload:
            payload["intercept"] = float(getattr(calibration, "intercept"))
        if "R_squared" not in payload:
            payload["R_squared"] = float(getattr(calibration, "R_squared"))

        payload["n_points"] = int(mesf_values.size)
        return payload

    def apply_fluorescence_calibration(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Applies calibration and optionally previews values.
        This does not write anything back to disk. For export, use export_fluorescence_calibration.
        """
        self._require_file_path()

        calibration_payload = data.get("calibration")
        if not isinstance(calibration_payload, dict):
            raise ValueError('Expected key "calibration" to be a dict.')

        column = data.get("column")
        if not column:
            raise ValueError('Missing required key "column".')
        column = str(column)

        preview_n = int(data.get("preview_n", 10))
        if preview_n < 1:
            preview_n = 1

        if not hasattr(FluorescenceCalibration, "from_dict"):
            raise ValueError("FluorescenceCalibration must implement from_dict().")

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

    def find_fluorescence_peaks(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Required keys
        column: str

        Optional keys
        max_peaks: int (default 10)
        min_cluster_size: int (default 200)
        threshold: float (default 0.0)
        number_of_points: int | None (default 40000)
        debug: bool (default False)

        Gating optional keys
        gating_column: str | None
        gating_threshold: float | None
        """
        self._require_file_path()

        column = data.get("column")
        if not column:
            raise ValueError('Missing required key "column".')
        column = str(column).strip()
        if not column:
            raise ValueError('Key "column" must be a non empty string.')

        max_peaks = int(data.get("max_peaks", 10))
        if max_peaks < 1:
            max_peaks = 1

        min_cluster_size = int(data.get("min_cluster_size", 200))
        if min_cluster_size < 2:
            min_cluster_size = 2

        threshold = float(data.get("threshold", 0.0))
        debug = bool(data.get("debug", False))
        number_of_points = data.get("number_of_points", 40_000)

        gating_column = data.get("gating_column", None)
        gating_threshold = data.get("gating_threshold", None)

        # Read owned arrays only. Do not keep dataframe_view or any view arrays alive.
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

        if values.size == 0:
            return {
                "peak_positions": [],
                "cluster_modes": [],
                "cluster_means": [],
                "cluster_sizes": [],
                "n_points": 0,
            }

        model = SigmaThresholdHDBSCAN()

        labels, means, modes, clean_data, clean_mask = model.fit(
            x=values,
            n_clusters=int(max_peaks),
            threshold_x=float(threshold),
            min_cluster_size=int(min_cluster_size),
            debug=debug,
        )

        labels = np.asarray(labels)
        means = np.asarray(means, dtype=float).squeeze()
        modes = np.asarray(modes, dtype=float).squeeze()

        labels = np.atleast_1d(labels)
        means = np.atleast_1d(means)
        modes = np.atleast_1d(modes)

        if modes.size == 0:
            return {
                "peak_positions": [],
                "cluster_modes": [],
                "cluster_means": [],
                "cluster_sizes": [],
                "n_points": int(values.size),
            }

        # Count sizes by label from returned labels (ignore noise = -1)
        good_labels = labels[labels >= 0]
        if good_labels.size == 0:
            return {
                "peak_positions": [],
                "cluster_modes": [],
                "cluster_means": [],
                "cluster_sizes": [],
                "n_points": int(values.size),
            }

        unique_labels, counts = np.unique(good_labels, return_counts=True)
        size_by_label = {int(lab): int(cnt) for lab, cnt in zip(unique_labels, counts)}

        # Build clusters using the returned label ids when possible.
        clusters: list[dict[str, Any]] = []
        for idx in range(int(modes.size)):
            mode_val = float(modes[idx])
            if not np.isfinite(mode_val):
                continue

            mean_val = float(means[idx]) if idx < means.size and np.isfinite(means[idx]) else float("nan")

            # If your SigmaThresholdHDBSCAN orders modes by label index, idx matches label.
            # If it doesn't, you should return explicit label ids from model.fit.
            label = int(idx)
            cluster_size = int(size_by_label.get(label, 0))

            clusters.append({"label": label, "mode": mode_val, "mean": mean_val, "size": cluster_size})

        # Keep only clusters that actually exist in labels
        clusters = [c for c in clusters if c["size"] > 0]

        if not clusters:
            return {
                "peak_positions": [],
                "cluster_modes": [],
                "cluster_means": [],
                "cluster_sizes": [],
                "n_points": int(values.size),
            }

        clusters.sort(key=lambda d: d["size"], reverse=True)
        clusters = clusters[: int(max_peaks)]
        clusters.sort(key=lambda d: d["mode"])

        peak_positions = [float(d["mode"]) for d in clusters]
        cluster_means = [float(d["mean"]) for d in clusters]
        cluster_sizes = [int(d["size"]) for d in clusters]

        return {
            "peak_positions": peak_positions,
            "cluster_modes": peak_positions,
            "cluster_means": cluster_means,
            "cluster_sizes": cluster_sizes,
            "n_points": int(values.size),
        }


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
            raise ValueError('"mode" must be "update_temp" or "save_new".')

        calibration = FluorescenceCalibration.from_dict(cal_payload)

        last_exc: Optional[Exception] = None
        for _attempt in range(5):
            try:
                with FCSFile(source_path, writable=False) as template:
                    df = template.dataframe_copy(deep=True)

                    if source_column not in df.columns:
                        raise ValueError(f'Column "{source_column}" not found.')

                    x = np.asarray(df[source_column].to_numpy(copy=False), dtype=float)
                    y = np.asarray(calibration.calibrate(x), dtype=np.float32)

                    # Write new column
                    df[new_column] = y

                    # Build writer: do NOT force float32 if you want fidelity
                    builder = FCSFile.builder_from_dataframe(
                        df,
                        template=template,
                        force_float32=True,
                    )

                    if mode == "update_temp":
                        tmp = source_path.with_name(
                            f"{source_path.stem}_calibrated_{uuid.uuid4().hex}{source_path.suffix}"
                        )
                        builder.write(tmp)
                        return {
                            "exported_path": str(tmp),
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
                last_exc = exc
                time.sleep(0.05)

        raise last_exc if last_exc is not None else RuntimeError("Failed to export calibrated FCS.")













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

        mesf_vals: list[float] = []
        intensity_vals: list[float] = []

        for row in table_data:
            if not isinstance(row, dict):
                continue

            mesf = BackEnd._safe_float(row.get("col1"))
            intensity = BackEnd._safe_float(row.get("col2"))

            if mesf is None or intensity is None:
                continue

            mesf_vals.append(mesf)
            intensity_vals.append(intensity)

        if len(mesf_vals) < 2:
            raise ValueError("Need at least 2 valid (MESF, intensity) points in the table.")

        return np.asarray(mesf_vals, dtype=float), np.asarray(intensity_vals, dtype=float)

    @staticmethod
    def _safe_float(value: Any) -> Optional[float]:
        if value is None:
            return None

        if isinstance(value, (int, float)):
            v = float(value)
            return v if np.isfinite(v) else None

        if isinstance(value, str):
            s = value.strip()
            if not s:
                return None
            try:
                v = float(s)
            except ValueError:
                return None
            return v if np.isfinite(v) else None

        return None

    @staticmethod
    def _otsu_threshold_1d(values: np.ndarray, nbins: int) -> Optional[float]:
        values = np.asarray(values, dtype=float)
        values = values[np.isfinite(values)]
        if values.size < 10:
            return None

        vmin = float(np.min(values))
        vmax = float(np.max(values))
        if not np.isfinite(vmin) or not np.isfinite(vmax) or vmax <= vmin:
            return None

        hist, bin_edges = np.histogram(values, bins=int(nbins), range=(vmin, vmax))
        hist = hist.astype(float)
        total = float(np.sum(hist))
        if total <= 0:
            return None

        prob = hist / total
        bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])

        omega = np.cumsum(prob)
        mu = np.cumsum(prob * bin_centers)
        mu_total = mu[-1]

        denom = omega * (1.0 - omega)
        denom[denom <= 0] = np.nan

        sigma_b2 = (mu_total * omega - mu) ** 2 / denom
        if not np.any(np.isfinite(sigma_b2)):
            return None

        best_index = int(np.nanargmax(sigma_b2))
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




