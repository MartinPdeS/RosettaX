__all__ = [
	"Header",
	"Upload",
	"Peaks",
	"Model",
	"ReferenceTable",
	"Calibration",
	"Save",
]


def __getattr__(name: str):
	if name == "Header":
		from .s00_header.main import Header

		return Header
	if name == "Upload":
		from .s01_upload.main import Upload

		return Upload
	if name == "Peaks":
		from .s02_peaks.main import Peaks

		return Peaks
	if name == "Model":
		from .s03_model.main import Model

		return Model
	if name == "ReferenceTable":
		from .s04_table.main import ReferenceTable

		return ReferenceTable
	if name == "Calibration":
		from .s05_calibration.main import Calibration

		return Calibration
	if name == "Save":
		from .s06_save.main import Save

		return Save

	raise AttributeError(f"module {__name__!r} has no attribute {name!r}")