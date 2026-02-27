# -*- coding: utf-8 -*-
from typing import Optional, Any

from pathlib import Path
import numpy as np
import time
import uuid

from RosettaX.utils.reader import FCSFile
from RosettaX.utils.clusterings import SigmaThresholdHDBSCAN
from RosettaX.pages.fluorescence.utils import FluorescenceCalibration


class BackEnd:
    """
    File bound backend for FCS derived operations.

    Responsibilities
    ----------------
    - Manage and validate an FCS file path.
    - Expose detector column names for UI dropdowns.
    - Estimate scattering thresholds for gating.
    - Fit and apply fluorescence calibrations.
    - Export a calibrated file by injecting a new column.
    - Find fluorescence peaks via clustering, optionally after gating.

    Non responsibilities
    --------------------
    - No Dash or UI concepts (no Stores, no callbacks, no components).
    - No caching of large arrays or dataframe views.
    - No long lived open file handles.

    Notes
    -----
    The methods in this class are designed to be called frequently from a web UI.
    Each method opens the file, reads the required data, and closes the file promptly.
    """

    def __init__(self, file_path: Optional[str | Path] = None) -> None:
        """
        Parameters
        ----------
        file_path : Optional[str | Path]
            Optional initial FCS file path. If provided, `set_file` is called.
        """
        self.file_path: Optional[Path] = None
        self.result: Optional[dict[str, Any]] = None

        if file_path is not None:
            self.set_file(file_path)

    def set_file(self, file_path: str | Path) -> None:
        """
        Set and validate the current FCS file path.

        This method validates that the file exists and can be opened. It does not keep the
        file open. A short retry loop is used to tolerate transient OS level locks for
        large files.

        Parameters
        ----------
        file_path : str | Path
            Path to an existing FCS file.

        Raises
        ------
        FileNotFoundError
            If the file does not exist.
        Exception
            Re raises the last exception encountered when opening the file after retries.
        RuntimeError
            If validation fails without an explicit exception.
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File {file_path} does not exist.")

        self.file_path = file_path

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
        """
        Return detector column names from the current FCS file.

        The implementation reads `$PAR` from the TEXT keywords and uses the "Detectors"
        metadata block to retrieve parameter names. If a detector entry lacks a name, a
        fallback like `P{index}` is used.

        Returns
        -------
        list[str]
            Detector names in the order they appear in the file.

        Raises
        ------
        RuntimeError
            If no file is set.
        KeyError, ValueError
            If the FCS metadata is missing expected fields or is malformed.
        """
        self._require_file_path()

        with FCSFile(self.file_path, writable=False) as fcs_file:
            detectors = fcs_file.text["Detectors"]
            num_parameters = int(fcs_file.text["Keywords"]["$PAR"])

            return [str(detectors[index].get("N", f"P{index}")) for index in range(1, num_parameters + 1)]

    def process_scattering(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Dispatch scattering related operations based on the payload.

        Parameters
        ----------
        data : dict[str, Any]
            Payload that must include key "operation".

        Returns
        -------
        dict[str, Any]
            Operation specific response payload.

        Raises
        ------
        ValueError
            If "operation" is missing or unsupported.
        """
        operation = data.get("operation")
        if not operation:
            raise ValueError('Missing required key "operation" in payload.')

        if operation == "estimate_scattering_threshold":
            return self.estimate_scattering_threshold(data)

        raise ValueError(f"Unsupported scattering operation: {operation}")

    def estimate_scattering_threshold(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Estimate a scattering threshold for gating.

        Inputs
        ------
        Required keys
            column : str
                Name of the scattering column.

        Optional keys
            nbins : int
                Histogram bins used for Otsu thresholding. Default 200.
                Clamped to [10, 5000].
            number_of_points : int | None
                If not None, the algorithm uses only the first N finite values.
                Default 200000.

        Algorithm
        ---------
        1) Load column values as float, filter finite values, optionally truncate.
        2) Compute Otsu threshold on a 1D histogram.
        3) Fallback to a robust threshold: median + k * MAD (k = 3.0).
        4) Final fallback to min(values).

        Returns
        -------
        dict[str, Any]
            Payload with:
            - threshold : float
            - method : str
            - n_points : int
            - nbins : int

        Notes
        -----
        If there is insufficient data, this function returns threshold 0.0 with method
        "insufficient_data".
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
        """
        Fit a fluorescence calibration model.

        Inputs
        ------
        The payload can provide calibration points in one of two formats.

        Format A
            MESF : array like
            intensity : array like

        Format B
            table_data : list[dict]
                Table rows that include:
                - "col1" for MESF
                - "col2" for intensity

        Returns
        -------
        dict[str, Any]
            Calibration payload that includes at least:
            - slope : float
            - intercept : float
            - R_squared : float
            - n_points : int

        Raises
        ------
        ValueError
            If the payload is missing inputs or inputs are invalid.
        """
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
        Apply a fluorescence calibration to a column and return a preview.

        This method does not write anything back to disk.
        For writing a new file or updating a temporary file, use `export_fluorescence_calibration`.

        Required keys
        -------------
        calibration : dict
            Calibration payload compatible with `FluorescenceCalibration.from_dict`.
        column : str
            Source column to calibrate.

        Optional keys
        -------------
        preview_n : int
            Number of calibrated values to return as a preview. Default 10.
        output_column : Any
            Passed through to the response for UI convenience.

        Returns
        -------
        dict[str, Any]
            - n_points : int
            - preview : list[float]
            - output_column : Any
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
        Find fluorescence peaks using clustering, optionally after gating.

        Required keys
        -------------
        column : str
            Fluorescence column used for clustering.

        Optional keys
        -------------
        max_peaks : int
            Maximum number of peaks to return. Default 10.
        min_cluster_size : int
            Minimum cluster size for HDBSCAN. Default 200.
        threshold : float
            Threshold on x used by the clustering helper. Default 0.0.
        number_of_points : int | None
            Maximum number of points to read from file. Default 40000.
        debug : bool
            Forwarded to the clustering helper. Default False.

        Gating optional keys
        --------------------
        gating_column : str | None
            Scattering column used for gating.
        gating_threshold : float | None
            Threshold on the gating column. Values below are excluded.

        Returns
        -------
        dict[str, Any]
            - peak_positions : list[float]
                Sorted by mode (ascending). The selection is biased toward larger clusters first.
            - cluster_modes : list[float]
                Same as peak_positions (kept for compatibility).
            - cluster_means : list[float]
                Cluster means aligned with peak_positions.
            - cluster_sizes : list[int]
                Cluster sizes aligned with peak_positions.
            - n_points : int
                Number of points used after filtering and optional gating.

        Notes
        -----
        This implementation assumes the clustering helper returns modes and means in an order
        that matches label indices (0..k-1). If that assumption is false, the clustering helper
        should return explicit label ids aligned with modes and means.
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

        clusters: list[dict[str, Any]] = []
        for idx in range(int(modes.size)):
            mode_val = float(modes[idx])
            if not np.isfinite(mode_val):
                continue

            mean_val = float(means[idx]) if idx < means.size and np.isfinite(means[idx]) else float("nan")

            label = int(idx)
            cluster_size = int(size_by_label.get(label, 0))

            clusters.append({"label": label, "mode": mode_val, "mean": mean_val, "size": cluster_size})

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
        """
        Export a calibrated FCS by injecting a new calibrated column.

        Required keys
        -------------
        calibration : dict
            Calibration payload compatible with `FluorescenceCalibration.from_dict`.
        source_column : str
            Column to calibrate.
        new_column : str
            Name of the new column to write.

        Optional keys
        -------------
        source_path : str | Path | None
            Path to the source file. Defaults to `self.file_path`.
        mode : str
            "update_temp" or "save_new". Default "save_new".
        export_filename : str
            Required only when mode is "save_new".

        Behavior
        --------
        - Reads the full dataframe from the template file (deep copy).
        - Computes calibrated values and writes them as a new column.
        - Builds an FCS payload using the original file as template.

        Returns
        -------
        dict[str, Any]
            If mode is "update_temp":
                - exported_path : str
            If mode is "save_new":
                - exported_bytes : bytes
                - export_name : str
            Always includes:
                - mode, source_column, new_column, n_points, dtype

        Notes
        -----
        This method uses a short retry loop to tolerate transient file locks.
        """
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

        last_exc: Optional[Exception] = None
        for _attempt in range(5):
            try:
                with FCSFile(source_path, writable=False) as template:
                    df = template.dataframe_copy(deep=True)

                    if source_column not in df.columns:
                        raise ValueError(f'Column "{source_column}" not found.')

                    x = np.asarray(df[source_column].to_numpy(copy=False), dtype=float)
                    y = np.asarray(calibration.calibrate(x), dtype=np.float32)

                    df[new_column] = y

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
        """
        Ensure that `self.file_path` is set.

        Raises
        ------
        RuntimeError
            If no file has been set with `set_file`.
        """
        if self.file_path is None:
            raise RuntimeError("No FCS file set in BackEnd. Call set_file() first.")

    @staticmethod
    def _extract_mesf_intensity(data: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
        """
        Extract MESF and intensity arrays from a payload.

        Supported payload formats
        -------------------------
        - Direct arrays:
            MESF and intensity keys
        - Table format:
            table_data key containing row dicts with "col1" (MESF) and "col2" (intensity)

        Validations
        -----------
        - Same length
        - At least 2 points
        - All finite values

        Returns
        -------
        tuple[np.ndarray, np.ndarray]
            (mesf_values, intensity_values)

        Raises
        ------
        ValueError
            If inputs are missing or invalid.
        """
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
        """
        Parse calibration points from a table like structure.

        Parameters
        ----------
        table_data : Any
            Expected to be a list of row dicts containing:
            - "col1" : MESF
            - "col2" : intensity

        Returns
        -------
        tuple[np.ndarray, np.ndarray]
            (mesf_values, intensity_values)

        Raises
        ------
        ValueError
            If the data is not a list or if fewer than 2 valid points are found.
        """
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
        """
        Parse a value into a finite float.

        Parameters
        ----------
        value : Any
            Candidate value (string, int, float, or None).

        Returns
        -------
        Optional[float]
            Finite float if parsable, otherwise None.
        """
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
        """
        Compute a 1D Otsu threshold over a histogram.

        Parameters
        ----------
        values : np.ndarray
            Input values.
        nbins : int
            Number of histogram bins.

        Returns
        -------
        Optional[float]
            Threshold value if computable, otherwise None.
        """
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
        """
        Robust threshold using median and MAD.

        The estimate is:
            threshold = median(values) + k * (1.4826 * MAD)

        Parameters
        ----------
        values : np.ndarray
            Input values.
        k : float
            Scale factor controlling how conservative the threshold is.

        Returns
        -------
        Optional[float]
            Threshold if computable, otherwise None.
        """
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