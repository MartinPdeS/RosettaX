from .s00_header import Header
from .s01_upload import Upload
from .s02_peaks import Peaks
from .s03_model import Model
from .s04_table import ReferenceTable
from .s05_calibration import Calibration
from .s06_save import Save
from RosettaX.utils import styling
from RosettaX.workflow.calibration_cards import build_workflow_sections

SECTION_TYPES = (Upload, Peaks, Model, ReferenceTable, Calibration, Save,)


def build_sections(page) -> list:
    """Build sections in workflow order and assign their numbers and colors."""
    return build_workflow_sections(
        page=page,
        section_types=SECTION_TYPES,
        header_type=Header,
        header_color=styling.get_workflow_page_header_color(),
    )
