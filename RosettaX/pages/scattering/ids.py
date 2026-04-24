# -*- coding: utf-8 -*-
from RosettaX.pages.scattering.sections.s01_upload.ids import UploadSectionIds
from RosettaX.pages.scattering.sections.s02_peaks.ids import PeakSectionIds
from RosettaX.pages.scattering.sections.s03_parameters.ids import ParameterSectionIds
from RosettaX.pages.scattering.sections.s04_calibration.ids import CalibrationSectionIds
from RosettaX.pages.scattering.sections.s05_save.ids import SaveSectionIds


PAGE_NAME = "scattering_calibration"


class Ids:
    """
    Scattering calibration page IDs.

    Each section owns its own ID factory. This keeps the page-level ID namespace
    explicit while avoiding nested string-only classes.
    """

    page_name = PAGE_NAME

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