from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class BackEnd:
    """
    Minimal fluorescence backend adapter used by the shared peak workflow.

    The fluorescence page currently only needs a container that exposes the
    uploaded FCS file path. This class makes that contract explicit.
    """

    fcs_file_path: Optional[str] = None
