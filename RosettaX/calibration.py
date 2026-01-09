import numpy as np



class FluorescenceCalibration:
    def __init__(self, MESF: np.ndarray, intensity: np.ndarray):
        self.MESF = np.asarray(MESF).squeeze()
        self.intensity = np.asarray(intensity).squeeze()

        self.MESF = np.sort(self.MESF)
        self.intensity = np.sort(self.intensity)
        self.slope, self.intercept = np.polyfit(self.intensity, self.MESF, 1)

    def calibrate(self, intensity: np.ndarray) -> np.ndarray:
        """
        Calibrate fluorescence intensity values to molecule counts.

        Parameters
        ----------
        intensity : np.ndarray
            Array of fluorescence intensity values.

        Returns
        -------
        np.ndarray
            Array of calibrated molecule counts.
        """
        return (intensity - self.intercept) / self.slope

    def add_calibration_to_dataframe(self, data: object, column: str) -> object:

        uncalibrated = data.data[column]

        calibrated = self.calibrate(uncalibrated)

        data.data[column + " [calibrated - MESF]"] = calibrated

        data.data.attrs['units'][column + " [calibrated - MESF]"] = "MESF"

        return data

