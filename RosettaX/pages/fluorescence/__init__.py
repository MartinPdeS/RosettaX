from .base import BaseSection, SectionContext
from .load import LoadSection
from .beads import BeadsSection
from .scattering import ScatteringSection
from .fluorescence import FluorescenceSection
from .output import OutputSection
from .save import SaveSection

class Sections:
    BaseSection = BaseSection
    SectionContext = SectionContext
    LoadSection = LoadSection
    BeadsSection = BeadsSection
    ScatteringSection = ScatteringSection
    FluorescenceSection = FluorescenceSection
    OutputSection = OutputSection
    SaveSection = SaveSection