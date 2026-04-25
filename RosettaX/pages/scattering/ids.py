# -*- coding: utf-8 -*-
from RosettaX.workflow.upload.ids import UploadIds as UploadSectionIds
from RosettaX.workflow.save.ids import SaveIds as SaveSectionIds
from RosettaX.pages.scattering.sections.s03_parameters.ids import ParameterSectionIds
from RosettaX.pages.scattering.sections.s04_calibration.ids import CalibrationSectionIds
from RosettaX.workflow.peak.ids import PeakIds


class PeakSectionIds(PeakIds):
    """
    Scattering peak section IDs.
    """

    def __init__(
        self,
        *,
        prefix: str,
    ) -> None:
        super().__init__(
            prefix=prefix,
            namespace="scattering",
        )


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