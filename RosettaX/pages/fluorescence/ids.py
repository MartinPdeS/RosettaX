PAGE_NAME = "fluorescent_calibration"
from RosettaX.pages.fluorescence.sections.s01_upload.ids import UploadSectionIds
from RosettaX.pages.fluorescence.sections.s02_gating.ids import GatingSectionIds
from RosettaX.pages.fluorescence.sections.s03_peaks.ids import PeakSectionIds
from RosettaX.pages.fluorescence.sections.s04_calibration.ids import CalibrationSectionIds
from RosettaX.pages.fluorescence.sections.s05_save.ids import SaveSectionIds

class Ids:
    page_name = PAGE_NAME

    Upload = UploadSectionIds(
        prefix=PAGE_NAME,
    )

    Scattering = GatingSectionIds(
        prefix=PAGE_NAME,
    )

    Fluorescence = PeakSectionIds(
        prefix=PAGE_NAME,
    )

    Calibration = CalibrationSectionIds(
        prefix=PAGE_NAME,
    )

    Save = SaveSectionIds(
        prefix=PAGE_NAME,
    )

    class Sidebar:
        sidebar_store = f"{PAGE_NAME}-sidebar-store"
        sidebar_content = f"{PAGE_NAME}-sidebar-content"
