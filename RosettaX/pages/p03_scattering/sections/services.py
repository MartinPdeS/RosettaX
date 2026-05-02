# -*- coding: utf-8 -*-

from RosettaX.utils import styling

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
            card_color=styling.get_workflow_page_header_color(),
        ),
        Upload(
            page=page,
            section_number=1,
            card_color=styling.get_workflow_section_color(1),
        ),
        Peaks(
            page=page,
            section_number=2,
            card_color=styling.get_workflow_section_color(2),
        ),
        Model(
            page=page,
            section_number=3,
            card_color=styling.get_workflow_section_color(3),
        ),
        ReferenceTable(
            page=page,
            section_number=4,
            card_color=styling.get_workflow_section_color(4),
        ),
        Calibration(
            page=page,
            section_number=5,
            card_color=styling.get_workflow_section_color(5),
        ),
        Save(
            page=page,
            section_number=6,
            card_color=styling.get_workflow_section_color(6),
        ),
    ]
