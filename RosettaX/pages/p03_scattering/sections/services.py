# -*- coding: utf-8 -*-

from .s00_header import Header
from .s01_upload import Upload
from .s02_peaks import Peaks
from .s03_model import Model
from .s04_table import ReferenceTable
from .s05_calibration import Calibration
from .s06_save import Save


def build_sections(page) -> list:
    """
    Build the ordered scattering page sections.
    """
    return [
        Header(
            page=page,
            card_color="white",
        ),
        Upload(
            page=page,
            section_number=1,
            card_color="pink",
        ),
        Peaks(
            page=page,
            section_number=2,
            card_color="blue",
        ),
        Model(
            page=page,
            section_number=3,
            card_color="orange",
        ),
        ReferenceTable(
            page=page,
            section_number=4,
            card_color="green",
        ),
        Calibration(
            page=page,
            section_number=5,
            card_color="yellow",
        ),
        Save(
            page=page,
            section_number=6,
            card_color="gray",
        ),
    ]
