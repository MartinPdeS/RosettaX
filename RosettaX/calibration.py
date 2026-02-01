import numpy as np
import pandas as pd


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
        MESF
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

    def calibrate(self, intensity: np.ndarray) -> np.ndarray:
        """
        Convert intensity values (a.u.) into MESF using the fitted linear model.
        """
        x = np.asarray(intensity, dtype=float)
        return self.slope * x + self.intercept

    def to_dict(self) -> dict:
        """
        Serialize calibration parameters for storage in Dash (dcc.Store).
        """
        return {"slope": float(self.slope), "intercept": float(self.intercept)}

    @classmethod
    def from_dict(cls, payload: dict) -> "FluorescenceCalibration":
        """
        Reconstruct a calibration from stored parameters.

        Notes
        -----
        This builds an instance without refitting. It is useful when you want the same API.
        """
        obj = cls.__new__(cls)
        obj.slope = float(payload["slope"])
        obj.intercept = float(payload["intercept"])
        obj.intensity = np.array([], dtype=float)
        obj.MESF = np.array([], dtype=float)
        return obj
