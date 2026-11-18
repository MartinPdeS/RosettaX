
from .s01_header import Header
from .s02_calibration_picker.main import CalibrationPicker
from .s03_file_picker.main import FilePicker
from .s04_apply.main import Apply
from RosettaX.workflow.calibration_cards import build_workflow_sections

SECTION_TYPES = (CalibrationPicker, FilePicker, Apply,)


def build_sections(page) -> list:
    """Build sections in workflow order and assign their numbers and colors."""
    return build_workflow_sections(
        page=page,
        section_types=SECTION_TYPES,
        header_type=Header,
        header_color=page.header_color,
    )
