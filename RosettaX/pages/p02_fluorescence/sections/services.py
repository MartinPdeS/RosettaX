# -*- coding: utf-8 -*-

from .s00_header import Header
from .s01_upload import Upload
from .s02_peaks import Peaks
from .s03_table import ReferenceTable
from .s04_calibration import Calibration
from .s05_save import Save


def build_sections(page) -> list:
    """
    Build the ordered fluorescence page sections.
    """
    return [
        Header(page=page, card_color="white"),
        Upload(page=page, section_number=1, card_color="pink"),
        Peaks(page=page, section_number=2, card_color="blue"),
        ReferenceTable(page=page, section_number=3, card_color="orange"),
        Calibration(page=page, section_number=4, card_color="green"),
        Save(page=page, section_number=5, card_color="gray"),
    ]
