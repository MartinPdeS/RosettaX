from __future__ import annotations

from pathlib import Path
from typing import Optional, Any
import shutil

import numpy as np

from RosettaX.reader import FCSFile
from RosettaX.clusterings import SigmaThresholdHDBSCAN
from RosettaX.calibration import FluorescenceCalibration


class BackEnd:
    def __init__(self, file_path: Optional[str | Path] = None) -> None:
        self.file_path: Optional[Path] = None
        self.fcs_file: Optional[FCSFile] = None
        self.result: Optional[dict[str, Any]] = None

        if file_path is not None:
            self.set_file(file_path)

    def set_file(self, file_path: str | Path) -> None:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File {file_path} does not exist.")

        self.file_path = file_path
        self.fcs_file = FCSFile(self.file_path)
        self.fcs_file.read_all_data()

    def process_scattering(self, data: dict[str, Any]) -> dict[str, Any]:
        operation = data.get("operation")
        if not operation:
            raise ValueError('Missing required key "operation" in payload.')

        if operation == "estimate_scattering_threshold":
            return self.estimate_scattering_threshold(data)

        raise ValueError(f"Unsupported scattering operation: {operation}")

    def estimate_scattering_threshold(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Estimate a scattering threshold separating low level noise from events.

        Required keys
        - column: str

        Optional keys
        - nbins: int (default 200)
        - number_of_points: int | None (default 200000)

        Implementation
        - Compute histogram on finite values
        - Apply Otsu threshold on the histogram
        - Fallback to median + 3*MAD when Otsu is ill conditioned
        """
        self._require_fcs_loaded()

        column = data.get("column")
        if not column:
            raise ValueError('Missing required key "column".')
        column = str(column)

        if column not in self.fcs_file.data:
            raise ValueError(f'Column "{column}" not found in FCS data.')

        nbins = int(data.get("nbins", 200))
        if nbins < 10:
            nbins = 10
        if nbins > 5000:
            nbins = 5000

        number_of_points = data.get("number_of_points", 200_000)

        values = self.fcs_file.data[column].to_numpy(dtype=float)
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
        self._require_fcs_loaded()

        calibration_payload = data.get("calibration")
        if not isinstance(calibration_payload, dict):
            raise ValueError('Expected key "calibration" to be a dict.')

        column = data.get("column")
        if not column:
            raise ValueError('Missing required key "column".')
        column = str(column)

        if column not in self.fcs_file.data:
            raise ValueError(f'Column "{column}" not found in FCS data.')

        preview_n = int(data.get("preview_n", 10))
        if preview_n < 1:
            preview_n = 1

        output_column = data.get("output_column", None)
        if output_column is not None:
            output_column = str(output_column).strip()
            if not output_column:
                output_column = None

        if not hasattr(FluorescenceCalibration, "from_dict"):
            raise ValueError("FluorescenceCalibration must implement from_dict().")

        calibration = FluorescenceCalibration.from_dict(calibration_payload)

        uncalibrated = self.fcs_file.data[column].to_numpy(dtype=float)
        calibrated = calibration.calibrate(uncalibrated)

        if output_column is not None:
            if not hasattr(self.fcs_file, "add_column"):
                raise NotImplementedError("FCSFile must implement add_column(name, values) to keep metadata consistent.")
            self.fcs_file.add_column(name=output_column, values=calibrated)

        return {
            "n_points": int(calibrated.size),
            "preview": calibrated[:preview_n].tolist(),
            "output_column": output_column,
        }

    def find_fluorescence_peaks(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Find fluorescence peaks by clustering 1D fluorescence values with SigmaThresholdHDBSCAN.

        Required keys
        - column: str

        Optional keys
        - max_peaks: int (default 10)
        - min_cluster_size: int (default 200)
        - threshold: float (default 0.0)  (passed to SigmaThresholdHDBSCAN as threshold_x)
        - number_of_points: int | None (default 40000)
        - debug: bool (default False)

        Gating optional keys
        - gating_column: str | None
        - gating_threshold: float | None
          If provided, we keep only rows where gating_column >= gating_threshold before clustering.
        """
        self._require_fcs_loaded()

        column = data.get("column")
        if not column:
            raise ValueError('Missing required key "column".')
        column = str(column)

        if column not in self.fcs_file.data:
            raise ValueError(f'Column "{column}" not found in FCS data.')

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

        fluorescence_values = self.fcs_file.data[column].to_numpy(dtype=float)

        if gating_column is not None:
            gating_column = str(gating_column)
            if gating_column not in self.fcs_file.data:
                raise ValueError(f'Gating column "{gating_column}" not found in FCS data.')
            scattering_values = self.fcs_file.data[gating_column].to_numpy(dtype=float)
            gating_threshold_value = float(gating_threshold) if gating_threshold is not None else None
            mask = np.isfinite(fluorescence_values) & np.isfinite(scattering_values)
            if gating_threshold_value is not None and np.isfinite(gating_threshold_value):
                mask = mask & (scattering_values >= gating_threshold_value)
            values = fluorescence_values[mask]
        else:
            values = fluorescence_values[np.isfinite(fluorescence_values)]

        if number_of_points is not None:
            values = values[: int(number_of_points)]

        if values.size == 0:
            return {
                "peak_positions": [],
                "cluster_modes": [],
                "cluster_means": [],
                "cluster_sizes": [],
                "n_points": 0,
            }

        model = SigmaThresholdHDBSCAN()

        labels, means, modes, clean_data, mask = model.fit(
            x=values,
            n_clusters=int(max_peaks),
            threshold_x=float(threshold),
            min_cluster_size=int(min_cluster_size),
            debug=debug,
        )

        labels = np.asarray(labels)
        means = np.asarray(means, dtype=float).squeeze()
        modes = np.asarray(modes, dtype=float).squeeze()

        if modes.size == 0:
            return {
                "peak_positions": [],
                "cluster_modes": [],
                "cluster_means": [],
                "cluster_sizes": [],
                "n_points": int(values.size),
            }

        unique_labels, counts = np.unique(labels[labels >= 0], return_counts=True)
        size_by_label = {int(lab): int(cnt) for lab, cnt in zip(unique_labels, counts)}

        clusters: list[dict[str, Any]] = []
        for idx in range(int(modes.size)):
            mode_val = float(modes[idx]) if idx < modes.size else float("nan")
            if not np.isfinite(mode_val):
                continue

            label = int(idx)
            cluster_size = int(size_by_label.get(label, 0))
            mean_val = float(means[idx]) if idx < means.size and np.isfinite(means[idx]) else float("nan")

            clusters.append({"label": label, "mode": mode_val, "mean": mean_val, "size": cluster_size})

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

    def _require_fcs_loaded(self) -> None:
        if self.fcs_file is None:
            raise RuntimeError("No FCS file loaded in BackEnd. Call set_file() first.")

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


    def export_fluorescence_calibration(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Export calibrated fluorescence as a new column, either by updating the current file
        or by saving a new permanent file.

        Required keys
        - calibration: dict
        - source_path: str | Path  (may be same as currently loaded file)
        - source_column: str
        - new_column: str
        - mode: str  ("update_temp" or "save_new")

        Optional keys
        - export_filename: str (used when mode == "save_new")
        - export_dir: str | Path (used when mode == "save_new"; default cwd/rosettax_exports)
        - overwrite: bool (default False; relevant for save_new)
        """
        self._require_fcs_loaded()

        calibration_payload = data.get("calibration")
        if not isinstance(calibration_payload, dict):
            raise ValueError('Expected key "calibration" to be a dict.')

        source_path = Path(data.get("source_path") or self.file_path)
        if source_path is None:
            raise ValueError('Missing required key "source_path".')

        source_column = data.get("source_column")
        if not source_column:
            raise ValueError('Missing required key "source_column".')
        source_column = str(source_column)

        new_column = data.get("new_column")
        if not new_column:
            raise ValueError('Missing required key "new_column".')
        new_column = str(new_column).strip()
        if not new_column:
            raise ValueError('Key "new_column" must be a non empty string.')

        mode = str(data.get("mode", "save_new")).strip()
        if mode not in {"update_temp", "save_new"}:
            raise ValueError('Key "mode" must be either "update_temp" or "save_new".')

        # Make sure we are operating on the requested file
        if self.file_path is None or self.fcs_file is None or Path(self.file_path) != source_path:
            self.set_file(source_path)

        if source_column not in self.fcs_file.data:
            raise ValueError(f'Column "{source_column}" not found in FCS data.')

        if not hasattr(FluorescenceCalibration, "from_dict"):
            raise ValueError("FluorescenceCalibration must implement from_dict().")
        calibration = FluorescenceCalibration.from_dict(calibration_payload)

        uncalibrated = self.fcs_file.data[source_column].to_numpy(dtype=float)
        calibrated = calibration.calibrate(uncalibrated)

        if not hasattr(self.fcs_file, "add_column"):
            raise NotImplementedError("FCSFile must implement add_column(name, values).")
        self.fcs_file.add_column(name=new_column, values=calibrated)

        overwrite = bool(data.get("overwrite", False))

        if mode == "update_temp":
            tmp_target = source_path.with_suffix(source_path.suffix + ".tmp")
            self.fcs_file.write(str(tmp_target))
            tmp_target.replace(source_path)
            return {
                "exported_path": str(source_path),
                "mode": mode,
                "source_column": source_column,
                "new_column": new_column,
                "n_points": int(np.asarray(calibrated).size),
            }

        export_filename = data.get("export_filename")
        if not export_filename:
            raise ValueError('Missing required key "export_filename" when mode is "save_new".')
        export_filename = str(export_filename).strip()
        if not export_filename:
            raise ValueError('Key "export_filename" must be a non empty string.')

        export_dir = Path(data.get("export_dir") or (Path.cwd() / "rosettax_exports"))
        export_dir.mkdir(parents=True, exist_ok=True)

        target_path = export_dir / export_filename
        if target_path.suffix.lower() != ".fcs":
            target_path = target_path.with_suffix(".fcs")

        if target_path.exists() and not overwrite:
            raise FileExistsError(f"Export target already exists: {target_path}")

        self.fcs_file.write(str(target_path))

        return {
            "exported_path": str(target_path),
            "mode": mode,
            "source_column": source_column,
            "new_column": new_column,
            "n_points": int(np.asarray(calibrated).size),
        }

    @staticmethod
    def _ensure_suffix(path: Path, suffix: str) -> Path:
        if path.suffix.lower() != suffix.lower():
            return path.with_suffix(suffix)
        return path

    def _write_fcs_file(self, target_path: Path) -> None:
        """
        Attempt to persist self.fcs_file to disk.

        This depends on your RosettaX.reader.FCSFile implementation.
        We try a few common method names. If none exist, raise a clear error.
        """
        self._require_fcs_loaded()

        # Keep file_path consistent with where we write
        self.file_path = Path(target_path)

        writer_candidates = [
            ("write", (target_path,)),
            ("save", (target_path,)),
            ("to_file", (target_path,)),
            ("write_fcs", (target_path,)),
        ]

        for method_name, args in writer_candidates:
            method = getattr(self.fcs_file, method_name, None)
            if callable(method):
                method(*args)
                return

        raise NotImplementedError(
            "FCSFile does not expose a writable API. "
            "Implement one of: FCSFile.write(path), FCSFile.save(path), FCSFile.to_file(path), FCSFile.write_fcs(path). "
            "Once FCSFile can write, export_fluorescence_calibration will persist calibrated columns as requested."
        )