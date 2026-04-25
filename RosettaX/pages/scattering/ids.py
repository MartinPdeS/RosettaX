# -*- coding: utf-8 -*-
from RosettaX.pages.scattering.sections.s01_upload.ids import UploadSectionIds
from RosettaX.pages.scattering.sections.s02_peaks.ids import PeakSectionIds
from RosettaX.pages.scattering.sections.s03_parameters.ids import ParameterSectionIds
from RosettaX.pages.scattering.sections.s04_calibration.ids import CalibrationSectionIds
from RosettaX.pages.scattering.sections.s05_save.ids import SaveSectionIds


PAGE_NAME = "scattering_calibration"

class Ids:
    page_name = PAGE_NAME

    class State:
        page_state_store = f"{PAGE_NAME}-page-state-store"

    Upload = UploadSectionIds(
        prefix=PAGE_NAME,
    )

    Scattering = PeakSectionIds(
        prefix=PAGE_NAME,
    )

    Parameters = ParameterSectionIds(
        prefix=PAGE_NAME,
    )

    Calibration = CalibrationSectionIds(
        prefix=PAGE_NAME,
    )

    Save = SaveSectionIds(
        prefix=PAGE_NAME,
    )