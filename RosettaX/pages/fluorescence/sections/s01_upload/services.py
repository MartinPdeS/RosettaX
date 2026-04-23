from typing import Any

from dataclasses import dataclass
import dash

@dataclass(frozen=True)
class UploadState:
    uploaded_fcs_path: Any = dash.no_update
    uploaded_filename: Any = dash.no_update
    scattering_detector_options: Any = dash.no_update
    scattering_detector_value: Any = dash.no_update
    fluorescence_detector_options: Any = dash.no_update
    fluorescence_detector_value: Any = dash.no_update
    runtime_config_data: Any = dash.no_update