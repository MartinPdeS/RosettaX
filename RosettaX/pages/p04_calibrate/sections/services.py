# -*- coding: utf-8 -*-

from .s01_header import Header
from .s02_calibration_picker import CalibrationPicker
from .s03_file_picker import FilePicker
from .s04_apply import Apply


def build_sections(page) -> list:
    """
    Build the ordered apply calibration page sections.
    """
    return [
        Header(
            page=page,
            card_color=page.header_color,
        ),
        CalibrationPicker(
            page=page,
            section_number=1,
            card_color=page.calibration_picker_color,
        ),
        FilePicker(
            page=page,
            section_number=2,
            card_color=page.file_picker_color,
        ),
        Apply(
            page=page,
            section_number=3,
            card_color=page.apply_color,
        ),
    ]
